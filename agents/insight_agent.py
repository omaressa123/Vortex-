class InsightAgent:
    def __init__(self, df, rag_system=None):
        self.df = df
        self.rag_system = rag_system

    def generate_insights(self):
        """
        Generates textual insights using LLM + RAG.
        """
        insights = []
        
        # Basic Statistical Insights
        desc = self.df.describe().to_string()
        insights.append(f"Statistical Summary:\n{desc}")

        if not self.rag_system or not self.rag_system.llm:
            return insights

        # RAG-based Insights
        # Schema-aware RAG
        schema_info = str(self.df.dtypes.to_dict())
        
        # 1. Ask for general trends
        trend_query = "What are the interesting trends in this data?"
        trend_insight = self.rag_system.analyze_schema(schema_info + "\nSample Data:\n" + self.df.head().to_string(), trend_query)
        insights.append(f"Trends:\n{trend_insight}")
        
        # 2. Ask for anomalies
        anomaly_query = "Are there any anomalies or potential data quality issues?"
        anomaly_insight = self.rag_system.analyze_schema(schema_info + "\nSample Data:\n" + self.df.head().to_string(), anomaly_query)
        insights.append(f"Anomalies:\n{anomaly_insight}")

        return insights
