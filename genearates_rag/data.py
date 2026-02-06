import pandas as pd
import numpy as np

# Use the ingested data
profiling_df = df.copy()

print("="*70)
print("COMPREHENSIVE DATA QUALITY PROFILING REPORT")
print("="*70)

# Initialize profiling report
profile_report = {
    'dataset_overview': {},
    'missing_values': {},
    'distributions': {},
    'correlations': {},
    'outliers': {},
    'data_types': {},
    'duplicates': {},
    'recommendations': []
}

# 1. DATASET OVERVIEW
print("\n📊 DATASET OVERVIEW")
print("-" * 70)
profile_report['dataset_overview'] = {
    'total_rows': len(profiling_df),
    'total_columns': len(profiling_df.columns),
    'memory_usage_mb': round(profiling_df.memory_usage(deep=True).sum() / 1024**2, 4),
    'duplicate_rows': profiling_df.duplicated().sum()
}
print(f"Total Rows: {profile_report['dataset_overview']['total_rows']}")
print(f"Total Columns: {profile_report['dataset_overview']['total_columns']}")
print(f"Total Memory Usage: {profile_report['dataset_overview']['memory_usage_mb']} MB")
print(f"Duplicate Rows: {profile_report['dataset_overview']['duplicate_rows']}")

# 2. MISSING VALUES ANALYSIS
print("\n❓ MISSING VALUES ANALYSIS")
print("-" * 70)
missing_stats = []
for col in profiling_df.columns:
    null_count = profiling_df[col].isnull().sum()
    null_pct = (null_count / len(profiling_df)) * 100
    missing_stats.append({
        'column': col,
        'missing_count': null_count,
        'missing_percentage': round(null_pct, 2),
        'data_type': str(profiling_df[col].dtype)
    })
    print(f"{col:20} | Missing: {null_count:4} ({null_pct:5.2f}%) | Type: {profiling_df[col].dtype}")

profile_report['missing_values'] = missing_stats
total_missing = sum(s['missing_count'] for s in missing_stats)
print(f"\nTotal Missing Values: {total_missing}")

# 3. DATA TYPE ANALYSIS
print("\n🏷️  DATA TYPE ANALYSIS")
print("-" * 70)
type_groups = {
    'numeric': profiling_df.select_dtypes(include=['int64', 'float64']).columns.tolist(),
    'categorical': profiling_df.select_dtypes(include=['object']).columns.tolist(),
    'boolean': profiling_df.select_dtypes(include=['bool']).columns.tolist()
}
profile_report['data_types'] = type_groups
print(f"Numeric Columns ({len(type_groups['numeric'])}): {', '.join(type_groups['numeric']) if type_groups['numeric'] else 'None'}")
print(f"Categorical Columns ({len(type_groups['categorical'])}): {', '.join(type_groups['categorical']) if type_groups['categorical'] else 'None'}")
print(f"Boolean Columns ({len(type_groups['boolean'])}): {', '.join(type_groups['boolean']) if type_groups['boolean'] else 'None'}")

# 4. DISTRIBUTION ANALYSIS (Numeric Columns)
print("\n📈 DISTRIBUTION ANALYSIS (Numeric Columns)")
print("-" * 70)
dist_analysis = {}
for col in type_groups['numeric']:
    _prof_col_data = profiling_df[col].dropna()
    if len(_prof_col_data) > 0:
        dist_stats = {
            'mean': round(_prof_col_data.mean(), 2),
            'median': round(_prof_col_data.median(), 2),
            'std': round(_prof_col_data.std(), 2),
            'min': round(_prof_col_data.min(), 2),
            'max': round(_prof_col_data.max(), 2),
            'q1': round(_prof_col_data.quantile(0.25), 2),
            'q3': round(_prof_col_data.quantile(0.75), 2),
            'skewness': round(_prof_col_data.skew(), 2),
            'kurtosis': round(_prof_col_data.kurtosis(), 2)
        }
        dist_analysis[col] = dist_stats
        
        print(f"\n{col}:")
        print(f"  Mean: {dist_stats['mean']:>10} | Median: {dist_stats['median']:>10} | Std: {dist_stats['std']:>10}")
        print(f"  Min:  {dist_stats['min']:>10} | Q1:     {dist_stats['q1']:>10} | Q3:  {dist_stats['q3']:>10} | Max: {dist_stats['max']:>10}")
        print(f"  Skewness: {dist_stats['skewness']:>6} | Kurtosis: {dist_stats['kurtosis']:>6}")

profile_report['distributions'] = dist_analysis

# 5. CORRELATION ANALYSIS
print("\n🔗 CORRELATION ANALYSIS")
print("-" * 70)
if len(type_groups['numeric']) > 1:
    corr_matrix = profiling_df[type_groups['numeric']].corr()
    profile_report['correlations'] = corr_matrix.to_dict()
    
    print("\nCorrelation Matrix:")
    print(corr_matrix.to_string())
    
    # Find high correlations
    high_corr_pairs = []
    for _prof_corr_i in range(len(corr_matrix.columns)):
        for _prof_corr_j in range(_prof_corr_i+1, len(corr_matrix.columns)):
            _prof_corr_val = corr_matrix.iloc[_prof_corr_i, _prof_corr_j]
            if abs(_prof_corr_val) > 0.7:
                high_corr_pairs.append({
                    'var1': corr_matrix.columns[_prof_corr_i],
                    'var2': corr_matrix.columns[_prof_corr_j],
                    'correlation': round(_prof_corr_val, 3)
                })
    
    if high_corr_pairs:
        print(f"\n⚠️  High Correlations (|r| > 0.7): {len(high_corr_pairs)} pairs")
        for pair in high_corr_pairs:
            print(f"  {pair['var1']} ↔ {pair['var2']}: {pair['correlation']}")
    else:
        print("\n✅ No high correlations detected")
else:
    print("Not enough numeric columns for correlation analysis")
    profile_report['correlations'] = {}

# 6. OUTLIER DETECTION (IQR Method)
print("\n🎯 OUTLIER DETECTION (IQR Method)")
print("-" * 70)
outlier_analysis = {}
for col in type_groups['numeric']:
    _prof_col_data = profiling_df[col].dropna()
    if len(_prof_col_data) > 0:
        _prof_q1 = _prof_col_data.quantile(0.25)
        _prof_q3 = _prof_col_data.quantile(0.75)
        _prof_iqr = _prof_q3 - _prof_q1
        _prof_lower_bound = _prof_q1 - 1.5 * _prof_iqr
        _prof_upper_bound = _prof_q3 + 1.5 * _prof_iqr
        
        _prof_outliers = _prof_col_data[(_prof_col_data < _prof_lower_bound) | (_prof_col_data > _prof_upper_bound)]
        _prof_outlier_count = len(_prof_outliers)
        _prof_outlier_pct = (_prof_outlier_count / len(_prof_col_data)) * 100
        
        outlier_analysis[col] = {
            'count': _prof_outlier_count,
            'percentage': round(_prof_outlier_pct, 2),
            'lower_bound': round(_prof_lower_bound, 2),
            'upper_bound': round(_prof_upper_bound, 2),
            'outlier_values': _prof_outliers.tolist() if _prof_outlier_count > 0 else []
        }
        
        _prof_status = f"⚠️  {_prof_outlier_count} outliers ({_prof_outlier_pct:.2f}%)" if _prof_outlier_count > 0 else "✅ No outliers"
        print(f"{col:20} | {_prof_status:30} | Valid range: [{_prof_lower_bound:.2f}, {_prof_upper_bound:.2f}]")

profile_report['outliers'] = outlier_analysis

# 7. CATEGORICAL ANALYSIS
print("\n📋 CATEGORICAL ANALYSIS")
print("-" * 70)
cat_analysis = {}
for col in type_groups['categorical']:
    _prof_value_counts = profiling_df[col].value_counts()
    unique_count = len(_prof_value_counts)
    cat_analysis[col] = {
        'unique_values': unique_count,
        'top_values': _prof_value_counts.head(5).to_dict(),
        'cardinality': 'high' if unique_count > len(profiling_df) * 0.5 else 'low'
    }
    print(f"\n{col}:")
    print(f"  Unique Values: {unique_count}")
    print(f"  Top Values:")
    for _prof_val, _prof_count in _prof_value_counts.head(5).items():
        _prof_pct = (_prof_count / len(profiling_df)) * 100
        print(f"    {str(_prof_val):15} : {_prof_count:3} ({_prof_pct:5.2f}%)")

profile_report['categorical_analysis'] = cat_analysis

# 8. GENERATE CLEANING RECOMMENDATIONS
print("\n💡 DATA CLEANING RECOMMENDATIONS")
print("-" * 70)
recommendations = []

# Check for missing values
total_missing_pct = (total_missing / (len(profiling_df) * len(profiling_df.columns))) * 100
if total_missing > 0:
    recommendations.append(f"Handle {total_missing} missing values ({total_missing_pct:.2f}% of dataset)")

# Check for duplicates
if profile_report['dataset_overview']['duplicate_rows'] > 0:
    recommendations.append(f"Remove {profile_report['dataset_overview']['duplicate_rows']} duplicate rows")

# Check for outliers
total_outliers = sum(v['count'] for v in outlier_analysis.values())
if total_outliers > 0:
    recommendations.append(f"Investigate {total_outliers} outliers across numeric columns")

# Check for high cardinality categoricals
high_card_cols = [col for col, stats in cat_analysis.items() if stats['cardinality'] == 'high']
if high_card_cols:
    recommendations.append(f"Review high cardinality categorical columns: {', '.join(high_card_cols)}")

# Check for potential type corrections
for col in profiling_df.columns:
    if profiling_df[col].dtype == 'object':
        # Check if it could be numeric
        sample_vals = profiling_df[col].dropna()
        if len(sample_vals) > 0:
            try:
                pd.to_numeric(sample_vals, errors='raise')
                recommendations.append(f"Column '{col}' could be converted to numeric type")
            except:
                pass

if not recommendations:
    recommendations.append("✅ Dataset appears clean - no major issues detected")

profile_report['recommendations'] = recommendations

for _prof_rec_idx, rec in enumerate(recommendations, 1):
    print(f"{_prof_rec_idx}. {rec}")

print("\n" + "="*70)
print("PROFILING COMPLETE")
print("="*70)
print(f"✅ Generated comprehensive data quality report")
print(f"📊 Analyzed {len(profiling_df)} rows across {len(profiling_df.columns)} columns")
print(f"💡 Generated {len(recommendations)} cleaning recommendations")