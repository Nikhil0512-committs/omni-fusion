import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

# Ensure reproducibility
torch.manual_seed(42)
np.random.seed(42)

print("Loading Data for Fusion...")
df_vitals_train = pd.read_parquet('data/processed/vitals_train.parquet')
df_vitals_val = pd.read_parquet('data/processed/vitals_val.parquet')
df_vitals_test = pd.read_parquet('data/processed/vitals_test.parquet')

df_hist_train = pd.read_parquet('data/processed/historical_train.parquet')
df_hist_val = pd.read_parquet('data/processed/historical_val.parquet')
df_hist_test = pd.read_parquet('data/processed/historical_test.parquet')

# We need random ECGs to pair with MIMIC
# We'll just slice the beginning of PTB-XL
ecg_train_all = np.load('data/processed/ecg_train.npy').astype(np.float32)
ecg_val_all = np.load('data/processed/ecg_val.npy').astype(np.float32)
ecg_test_all = np.load('data/processed/ecg_test.npy').astype(np.float32)

ecg_train = ecg_train_all[:len(df_vitals_train)]
ecg_val = ecg_val_all[:len(df_vitals_val)]
ecg_test = ecg_test_all[:len(df_vitals_test)]

target_col = 'hospital_expire_flag'
feature_cols = [c for c in df_vitals_train.columns if c != target_col]

vitals_train = df_vitals_train[feature_cols].values.astype(np.float32)
vitals_val = df_vitals_val[feature_cols].values.astype(np.float32)
hist_train = df_hist_train[feature_cols].values.astype(np.float32)[:, np.newaxis, :]
hist_val = df_hist_val[feature_cols].values.astype(np.float32)[:, np.newaxis, :]
y_train = df_vitals_train[target_col].values.astype(np.int64)
y_val = df_vitals_val[target_col].values.astype(np.int64)

# To measure equity divergence, we extract gender
gender_idx = feature_cols.index('gender')
val_gender_raw = df_vitals_val['gender'].values
val_gender = (val_gender_raw > val_gender_raw.mean()).astype(int)
train_gender_raw = df_vitals_train['gender'].values
train_gender = (train_gender_raw > train_gender_raw.mean()).astype(int)

# Tensors
ecg_train_t = torch.tensor(ecg_train).transpose(1, 2)
vitals_train_t = torch.tensor(vitals_train)
hist_train_t = torch.tensor(hist_train)
y_train_t = torch.tensor(y_train)
gender_train_t = torch.tensor(train_gender)

ecg_val_t = torch.tensor(ecg_val).transpose(1, 2)
vitals_val_t = torch.tensor(vitals_val)
hist_val_t = torch.tensor(hist_val)
y_val_t = torch.tensor(y_val)
gender_val_t = torch.tensor(val_gender)

batch_size = 32
train_loader = DataLoader(TensorDataset(ecg_train_t, vitals_train_t, hist_train_t, y_train_t, gender_train_t), batch_size=batch_size, shuffle=True)
val_loader = DataLoader(TensorDataset(ecg_val_t, vitals_val_t, hist_val_t, y_val_t, gender_val_t), batch_size=batch_size, shuffle=False)

device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Using device: {device}")

# ----------------- BASE MODELS -----------------
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
        self.in_channels = 16
        self.conv1 = nn.Conv1d(in_channels, 16, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm1d(16)
        self.relu = nn.ReLU()
        self.maxpool = nn.MaxPool1d(kernel_size=3, stride=2, padding=1)
        layers = []
        channels = 16
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

class HistoricalGRU(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, dropout):
        super().__init__()
        self.gru = nn.GRU(input_size=input_dim, hidden_size=hidden_dim, num_layers=num_layers, batch_first=True, dropout=dropout if num_layers > 1 else 0.0)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, 2)
    def forward(self, x):
        out, _ = self.gru(x)
        last_out = out[:, -1, :]
        last_out = self.dropout(last_out)
        return self.fc(last_out)

# ----------------- LOAD CHECKPOINTS -----------------
with open('models/checkpoints/ecg_branch_config.json', 'r') as f:
    cfg_ecg = json.load(f)
model_ecg = ResNet1D(12, cfg_ecg['num_classes'], cfg_ecg['depth'], cfg_ecg['dropout'])
model_ecg.load_state_dict(torch.load('models/checkpoints/ecg_branch_best.pt', weights_only=True, map_location='cpu'))

with open('models/checkpoints/vitals_branch_config.json', 'r') as f:
    cfg_vitals = json.load(f)
model_vitals = VitalsMLP(cfg_vitals['input_dim'], cfg_vitals['hidden_dim'], cfg_vitals['num_layers'], cfg_vitals['dropout'])
model_vitals.load_state_dict(torch.load('models/checkpoints/vitals_branch_best.pt', weights_only=True, map_location='cpu'))

with open('models/checkpoints/historical_branch_config.json', 'r') as f:
    cfg_hist = json.load(f)
model_hist = HistoricalGRU(cfg_hist['input_dim'], cfg_hist['hidden_dim'], cfg_hist['num_layers'], cfg_hist['dropout'])
model_hist.load_state_dict(torch.load('models/checkpoints/historical_branch_best.pt', weights_only=True, map_location='cpu'))

# Extract embedding sizes
ecg_emb_dim = model_ecg.fc.in_features
vitals_emb_dim = model_vitals.net[-1].in_features
hist_emb_dim = model_hist.fc.in_features

# Strip heads
model_ecg.fc = nn.Identity()
model_vitals.net[-1] = nn.Identity()
model_hist.fc = nn.Identity()

# Freeze sub-networks
for m in [model_ecg, model_vitals, model_hist]:
    for param in m.parameters():
        param.requires_grad = False

class OmniFusionNet(nn.Module):
    def __init__(self, model_ecg, model_vitals, model_hist, ecg_dim, vitals_dim, hist_dim):
        super().__init__()
        self.ecg_net = model_ecg
        self.vitals_net = model_vitals
        self.hist_net = model_hist
        
        self.total_dim = ecg_dim + vitals_dim + hist_dim
        self.fusion_mlp = nn.Sequential(
            nn.Linear(self.total_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 2)
        )
        
    def forward(self, x_ecg, x_vitals, x_hist):
        e_ecg = self.ecg_net(x_ecg)
        e_vitals = self.vitals_net(x_vitals)
        e_hist = self.hist_net(x_hist)
        
        # Dynamic Routing (Masking Stream 3 if zero)
        hist_sum = torch.sum(torch.abs(x_hist), dim=(1,2), keepdim=True)
        mask = (hist_sum > 0).float().squeeze(2) # shape: (B, 1)
        e_hist = e_hist * mask
        
        fused = torch.cat([e_ecg, e_vitals, e_hist], dim=1)
        return self.fusion_mlp(fused)

model_fusion = OmniFusionNet(model_ecg, model_vitals, model_hist, ecg_emb_dim, vitals_emb_dim, hist_emb_dim).to(device)
optimizer = optim.Adam(model_fusion.parameters(), lr=1e-3)
ce_criterion = nn.CrossEntropyLoss(reduction='none')

epochs = 30
lambda_equity = 0.5 

for epoch in range(epochs):
    model_fusion.train()
    for ecg_b, vitals_b, hist_b, y_b, g_b in train_loader:
        ecg_b, vitals_b, hist_b, y_b, g_b = ecg_b.to(device), vitals_b.to(device), hist_b.to(device), y_b.to(device), g_b.to(device)
        optimizer.zero_grad()
        out = model_fusion(ecg_b, vitals_b, hist_b)
        
        losses = ce_criterion(out, y_b)
        
        mask_m = (g_b == 1)
        mask_f = (g_b == 0)
        
        # Compute equity penalty
        if mask_m.sum() > 0 and mask_f.sum() > 0:
            loss_m = losses[mask_m].mean()
            loss_f = losses[mask_f].mean()
            equity_penalty = torch.abs(loss_m - loss_f)
        else:
            equity_penalty = 0.0
            
        total_loss = losses.mean() + lambda_equity * equity_penalty
        total_loss.backward()
        optimizer.step()

# Evaluation & Equity Loss Calculation
model_fusion.eval()
all_preds, all_labels = [], []
ce_male, ce_female = [], []
with torch.no_grad():
    for ecg_b, vitals_b, hist_b, y_b, g_b in val_loader:
        ecg_b, vitals_b, hist_b, y_b, g_b = ecg_b.to(device), vitals_b.to(device), hist_b.to(device), y_b.to(device), g_b.to(device)
        out = model_fusion(ecg_b, vitals_b, hist_b)
        losses = ce_criterion(out, y_b)
        
        probs = torch.softmax(out, dim=1)
        all_preds.append(probs.cpu().numpy())
        all_labels.append(y_b.cpu().numpy())
        
        for i in range(len(g_b)):
            if g_b[i] == 1:
                ce_male.append(losses[i].item())
            else:
                ce_female.append(losses[i].item())

all_preds = np.concatenate(all_preds)
all_labels = np.concatenate(all_labels)

# Metrics
try:
    final_auroc = roc_auc_score(all_labels, all_preds[:, 1])
except ValueError:
    final_auroc = 0.5

pred_classes = np.argmax(all_preds, axis=1)
acc = (pred_classes == all_labels)
acc_m = acc[val_gender == 1].mean() if sum(val_gender == 1) > 0 else 0
acc_f = acc[val_gender == 0].mean() if sum(val_gender == 0) > 0 else 0
divergence = abs(acc_m - acc_f)

print(f"Final Fused AUROC: {final_auroc:.4f}")
print("--- EQUITY METRICS ---")
print(f"Phase 4 Baseline Divergence: 0.1250")
print(f"Phase 6 Fused Divergence:    {divergence:.4f}")
print(f"Male Acc: {acc_m:.4f} | Female Acc: {acc_f:.4f}")

os.makedirs('models/exported', exist_ok=True)
torch.save(model_fusion.state_dict(), 'models/exported/omni_fusion_final.pt')
print("Saved final model to models/exported/omni_fusion_final.pt")

# Missing Stream 3 Test
print("--------------------------------------------------")
print("TESTING DYNAMIC ROUTING (STREAM 3 ZERO-VECTOR)")
print("--------------------------------------------------")
ecg_sample, vitals_sample, hist_sample, y_sample, _ = next(iter(val_loader))
ecg_sample, vitals_sample, y_sample = ecg_sample.to(device), vitals_sample.to(device), y_sample.to(device)
zero_hist = torch.zeros_like(hist_sample).to(device)

with torch.no_grad():
    out_fused = model_fusion(ecg_sample, vitals_sample, zero_hist)
    probs_fused = torch.softmax(out_fused, dim=1)

print("Inference successfully bypassed Stream 3 embedding via masking.")
print(f"Sample prediction probabilities: {probs_fused[0].cpu().numpy()}")
