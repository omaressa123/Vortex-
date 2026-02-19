# Visualization Agent
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
import base64

sns.set(style="whitegrid")


class VisualizationAgent:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        self.datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()


    # Numeric Visualization
    def plot_numeric_distribution(self, column):
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        sns.histplot(self.df[column], kde=True, ax=axes[0], color="#ff2d2d")
        axes[0].set_title(f"Distribution of {column}")

        sns.boxplot(x=self.df[column], ax=axes[1], color="#ff2d2d")
        axes[1].set_title(f"Boxplot of {column}")

        plt.tight_layout()
        # Convert to base64 string
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=80)
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        return img_base64


    # Categorical Visualization
    def plot_categorical(self, column, top_n=10):
        counts = self.df[column].value_counts().head(top_n)

        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x=counts.values, y=counts.index, ax=ax, color="#ff2d2d")

        ax.set_title(f"Top {top_n} Categories in {column}")
        ax.set_xlabel("Count")
        ax.set_ylabel(column)

        plt.tight_layout()
        # Convert to base64 string
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=80)
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        return img_base64


    # Time Series Visualization
    def plot_time_series(self, date_col, value_col, freq="M"):
        temp = self.df[[date_col, value_col]].dropna()
        temp = temp.sort_values(date_col)

        temp = temp.set_index(date_col).resample(freq).sum()

        fig, ax = plt.subplots(figsize=(12, 5))
        temp.plot(ax=ax, color="#ff2d2d")
        ax.set_title(f"Time Series: {value_col}")
        ax.set_xlabel("Date")
        ax.set_ylabel(value_col)

        plt.tight_layout()
        # Convert to base64 string
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=80)
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        return img_base64

    # Correlation Heatmap
    def plot_correlation(self):
        if len(self.numeric_cols) < 2:
            return None

        corr = self.df[self.numeric_cols].corr()

        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(
            corr,
            annot=True,
            fmt=".2f",
            cmap=sns.color_palette(["#ff2d2d", "#1a1a1a"], as_cmap=True),
            ax=ax
        )

        ax.set_title("Correlation Heatmap")
        plt.tight_layout()
        # Convert to base64 string
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=80)
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        return img_base64

    # Auto Visualization Selector
    def auto_visualize(self):
        figures = []

        # Numeric
        for col in self.numeric_cols[:2]:
            figures.append(
                ("numeric", col, self.plot_numeric_distribution(col))
            )

        # Categorical
        for col in self.categorical_cols[:2]:
            figures.append(
                ("categorical", col, self.plot_categorical(col))
            )

        # Time Series
        if self.datetime_cols and self.numeric_cols:
            figures.append(
                (
                    "time_series",
                    f"{self.datetime_cols[0]} vs {self.numeric_cols[0]}",
                    self.plot_time_series(self.datetime_cols[0], self.numeric_cols[0])
                )
            )

        # Correlation
        corr_fig = self.plot_correlation()
        if corr_fig:
            figures.append(("correlation", "numeric", corr_fig))

        return figures
