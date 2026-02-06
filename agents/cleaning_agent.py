from sklearn.ensemble import IsolationForest
from sklearn.impute import KNNImputer
import pandas as pd
import numpy as np

class CleaningAgent:
    def __init__(self, rag_system=None):
        self.rag_system = rag_system

    def clean_data(self, df, profile, use_knn=True, use_isolation_forest=True):
        """
        Hybrid Cleaning: Rule-based + LLM/RAG + ML
        """
        cleaned_df = df.copy()
        
        # 1. Consult RAG for high-level rules if available
        # Example: Check if we should delete columns based on domain knowledge
        if self.rag_system:
             # In a real scenario, we would iterate over columns or ask specific questions
             # For now, we apply the general logic but guided by "rules" implicitly
             pass

        # 2. Handle missing values and drop high-missing features
        total_rows = len(cleaned_df)
        
        for col in cleaned_df.columns:
            # Get missing count from profile if available, else calculate
            if isinstance(profile, dict) and col in profile and "missing_count" in profile[col]:
                missing_count = profile[col]["missing_count"]
            else:
                missing_count = cleaned_df[col].isnull().sum()
            
            ratio = missing_count / total_rows if total_rows > 0 else 0
            
            # Rule: If Missing > 40% -> Suggest deletion (Automatic in this agent for now)
            # RAG Check: "If the data is financial -> do not delete the columns"
            # We would simulate this check:
            should_delete = True
            if self.rag_system:
                context = f"Column '{col}' has {ratio*100:.1f}% missing values."
                advice = self.rag_system.get_decision_support(context, f"Should I delete column '{col}'?")
                if "do not delete" in str(advice).lower():
                    should_delete = False

            if ratio > 0.4 and should_delete:
                cleaned_df.drop(columns=[col], inplace=True)
            elif col in cleaned_df.columns:
                if cleaned_df[col].dtype == "object":
                    cleaned_df[col].fillna(cleaned_df[col].mode()[0], inplace=True)
                else:
                    cleaned_df[col].fillna(cleaned_df[col].median(), inplace=True)

        # 3. Use KNNImputer for numeric columns if requested
        if use_knn:
            num_cols = cleaned_df.select_dtypes(include=["number"]).columns
            if len(num_cols) > 0:
                knn_imputer = KNNImputer()
                cleaned_df[num_cols] = knn_imputer.fit_transform(cleaned_df[num_cols])

        # 4. Remove duplicates
        cleaned_df.drop_duplicates(inplace=True)
        
        # 5. Use IsolationForest for outlier detection and removal if requested
        if use_isolation_forest:
            num_cols = cleaned_df.select_dtypes(include=["number"]).columns
            # Only apply if we have enough samples and at least one numeric column
            if len(num_cols) > 0 and len(cleaned_df) > 10:
                # RAG Check for outliers
                # context = "Detecting outliers."
                # advice = self.rag_system.get_decision_support(context, "How to handle outliers in salary?")
                
                iso_forest = IsolationForest(contamination=0.01, random_state=42)
                outliers = iso_forest.fit_predict(cleaned_df[num_cols])
                cleaned_df = cleaned_df[outliers == 1].reset_index(drop=True)

        return cleaned_df
