# Model Checkpoints & Inference Artifacts

This directory contains the necessary artifacts to run the `InferenceService`.

## Required Files for Cold-Start:
- `vitals_scaler.pkl`: StandardScaler fitted on the vitals training set. Used to standardize real-world clinical units to the 0-mean/1-std space the model was trained on.
- `vitals_scaler_feature_order.pkl`: A Python list containing the exact column order expected by the scaler.
- `historical_knn_imputer.pkl`: KNNImputer fitted on the historical training set.
- `shap_background.npy`: A 50-row representative sample of the scaled training data, used as the background reference for the SHAP KernelExplainer.
- `ecg_branch_config.json`, `vitals_branch_config.json`, `historical_branch_config.json`: Architecture configs used to instantiate the individual branch models before fusion.

Do not delete these files. The backend will fail to start if they are missing.
