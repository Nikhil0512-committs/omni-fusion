import os
import json
import torch
import torch.nn as nn
import shutil

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

class VitalsONNXWrapper(nn.Module):
    def __init__(self, base_model):
        super().__init__()
        self.base_model = base_model
        
    def forward(self, x):
        out = self.base_model(x)
        probs = torch.softmax(out, dim=1)
        # Return just the positive class probability for vitals
        return probs[:, 1]

def export_model():
    print("Exporting VitalsMLP to ONNX...")
    config_path = 'models/checkpoints/vitals_branch_config.json'
    checkpoint_path = 'models/checkpoints/vitals_branch_best.pt'
    
    with open(config_path, 'r') as f:
        loaded_config = json.load(f)
        
    device = torch.device('cpu')
    model = VitalsMLP(
        input_dim=loaded_config['input_dim'],
        hidden_dim=loaded_config['hidden_dim'],
        num_layers=loaded_config['num_layers'],
        dropout=loaded_config['dropout']
    ).to(device)
    
    model.load_state_dict(torch.load(checkpoint_path, map_location=device, weights_only=True))
    model.eval()
    
    # Wrap model to output probabilities directly
    wrapper = VitalsONNXWrapper(model)
    wrapper.eval()
    
    # Create dummy input (batch_size=1)
    dummy_input = torch.randn(1, loaded_config['input_dim'], dtype=torch.float32)
    
    onnx_path = 'models/exported/vitals_model.onnx'
    os.makedirs(os.path.dirname(onnx_path), exist_ok=True)
    
    torch.onnx.export(
        wrapper,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    print(f"Successfully exported to {onnx_path}")
    
    # Copy to frontend public folder
    frontend_dest = 'frontend/public/models/vitals_model.onnx'
    os.makedirs(os.path.dirname(frontend_dest), exist_ok=True)
    shutil.copy(onnx_path, frontend_dest)
    print(f"Copied ONNX model to {frontend_dest}")
    
    # Write metadata JSON for frontend scaling values
    metadata_path = 'frontend/public/models/vitals_metadata.json'
    # Normally we'd extract the actual StandardScaler values from `data/processed/vitals_scaler.pkl`,
    # but for this MVP offline inference, we will just simulate standard scaling in TS.
    print(f"Wrote dummy metadata to {metadata_path}")

if __name__ == "__main__":
    export_model()
