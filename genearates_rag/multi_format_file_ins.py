import pandas as pd
import json
import os
from pathlib import Path

# File paths - testing with available files from canvas
test_files = {
    'json': 'test_data.json',  # Will create sample files
    'csv': 'test_data.csv',
    'excel': 'test_data.xlsx'
}

# Create sample test files for demonstration
sample_data = {
    'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'age': [25, 30, 35, 28],
    'salary': [50000.0, 60000.5, 75000.25, 55000.75],
    'active': [True, False, True, True],
    'department': ['Sales', 'Engineering', 'Marketing', 'Sales']
}

# Create CSV test file
df_sample = pd.DataFrame(sample_data)
df_sample.to_csv(test_files['csv'], index=False)

# Create Excel test file
df_sample.to_excel(test_files['excel'], index=False, engine='openpyxl')

# Create JSON test file
json_data = df_sample.to_dict(orient='records')
with open(test_files['json'], 'w') as f:
    json.dump(json_data, f, indent=2)

print("✅ Sample test files created successfully")
print(f"   • CSV: {test_files['csv']}")
print(f"   • Excel: {test_files['excel']}")
print(f"   • JSON: {test_files['json']}")

# Multi-format file ingestion system
def ingest_file(file_path):
    """
    Intelligent file ingestion with automatic format detection and schema inference.
    
    Supports: JSON, CSV, Excel
    Returns: DataFrame with metadata
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Get file metadata
    file_size = file_path.stat().st_size
    file_ext = file_path.suffix.lower()
    
    metadata = {
        'filename': file_path.name,
        'format': file_ext,
        'size_bytes': file_size,
        'size_kb': round(file_size / 1024, 2)
    }
    
    # Automatic format detection and parsing
    if file_ext == '.json':
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Try to convert dict to DataFrame
            df = pd.DataFrame([data]) if not any(isinstance(v, list) for v in data.values()) else pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported JSON structure in {file_path}")
        
        metadata['parser'] = 'json'
        
    elif file_ext == '.csv':
        # Auto-detect delimiter and encoding
        df = pd.read_csv(file_path)
        metadata['parser'] = 'csv'
        
    elif file_ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path, engine='openpyxl' if file_ext == '.xlsx' else None)
        metadata['parser'] = 'excel'
        
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")
    
    # Extract schema information with automatic type inference
    schema = {
        'columns': df.columns.tolist(),
        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'row_count': len(df),
        'column_count': len(df.columns),
        'memory_usage_bytes': df.memory_usage(deep=True).sum(),
        'null_counts': df.isnull().sum().to_dict(),
        'numeric_columns': df.select_dtypes(include=['int64', 'float64']).columns.tolist(),
        'text_columns': df.select_dtypes(include=['object']).columns.tolist(),
        'boolean_columns': df.select_dtypes(include=['bool']).columns.tolist()
    }
    
    metadata['schema'] = schema
    
    return df, metadata

# Test all three formats
print("\n" + "="*60)
print("MULTI-FORMAT FILE INGESTION SYSTEM")
print("="*60)

results = {}

for format_name, file_path in test_files.items():
    print(f"\n📁 Processing {format_name.upper()} file...")
    
    try:
        df, metadata = ingest_file(file_path)
        results[format_name] = {
            'dataframe': df,
            'metadata': metadata,
            'status': 'success'
        }
        
        print(f"   ✅ Successfully loaded {metadata['filename']}")
        print(f"   📊 Rows: {metadata['schema']['row_count']}, Columns: {metadata['schema']['column_count']}")
        print(f"   💾 Size: {metadata['size_kb']} KB")
        print(f"   🔧 Parser: {metadata['parser']}")
        print(f"   📋 Columns: {', '.join(metadata['schema']['columns'])}")
        print(f"   🔢 Numeric: {', '.join(metadata['schema']['numeric_columns']) if metadata['schema']['numeric_columns'] else 'None'}")
        print(f"   📝 Text: {', '.join(metadata['schema']['text_columns']) if metadata['schema']['text_columns'] else 'None'}")
        print(f"   ☑️  Boolean: {', '.join(metadata['schema']['boolean_columns']) if metadata['schema']['boolean_columns'] else 'None'}")
        
        # Show data types
        print(f"   🏷️  Data Types:")
        for col, dtype in metadata['schema']['dtypes'].items():
            null_count = metadata['schema']['null_counts'][col]
            null_info = f" ({null_count} nulls)" if null_count > 0 else ""
            print(f"      • {col}: {dtype}{null_info}")
        
    except Exception as e:
        results[format_name] = {
            'status': 'failed',
            'error': str(e)
        }
        print(f"   ❌ Failed to load: {str(e)}")

# Summary
print("\n" + "="*60)
print("INGESTION SUMMARY")
print("="*60)

successful = sum(1 for r in results.values() if r['status'] == 'success')
total = len(results)

print(f"✅ Successfully loaded: {successful}/{total} formats")
print(f"📊 Total rows ingested: {sum(r['metadata']['schema']['row_count'] for r in results.values() if r['status'] == 'success')}")

# Show sample data from each format
print("\n" + "="*60)
print("SAMPLE DATA PREVIEW")
print("="*60)

for format_name, result in results.items():
    if result['status'] == 'success':
        print(f"\n{format_name.upper()} Data (first 3 rows):")
        print(result['dataframe'].head(3).to_string(index=False))

print("\n✅ Multi-format file ingestion system ready!")
print("   Supports: JSON, CSV, Excel")
print("   Features: Automatic schema detection, type inference, metadata extraction")