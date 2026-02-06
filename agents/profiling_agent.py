# Data Profiling Agent
import pandas as pd
import numpy as np

class DataProfilingAgent:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.total_rows = df.shape[0]
        self.total_cols = df.shape[1]

        self.numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        self.datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()


    #  Dataset Overview
    def dataset_overview(self):
        return {
            "rows": self.total_rows,
            "columns": self.total_cols,
            "numeric_cols": len(self.numeric_cols),
            "categorical_cols": len(self.categorical_cols),
            "datetime_cols": len(self.datetime_cols),
            "duplicate_rows": int(self.df.duplicated().sum())
        }


    # Column Profiling
    def column_profile(self):
        profile = {}

        for col in self.df.columns:
            series = self.df[col]
            missing = series.isnull().sum()
            missing_ratio = round((missing / self.total_rows) * 100, 2)

            col_data = {
                "dtype": str(series.dtype),
                "missing_count": int(missing),
                "missing_ratio_%": missing_ratio,
                "unique_values": int(series.nunique())
            }

            if col in self.numeric_cols:
                col_data.update({
                    "min": series.min(),
                    "max": series.max(),
                    "mean": round(series.mean(), 2),
                    "std": round(series.std(), 2),
                    "outliers": int(self._detect_outliers(series))
                })

            elif col in self.categorical_cols:
                col_data.update({
                    "top_values": series.value_counts().head(5).to_dict(),
                    "cardinality": self._cardinality_level(series)
                })

            elif col in self.datetime_cols:
                col_data.update({
                    "start_date": str(series.min()),
                    "end_date": str(series.max())
                })

            profile[col] = col_data

        return profile

    def _detect_outliers(self, series):
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return ((series < lower) | (series > upper)).sum()

    def _cardinality_level(self, series):
        ratio = series.nunique() / self.total_rows

        if ratio < 0.05:
            return "LOW"
        elif ratio < 0.3:
            return "MEDIUM"
        else:
            return "HIGH"


    # Data Quality Score
    def data_quality_score(self):
        score = 100

        missing_ratio = self.df.isnull().sum().sum() / (self.total_rows * self.total_cols)
        duplicates_ratio = self.df.duplicated().sum() / self.total_rows

        score -= missing_ratio * 40
        score -= duplicates_ratio * 30

        score = max(round(score, 2), 0)

        return {
            "score": score,
            "status": self._quality_label(score)
        }

    def _quality_label(self, score):
        if score > 85:
            return "EXCELLENT"
        elif score > 70:
            return "GOOD"
        elif score > 50:
            return "FAIR"
        else:
            return "POOR"


    # Global Profiling Report
    def generate_report(self):
        return {
            "dataset_overview": self.dataset_overview(),
            "column_profile": self.column_profile(),
            "data_quality": self.data_quality_score()
        }
