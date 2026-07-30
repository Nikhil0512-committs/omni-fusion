import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import KNNImputer
import joblib

os.makedirs('data/processed', exist_ok=True)
RANDOM_SEED = 42

print("Processing MIMIC-IV Clinical Demo...")
mimic_hosp = 'data/raw/mimic_iv_demo/mimic-iv-clinical-database-demo-2.2/hosp/'
mimic_icu = 'data/raw/mimic_iv_demo/mimic-iv-clinical-database-demo-2.2/icu/'

# Load patients
patients = pd.read_csv(os.path.join(mimic_hosp, 'patients.csv.gz'))
admissions = pd.read_csv(os.path.join(mimic_hosp, 'admissions.csv.gz'), usecols=['subject_id', 'hospital_expire_flag'])
adm_agg = admissions.groupby('subject_id')['hospital_expire_flag'].max().reset_index()
patients = patients.merge(adm_agg, on='subject_id', how='left')
patients['hospital_expire_flag'] = patients['hospital_expire_flag'].fillna(0).astype(int)

# Load labevents (e.g., Glucose=50931, Potassium=50971, Sodium=50983, Creatinine=50912)
labevents = pd.read_csv(os.path.join(mimic_hosp, 'labevents.csv.gz'))
target_labs = [50931, 50971, 50983, 50912]
labs_filtered = labevents[labevents['itemid'].isin(target_labs)].copy()
labs_pivot = labs_filtered.pivot_table(index='subject_id', columns='itemid', values='valuenum', aggfunc='mean')
labs_pivot.columns = ['Creatinine', 'Glucose', 'Potassium', 'Sodium']

# Load chartevents (Vitals: HR=220045, RR=220210, O2=220277, SBP=220179, DBP=220180)
chartevents = pd.read_csv(os.path.join(mimic_icu, 'chartevents.csv.gz'), usecols=['subject_id', 'itemid', 'valuenum'])
target_vitals = [220045, 220210, 220277, 220179, 220180]
vitals_filtered = chartevents[chartevents['itemid'].isin(target_vitals)].copy()
vitals_pivot = vitals_filtered.pivot_table(index='subject_id', columns='itemid', values='valuenum', aggfunc='mean')
vitals_pivot.columns = ['HR', 'SBP', 'DBP', 'RR', 'O2']

# Merge
df_mimic = patients[['subject_id', 'anchor_age', 'gender', 'hospital_expire_flag']].set_index('subject_id')
df_mimic = df_mimic.join(labs_pivot, how='left').join(vitals_pivot, how='left')
df_mimic['gender'] = (df_mimic['gender'] == 'M').astype(int)

# Median Imputation
for col in df_mimic.columns:
    df_mimic[col] = df_mimic[col].fillna(df_mimic[col].median())

# Split
X_m_train_val, X_m_test = train_test_split(df_mimic, test_size=0.15, random_state=RANDOM_SEED)
X_m_train, X_m_val = train_test_split(X_m_train_val, test_size=0.15/0.85, random_state=RANDOM_SEED)

# Scale only features
features = [c for c in X_m_train.columns if c != 'hospital_expire_flag']
scaler = StandardScaler()
X_m_train_scaled = X_m_train.copy()
X_m_val_scaled = X_m_val.copy()
X_m_test_scaled = X_m_test.copy()

X_m_train_scaled[features] = scaler.fit_transform(X_m_train[features])
X_m_val_scaled[features] = scaler.transform(X_m_val[features])
X_m_test_scaled[features] = scaler.transform(X_m_test[features])

# Save
X_m_train_scaled.to_parquet('data/processed/vitals_train.parquet')
X_m_val_scaled.to_parquet('data/processed/vitals_val.parquet')
X_m_test_scaled.to_parquet('data/processed/vitals_test.parquet')

# Save artifacts for inference
os.makedirs('models/checkpoints', exist_ok=True)
joblib.dump(scaler, 'models/checkpoints/vitals_scaler.pkl')
joblib.dump(features, 'models/checkpoints/vitals_scaler_feature_order.pkl')
print(f"Scaler saved. Mean: {scaler.mean_}, Scale: {scaler.scale_}")

# Export a small representative background sample for SHAP (50 rows from the scaled training set)
X_sample_scaled = X_m_train_scaled[features].head(50).values
np.save('models/checkpoints/shap_background.npy', X_sample_scaled)
print(f"SHAP background saved. Shape: {X_sample_scaled.shape}")

print("MIMIC-IV Shapes:")
print(f"Train: {X_m_train_scaled.shape}")
print(f"Val:   {X_m_val_scaled.shape}")
print(f"Test:  {X_m_test_scaled.shape}")

print("Processing Historical Stream (Optional)...")
df_hist = df_mimic.copy()
# Introduce some missingness to demonstrate KNN
np.random.seed(RANDOM_SEED)
mask = np.random.rand(*df_hist.shape) < 0.2
df_hist[mask] = np.nan

# Split first, then impute to avoid data leakage
X_h_train_val, X_h_test = train_test_split(df_hist, test_size=0.15, random_state=RANDOM_SEED)
X_h_train, X_h_val = train_test_split(X_h_train_val, test_size=0.15/0.85, random_state=RANDOM_SEED)

knn_imputer = KNNImputer(n_neighbors=5)
X_h_train_imp = pd.DataFrame(knn_imputer.fit_transform(X_h_train), columns=X_h_train.columns)
X_h_val_imp = pd.DataFrame(knn_imputer.transform(X_h_val), columns=X_h_val.columns)
X_h_test_imp = pd.DataFrame(knn_imputer.transform(X_h_test), columns=X_h_test.columns)

# Save
X_h_train_imp.to_parquet('data/processed/historical_train.parquet')
X_h_val_imp.to_parquet('data/processed/historical_val.parquet')
X_h_test_imp.to_parquet('data/processed/historical_test.parquet')

# Save KNN imputer for inference
joblib.dump(knn_imputer, 'models/checkpoints/historical_knn_imputer.pkl')
print("KNN imputer saved.")

print("Historical Stream Shapes:")
print(f"Train: {X_h_train_imp.shape}")
print(f"Val:   {X_h_val_imp.shape}")
print(f"Test:  {X_h_test_imp.shape}")
import os
import ast
import zipfile
import pandas as pd
import numpy as np
import wfdb
from scipy.signal import butter, filtfilt
from sklearn.model_selection import train_test_split

RANDOM_SEED = 42

def butter_highpass_filter(data, cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    y = filtfilt(b, a, data, axis=0)
#     return y
# 
# ptbxl_dir = "data/raw/ptbxl/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3/"
# 
# print("Loading PTB-XL metadata...")
# df_ptbxl = pd.read_csv(os.path.join(ptbxl_dir, 'ptbxl_database.csv'), index_col='ecg_id')
# df_ptbxl['scp_codes'] = df_ptbxl.scp_codes.apply(ast.literal_eval)
# 
# agg_df = pd.read_csv(os.path.join(ptbxl_dir, 'scp_statements.csv'), index_col=0)
# agg_df = agg_df[agg_df.diagnostic == 1]
# 
# def agg_diag(y_dic):
#     tmp = []
#     for k in y_dic.keys():
#         if k in agg_df.index:
#             tmp.append(agg_df.loc[k].diagnostic_class)
#     return list(set(tmp))
# 
# df_ptbxl['diagnostic_superclass'] = df_ptbxl.scp_codes.apply(agg_diag)
# 
# # Keep only single-class records to simplify to a multi-class problem instead of multi-label
# df_ptbxl = df_ptbxl[df_ptbxl['diagnostic_superclass'].apply(len) == 1].copy()
# df_ptbxl['diagnostic_superclass'] = df_ptbxl['diagnostic_superclass'].apply(lambda x: x[0])
# 
# # To save memory and time while running locally, let's process 2000 records.
# # (If we do all 16000 it takes a long time and uses 1.6GB of RAM, but the user wants the full dataset!
# # I will process the full 16,244 records to fulfill the user's requirements for Phase 3.)
# print(f"Total records to process: {len(df_ptbxl)}")
# 
# signals = []
# valid_indices = []
# 
# for i, (idx, row) in enumerate(df_ptbxl.iterrows()):
#     if i % 1000 == 0:
#         print(f"Processed {i} / {len(df_ptbxl)} records...")
#     try:
#         record = wfdb.rdrecord(os.path.join(ptbxl_dir, row['filename_lr'])) # 100Hz
#         sig = record.p_signal
#         # Apply baseline wander filter
#         sig_filtered = butter_highpass_filter(sig, cutoff=0.5, fs=100)
#         signals.append(sig_filtered)
#         valid_indices.append(idx)
#     except Exception as e:
#         print(f"Failed to read {idx}: {e}")
# 
# X_ecg = np.array(signals)
# df_valid = df_ptbxl.loc[valid_indices]
# y_ecg = df_valid['diagnostic_superclass'].values
# 
# print("Splitting data...")
# # Split 70/15/15
# X_train_val, X_test, y_train_val, y_test = train_test_split(X_ecg, y_ecg, test_size=0.15, random_state=RANDOM_SEED)
# X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=0.15/0.85, random_state=RANDOM_SEED)
# 
# print("Saving to data/processed/...")
# os.makedirs('data/processed', exist_ok=True)
# np.save('data/processed/ecg_train.npy', X_train)
# np.save('data/processed/ecg_val.npy', X_val)
# np.save('data/processed/ecg_test.npy', X_test)
# np.save('data/processed/y_ecg_train.npy', y_train)
# np.save('data/processed/y_ecg_val.npy', y_val)
# np.save('data/processed/y_ecg_test.npy', y_test)
# 
# print("PTB-XL Shapes:")
# print(f"X_train: {X_train.shape}, y_train: {y_train.shape}")
# print(f"X_val:   {X_val.shape}, y_val: {y_val.shape}")
# print(f"X_test:  {X_test.shape}, y_test: {y_test.shape}")
# print("Phase 1 & 2 fully executed locally.")
