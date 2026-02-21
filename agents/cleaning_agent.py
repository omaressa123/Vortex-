from sklearn.ensemble import IsolationForest
from sklearn.impute import KNNImputer
from sklearn.linear_model import LinearRegression
import pandas as pd
import numpy as np
from scipy import stats

class CleaningAgent:
    """
    Data Cleaning Agent - Methods-based (No API/LLM required)
    
    Supported cleaning methods:
    1. Statistical/Math methods (Z-score, IQR)
    2. Isolation Forest (anomaly detection)
    3. KNN Imputer (missing value imputation)
    4. Linear Regression (trend-based outlier detection)
    """
    
    def __init__(self):
        self.cleaning_report = {}

    def clean_data(self, df, profile, methods=None):
        """
        Clean data using selected methods.
        
        Args:
            df: pandas DataFrame
            profile: column profile dict from DataProfilingAgent
            methods: dict of methods to apply, e.g.:
                {
                    'handle_missing': True,
                    'remove_duplicates': True,
                    'knn_impute': True,
                    'isolation_forest': True,
                    'linear_regression_outliers': False,
                    'statistical_outliers': True,  # Z-score + IQR
                    'z_score_threshold': 3.0,
                    'iqr_multiplier': 1.5,
                    'isolation_contamination': 0.01
                }
        """
        if methods is None:
            methods = {
                'handle_missing': True,
                'remove_duplicates': True,
                'knn_impute': True,
                'isolation_forest': True,
                'linear_regression_outliers': False,
                'statistical_outliers': True,
                'z_score_threshold': 3.0,
                'iqr_multiplier': 1.5,
                'isolation_contamination': 0.01
            }
        
        cleaned_df = df.copy()
        original_shape = cleaned_df.shape
        self.cleaning_report = {
            'original_rows': original_shape[0],
            'original_cols': original_shape[1],
            'steps': []
        }

        # Step 1: Handle missing values (drop high-missing columns, fill rest)
        if methods.get('handle_missing', True):
            cleaned_df = self._handle_missing_values(cleaned_df, profile)

        # Step 2: Remove duplicates
        if methods.get('remove_duplicates', True):
            before = len(cleaned_df)
            cleaned_df.drop_duplicates(inplace=True)
            removed = before - len(cleaned_df)
            self.cleaning_report['steps'].append({
                'method': 'Remove Duplicates',
                'rows_removed': removed
            })

        # Step 3: KNN Imputation for remaining missing numeric values
        if methods.get('knn_impute', True):
            cleaned_df = self._knn_impute(cleaned_df)

        # Step 4: Statistical outlier detection (Z-score + IQR)
        if methods.get('statistical_outliers', True):
            z_threshold = methods.get('z_score_threshold', 3.0)
            iqr_mult = methods.get('iqr_multiplier', 1.5)
            cleaned_df = self._statistical_outlier_removal(cleaned_df, z_threshold, iqr_mult)

        # Step 5: Isolation Forest outlier detection
        if methods.get('isolation_forest', True):
            contamination = methods.get('isolation_contamination', 0.01)
            cleaned_df = self._isolation_forest_outliers(cleaned_df, contamination)

        # Step 6: Linear Regression trend-based outlier detection
        if methods.get('linear_regression_outliers', False):
            cleaned_df = self._linear_regression_outliers(cleaned_df)

        self.cleaning_report['final_rows'] = len(cleaned_df)
        self.cleaning_report['final_cols'] = len(cleaned_df.columns)
        self.cleaning_report['total_rows_removed'] = original_shape[0] - len(cleaned_df)
        self.cleaning_report['total_cols_removed'] = original_shape[1] - len(cleaned_df.columns)

        return cleaned_df

    def _handle_missing_values(self, df, profile):
        """Handle missing values: drop high-missing columns, fill rest with mode/median"""
        total_rows = len(df)
        cols_dropped = []
        cols_filled = []
        
        for col in df.columns:
            # Get missing count from profile if available
            if isinstance(profile, dict) and col in profile and "missing_count" in profile[col]:
                missing_count = profile[col]["missing_count"]
            else:
                missing_count = df[col].isnull().sum()
            
            ratio = missing_count / total_rows if total_rows > 0 else 0
            
            # If missing > 40% -> drop column
            if ratio > 0.4:
                df.drop(columns=[col], inplace=True)
                cols_dropped.append(col)
            elif col in df.columns and missing_count > 0:
                if df[col].dtype == "object":
                    mode_val = df[col].mode()
                    if len(mode_val) > 0:
                        df[col].fillna(mode_val[0], inplace=True)
                else:
                    df[col].fillna(df[col].median(), inplace=True)
                cols_filled.append(col)
        
        self.cleaning_report['steps'].append({
            'method': 'Handle Missing Values',
            'columns_dropped': cols_dropped,
            'columns_filled': cols_filled
        })
        
        return df

    def _knn_impute(self, df):
        """Use KNN Imputer for remaining missing numeric values"""
        num_cols = df.select_dtypes(include=["number"]).columns
        if len(num_cols) > 0 and df[num_cols].isnull().sum().sum() > 0:
            try:
                knn_imputer = KNNImputer(n_neighbors=5)
                df[num_cols] = knn_imputer.fit_transform(df[num_cols])
                self.cleaning_report['steps'].append({
                    'method': 'KNN Imputation',
                    'columns_imputed': num_cols.tolist()
                })
            except Exception as e:
                self.cleaning_report['steps'].append({
                    'method': 'KNN Imputation',
                    'error': str(e)
                })
        return df

    def _statistical_outlier_removal(self, df, z_threshold=3.0, iqr_multiplier=1.5):
        """Remove outliers using Z-score and IQR methods combined"""
        num_cols = df.select_dtypes(include=["number"]).columns
        if len(num_cols) == 0 or len(df) <= 10:
            return df
        
        before = len(df)
        mask = pd.Series([True] * len(df), index=df.index)
        
        for col in num_cols:
            # Z-score method
            z_scores = np.abs(stats.zscore(df[col].dropna()))
            z_mask = pd.Series([True] * len(df), index=df.index)
            non_null_idx = df[col].dropna().index
            z_mask.loc[non_null_idx] = z_scores < z_threshold
            
            # IQR method
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - iqr_multiplier * iqr
            upper = q3 + iqr_multiplier * iqr
            iqr_mask = (df[col] >= lower) & (df[col] <= upper) | df[col].isna()
            
            # Combined: remove only if BOTH methods flag it
            mask = mask & (z_mask | iqr_mask)
        
        df = df[mask].reset_index(drop=True)
        removed = before - len(df)
        
        self.cleaning_report['steps'].append({
            'method': 'Statistical Outlier Removal (Z-score + IQR)',
            'z_score_threshold': z_threshold,
            'iqr_multiplier': iqr_multiplier,
            'rows_removed': removed
        })
        
        return df

    def _isolation_forest_outliers(self, df, contamination=0.01):
        """Remove outliers using Isolation Forest"""
        num_cols = df.select_dtypes(include=["number"]).columns
        if len(num_cols) == 0 or len(df) <= 10:
            return df
        
        before = len(df)
        try:
            iso_forest = IsolationForest(contamination=contamination, random_state=42)
            outliers = iso_forest.fit_predict(df[num_cols])
            df = df[outliers == 1].reset_index(drop=True)
            removed = before - len(df)
            
            self.cleaning_report['steps'].append({
                'method': 'Isolation Forest',
                'contamination': contamination,
                'rows_removed': removed
            })
        except Exception as e:
            self.cleaning_report['steps'].append({
                'method': 'Isolation Forest',
                'error': str(e)
            })
        
        return df

    def _linear_regression_outliers(self, df, residual_threshold=3.0):
        """
        Detect outliers using Linear Regression residuals.
        For each numeric column pair, fit a linear model and flag points
        with high residuals as outliers.
        """
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if len(num_cols) < 2 or len(df) <= 10:
            return df
        
        before = len(df)
        mask = pd.Series([True] * len(df), index=df.index)
        
        # Use the first numeric column as target, rest as features
        # This catches rows that don't follow the linear trend
        target_col = num_cols[0]
        feature_cols = num_cols[1:]
        
        try:
            X = df[feature_cols].values
            y = df[target_col].values
            
            # Handle any remaining NaN
            valid_mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
            if valid_mask.sum() < 10:
                return df
            
            X_valid = X[valid_mask]
            y_valid = y[valid_mask]
            
            model = LinearRegression()
            model.fit(X_valid, y_valid)
            
            predictions = model.predict(X_valid)
            residuals = np.abs(y_valid - predictions)
            
            # Flag outliers based on residual std
            residual_std = np.std(residuals)
            residual_mean = np.mean(residuals)
            
            if residual_std > 0:
                outlier_flags = residuals > (residual_mean + residual_threshold * residual_std)
                valid_indices = df.index[valid_mask]
                mask.loc[valid_indices[outlier_flags]] = False
            
            df = df[mask].reset_index(drop=True)
            removed = before - len(df)
            
            self.cleaning_report['steps'].append({
                'method': 'Linear Regression Outlier Detection',
                'target_column': target_col,
                'feature_columns': feature_cols,
                'residual_threshold': residual_threshold,
                'rows_removed': removed
            })
        except Exception as e:
            self.cleaning_report['steps'].append({
                'method': 'Linear Regression Outlier Detection',
                'error': str(e)
            })
        
        return df

    def get_cleaning_report(self):
        """Get detailed report of all cleaning steps performed"""
        return self.cleaning_report
