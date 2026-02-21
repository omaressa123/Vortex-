import pandas as pd
import json

class MapperAgent:
    """
    Maps dataframe columns to dashboard template components.
    Uses heuristic/statistical methods - No API keys required.
    """
    
    def __init__(self, df):
        self.df = df
        self.numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        self.categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        self.datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        # Try to detect date columns from string columns
        for col in self.categorical_cols[:]:
            try:
                pd.to_datetime(df[col].head(5))
                self.datetime_cols.append(col)
                self.categorical_cols.remove(col)
            except (ValueError, TypeError):
                pass

    def map_columns(self, template_spec):
        """
        Maps dataframe columns to template components using heuristics.
        """
        mapping = {}
        components = template_spec.get('components', [])
        
        # KPI assignments - use numeric columns
        kpi_count = 0
        for col in self.numeric_cols[:4]:
            kpi_count += 1
            # Decide aggregation based on column name heuristics
            col_lower = col.lower()
            if any(kw in col_lower for kw in ['count', 'quantity', 'number', 'qty']):
                agg = 'sum'
            elif any(kw in col_lower for kw in ['rate', 'ratio', 'percentage', 'avg', 'average', 'score']):
                agg = 'avg'
            else:
                agg = 'sum'
            
            mapping[f'kpi_{kpi_count}'] = {
                'column': col,
                'aggregation': agg
            }
        
        # Chart assignments
        chart_count = 0
        
        # Line chart: date vs numeric
        if self.datetime_cols and self.numeric_cols:
            chart_count += 1
            mapping[f'chart_{chart_count}'] = {
                'x': self.datetime_cols[0],
                'y': self.numeric_cols[0],
                'type': 'line'
            }
        
        # Bar chart: categorical vs numeric
        if self.categorical_cols and self.numeric_cols:
            chart_count += 1
            y_col = self.numeric_cols[1] if len(self.numeric_cols) > 1 else self.numeric_cols[0]
            mapping[f'chart_{chart_count}'] = {
                'x': self.categorical_cols[0],
                'y': y_col,
                'type': 'bar'
            }
        
        # Pie chart: if we have categorical data
        if len(self.categorical_cols) > 1 and self.numeric_cols:
            chart_count += 1
            mapping[f'chart_{chart_count}'] = {
                'x': self.categorical_cols[1] if len(self.categorical_cols) > 1 else self.categorical_cols[0],
                'y': self.numeric_cols[0],
                'type': 'pie'
            }
        
        return mapping

    def generate_dashboard_data(self, mapping):
        """
        Executes the mapping to generate actual data for the frontend.
        """
        data = {}
        
        for comp_id, config in mapping.items():
            if not config or config == "None":
                data[comp_id] = {"value": "N/A", "label": "No Data"}
                continue
                
            try:
                # Handle KPIs
                if "aggregation" in config:
                    col = config.get("column")
                    agg = config.get("aggregation")
                    
                    if col == "None" or not col or col not in self.df.columns:
                        val = self.df.shape[0]
                        label = "Total Records"
                    elif agg == "sum":
                        val = self.df[col].sum()
                        label = f"Total {col}"
                    elif agg == "avg":
                        val = self.df[col].mean()
                        label = f"Avg {col}"
                    elif agg == "count":
                        val = self.df[col].count()
                        label = f"Count of {col}"
                    else:
                        val = self.df[col].sum()
                        label = f"Total {col}"
                        
                    # Format number
                    if isinstance(val, (int, float)):
                        if val > 1000000:
                            val_str = f"{val/1000000:.1f}M"
                        elif val > 1000:
                            val_str = f"{val/1000:.1f}K"
                        else:
                            val_str = f"{val:.1f}"
                    else:
                        val_str = str(val)
                        
                    data[comp_id] = {"value": val_str, "label": label}
                
                # Handle Charts
                elif "x" in config and "y" in config:
                    x_col = config.get("x")
                    y_col = config.get("y")
                    chart_type = config.get("type", "bar")
                    
                    if x_col and y_col and x_col != "None" and y_col != "None":
                        if x_col in self.df.columns and y_col in self.df.columns:
                            if chart_type == "line":
                                try:
                                    self.df[x_col] = pd.to_datetime(self.df[x_col])
                                    chart_df = self.df.groupby(x_col)[y_col].sum().reset_index().sort_values(x_col)
                                    chart_df[x_col] = chart_df[x_col].dt.strftime('%Y-%m-%d')
                                except Exception:
                                    chart_df = self.df.groupby(x_col)[y_col].sum().reset_index().head(20)
                            elif chart_type == "pie":
                                chart_df = self.df.groupby(x_col)[y_col].sum().reset_index().sort_values(y_col, ascending=False).head(8)
                            else:
                                chart_df = self.df.groupby(x_col)[y_col].sum().reset_index().sort_values(y_col, ascending=False).head(10)
                                
                            data[comp_id] = {
                                "type": chart_type,
                                "labels": chart_df[x_col].tolist(),
                                "datasets": [{
                                    "label": y_col,
                                    "data": chart_df[y_col].tolist()
                                }]
                            }
            except Exception as e:
                print(f"Error generating data for {comp_id}: {e}")
                data[comp_id] = {"error": str(e)}
                
        return data
