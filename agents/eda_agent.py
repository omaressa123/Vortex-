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
                "mean": round(series.mean(), 2),
                "median": round(series.median(), 2),
                "std": round(series.std(), 2),
                "min": series.min(),
                "max": series.max(),
                "missing": int(series.isnull().sum()),
                "outliers": int(self._count_outliers(series))
            }
        return summary

    def _count_outliers(self, series):
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
                "top_values": series.value_counts().head(5).to_dict(),
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
                "total": round(self.df[col].sum(), 2),
                "average": round(self.df[col].mean(), 2),
                "max": self.df[col].max(),
                "min": self.df[col].min()
            }

        # Growth KPI 
        if self.datetime_cols and self.numeric_cols:
            time_col = self.datetime_cols[0]
            value_col = self.numeric_cols[0]
            temp = self.df.sort_values(time_col)

            first = temp[value_col].iloc[0]
            last = temp[value_col].iloc[-1]

            if first != 0:
                growth = ((last - first) / abs(first)) * 100
                kpis["growth_rate_%"] = round(growth, 2)

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
