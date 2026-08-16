import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
import pandas as pd
import optuna
from sklearn.metrics import roc_auc_score

# Ensure reproducibility
torch.manual_seed(42)
np.random.seed(42)

print("Loading MIMIC-IV vitals data...")
df_train = pd.read_parquet('data/processed/vitals_train.parquet')
df_val = pd.read_parquet('data/processed/vitals_val.parquet')
df_test = pd.read_parquet('data/processed/vitals_test.parquet')

# Features and target
target_col = 'hospital_expire_flag'
feature_cols = [c for c in df_train.columns if c != target_col]

X_train = df_train[feature_cols].values.astype(np.float32)
y_train = df_train[target_col].values.astype(np.int64)

X_val = df_val[feature_cols].values.astype(np.float32)
y_val = df_val[target_col].values.astype(np.int64)

# Keep track of val gender for demographic evaluation (gender is 'gender' col)
gender_idx = feature_cols.index('gender')
# Note: gender is scaled! But we can just threshold it at 0. > 0 is M, < 0 is F (if mean is around 0.5)
# Actually, wait, gender in mimic is binary, we shouldn't have scaled it ideally. 
# But let's check unscaled gender from the original df if needed, or just threshold it.
# Let's threshold at 0 since standard scaler centers around mean.
val_gender_raw = df_val['gender'].values
val_gender = (val_gender_raw > val_gender_raw.mean()).astype(int)

X_train_t = torch.tensor(X_train)
y_train_t = torch.tensor(y_train)
X_val_t = torch.tensor(X_val)
y_val_t = torch.tensor(y_val)

batch_size = 32
train_loader = DataLoader(TensorDataset(X_train_t, y_train_t), batch_size=batch_size, shuffle=True)
val_loader = DataLoader(TensorDataset(X_val_t, y_val_t), batch_size=batch_size, shuffle=False)

device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Using device: {device}")

os.makedirs('models/checkpoints', exist_ok=True)
os.makedirs('logs', exist_ok=True)

class VitalsMLP(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, dropout):
        super().__init__()
        layers = []
        in_dim = input_dim
        
        for _ in range(num_layers):
            layers.append(nn.Linear(in_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            in_dim = hidden_dim
            
        layers.append(nn.Linear(in_dim, 2))
        self.net = nn.Sequential(*layers)
        
    def forward(self, x):
        return self.net(x)

class EarlyStopping:
    def __init__(self, patience=5, min_delta=0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False
        
    def __call__(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0

def train_epoch(model, loader, optimizer, criterion):
    model.train()
    total_loss = 0
    for X_b, y_b in loader:
        X_b, y_b = X_b.to(device), y_b.to(device)
        optimizer.zero_grad()
        out = model(X_b)
        loss = criterion(out, y_b)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * X_b.size(0)
    return total_loss / len(loader.dataset)

def eval_model(model, loader, criterion):
    model.eval()
    total_loss = 0
    all_preds, all_labels = [], []
    with torch.no_grad():
        for X_b, y_b in loader:
            X_b, y_b = X_b.to(device), y_b.to(device)
            out = model(X_b)
            loss = criterion(out, y_b)
            total_loss += loss.item() * X_b.size(0)
            
            probs = torch.softmax(out, dim=1)
            all_preds.append(probs.cpu().numpy())
            all_labels.append(y_b.cpu().numpy())
            
    all_preds = np.concatenate(all_preds)
    all_labels = np.concatenate(all_labels)
    try:
        auroc = roc_auc_score(all_labels, all_preds[:, 1])
    except ValueError:
        auroc = 0.5
    
    return total_loss / len(loader.dataset), auroc, all_preds, all_labels

best_study_loss = float('inf')
best_model_state = None
best_config = None
training_history = []
final_auroc = 0
final_preds = None
final_labels = None

def objective(trial):
    global best_study_loss, best_model_state, best_config, training_history, final_auroc, final_preds, final_labels
    
    lr = trial.suggest_float('lr', 1e-4, 1e-2, log=True)
    hidden_dim = trial.suggest_categorical('hidden_dim', [32, 64, 128])
    num_layers = trial.suggest_int('num_layers', 1, 3)
    dropout = trial.suggest_float('dropout', 0.1, 0.5)
    
    model = VitalsMLP(input_dim=X_train.shape[1], hidden_dim=hidden_dim, num_layers=num_layers, dropout=dropout).to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    # The dataset has severe class imbalance (mortality is low). We use pos_weight or just simple CE for baseline.
    criterion = nn.CrossEntropyLoss()
    early_stopping = EarlyStopping(patience=5)
    
    epochs = 30
    local_history = []
    
    for epoch in range(epochs):
        train_loss = train_epoch(model, train_loader, optimizer, criterion)
        val_loss, val_auroc, val_preds, val_labels = eval_model(model, val_loader, criterion)
        
        local_history.append({'epoch': epoch, 'train_loss': train_loss, 'val_loss': val_loss, 'val_auroc': val_auroc})
        
        trial.report(val_loss, epoch)
        if trial.should_prune():
            raise optuna.exceptions.TrialPruned()
            
        early_stopping(val_loss)
        if early_stopping.early_stop:
            break
            
    final_val_loss = local_history[-1]['val_loss']
    
    if final_val_loss < best_study_loss:
        best_study_loss = final_val_loss
        best_model_state = model.state_dict()
        best_config = {'lr': lr, 'hidden_dim': hidden_dim, 'num_layers': num_layers, 'dropout': dropout, 'input_dim': X_train.shape[1]}
        training_history = local_history
        final_auroc = local_history[-1]['val_auroc']
        final_preds = val_preds
        final_labels = val_labels
        
    return final_val_loss

print("Starting Optuna HPO...")
optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=10)
print(f"Best Trial config: {study.best_trial.params}")
print(f"BEST VAL AUROC: {final_auroc:.4f}")

# Demographic evaluation
pred_classes = np.argmax(final_preds, axis=1)
acc = (pred_classes == final_labels)

# Assuming val_gender=1 is Male, 0 is Female
acc_m = acc[val_gender == 1].mean() if sum(val_gender == 1) > 0 else 0
acc_f = acc[val_gender == 0].mean() if sum(val_gender == 0) > 0 else 0

print(f"Validation Accuracy (Male): {acc_m:.4f}")
print(f"Validation Accuracy (Female): {acc_f:.4f}")
print(f"Baseline Gender Accuracy Divergence: {abs(acc_m - acc_f):.4f}")

# Checkpoint save
checkpoint_path = 'models/checkpoints/vitals_branch_best.pt'
config_path = 'models/checkpoints/vitals_branch_config.json'
torch.save(best_model_state, checkpoint_path)
with open(config_path, 'w') as f:
    json.dump(best_config, f)
print("Saved best model.")

# Save logs
pd.DataFrame(training_history).to_csv('logs/vitals_training_logs.csv', index=False)

# Checkpoint reload test
with open(config_path, 'r') as f:
    loaded_config = json.load(f)
reloaded_model = VitalsMLP(
    input_dim=loaded_config['input_dim'],
    hidden_dim=loaded_config['hidden_dim'],
    num_layers=loaded_config['num_layers'],
    dropout=loaded_config['dropout']
).to(device)
reloaded_model.load_state_dict(torch.load(checkpoint_path, weights_only=True, map_location=device))
reloaded_model.eval()

X_sample, _ = next(iter(val_loader))
X_sample = X_sample.to(device)
with torch.no_grad():
    out = reloaded_model(X_sample)
print("Checkpoint reload verification successful! Output shape:", out.shape)
