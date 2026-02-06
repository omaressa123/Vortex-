# File Loader Utility
import pandas as pd

def load_file(path):
    if path.endswith(".csv"):
        return pd.read_csv(path)
    elif path.endswith(".xlsx"):
        return pd.read_excel(path)
    elif path.endswith(".json"):
        return pd.read_json(path)
    else:
        raise ValueError("Unsupported file format")
