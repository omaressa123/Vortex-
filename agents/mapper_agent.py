import pandas as pd
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import json

class MapperAgent:
    def __init__(self, df, api_key):
        self.df = df
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", api_key=api_key)

    def map_columns(self, template_spec):
        """
        Maps dataframe columns to template components using LLM.
        """
        # 1. Profile the Data (Simplified for Prompt)
        dtypes = self.df.dtypes.to_dict()
        sample = self.df.head(3).to_dict()
        columns_info = []
        for col, dtype in dtypes.items():
            columns_info.append(f"- {col} ({dtype})")
        
        columns_text = "\n".join(columns_info)
        
        # 2. Prepare Prompt
        components_text = json.dumps(template_spec['components'], indent=2)
        
        prompt = f"""
        You are an intelligent data visualization assistant.
        Your task is to map the provided dataset columns to the required dashboard components.
        
        Dataset Columns:
        {columns_text}
        
        Sample Data:
        {sample}
        
        Dashboard Template Components (JSON):
        {components_text}
        
        Rules:
        1. For 'kpi' type, choose a numeric column for aggregation (sum/avg) or 'count' for row count.
        2. For 'line' chart, find a Date/Time column for X-axis and a Numeric column for Y-axis.
        3. For 'bar' chart, find a Categorical column for X-axis and a Numeric column for Y-axis.
        4. Return ONLY valid JSON mapping in the following format:
        {{
            "kpi_1": {{ "column": "col_name", "aggregation": "sum" }},
            "chart_main": {{ "x": "date_col", "y": "val_col", "type": "line" }},
            ...
        }}
        5. If no suitable column exists, use "None".
        
        JSON Response:
        """
        
        try:
            response = self.llm.invoke(prompt)
            mapping_json = response.content.strip()
            # Clean up markdown code blocks if present
            if "```json" in mapping_json:
                mapping_json = mapping_json.split("```json")[1].split("```")[0]
            elif "```" in mapping_json:
                mapping_json = mapping_json.split("```")[1].split("```")[0]
                
            mapping = json.loads(mapping_json)
            return mapping
        except Exception as e:
            print(f"Error in MapperAgent: {e}")
            return {}

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
                    
                    if col == "None" or not col:
                        val = self.df.shape[0] # Default to row count
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
                        val = 0
                        label = "N/A"
                        
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
                        # Group Data
                        if chart_type == "line":
                            # Sort by date
                            try:
                                self.df[x_col] = pd.to_datetime(self.df[x_col])
                                chart_df = self.df.groupby(x_col)[y_col].sum().reset_index().sort_values(x_col)
                                chart_df[x_col] = chart_df[x_col].dt.strftime('%Y-%m-%d')
                            except:
                                # Fallback if not date
                                chart_df = self.df.groupby(x_col)[y_col].sum().reset_index().head(20)
                        else:
                            # Bar / Others (Top 10)
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
