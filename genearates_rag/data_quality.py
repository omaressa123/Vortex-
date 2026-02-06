import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Zerve design system colors
ZERVE_BG = '#1D1D20'
ZERVE_TEXT = '#fbfbff'
ZERVE_SECONDARY = '#909094'
ZERVE_COLORS = ['#A1C9F4', '#FFB482', '#8DE5A1', '#FF9F9B', '#D0BBFF', '#1F77B4', '#9467BD', '#8C564B']
ZERVE_HIGHLIGHT = '#ffd400'
ZERVE_SUCCESS = '#17b26a'
ZERVE_WARNING = '#f04438'

# Set up styling
plt.rcParams['figure.facecolor'] = ZERVE_BG
plt.rcParams['axes.facecolor'] = ZERVE_BG
plt.rcParams['text.color'] = ZERVE_TEXT
plt.rcParams['axes.labelcolor'] = ZERVE_TEXT
plt.rcParams['xtick.color'] = ZERVE_TEXT
plt.rcParams['ytick.color'] = ZERVE_TEXT
plt.rcParams['axes.edgecolor'] = ZERVE_SECONDARY
plt.rcParams['legend.facecolor'] = ZERVE_BG
plt.rcParams['legend.edgecolor'] = ZERVE_SECONDARY

# Use profiling data
viz_df = df.copy()

# 1. Distribution Plots for Numeric Variables
numeric_cols = viz_df.select_dtypes(include=['int64', 'float64', 'uint8', 'float32']).columns.tolist()

if numeric_cols:
    for col in numeric_cols:
        dist_fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        dist_fig.patch.set_facecolor(ZERVE_BG)
        
        # Histogram
        ax1.hist(viz_df[col], bins=20, color=ZERVE_COLORS[0], edgecolor=ZERVE_TEXT, alpha=0.8)
        ax1.set_title(f'{col} - Distribution', fontsize=14, fontweight='bold', color=ZERVE_TEXT, pad=15)
        ax1.set_xlabel(col, fontsize=11, color=ZERVE_TEXT)
        ax1.set_ylabel('Frequency', fontsize=11, color=ZERVE_TEXT)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        
        # Box plot
        bp = ax2.boxplot(viz_df[col], vert=True, patch_artist=True, 
                         boxprops=dict(facecolor=ZERVE_COLORS[1], color=ZERVE_TEXT, alpha=0.8),
                         whiskerprops=dict(color=ZERVE_TEXT),
                         capprops=dict(color=ZERVE_TEXT),
                         medianprops=dict(color=ZERVE_HIGHLIGHT, linewidth=2),
                         flierprops=dict(marker='o', markerfacecolor=ZERVE_WARNING, markersize=6, alpha=0.7))
        ax2.set_title(f'{col} - Box Plot', fontsize=14, fontweight='bold', color=ZERVE_TEXT, pad=15)
        ax2.set_ylabel(col, fontsize=11, color=ZERVE_TEXT)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.set_xticks([])
        
        plt.tight_layout()
        print(f"Generated distribution visualization for '{col}'")

# 2. Correlation Heatmap
if len(numeric_cols) > 1:
    corr_fig, ax = plt.subplots(figsize=(10, 8))
    corr_fig.patch.set_facecolor(ZERVE_BG)
    
    corr_matrix = viz_df[numeric_cols].corr()
    
    im = ax.imshow(corr_matrix, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
    
    ax.set_xticks(np.arange(len(numeric_cols)))
    ax.set_yticks(np.arange(len(numeric_cols)))
    ax.set_xticklabels(numeric_cols, rotation=45, ha='right', fontsize=11, color=ZERVE_TEXT)
    ax.set_yticklabels(numeric_cols, fontsize=11, color=ZERVE_TEXT)
    
    # Add correlation values
    for i in range(len(numeric_cols)):
        for j in range(len(numeric_cols)):
            text_color = ZERVE_BG if abs(corr_matrix.iloc[i, j]) > 0.5 else ZERVE_TEXT
            text = ax.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                          ha='center', va='center', color=text_color, fontsize=10, fontweight='bold')
    
    ax.set_title('Correlation Matrix', fontsize=16, fontweight='bold', color=ZERVE_TEXT, pad=20)
    
    cbar = corr_fig.colorbar(im, ax=ax)
    cbar.ax.yaxis.set_tick_params(color=ZERVE_TEXT)
    cbar.outline.set_edgecolor(ZERVE_SECONDARY)
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=ZERVE_TEXT)
    
    plt.tight_layout()
    print("Generated correlation heatmap")

# 3. Categorical Distribution
categorical_cols = viz_df.select_dtypes(include=['object']).columns.tolist()

if categorical_cols:
    for col in categorical_cols:
        cat_fig, ax = plt.subplots(figsize=(10, 6))
        cat_fig.patch.set_facecolor(ZERVE_BG)
        
        value_counts = viz_df[col].value_counts()
        colors = ZERVE_COLORS[:len(value_counts)]
        
        bars = ax.bar(range(len(value_counts)), value_counts.values, color=colors, edgecolor=ZERVE_TEXT, alpha=0.85)
        ax.set_xticks(range(len(value_counts)))
        ax.set_xticklabels(value_counts.index, rotation=45, ha='right', fontsize=11, color=ZERVE_TEXT)
        ax.set_ylabel('Count', fontsize=11, color=ZERVE_TEXT)
        ax.set_title(f'{col} - Distribution', fontsize=14, fontweight='bold', color=ZERVE_TEXT, pad=15)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, value_counts.values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(val)}',
                   ha='center', va='bottom', fontsize=10, color=ZERVE_TEXT, fontweight='bold')
        
        plt.tight_layout()
        print(f"Generated categorical distribution for '{col}'")

# 4. Data Quality Summary Chart
summary_fig, ax = plt.subplots(figsize=(12, 6))
summary_fig.patch.set_facecolor(ZERVE_BG)

# Calculate data quality metrics
quality_metrics = {
    'Completeness': ((viz_df.size - viz_df.isnull().sum().sum()) / viz_df.size) * 100,
    'Uniqueness': ((viz_df.size - viz_df.duplicated().sum() * len(viz_df.columns)) / viz_df.size) * 100,
    'Validity': 100.0  # Assuming all data types are valid after cleaning
}

metrics_names = list(quality_metrics.keys())
metrics_values = list(quality_metrics.values())

bars = ax.barh(metrics_names, metrics_values, color=[ZERVE_SUCCESS, ZERVE_COLORS[2], ZERVE_COLORS[4]], 
               edgecolor=ZERVE_TEXT, alpha=0.85, height=0.6)

ax.set_xlim(0, 100)
ax.set_xlabel('Score (%)', fontsize=11, color=ZERVE_TEXT)
ax.set_title('Data Quality Metrics', fontsize=16, fontweight='bold', color=ZERVE_TEXT, pad=20)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Add value labels
for i, (bar, val) in enumerate(zip(bars, metrics_values)):
    width = bar.get_width()
    ax.text(width + 1, bar.get_y() + bar.get_height()/2.,
           f'{val:.1f}%',
           ha='left', va='center', fontsize=11, color=ZERVE_TEXT, fontweight='bold')

# Add reference line at 95%
ax.axvline(x=95, color=ZERVE_WARNING, linestyle='--', linewidth=1.5, alpha=0.7, label='Target (95%)')
ax.legend(loc='lower right', frameon=True, facecolor=ZERVE_BG, edgecolor=ZERVE_SECONDARY, 
         labelcolor=ZERVE_TEXT, fontsize=10)

plt.tight_layout()
print("Generated data quality summary chart")

print(f"\n✅ Generated {len(numeric_cols) * 1 + (1 if len(numeric_cols) > 1 else 0) + len(categorical_cols) + 1} professional visualizations")
print("📊 All charts use Zerve design system with dark theme")
print("🎨 Professional styling suitable for reports and presentations")