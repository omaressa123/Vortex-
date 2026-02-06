import pandas as pd
import numpy as np

# Start with the original data
cleaning_df = df.copy()

print("="*70)
print("INTELLIGENT DATA CLEANING PIPELINE")
print("="*70)

# Track all cleaning actions
cleaning_actions = []

# Store original state
original_shape = cleaning_df.shape
original_dtypes = cleaning_df.dtypes.to_dict()

print(f"\n📊 Original Dataset: {original_shape[0]} rows × {original_shape[1]} columns")

# 1. HANDLE DUPLICATES
print("\n🔍 STEP 1: DUPLICATE DETECTION & REMOVAL")
print("-" * 70)
duplicate_count = cleaning_df.duplicated().sum()
if duplicate_count > 0:
    before_rows = len(cleaning_df)
    cleaning_df = cleaning_df.drop_duplicates()
    removed = before_rows - len(cleaning_df)
    action = f"Removed {removed} duplicate rows"
    cleaning_actions.append(action)
    print(f"✅ {action}")
else:
    print("✅ No duplicates found")
    cleaning_actions.append("No duplicates detected")

# 2. HANDLE MISSING VALUES
print("\n❓ STEP 2: MISSING VALUE TREATMENT")
print("-" * 70)
missing_before = cleaning_df.isnull().sum().sum()

if missing_before > 0:
    print(f"Found {missing_before} missing values")
    
    # Separate columns by type for intelligent imputation
    numeric_cols = cleaning_df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = cleaning_df.select_dtypes(include=['object']).columns.tolist()
    boolean_cols = cleaning_df.select_dtypes(include=['bool']).columns.tolist()
    
    # Handle numeric missing values
    for col in numeric_cols:
        null_count = cleaning_df[col].isnull().sum()
        if null_count > 0:
            # Use median for skewed data, mean for normal distribution
            skewness = cleaning_df[col].dropna().skew()
            if abs(skewness) > 1:
                fill_value = cleaning_df[col].median()
                method = "median"
            else:
                fill_value = cleaning_df[col].mean()
                method = "mean"
            
            cleaning_df[col].fillna(fill_value, inplace=True)
            action = f"Filled {null_count} missing values in '{col}' with {method} ({fill_value:.2f})"
            cleaning_actions.append(action)
            print(f"  ✅ {action}")
    
    # Handle categorical missing values
    for col in categorical_cols:
        null_count = cleaning_df[col].isnull().sum()
        if null_count > 0:
            # Use mode (most frequent value)
            mode_val = cleaning_df[col].mode()[0] if len(cleaning_df[col].mode()) > 0 else 'Unknown'
            cleaning_df[col].fillna(mode_val, inplace=True)
            action = f"Filled {null_count} missing values in '{col}' with mode ('{mode_val}')"
            cleaning_actions.append(action)
            print(f"  ✅ {action}")
    
    # Handle boolean missing values
    for col in boolean_cols:
        null_count = cleaning_df[col].isnull().sum()
        if null_count > 0:
            mode_val = cleaning_df[col].mode()[0] if len(cleaning_df[col].mode()) > 0 else False
            cleaning_df[col].fillna(mode_val, inplace=True)
            action = f"Filled {null_count} missing values in '{col}' with mode ({mode_val})"
            cleaning_actions.append(action)
            print(f"  ✅ {action}")
    
    missing_after = cleaning_df.isnull().sum().sum()
    print(f"\n  📊 Missing values: {missing_before} → {missing_after}")
else:
    print("✅ No missing values found")
    cleaning_actions.append("No missing values detected")

# 3. DATA TYPE CORRECTIONS
print("\n🏷️  STEP 3: DATA TYPE OPTIMIZATION")
print("-" * 70)
type_corrections = 0

for col in cleaning_df.columns:
    original_dtype = cleaning_df[col].dtype
    
    # Try to optimize integer storage
    if cleaning_df[col].dtype in ['int64']:
        col_min = cleaning_df[col].min()
        col_max = cleaning_df[col].max()
        
        if col_min >= 0 and col_max <= 255:
            cleaning_df[col] = cleaning_df[col].astype('uint8')
            action = f"Optimized '{col}': int64 → uint8"
            cleaning_actions.append(action)
            print(f"  ✅ {action}")
            type_corrections += 1
        elif col_min >= -128 and col_max <= 127:
            cleaning_df[col] = cleaning_df[col].astype('int8')
            action = f"Optimized '{col}': int64 → int8"
            cleaning_actions.append(action)
            print(f"  ✅ {action}")
            type_corrections += 1
        elif col_min >= -32768 and col_max <= 32767:
            cleaning_df[col] = cleaning_df[col].astype('int16')
            action = f"Optimized '{col}': int64 → int16"
            cleaning_actions.append(action)
            print(f"  ✅ {action}")
            type_corrections += 1
    
    # Try to optimize float storage
    elif cleaning_df[col].dtype == 'float64':
        col_min = cleaning_df[col].min()
        col_max = cleaning_df[col].max()
        
        # Check if we can use float32
        if col_min > np.finfo(np.float32).min and col_max < np.finfo(np.float32).max:
            cleaning_df[col] = cleaning_df[col].astype('float32')
            action = f"Optimized '{col}': float64 → float32"
            cleaning_actions.append(action)
            print(f"  ✅ {action}")
            type_corrections += 1

if type_corrections == 0:
    print("✅ Data types are already optimal")

# 4. OUTLIER TREATMENT
print("\n🎯 STEP 4: OUTLIER TREATMENT (IQR Method)")
print("-" * 70)
numeric_cols = cleaning_df.select_dtypes(include=['int64', 'int32', 'int16', 'int8', 'uint8', 'float64', 'float32']).columns.tolist()
outliers_treated = 0

for col in numeric_cols:
    _clean_col_data = cleaning_df[col]
    _clean_q1 = _clean_col_data.quantile(0.25)
    _clean_q3 = _clean_col_data.quantile(0.75)
    _clean_iqr = _clean_q3 - _clean_q1
    _clean_lower_bound = _clean_q1 - 1.5 * _clean_iqr
    _clean_upper_bound = _clean_q3 + 1.5 * _clean_iqr
    
    _clean_outlier_mask = (_clean_col_data < _clean_lower_bound) | (_clean_col_data > _clean_upper_bound)
    _clean_outlier_count = _clean_outlier_mask.sum()
    
    if _clean_outlier_count > 0:
        # Cap outliers at boundaries (winsorization)
        cleaning_df.loc[_clean_col_data < _clean_lower_bound, col] = _clean_lower_bound
        cleaning_df.loc[_clean_col_data > _clean_upper_bound, col] = _clean_upper_bound
        
        action = f"Capped {_clean_outlier_count} outliers in '{col}' to range [{_clean_lower_bound:.2f}, {_clean_upper_bound:.2f}]"
        cleaning_actions.append(action)
        print(f"  ✅ {action}")
        outliers_treated += _clean_outlier_count

if outliers_treated == 0:
    print("✅ No outliers detected")
    cleaning_actions.append("No outliers detected")

# 5. CATEGORICAL DATA STANDARDIZATION
print("\n📋 STEP 5: CATEGORICAL DATA STANDARDIZATION")
print("-" * 70)
categorical_cols = cleaning_df.select_dtypes(include=['object']).columns.tolist()
standardizations = 0

for col in categorical_cols:
    # Trim whitespace
    if cleaning_df[col].dtype == 'object':
        before_unique = cleaning_df[col].nunique()
        cleaning_df[col] = cleaning_df[col].str.strip()
        after_unique = cleaning_df[col].nunique()
        
        if before_unique != after_unique:
            action = f"Standardized '{col}': removed whitespace ({before_unique} → {after_unique} unique values)"
            cleaning_actions.append(action)
            print(f"  ✅ {action}")
            standardizations += 1

if standardizations == 0:
    print("✅ Categorical data already standardized")

# 6. FINAL VALIDATION
print("\n✅ STEP 6: FINAL VALIDATION")
print("-" * 70)
final_shape = cleaning_df.shape
final_missing = cleaning_df.isnull().sum().sum()
memory_before = sum([df[col].memory_usage(deep=True) for col in df.columns]) / 1024**2
memory_after = sum([cleaning_df[col].memory_usage(deep=True) for col in cleaning_df.columns]) / 1024**2

print(f"Rows:          {original_shape[0]} → {final_shape[0]} (Δ {final_shape[0] - original_shape[0]})")
print(f"Columns:       {original_shape[1]} → {final_shape[1]} (Δ {final_shape[1] - original_shape[1]})")
print(f"Missing:       {missing_before} → {final_missing}")
print(f"Memory Usage:  {memory_before:.4f} MB → {memory_after:.4f} MB (Δ {memory_after - memory_before:.4f} MB)")

# Generate cleaning summary
print("\n" + "="*70)
print("CLEANING SUMMARY")
print("="*70)
print(f"Total Actions Performed: {len(cleaning_actions)}")
print("\nDetailed Actions:")
for _action_idx, action in enumerate(cleaning_actions, 1):
    print(f"  {_action_idx}. {action}")

print("\n" + "="*70)
print("CLEANED DATA PREVIEW")
print("="*70)
print(cleaning_df.head(10))

print("\n" + "="*70)
print("DATA QUALITY VERIFICATION")
print("="*70)
print(f"✅ Zero missing values: {cleaning_df.isnull().sum().sum() == 0}")
print(f"✅ Zero duplicates: {cleaning_df.duplicated().sum() == 0}")
print(f"✅ Data types optimized: {type_corrections} optimizations applied")
print(f"✅ Outliers treated: {outliers_treated} outliers capped")

# Store cleaned data for downstream use
cleaned_data = cleaning_df.copy()
cleaning_summary = {
    'original_shape': original_shape,
    'final_shape': final_shape,
    'actions': cleaning_actions,
    'missing_values_removed': missing_before,
    'outliers_treated': outliers_treated,
    'type_optimizations': type_corrections,
    'duplicates_removed': duplicate_count
}

print("\n✅ Data cleaning pipeline complete!")
print(f"📊 Cleaned dataset ready: {final_shape[0]} rows × {final_shape[1]} columns")