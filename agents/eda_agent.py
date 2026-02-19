# EDA & KPI Agent
import pandas as pd
import numpy as np

class EDAAgent:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        self.datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

 
    # Numeric EDA
    def numeric_summary(self):
        summary = {}
        for col in self.numeric_cols:
            series = self.df[col]
            summary[col] = {
                "mean": float(round(series.mean(), 2)),
                "median": float(round(series.median(), 2)),
                "std": float(round(series.std(), 2)),
                "min": float(series.min()),
                "max": float(series.max()),
                "q25": float(series.quantile(0.25)),
                "q75": float(series.quantile(0.75)),
                "outliers": int(self._detect_outliers(series))
            }
        return summary

    def _detect_outliers(self, series):
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return ((series < lower) | (series > upper)).sum()

  
    # Categorical EDA
    def categorical_summary(self):
        summary = {}
        for col in self.categorical_cols:
            series = self.df[col]
            summary[col] = {
                "unique_values": int(series.nunique()),
                "top_values": {str(k): int(v) for k, v in series.value_counts().head(5).to_dict().items()},
                "missing": int(series.isnull().sum())
            }
        return summary


    #Time Series EDA
    def datetime_summary(self):
        summary = {}
        for col in self.datetime_cols:
            series = self.df[col]
            summary[col] = {
                "start_date": str(series.min()),
                "end_date": str(series.max()),
                "range_days": (series.max() - series.min()).days
            }
        return summary

 
    #KPI Generator
    def generate_kpis(self):
        kpis = {}

        for col in self.numeric_cols:
            kpis[col] = {
                "total": float(round(self.df[col].sum(), 2)),
                "average": float(round(self.df[col].mean(), 2)),
                "max": float(self.df[col].max()),
                "min": float(self.df[col].min())
            }

        # Growth KPI 
        if self.datetime_cols and self.numeric_cols:
            time_col = self.datetime_cols[0]
            value_col = self.numeric_cols[0]
            
            # Convert to datetime if needed
            if not pd.api.types.is_datetime64_any_dtype(self.df[time_col]):
                self.df[time_col] = pd.to_datetime(self.df[time_col])
            
            # Group by time period
            time_series = self.df.groupby(self.df[time_col].dt.to_period('M'))[value_col].sum()
            
            if len(time_series) > 1:
                growth = ((time_series.iloc[-1] - time_series.iloc[0]) / time_series.iloc[0]) * 100
                kpis['growth'] = {
                    "percentage": float(round(growth, 2)),
                    "trend": "increasing" if growth > 0 else "decreasing"
                }
        
        return kpis

 
    # Correlation Analysis
    def correlation_matrix(self):
        if len(self.numeric_cols) < 2:
            return None
        return self.df[self.numeric_cols].corr().round(2)

  
   # Global EDA Report
    def generate_report(self):
        report = {
            "numeric_summary": self.numeric_summary(),
            "categorical_summary": self.categorical_summary(),
            "datetime_summary": self.datetime_summary(),
            "kpis": self.generate_kpis(),
            "correlations": self.correlation_matrix().to_dict()
            if self.correlation_matrix() is not None else None
        }
        return report
