"""PyTorch architectures used by the Omni-Fusion inference checkpoint."""

import torch
import torch.nn as nn

class ResBlock1D(nn.Module):
    """Residual 1D convolution block mapping ``(B, C_in, T)`` to ``(B, C_out, T')``."""
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
    """Encode a 12-lead ECG ``(B, 12, 1000)`` into logits or an ECG embedding.

    With its original classifier head this returns raw diagnostic-class logits,
    not a mortality risk score. In ``InferenceService`` the head is replaced by
    identity so the fusion model receives the learned ECG embedding.
    """
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
    """Encode scaled tabular vitals ``(B, features)`` into logits or an embedding."""
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
    """Encode longitudinal features ``(B, visits, features)`` into an embedding."""
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

class OmniFusionNet(nn.Module):
    """Fuse ECG, vitals, and optional-history embeddings into two mortality logits.

    Inputs are ``x_ecg=(B, 12, 1000)``, ``x_vitals=(B, 11)``, and
    ``x_hist=(B, visits, 11)``. Output ``(B, 2)`` contains raw survival and
    hospital-mortality logits; softmax class 1 is the reported risk score.
    """
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
        hist_sum = torch.sum(torch.abs(x_hist), dim=(1,2), keepdim=True)
        mask = (hist_sum > 0).float().squeeze(2)
        e_hist = e_hist * mask
        fused = torch.cat([e_ecg, e_vitals, e_hist], dim=1)
        return self.fusion_mlp(fused)
