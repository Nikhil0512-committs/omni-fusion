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

print("Loading MIMIC-IV historical data...")
df_train = pd.read_parquet('data/processed/historical_train.parquet')
df_val = pd.read_parquet('data/processed/historical_val.parquet')
df_test = pd.read_parquet('data/processed/historical_test.parquet')

target_col = 'hospital_expire_flag'
feature_cols = [c for c in df_train.columns if c != target_col]

X_train = df_train[feature_cols].values.astype(np.float32)
y_train = df_train[target_col].values.astype(np.int64)

X_val = df_val[feature_cols].values.astype(np.float32)
y_val = df_val[target_col].values.astype(np.int64)

# Reshape for GRU: (Batch, Sequence=1, Features)
X_train = X_train[:, np.newaxis, :]
X_val = X_val[:, np.newaxis, :]

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

class HistoricalGRU(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, dropout):
        super().__init__()
        self.gru = nn.GRU(input_size=input_dim, hidden_size=hidden_dim, 
                          num_layers=num_layers, batch_first=True, 
                          dropout=dropout if num_layers > 1 else 0.0)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, 2)
        
    def forward(self, x):
        # x is (Batch, SeqLen, Features)
        out, _ = self.gru(x)
        # Take the output of the last time step
        last_out = out[:, -1, :]
        last_out = self.dropout(last_out)
        return self.fc(last_out)

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

def objective(trial):
    global best_study_loss, best_model_state, best_config, training_history, final_auroc, final_preds
    
    lr = trial.suggest_float('lr', 1e-4, 1e-2, log=True)
    hidden_dim = trial.suggest_categorical('hidden_dim', [32, 64, 128])
    num_layers = trial.suggest_int('num_layers', 1, 2)
    dropout = trial.suggest_float('dropout', 0.1, 0.5)
    
    model = HistoricalGRU(input_dim=X_train.shape[2], hidden_dim=hidden_dim, num_layers=num_layers, dropout=dropout).to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    early_stopping = EarlyStopping(patience=5)
    
    epochs = 30
    local_history = []
    
    for epoch in range(epochs):
        train_loss = train_epoch(model, train_loader, optimizer, criterion)
        val_loss, val_auroc, val_preds, _ = eval_model(model, val_loader, criterion)
        
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
        best_config = {'lr': lr, 'hidden_dim': hidden_dim, 'num_layers': num_layers, 'dropout': dropout, 'input_dim': X_train.shape[2]}
        training_history = local_history
        final_auroc = local_history[-1]['val_auroc']
        final_preds = val_preds
        
    return final_val_loss

print("Starting Optuna HPO...")
optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=10)
print(f"Best Trial config: {study.best_trial.params}")
print(f"BEST VAL AUROC: {final_auroc:.4f}")

# Checkpoint save
checkpoint_path = 'models/checkpoints/historical_branch_best.pt'
config_path = 'models/checkpoints/historical_branch_config.json'
torch.save(best_model_state, checkpoint_path)
with open(config_path, 'w') as f:
    json.dump(best_config, f)
print("Saved best model.")

# Save logs
pd.DataFrame(training_history).to_csv('logs/historical_training_logs.csv', index=False)

# Missing Stream Protocol Check
print("--------------------------------------------------")
print("TESTING MISSING STREAM PROTOCOL (ZERO-VECTOR INPUT)")
print("--------------------------------------------------")
reloaded_model = HistoricalGRU(
    input_dim=best_config['input_dim'],
    hidden_dim=best_config['hidden_dim'],
    num_layers=best_config['num_layers'],
    dropout=best_config['dropout']
).to(device)
reloaded_model.load_state_dict(torch.load(checkpoint_path, weights_only=True, map_location=device))
reloaded_model.eval()

# Create a batch of exact zeroes (e.g., 5 samples)
missing_batch = torch.zeros((5, 1, best_config['input_dim'])).to(device)
with torch.no_grad():
    out = reloaded_model(missing_batch)
    probs = torch.softmax(out, dim=1)

print("Inference on Zero-Vector succeeded.")
print("Output Probabilities (Class 0, Class 1) for missing stream:")
for i in range(5):
    print(f"Sample {i+1}: {probs[i].cpu().numpy()}")

# Checkpoint reload test
X_sample, _ = next(iter(val_loader))
X_sample = X_sample.to(device)
with torch.no_grad():
    out = reloaded_model(X_sample)
print("Checkpoint reload verification successful! Output shape:", out.shape)
