import pandas as pd
import numpy as np
from scipy import stats

# Use cleaned data for EDA
eda_df = cleaned_data.copy()

print("="*80)
print("COMPREHENSIVE EXPLORATORY DATA ANALYSIS (EDA)")
print("="*80)

# ============================================================================
# 1. DATASET OVERVIEW
# ============================================================================
print("\n📊 SECTION 1: DATASET OVERVIEW")
print("-"*80)
print(f"Dataset Shape: {eda_df.shape[0]} rows × {eda_df.shape[1]} columns")
print(f"Total Data Points: {eda_df.shape[0] * eda_df.shape[1]}")
print(f"Memory Usage: {eda_df.memory_usage(deep=True).sum() / 1024:.2f} KB")

print("\n📋 Column Information:")
for col in eda_df.columns:
    dtype = eda_df[col].dtype
    unique = eda_df[col].nunique()
    missing = eda_df[col].isnull().sum()
    print(f"  • {col:15s} | Type: {str(dtype):10s} | Unique: {unique:3d} | Missing: {missing}")

# ============================================================================
# 2. STATISTICAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("📈 SECTION 2: STATISTICAL SUMMARY")
print("-"*80)

# Separate numeric and categorical columns
numeric_cols = eda_df.select_dtypes(include=[np.number]).columns.tolist()
categorical_cols = eda_df.select_dtypes(include=['object', 'bool']).columns.tolist()

print(f"\nNumeric Features ({len(numeric_cols)}): {', '.join(numeric_cols)}")
print(f"Categorical Features ({len(categorical_cols)}): {', '.join(categorical_cols)}")

# Detailed numeric statistics
if len(numeric_cols) > 0:
    print("\n📊 NUMERIC FEATURE STATISTICS:")
    print("-"*80)
    
    for col in numeric_cols:
        data = eda_df[col]
        
        print(f"\n{col.upper()}:")
        print(f"  Count:        {data.count()}")
        print(f"  Mean:         {data.mean():.2f}")
        print(f"  Median:       {data.median():.2f}")
        print(f"  Std Dev:      {data.std():.2f}")
        print(f"  Min:          {data.min():.2f}")
        print(f"  25th %ile:    {data.quantile(0.25):.2f}")
        print(f"  75th %ile:    {data.quantile(0.75):.2f}")
        print(f"  Max:          {data.max():.2f}")
        print(f"  Range:        {data.max() - data.min():.2f}")
        print(f"  IQR:          {data.quantile(0.75) - data.quantile(0.25):.2f}")
        print(f"  Variance:     {data.var():.2f}")
        print(f"  Skewness:     {data.skew():.4f} {'(Right-skewed)' if data.skew() > 0 else '(Left-skewed)' if data.skew() < 0 else '(Symmetric)'}")
        print(f"  Kurtosis:     {data.kurtosis():.4f} {'(Heavy-tailed)' if data.kurtosis() > 0 else '(Light-tailed)'}")
        
        # Coefficient of variation
        cv = (data.std() / data.mean() * 100) if data.mean() != 0 else 0
        print(f"  CV:           {cv:.2f}% {'(High variability)' if cv > 30 else '(Moderate variability)' if cv > 15 else '(Low variability)'}")

# Categorical statistics
if len(categorical_cols) > 0:
    print("\n" + "="*80)
    print("📋 CATEGORICAL FEATURE STATISTICS:")
    print("-"*80)
    
    for col in categorical_cols:
        print(f"\n{col.upper()}:")
        print(f"  Unique Values: {eda_df[col].nunique()}")
        print(f"  Most Common:   {eda_df[col].mode()[0]} (appears {(eda_df[col] == eda_df[col].mode()[0]).sum()} times, {(eda_df[col] == eda_df[col].mode()[0]).sum() / len(eda_df) * 100:.1f}%)")
        
        print(f"\n  Value Distribution:")
        _eda_value_counts = eda_df[col].value_counts()
        for val, count in _eda_value_counts.items():
            pct = count / len(eda_df) * 100
            bar = "█" * int(pct / 5)
            print(f"    {str(val):15s}: {count:3d} ({pct:5.1f}%) {bar}")

# ============================================================================
# 3. CORRELATION ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("🔗 SECTION 3: CORRELATION ANALYSIS")
print("-"*80)

if len(numeric_cols) >= 2:
    eda_corr_matrix = eda_df[numeric_cols].corr()
    
    print("\nCorrelation Matrix:")
    print(eda_corr_matrix.to_string())
    
    # Find strong correlations (above 0.7 or below -0.7)
    print("\n🔍 Strong Correlations (|r| > 0.7):")
    strong_corrs = []
    for _corr_i in range(len(eda_corr_matrix.columns)):
        for _corr_j in range(_corr_i+1, len(eda_corr_matrix.columns)):
            corr_val = eda_corr_matrix.iloc[_corr_i, _corr_j]
            if abs(corr_val) > 0.7:
                col1 = eda_corr_matrix.columns[_corr_i]
                col2 = eda_corr_matrix.columns[_corr_j]
                strength = "Very Strong" if abs(corr_val) > 0.9 else "Strong"
                direction = "Positive" if corr_val > 0 else "Negative"
                print(f"  • {col1} ↔ {col2}: {corr_val:.4f} ({strength} {direction})")
                strong_corrs.append({'col1': col1, 'col2': col2, 'correlation': corr_val})
    
    if len(strong_corrs) == 0:
        print("  No strong correlations found")
else:
    print("\nInsufficient numeric features for correlation analysis")
    eda_corr_matrix = pd.DataFrame()
    strong_corrs = []

# ============================================================================
# 4. DISTRIBUTION ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("📊 SECTION 4: DISTRIBUTION ANALYSIS")
print("-"*80)

distribution_insights = {}

for col in numeric_cols:
    data = eda_df[col]
    
    # Normality test (Shapiro-Wilk)
    if len(data) >= 3:
        stat, p_value = stats.shapiro(data)
        is_normal = p_value > 0.05
        
        distribution_insights[col] = {
            'normality_test_statistic': stat,
            'normality_p_value': p_value,
            'is_normal': is_normal,
            'skewness': data.skew(),
            'kurtosis': data.kurtosis()
        }
        
        print(f"\n{col.upper()}:")
        print(f"  Shapiro-Wilk Test: W={stat:.4f}, p={p_value:.4f}")
        print(f"  Distribution: {'Normal' if is_normal else 'Non-normal'} (α=0.05)")
        print(f"  Skewness: {data.skew():.4f}")
        print(f"  Kurtosis: {data.kurtosis():.4f}")

# ============================================================================
# 5. HR/EMPLOYEE DOMAIN-SPECIFIC KPIs
# ============================================================================
print("\n" + "="*80)
print("📌 SECTION 5: DOMAIN-SPECIFIC KEY PERFORMANCE INDICATORS (KPIs)")
print("-"*80)

# Detect domain based on column names
print("\n🏢 DOMAIN IDENTIFIED: Human Resources / Employee Analytics")
print("\nCalculating HR-specific KPIs...\n")

kpis = {}

# KPI 1: Workforce Size
kpis['total_employees'] = len(eda_df)
print(f"1. Total Workforce: {kpis['total_employees']} employees")

# KPI 2: Average Employee Age
if 'age' in eda_df.columns:
    kpis['avg_age'] = eda_df['age'].mean()
    kpis['median_age'] = eda_df['age'].median()
    print(f"2. Average Employee Age: {kpis['avg_age']:.1f} years")
    print(f"   Median Employee Age: {kpis['median_age']:.1f} years")

# KPI 3: Average Compensation
if 'salary' in eda_df.columns:
    kpis['avg_salary'] = eda_df['salary'].mean()
    kpis['median_salary'] = eda_df['salary'].median()
    kpis['total_payroll'] = eda_df['salary'].sum()
    print(f"3. Average Salary: ${kpis['avg_salary']:,.2f}")
    print(f"   Median Salary: ${kpis['median_salary']:,.2f}")
    print(f"   Total Annual Payroll: ${kpis['total_payroll']:,.2f}")
    
    # Salary range and distribution
    kpis['salary_range'] = eda_df['salary'].max() - eda_df['salary'].min()
    kpis['salary_std'] = eda_df['salary'].std()
    print(f"   Salary Range: ${kpis['salary_range']:,.2f}")
    print(f"   Salary Std Dev: ${kpis['salary_std']:,.2f}")

# KPI 4: Employee Activity Rate
if 'active' in eda_df.columns:
    kpis['active_employees'] = eda_df['active'].sum() if eda_df['active'].dtype == bool else (eda_df['active'] == True).sum()
    kpis['inactive_employees'] = kpis['total_employees'] - kpis['active_employees']
    kpis['activity_rate'] = (kpis['active_employees'] / kpis['total_employees']) * 100
    kpis['attrition_rate'] = (kpis['inactive_employees'] / kpis['total_employees']) * 100
    print(f"4. Active Employees: {kpis['active_employees']} ({kpis['activity_rate']:.1f}%)")
    print(f"   Inactive Employees: {kpis['inactive_employees']} ({kpis['attrition_rate']:.1f}%)")
    print(f"   Attrition Rate: {kpis['attrition_rate']:.1f}%")

# KPI 5: Department Distribution
if 'department' in eda_df.columns:
    dept_counts = eda_df['department'].value_counts()
    kpis['departments'] = len(dept_counts)
    kpis['largest_department'] = dept_counts.index[0]
    kpis['largest_dept_size'] = dept_counts.iloc[0]
    kpis['dept_concentration'] = (kpis['largest_dept_size'] / kpis['total_employees']) * 100
    
    print(f"5. Number of Departments: {kpis['departments']}")
    print(f"   Largest Department: {kpis['largest_department']} ({kpis['largest_dept_size']} employees, {kpis['dept_concentration']:.1f}%)")
    print(f"\n   Department Breakdown:")
    for dept, count in dept_counts.items():
        pct = (count / kpis['total_employees']) * 100
        print(f"     • {dept}: {count} employees ({pct:.1f}%)")
    
    # Department-specific salary analysis
    if 'salary' in eda_df.columns:
        print(f"\n   Average Salary by Department:")
        dept_salary = eda_df.groupby('department')['salary'].agg(['mean', 'median', 'count'])
        for dept in dept_salary.index:
            avg = dept_salary.loc[dept, 'mean']
            med = dept_salary.loc[dept, 'median']
            cnt = dept_salary.loc[dept, 'count']
            print(f"     • {dept}: ${avg:,.2f} (median: ${med:,.2f}, n={int(cnt)})")

# KPI 6: Age-Salary Relationship
if 'age' in eda_df.columns and 'salary' in eda_df.columns:
    age_salary_corr = eda_df[['age', 'salary']].corr().iloc[0, 1]
    kpis['age_salary_correlation'] = age_salary_corr
    print(f"\n6. Age-Salary Correlation: {age_salary_corr:.4f}")
    if abs(age_salary_corr) > 0.7:
        print(f"   → Strong {'positive' if age_salary_corr > 0 else 'negative'} relationship")
    elif abs(age_salary_corr) > 0.4:
        print(f"   → Moderate {'positive' if age_salary_corr > 0 else 'negative'} relationship")
    else:
        print(f"   → Weak relationship")

# KPI 7: Compensation Equity Ratio (highest to lowest salary)
if 'salary' in eda_df.columns:
    kpis['compensation_equity_ratio'] = eda_df['salary'].max() / eda_df['salary'].min()
    print(f"\n7. Compensation Equity Ratio: {kpis['compensation_equity_ratio']:.2f}:1")
    print(f"   (Highest salary is {kpis['compensation_equity_ratio']:.2f}x the lowest)")

# ============================================================================
# 6. KEY INSIGHTS & RECOMMENDATIONS
# ============================================================================
print("\n" + "="*80)
print("💡 SECTION 6: KEY INSIGHTS & RECOMMENDATIONS")
print("-"*80)

insights = []

# Workforce insights
insights.append(f"Small workforce of {kpis['total_employees']} employees with {kpis['departments']} departments")

# Age insights
if 'age' in eda_df.columns:
    if kpis['avg_age'] < 30:
        insights.append(f"Young workforce (avg age {kpis['avg_age']:.1f}) - focus on career development and growth opportunities")
    elif kpis['avg_age'] > 45:
        insights.append(f"Mature workforce (avg age {kpis['avg_age']:.1f}) - consider succession planning and knowledge transfer")
    else:
        insights.append(f"Balanced age distribution (avg {kpis['avg_age']:.1f} years)")

# Salary insights
if 'salary' in eda_df.columns:
    cv = (kpis['salary_std'] / kpis['avg_salary']) * 100
    if cv > 20:
        insights.append(f"High salary variation (CV={cv:.1f}%) - review compensation structure for equity")
    
    if kpis['compensation_equity_ratio'] > 2:
        insights.append(f"Significant pay disparity ({kpis['compensation_equity_ratio']:.1f}:1 ratio) - monitor for fairness")

# Attrition insights
if 'active' in eda_df.columns:
    if kpis['attrition_rate'] > 20:
        insights.append(f"HIGH attrition rate ({kpis['attrition_rate']:.1f}%) - investigate retention issues urgently")
    elif kpis['attrition_rate'] > 10:
        insights.append(f"Moderate attrition rate ({kpis['attrition_rate']:.1f}%) - monitor employee satisfaction")
    else:
        insights.append(f"Low attrition rate ({kpis['attrition_rate']:.1f}%) - good retention performance")

# Department concentration
if 'department' in eda_df.columns:
    if kpis['dept_concentration'] > 50:
        insights.append(f"Heavy concentration in {kpis['largest_department']} ({kpis['dept_concentration']:.1f}%) - diversification may reduce organizational risk")

print("\n🔍 Key Insights:")
for _insight_idx, insight in enumerate(insights, 1):
    print(f"  {_insight_idx}. {insight}")

# ============================================================================
# SUMMARY OUTPUT
# ============================================================================
print("\n" + "="*80)
print("✅ EDA COMPLETE")
print("="*80)
print(f"Analyzed {eda_df.shape[0]} records across {eda_df.shape[1]} features")
print(f"Generated {len(kpis)} domain-specific KPIs")
print(f"Identified {len(insights)} actionable insights")

# Store results for downstream use
eda_summary = {
    'dataset_shape': eda_df.shape,
    'numeric_features': numeric_cols,
    'categorical_features': categorical_cols,
    'correlation_matrix': eda_corr_matrix,
    'strong_correlations': strong_corrs,
    'distribution_insights': distribution_insights,
    'kpis': kpis,
    'insights': insights
}