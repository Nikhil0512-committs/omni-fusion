import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
import pandas as pd
import optuna
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import roc_auc_score, roc_curve, auc
import matplotlib.pyplot as plt

print("Loading data...")
X_train = np.load('data/processed/ecg_train.npy').astype(np.float32)
y_train_raw = np.load('data/processed/y_ecg_train.npy', allow_pickle=True)

X_val = np.load('data/processed/ecg_val.npy').astype(np.float32)
y_val_raw = np.load('data/processed/y_ecg_val.npy', allow_pickle=True)

X_test = np.load('data/processed/ecg_test.npy').astype(np.float32)
y_test_raw = np.load('data/processed/y_ecg_test.npy', allow_pickle=True)

le = LabelEncoder()
y_train = le.fit_transform(y_train_raw)
y_val = le.transform(y_val_raw)
y_test = le.transform(y_test_raw)

num_classes = len(le.classes_)

X_train_t = torch.tensor(X_train).transpose(1, 2)
y_train_t = torch.tensor(y_train, dtype=torch.long)
X_val_t = torch.tensor(X_val).transpose(1, 2)
y_val_t = torch.tensor(y_val, dtype=torch.long)

batch_size = 64
train_loader = DataLoader(TensorDataset(X_train_t, y_train_t), batch_size=batch_size, shuffle=True)
val_loader = DataLoader(TensorDataset(X_val_t, y_val_t), batch_size=batch_size, shuffle=False)

# NEW: Use MPS if available, otherwise CPU
device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Using device: {device}")

os.makedirs('models/checkpoints', exist_ok=True)
os.makedirs('logs', exist_ok=True)

class ResBlock1D(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size=5, stride=stride, padding=2, bias=False)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size=5, stride=1, padding=2, bias=False)
        self.bn2 = nn.BatchNorm1d(out_channels)
        
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm1d(out_channels)
            )

    def forward(self, x):
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        return self.relu(out)

class ResNet1D(nn.Module):
    def __init__(self, in_channels, num_classes, depth, dropout):
        super().__init__()
        self.in_channels = 32
        self.conv1 = nn.Conv1d(in_channels, 32, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm1d(32)
        self.relu = nn.ReLU()
        self.maxpool = nn.MaxPool1d(kernel_size=3, stride=2, padding=1)
        
        layers = []
        channels = 32
        for i in range(depth):
            out_channels = channels * 2 if i > 0 else channels
            stride = 2 if i > 0 else 1
            layers.append(ResBlock1D(self.in_channels, out_channels, stride))
            self.in_channels = out_channels
            channels = out_channels
            
        self.layer = nn.Sequential(*layers)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(self.in_channels, num_classes)

    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.maxpool(x)
        x = self.layer(x)
        x = torch.mean(x, dim=2)
        x = self.dropout(x)
        return self.fc(x)

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
        auroc = roc_auc_score(all_labels, all_preds, multi_class='ovr')
    except ValueError:
        auroc = 0.5
    
    return total_loss / len(loader.dataset), auroc, all_preds, all_labels

best_study_loss = float('inf')
best_model_state = None
best_config = None
training_history = []
final_auroc = 0

def objective(trial):
    global best_study_loss, best_model_state, best_config, training_history, final_auroc
    
    lr = trial.suggest_float('lr', 1e-4, 1e-2, log=True)
    depth = trial.suggest_int('depth', 1, 3)
    dropout = trial.suggest_float('dropout', 0.1, 0.5)
    
    model = ResNet1D(in_channels=12, num_classes=num_classes, depth=depth, dropout=dropout).to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    early_stopping = EarlyStopping(patience=5)
    
    epochs = 30
    local_history = []
    
    for epoch in range(epochs):
        train_loss = train_epoch(model, train_loader, optimizer, criterion)
        val_loss, val_auroc, _, _ = eval_model(model, val_loader, criterion)
        
        local_history.append({'epoch': epoch, 'train_loss': train_loss, 'val_loss': val_loss, 'val_auroc': val_auroc})
        print(f"Trial {trial.number} Epoch {epoch}: Train Loss {train_loss:.4f} Val Loss {val_loss:.4f} Val AUROC {val_auroc:.4f}")
        
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
        best_config = {'lr': lr, 'depth': depth, 'dropout': dropout, 'num_classes': num_classes}
        training_history = local_history
        final_auroc = local_history[-1]['val_auroc']
        
    return final_val_loss

print("Starting Optuna HPO...")
optuna.logging.set_verbosity(optuna.logging.INFO)
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=10)
print(f"Best Trial config: {study.best_trial.params}")
print(f"BEST VAL AUROC: {final_auroc}")

# Checkpoint save
checkpoint_path = 'models/checkpoints/ecg_branch_best.pt'
config_path = 'models/checkpoints/ecg_branch_config.json'
torch.save(best_model_state, checkpoint_path)
with open(config_path, 'w') as f:
    json.dump(best_config, f)
print("Saved best model.")

# Save logs
pd.DataFrame(training_history).to_csv('logs/training_logs.csv', index=False)

# Checkpoint reload test
with open(config_path, 'r') as f:
    loaded_config = json.load(f)
reloaded_model = ResNet1D(
    in_channels=12, 
    num_classes=loaded_config['num_classes'], 
    depth=loaded_config['depth'], 
    dropout=loaded_config['dropout']
).to(device)
reloaded_model.load_state_dict(torch.load(checkpoint_path, weights_only=True, map_location=device))
reloaded_model.eval()

X_sample, _ = next(iter(val_loader))
X_sample = X_sample.to(device)
with torch.no_grad():
    out = reloaded_model(X_sample)
print("Checkpoint reload verification successful! Output shape:", out.shape)
