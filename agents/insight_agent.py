"""
InsightAgent - DEPRECATED
Insights are now generated directly by the DataRAGEngine.
This file is kept for backwards compatibility but is not used.
"""

class InsightAgent:
    """
    DEPRECATED: Use DataRAGEngine for data insights instead.
    This agent previously used LLM/RAG for generating insights.
    The system now uses the methods-based DataRAGEngine for all insights.
    """
    def __init__(self, df, rag_system=None):
        self.df = df

    def generate_insights(self):
        """
        Generate basic statistical insights (no LLM needed).
        For advanced insights, use DataRAGEngine.answer_question() instead.
        """
        insights = []
        
        # Basic Statistical Insights only
        desc = self.df.describe().to_string()
        insights.append(f"Statistical Summary:\n{desc}")
        
        # Missing value summary
        missing = self.df.isnull().sum()
        if missing.any():
            missing_info = missing[missing > 0].to_string()
            insights.append(f"Missing Values:\n{missing_info}")
        
        # Data types summary
        dtypes = self.df.dtypes.value_counts().to_string()
        insights.append(f"Data Types Distribution:\n{dtypes}")
        
        return insights
