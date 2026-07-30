import uuid
import pandas as pd
import io
import json
from sklearn.impute import KNNImputer
from app.core.supabase_client import supabase

class HistoricalService:
    """Parse, impute, persist, and aggregate historical CSV uploads.

    Values returned by this service remain in raw clinical units. Scaling is
    applied exclusively in ``InferenceService.predict``.
    """
    def process_csv_upload(self, csv_bytes: bytes) -> dict:
        """Process CSV bytes and return a persisted upload-session summary."""
        try:
            df = pd.read_csv(io.BytesIO(csv_bytes))
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")
        
        row_count = len(df)
        if row_count == 0:
            raise ValueError("CSV is empty.")
            
        missing_before = df.isnull().sum().to_dict()
        
        # Imputation logic
        numeric_df = df.select_dtypes(include=['number'])
        imputation_method = "knn"
        
        if len(numeric_df.columns) > 0:
            if row_count < 3:
                # Fallback to mean imputation if possible, else skip
                if row_count > 1:
                    df[numeric_df.columns] = numeric_df.fillna(numeric_df.mean())
                    imputation_method = "mean_fallback_low_n"
                else:
                    imputation_method = "none_fallback_low_n"
            else:
                n_neighbors = min(5, row_count)
                imputer = KNNImputer(n_neighbors=n_neighbors)
                imputed_arr = imputer.fit_transform(numeric_df)
                df[numeric_df.columns] = imputed_arr
            
        missing_after = df.isnull().sum().to_dict()
        
        imputation_summary = {
            col: int(missing_before[col] - missing_after.get(col, 0))
            for col in missing_before if missing_before[col] > 0
        }
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Imputation method used: {imputation_method}")
        session_id = str(uuid.uuid4())
        
        # Insert into upload_sessions
        supabase.table('upload_sessions').insert({
            'id': session_id,
            'source_filename': 'uploaded.csv',
            'row_count': row_count,
            'imputation_summary': imputation_summary,
            'status': 'PROCESSED'
        }).execute()
        
        # Calculate means for the required feature columns to use as historical baseline
        feature_cols = ['anchor_age', 'gender', 'Creatinine', 'Glucose', 'Potassium', 'Sodium', 'HR', 'SBP', 'DBP', 'RR', 'O2']
        aggregated_data = {}
        for col in feature_cols:
            if col in df.columns:
                aggregated_data[col] = float(df[col].mean())
            else:
                aggregated_data[col] = 0.0

        return {
            "session_id": session_id,
            "row_count": row_count,
            "imputation_summary": imputation_summary,
            "status": "PROCESSED",
            "aggregated_data": aggregated_data
        }

historical_service = HistoricalService()
