"""
Advanced InsightAgent - Generates strategic business insights
Answers: What drives performance? What influences what? Where are anomalies?
What trends? What segments differ? What's likely to happen next?
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class InsightAgent:
    """
    Advanced Insight Agent that goes beyond basic statistics to provide
    strategic business insights and predictive analytics.
    """
    
    def __init__(self, df):
        self.df = df.copy()
        self.numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        self.date_cols = self._detect_date_columns()
        
    def _detect_date_columns(self):
        """Detect columns that contain dates"""
        date_cols = []
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                try:
                    pd.to_datetime(self.df[col].head(), errors='raise')
                    date_cols.append(col)
                except:
                    continue
        return date_cols
    
    def _detect_outliers_zscore(self, data, threshold=3):
        """Detect outliers using Z-score method"""
        z_scores = np.abs(stats.zscore(data.dropna()))
        return z_scores > threshold
    
    def _calculate_correlation_insights(self):
        """Find strong relationships between variables"""
        insights = []
        
        if len(self.numeric_cols) < 2:
            return insights
            
        # Calculate correlation matrix
        corr_matrix = self.df[self.numeric_cols].corr()
        
        # Find strong correlations (|r| > 0.7)
        strong_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:
                    var1 = corr_matrix.columns[i]
                    var2 = corr_matrix.columns[j]
                    direction = "positively" if corr_val > 0 else "negatively"
                    strength = "very strong" if abs(corr_val) > 0.8 else "strong"
                    strong_correlations.append(f"{var1} and {var2} have a {strength} {direction} correlation ({corr_val:.2f})")
        
        if strong_correlations:
            insights.append("🔗 **Key Relationships:**")
            insights.extend([f"• {corr}" for corr in strong_correlations[:5]])  # Top 5
            
        return insights
    
    def _detect_anomalies(self):
        """Detect outliers and anomalies in the data"""
        insights = []
        
        for col in self.numeric_cols:
            data = self.df[col].dropna()
            if len(data) < 10:  # Need sufficient data
                continue
                
            outliers = self._detect_outliers_zscore(data)
            outlier_count = outliers.sum()
            outlier_percentage = (outlier_count / len(data)) * 100
            
            if outlier_count > 0:
                # Find the actual outlier values
                outlier_values = data[outliers]
                min_outlier = outlier_values.min()
                max_outlier = outlier_values.max()
                
                insights.append(f"⚠️ **Anomaly in {col}:** {outlier_count} outliers detected ({outlier_percentage:.1f}%)")
                insights.append(f"   Range: {min_outlier:.2f} to {max_outlier:.2f}")
                
                # Suggest potential causes
                if outlier_percentage > 10:
                    insights.append(f"   High anomaly rate suggests data quality issues or special events")
                elif outlier_percentage < 5:
                    insights.append(f"   Few anomalies may indicate exceptional performance or errors")
        
        return insights
    
    def _analyze_trends(self):
        """Analyze trends in time series data"""
        insights = []
        
        if not self.date_cols:
            return insights
            
        for date_col in self.date_cols:
            for num_col in self.numeric_cols:
                try:
                    # Convert to datetime and sort
                    df_temp = self.df.copy()
                    df_temp[date_col] = pd.to_datetime(df_temp[date_col])
                    df_temp = df_temp.sort_values(date_col)
                    
                    # Remove rows with missing values
                    df_temp = df_temp.dropna(subset=[date_col, num_col])
                    
                    if len(df_temp) < 5:  # Need sufficient data points
                        continue
                    
                    # Calculate trend
                    x = np.arange(len(df_temp))
                    y = df_temp[num_col].values
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                    
                    # Calculate growth rate
                    if len(df_temp) >= 2:
                        first_val = df_temp[num_col].iloc[0]
                        last_val = df_temp[num_col].iloc[-1]
                        if first_val != 0:
                            growth_rate = ((last_val - first_val) / first_val) * 100
                        else:
                            growth_rate = 0
                    else:
                        growth_rate = 0
                    
                    # Determine trend direction and strength
                    if abs(slope) < 0.01:
                        trend_desc = "stable"
                    elif slope > 0:
                        trend_desc = "increasing"
                    else:
                        trend_desc = "decreasing"
                    
                    strength = "strong" if abs(r_value) > 0.7 else "moderate" if abs(r_value) > 0.4 else "weak"
                    
                    if abs(r_value) > 0.3:  # Only report meaningful trends
                        insights.append(f"📈 **Trend in {num_col}:** {strength} {trend_desc} trend")
                        insights.append(f"   Growth rate: {growth_rate:.1f}% over the period")
                        
                        # Predict next value
                        next_x = len(df_temp)
                        next_pred = slope * next_x + intercept
                        insights.append(f"   Next period prediction: {next_pred:.2f}")
                        
                except Exception as e:
                    continue
        
        return insights
    
    def _segment_analysis(self):
        """Analyze performance by segments"""
        insights = []
        
        if not self.categorical_cols or len(self.numeric_cols) == 0:
            return insights
        
        # For each categorical column with reasonable cardinality
        for cat_col in self.categorical_cols:
            unique_values = self.df[cat_col].nunique()
            if unique_values < 2 or unique_values > 20:  # Skip binary or too high cardinality
                continue
            
            # For each numeric column, analyze by segment
            for num_col in self.numeric_cols:
                try:
                    segment_stats = self.df.groupby(cat_col)[num_col].agg(['mean', 'count', 'std'])
                    segment_stats = segment_stats.dropna()
                    
                    if len(segment_stats) < 2:
                        continue
                    
                    # Find best and worst performing segments
                    best_segment = segment_stats['mean'].idxmax()
                    worst_segment = segment_stats['mean'].idxmin()
                    best_value = segment_stats.loc[best_segment, 'mean']
                    worst_value = segment_stats.loc[worst_segment, 'mean']
                    
                    # Calculate performance difference
                    if worst_value != 0:
                        performance_diff = ((best_value - worst_value) / worst_value) * 100
                    else:
                        performance_diff = 0
                    
                    # Only report significant differences
                    if abs(performance_diff) > 20:  # More than 20% difference
                        insights.append(f"🎯 **Segment Analysis - {cat_col}:**")
                        insights.append(f"   Best performer: {best_segment} ({best_value:.2f})")
                        insights.append(f"   Worst performer: {worst_segment} ({worst_value:.2f})")
                        insights.append(f"   Performance gap: {performance_diff:.1f}%")
                        
                        # Add strategic recommendation
                        if performance_diff > 50:
                            insights.append(f"   Recommendation: Investigate success factors of {best_segment}")
                        
                except Exception:
                    continue
        
        return insights
    
    def _predictive_insights(self):
        """Generate predictive insights about what's likely to happen next"""
        insights = []
        
        if len(self.numeric_cols) < 2:
            return insights
        
        # Simple linear regression for prediction
        target_vars = [col for col in self.numeric_cols if col.lower() in ['revenue', 'sales', 'profit', 'income']]
        
        for target in target_vars:
            if target not in self.numeric_cols:
                continue
                
            # Find potential predictor variables
            predictors = [col for col in self.numeric_cols if col != target]
            
            for predictor in predictors[:3]:  # Limit to top 3 predictors
                try:
                    x = self.df[predictor].dropna()
                    y = self.df.loc[x.index, target].dropna()
                    
                    if len(x) < 10:  # Need sufficient data
                        continue
                    
                    # Simple linear regression
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                    
                    if abs(r_value) > 0.5 and p_value < 0.05:  # Significant relationship
                        insights.append(f"🔮 **Predictive Insight:** {predictor} influences {target}")
                        insights.append(f"   Strength: {abs(r_value):.2f} (R²)")
                        insights.append(f"   Each unit change in {predictor} leads to {slope:.2f} change in {target}")
                        
                except Exception:
                    continue
        
        return insights
    
    def _performance_drivers(self):
        """Identify what is driving performance"""
        insights = []
        
        if len(self.numeric_cols) < 2:
            return insights
        
        # Find the most important numeric column (assume it's the KPI)
        kpi_candidates = [col for col in self.numeric_cols if any(keyword in col.lower() 
                          for keyword in ['revenue', 'sales', 'profit', 'income', 'total', 'amount'])]
        
        if not kpi_candidates:
            # If no obvious KPI, use the first numeric column
            kpi_candidates = [self.numeric_cols[0]]
        
        kpi = kpi_candidates[0]
        
        # Find correlations with KPI
        correlations = []
        for col in self.numeric_cols:
            if col != kpi:
                corr = self.df[kpi].corr(self.df[col])
                if not pd.isna(corr) and abs(corr) > 0.3:
                    correlations.append((col, corr))
        
        # Sort by absolute correlation
        correlations.sort(key=lambda x: abs(x[1]), reverse=True)
        
        if correlations:
            insights.append(f"🚀 **Performance Drivers for {kpi}:**")
            for col, corr in correlations[:5]:  # Top 5 drivers
                direction = "drives up" if corr > 0 else "drives down"
                strength = "strongly" if abs(corr) > 0.7 else "moderately" if abs(corr) > 0.5 else "weakly"
                insights.append(f"   {col} {strength} {direction} performance (correlation: {corr:.2f})")
        
        return insights
    
    def generate_insights(self):
        """
        Generate comprehensive strategic insights covering:
        - Performance drivers
        - Variable relationships  
        - Anomalies and outliers
        - Trends and patterns
        - Segment differences
        - Predictive insights
        """
        insights = []
        
        # Header
        insights.append("🧠 **ADVANCED BUSINESS INSIGHTS**")
        insights.append("=" * 50)
        insights.append("")
        
        # 1. Performance Drivers
        performance_insights = self._performance_drivers()
        if performance_insights:
            insights.extend(performance_insights)
            insights.append("")
        
        # 2. Correlation & Hidden Relationships
        correlation_insights = self._calculate_correlation_insights()
        if correlation_insights:
            insights.extend(correlation_insights)
            insights.append("")
        
        # 3. Anomaly Detection
        anomaly_insights = self._detect_anomalies()
        if anomaly_insights:
            insights.extend(anomaly_insights)
            insights.append("")
        
        # 4. Trend Analysis
        trend_insights = self._analyze_trends()
        if trend_insights:
            insights.extend(trend_insights)
            insights.append("")
        
        # 5. Segmentation Analysis
        segment_insights = self._segment_analysis()
        if segment_insights:
            insights.extend(segment_insights)
            insights.append("")
        
        # 6. Predictive Insights
        predictive_insights = self._predictive_insights()
        if predictive_insights:
            insights.extend(predictive_insights)
            insights.append("")
        
        # Summary if no insights found
        if len(insights) <= 2:  # Only header and separator
            insights.append("📊 **Basic Data Overview:**")
            insights.append(f"• Dataset contains {len(self.df)} rows and {len(self.df.columns)} columns")
            insights.append(f"• Numeric columns: {len(self.numeric_cols)}")
            insights.append(f"• Categorical columns: {len(self.categorical_cols)}")
            if self.date_cols:
                insights.append(f"• Date columns detected: {', '.join(self.date_cols)}")
        
        return insights
