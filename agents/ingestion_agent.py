import pandas as pd
import os

class IngestionAgent:
    def __init__(self):
        self.supported_extensions = ['.csv', '.xlsx', '.xls', '.json']

    def load_file(self, uploaded_file):
        """
        Load a file from a Streamlit UploadedFile object or a file path.
        """
        if uploaded_file is None:
            return None

        # Check if it's a Streamlit UploadedFile (has 'name' attribute)
        try:
            filename = uploaded_file.name
        except AttributeError:
            # Assume it's a file path string
            filename = uploaded_file

        ext = os.path.splitext(filename)[1].lower()

        if ext not in self.supported_extensions:
            raise ValueError(f"Unsupported file format: {ext}. Supported: {self.supported_extensions}")

        try:
            if ext == '.csv':
                return pd.read_csv(uploaded_file)
            elif ext in ['.xlsx', '.xls']:
                return pd.read_excel(uploaded_file)
            elif ext == '.json':
                return pd.read_json(uploaded_file)
        except Exception as e:
            raise ValueError(f"Error loading file: {str(e)}")
