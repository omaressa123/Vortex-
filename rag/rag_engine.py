"""
Data-Aware Conversational RAG Engine

This engine enables conversational data analysis without any API keys.
When data is uploaded, it creates a knowledge base from the data itself,
allowing users to ask questions about their data and understand KPIs.

Uses sentence-transformers for embeddings and understands data schema,
statistics, and relationships locally.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Any

# Try to import sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    print("✅ Sentence transformers available for RAG")
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("❌ Sentence transformers not available. Install with: pip install sentence-transformers")


class DataRAGEngine:
    """
    Local Data-Aware RAG Engine - No API Keys Required
    
    Features:
    - Understands uploaded data schema, columns, types
    - Extracts KPIs automatically from numeric data
    - Creates embeddings of data context for retrieval
    - Answers questions about the data using statistical analysis
    """
    
    def __init__(self):
        self.embeddings_model = None
        self.data_documents = []
        self.data_embeddings = None
        self.data_summary = {}
        self.df = None
        self.kpis = {}
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                print("🔄 Loading embedding model...")
                self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Embedding model loaded")
            except Exception as e:
                print(f"❌ Error loading embedding model: {e}")
                self.embeddings_model = None
    
    def load_data(self, df: pd.DataFrame):
        """
        Load a DataFrame and build the knowledge base from it.
        This creates documents about the data that can be searched.
        """
        self.df = df.copy()
        self.data_documents = []
        self.data_summary = {}
        self.kpis = {}
        
        # Build knowledge documents from the data
        self._build_schema_documents()
        self._build_statistical_documents()
        self._build_kpi_documents()
        self._build_correlation_documents()
        self._build_distribution_documents()
        self._build_categorical_documents()
        self._build_time_analysis_documents()
        
        # Create embeddings for retrieval
        if self.embeddings_model and self.data_documents:
            texts = [doc['content'] for doc in self.data_documents]
            self.data_embeddings = self.embeddings_model.encode(texts)
            print(f"✅ Data RAG initialized with {len(self.data_documents)} knowledge documents")
        else:
            print("⚠️ RAG running without embeddings (keyword search only)")
        
        return {
            'documents_created': len(self.data_documents),
            'kpis': self.kpis,
            'summary': self.data_summary
        }
    
    def _build_schema_documents(self):
        """Create documents about data schema"""
        if self.df is None:
            return
        
        # Overall schema document
        schema_info = {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'columns': {}
        }
        
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            missing = int(self.df[col].isnull().sum())
            unique = int(self.df[col].nunique())
            schema_info['columns'][col] = {
                'dtype': dtype,
                'missing': missing,
                'unique_values': unique
            }
        
        self.data_summary['schema'] = schema_info
        
        # Schema overview document
        cols_desc = []
        for col, info in schema_info['columns'].items():
            cols_desc.append(f"- {col} (type: {info['dtype']}, missing: {info['missing']}, unique: {info['unique_values']})")
        
        self.data_documents.append({
            'type': 'schema',
            'title': 'Dataset Schema Overview',
            'content': f"The dataset has {schema_info['total_rows']} rows and {schema_info['total_columns']} columns.\n"
                       f"Columns:\n" + "\n".join(cols_desc)
        })
        
        # Individual column documents
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            missing = int(self.df[col].isnull().sum())
            missing_pct = round(missing / len(self.df) * 100, 2) if len(self.df) > 0 else 0
            unique = int(self.df[col].nunique())
            
            content = f"Column '{col}': Type is {dtype}. Has {missing} missing values ({missing_pct}%). Has {unique} unique values."
            
            if self.df[col].dtype in ['int64', 'float64']:
                content += f" Min: {self.df[col].min()}, Max: {self.df[col].max()}, Mean: {round(self.df[col].mean(), 2)}, Median: {round(self.df[col].median(), 2)}."
            elif self.df[col].dtype == 'object':
                top_vals = self.df[col].value_counts().head(5)
                content += f" Top values: {dict(top_vals)}."
            
            self.data_documents.append({
                'type': 'column',
                'title': f'Column: {col}',
                'content': content
            })
    
    def _build_statistical_documents(self):
        """Create documents about statistical summaries"""
        if self.df is None:
            return
        
        numeric_cols = self.df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if not numeric_cols:
            return
        
        # Descriptive statistics document
        desc = self.df[numeric_cols].describe()
        stats_text = "Statistical Summary of numeric columns:\n"
        for col in numeric_cols:
            stats_text += (
                f"\n{col}:\n"
                f"  Count: {int(desc.loc['count', col])}\n"
                f"  Mean: {round(desc.loc['mean', col], 2)}\n"
                f"  Std: {round(desc.loc['std', col], 2)}\n"
                f"  Min: {round(desc.loc['min', col], 2)}\n"
                f"  25%: {round(desc.loc['25%', col], 2)}\n"
                f"  50% (Median): {round(desc.loc['50%', col], 2)}\n"
                f"  75%: {round(desc.loc['75%', col], 2)}\n"
                f"  Max: {round(desc.loc['max', col], 2)}\n"
            )
        
        self.data_documents.append({
            'type': 'statistics',
            'title': 'Statistical Summary',
            'content': stats_text
        })
        
        self.data_summary['statistics'] = desc.to_dict()
    
    def _build_kpi_documents(self):
        """Extract and document KPIs from the data"""
        if self.df is None:
            return
        
        numeric_cols = self.df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        kpi_text = "Key Performance Indicators (KPIs):\n\n"
        
        for col in numeric_cols:
            total = round(float(self.df[col].sum()), 2)
            avg = round(float(self.df[col].mean()), 2)
            max_val = round(float(self.df[col].max()), 2)
            min_val = round(float(self.df[col].min()), 2)
            
            self.kpis[col] = {
                'total': total,
                'average': avg,
                'max': max_val,
                'min': min_val
            }
            
            kpi_text += f"{col}:\n  Total: {total}\n  Average: {avg}\n  Max: {max_val}\n  Min: {min_val}\n\n"
        
        # Revenue/Sales specific KPIs
        revenue_cols = [c for c in numeric_cols if any(kw in c.lower() for kw in ['revenue', 'sales', 'total', 'amount', 'income'])]
        cost_cols = [c for c in numeric_cols if any(kw in c.lower() for kw in ['cost', 'expense', 'cogs'])]
        
        if revenue_cols and cost_cols:
            rev = self.df[revenue_cols[0]].sum()
            cost = self.df[cost_cols[0]].sum()
            profit = rev - cost
            margin = (profit / rev * 100) if rev > 0 else 0
            
            self.kpis['_calculated'] = {
                'total_revenue': round(float(rev), 2),
                'total_cost': round(float(cost), 2),
                'total_profit': round(float(profit), 2),
                'profit_margin': round(float(margin), 2)
            }
            
            kpi_text += (
                f"\nCalculated KPIs:\n"
                f"  Total Revenue ({revenue_cols[0]}): {round(float(rev), 2)}\n"
                f"  Total Cost ({cost_cols[0]}): {round(float(cost), 2)}\n"
                f"  Profit: {round(float(profit), 2)}\n"
                f"  Profit Margin: {round(float(margin), 2)}%\n"
            )
        
        self.data_documents.append({
            'type': 'kpis',
            'title': 'Key Performance Indicators',
            'content': kpi_text
        })
        
        self.data_summary['kpis'] = self.kpis
    
    def _build_correlation_documents(self):
        """Create documents about column correlations"""
        if self.df is None:
            return
        
        numeric_cols = self.df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if len(numeric_cols) < 2:
            return
        
        corr = self.df[numeric_cols].corr()
        
        # Find strong correlations
        strong_corrs = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                val = corr.iloc[i, j]
                if abs(val) > 0.5:
                    strength = "strong positive" if val > 0.7 else "moderate positive" if val > 0 else "strong negative" if val < -0.7 else "moderate negative"
                    strong_corrs.append(f"- {numeric_cols[i]} and {numeric_cols[j]}: {round(val, 3)} ({strength} correlation)")
        
        if strong_corrs:
            corr_text = "Notable correlations between columns:\n" + "\n".join(strong_corrs)
        else:
            corr_text = "No strong correlations (>0.5) found between numeric columns."
        
        self.data_documents.append({
            'type': 'correlations',
            'title': 'Column Correlations',
            'content': corr_text
        })
    
    def _build_distribution_documents(self):
        """Create documents about data distributions"""
        if self.df is None:
            return
        
        numeric_cols = self.df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        for col in numeric_cols:
            series = self.df[col].dropna()
            if len(series) == 0:
                continue
            
            # Skewness and kurtosis
            skew = round(float(series.skew()), 2)
            kurt = round(float(series.kurtosis()), 2)
            
            # Quartiles
            q1 = round(float(series.quantile(0.25)), 2)
            q3 = round(float(series.quantile(0.75)), 2)
            iqr = round(q3 - q1, 2)
            
            # Outlier count
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outlier_count = int(((series < lower) | (series > upper)).sum())
            
            skew_desc = "right-skewed" if skew > 0.5 else "left-skewed" if skew < -0.5 else "approximately symmetric"
            
            content = (
                f"Distribution of '{col}':\n"
                f"  Shape: {skew_desc} (skewness: {skew})\n"
                f"  Kurtosis: {kurt}\n"
                f"  IQR: {iqr} (Q1: {q1}, Q3: {q3})\n"
                f"  Outliers (IQR method): {outlier_count} values outside [{round(lower, 2)}, {round(upper, 2)}]"
            )
            
            self.data_documents.append({
                'type': 'distribution',
                'title': f'Distribution: {col}',
                'content': content
            })
    
    def _build_categorical_documents(self):
        """Create documents about categorical columns"""
        if self.df is None:
            return
        
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        for col in cat_cols:
            value_counts = self.df[col].value_counts()
            total = len(self.df)
            
            top_values = value_counts.head(10)
            content = f"Categorical column '{col}' has {len(value_counts)} unique values.\n"
            content += "Top values:\n"
            for val, count in top_values.items():
                pct = round(count / total * 100, 1)
                content += f"  - {val}: {count} ({pct}%)\n"
            
            self.data_documents.append({
                'type': 'categorical',
                'title': f'Categories: {col}',
                'content': content
            })
    
    def _build_time_analysis_documents(self):
        """Create documents about time-based analysis if date columns exist"""
        if self.df is None:
            return
        
        # Try to find date columns
        date_cols = self.df.select_dtypes(include=['datetime64']).columns.tolist()
        
        # Also check string columns that might be dates
        for col in self.df.select_dtypes(include=['object']).columns:
            if any(kw in col.lower() for kw in ['date', 'time', 'day', 'month', 'year']):
                try:
                    pd.to_datetime(self.df[col].head(10))
                    date_cols.append(col)
                except (ValueError, TypeError):
                    pass
        
        if not date_cols:
            return
        
        numeric_cols = self.df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if not numeric_cols:
            return
        
        for date_col in date_cols[:1]:  # Process first date column
            try:
                dates = pd.to_datetime(self.df[date_col], errors='coerce')
                valid_dates = dates.dropna()
                
                if len(valid_dates) == 0:
                    continue
                
                date_range = f"{valid_dates.min()} to {valid_dates.max()}"
                span_days = (valid_dates.max() - valid_dates.min()).days
                
                content = (
                    f"Time analysis based on '{date_col}':\n"
                    f"  Date range: {date_range}\n"
                    f"  Span: {span_days} days\n"
                    f"  Total records: {len(valid_dates)}\n"
                )
                
                # Monthly aggregation for first numeric column
                if numeric_cols:
                    val_col = numeric_cols[0]
                    temp_df = self.df.copy()
                    temp_df['_date'] = dates
                    monthly = temp_df.groupby(temp_df['_date'].dt.to_period('M'))[val_col].sum()
                    if len(monthly) > 1:
                        growth = ((monthly.iloc[-1] - monthly.iloc[0]) / monthly.iloc[0] * 100) if monthly.iloc[0] != 0 else 0
                        content += f"  Monthly trend for {val_col}: {round(float(growth), 1)}% overall growth\n"
                        content += f"  Best month: {monthly.idxmax()} ({round(float(monthly.max()), 2)})\n"
                        content += f"  Worst month: {monthly.idxmin()} ({round(float(monthly.min()), 2)})\n"
                
                self.data_documents.append({
                    'type': 'time_analysis',
                    'title': f'Time Analysis: {date_col}',
                    'content': content
                })
            except Exception as e:
                print(f"⚠️ Error analyzing time column {date_col}: {e}")
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """Retrieve relevant documents for a query"""
        if not self.data_documents:
            return []
        
        # Use embedding-based retrieval if available
        if self.embeddings_model and self.data_embeddings is not None:
            query_embedding = self.embeddings_model.encode([query])
            similarities = np.dot(self.data_embeddings, query_embedding.T).flatten()
            top_indices = np.argsort(similarities)[-k:][::-1]
            return [self.data_documents[i] for i in top_indices]
        
        # Fallback: keyword-based retrieval
        query_lower = query.lower()
        scored_docs = []
        for doc in self.data_documents:
            score = 0
            content_lower = doc['content'].lower()
            title_lower = doc['title'].lower()
            
            # Score based on keyword matches
            for word in query_lower.split():
                if word in content_lower:
                    score += 1
                if word in title_lower:
                    score += 2
            
            scored_docs.append((score, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:k]]
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a question about the loaded data.
        Uses retrieval + statistical analysis to generate answers.
        """
        if self.df is None:
            return {
                'answer': 'No data loaded. Please upload a data file first.',
                'sources': [],
                'kpis': {}
            }
        
        # Retrieve relevant documents
        relevant_docs = self.retrieve(question, k=5)
        
        # Build context from retrieved documents
        context_parts = []
        for doc in relevant_docs:
            context_parts.append(f"[{doc['title']}]\n{doc['content']}")
        
        context = "\n\n".join(context_parts)
        
        # Generate answer based on the question type
        answer = self._generate_answer(question, context, relevant_docs)
        
        return {
            'answer': answer,
            'sources': [{'title': d['title'], 'type': d['type']} for d in relevant_docs],
            'kpis': self.kpis
        }
    
    def _generate_answer(self, question: str, context: str, docs: List[Dict]) -> str:
        """Generate an answer based on question analysis and retrieved context"""
        q_lower = question.lower()
        
        # Handle specific question types
        if any(kw in q_lower for kw in ['kpi', 'key performance', 'metric', 'metrics']):
            return self._answer_kpi_question(question)
        
        if any(kw in q_lower for kw in ['column', 'columns', 'field', 'fields', 'schema', 'structure']):
            return self._answer_schema_question(question)
        
        if any(kw in q_lower for kw in ['mean', 'average', 'avg', 'sum', 'total', 'count', 'max', 'min', 'median']):
            return self._answer_statistics_question(question)
        
        if any(kw in q_lower for kw in ['correlation', 'correlate', 'relationship', 'related']):
            return self._answer_correlation_question(question)
        
        if any(kw in q_lower for kw in ['distribution', 'spread', 'skew', 'outlier', 'outliers']):
            return self._answer_distribution_question(question)
        
        if any(kw in q_lower for kw in ['trend', 'time', 'growth', 'monthly', 'daily', 'weekly']):
            return self._answer_trend_question(question)
        
        if any(kw in q_lower for kw in ['category', 'type', 'group', 'segment']):
            return self._answer_category_question(question)
        
        if any(kw in q_lower for kw in ['missing', 'null', 'empty', 'quality']):
            return self._answer_quality_question(question)
        
        if any(kw in q_lower for kw in ['summary', 'overview', 'describe', 'tell me about']):
            return self._answer_summary_question(question)
        
        # General answer from context
        return self._answer_general_question(question, context)
    
    def _answer_kpi_question(self, question: str) -> str:
        """Answer questions about KPIs"""
        if not self.kpis:
            return "No KPIs could be extracted from the data. The dataset may not contain numeric columns."
        
        answer = "📊 **Key Performance Indicators (KPIs):**\n\n"
        
        for col, values in self.kpis.items():
            if col == '_calculated':
                answer += "**Calculated KPIs:**\n"
                for k, v in values.items():
                    label = k.replace('_', ' ').title()
                    if 'margin' in k:
                        answer += f"  • {label}: {v}%\n"
                    else:
                        answer += f"  • {label}: {v:,.2f}\n"
            else:
                answer += f"**{col}:**\n"
                answer += f"  • Total: {values['total']:,.2f}\n"
                answer += f"  • Average: {values['average']:,.2f}\n"
                answer += f"  • Range: {values['min']:,.2f} - {values['max']:,.2f}\n"
            answer += "\n"
        
        return answer
    
    def _answer_schema_question(self, question: str) -> str:
        """Answer questions about data schema"""
        if self.df is None:
            return "No data loaded."
        
        answer = f"📋 **Dataset Schema:**\n\n"
        answer += f"• **Rows:** {len(self.df):,}\n"
        answer += f"• **Columns:** {len(self.df.columns)}\n\n"
        
        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = self.df.select_dtypes(include=['datetime64']).columns.tolist()
        
        if numeric_cols:
            answer += f"**Numeric columns ({len(numeric_cols)}):** {', '.join(numeric_cols)}\n\n"
        if cat_cols:
            answer += f"**Categorical columns ({len(cat_cols)}):** {', '.join(cat_cols)}\n\n"
        if date_cols:
            answer += f"**Date columns ({len(date_cols)}):** {', '.join(date_cols)}\n\n"
        
        return answer
    
    def _answer_statistics_question(self, question: str) -> str:
        """Answer statistical questions"""
        if self.df is None:
            return "No data loaded."
        
        q_lower = question.lower()
        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        
        # Find which column the user is asking about
        target_col = None
        for col in self.df.columns:
            if col.lower() in q_lower:
                target_col = col
                break
        
        if target_col and target_col in numeric_cols:
            series = self.df[target_col]
            answer = f"📈 **Statistics for '{target_col}':**\n\n"
            answer += f"• Count: {int(series.count()):,}\n"
            answer += f"• Sum/Total: {series.sum():,.2f}\n"
            answer += f"• Mean: {series.mean():,.2f}\n"
            answer += f"• Median: {series.median():,.2f}\n"
            answer += f"• Std Dev: {series.std():,.2f}\n"
            answer += f"• Min: {series.min():,.2f}\n"
            answer += f"• Max: {series.max():,.2f}\n"
            answer += f"• Q1 (25%): {series.quantile(0.25):,.2f}\n"
            answer += f"• Q3 (75%): {series.quantile(0.75):,.2f}\n"
            return answer
        
        # General statistics for all numeric columns
        answer = "📈 **Statistics Summary:**\n\n"
        for col in numeric_cols:
            series = self.df[col]
            answer += f"**{col}:** Total={series.sum():,.2f}, Avg={series.mean():,.2f}, Min={series.min():,.2f}, Max={series.max():,.2f}\n"
        
        return answer
    
    def _answer_correlation_question(self, question: str) -> str:
        """Answer questions about correlations"""
        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        
        if len(numeric_cols) < 2:
            return "Not enough numeric columns for correlation analysis."
        
        corr = self.df[numeric_cols].corr()
        
        answer = "🔗 **Correlation Analysis:**\n\n"
        
        # Find strongest correlations
        pairs = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                val = corr.iloc[i, j]
                pairs.append((numeric_cols[i], numeric_cols[j], val))
        
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        
        for col1, col2, val in pairs[:10]:
            strength = "🟢 Strong" if abs(val) > 0.7 else "🟡 Moderate" if abs(val) > 0.4 else "🔴 Weak"
            direction = "positive" if val > 0 else "negative"
            answer += f"• {col1} ↔ {col2}: {val:.3f} ({strength} {direction})\n"
        
        return answer
    
    def _answer_distribution_question(self, question: str) -> str:
        """Answer questions about distributions"""
        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            return "No numeric columns available for distribution analysis."
        
        answer = "📊 **Distribution Analysis:**\n\n"
        
        for col in numeric_cols:
            series = self.df[col].dropna()
            if len(series) == 0:
                continue
            
            skew = series.skew()
            kurt = series.kurtosis()
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            outliers = int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())
            
            shape = "right-skewed ↗" if skew > 0.5 else "left-skewed ↙" if skew < -0.5 else "symmetric ↔"
            
            answer += f"**{col}:**\n"
            answer += f"  Shape: {shape} (skewness: {skew:.2f})\n"
            answer += f"  IQR: {iqr:.2f}\n"
            answer += f"  Outliers: {outliers}\n\n"
        
        return answer
    
    def _answer_trend_question(self, question: str) -> str:
        """Answer questions about trends"""
        # Find date column
        date_cols = self.df.select_dtypes(include=['datetime64']).columns.tolist()
        
        if not date_cols:
            for col in self.df.columns:
                if any(kw in col.lower() for kw in ['date', 'time']):
                    try:
                        pd.to_datetime(self.df[col].head(5))
                        date_cols.append(col)
                    except:
                        pass
        
        if not date_cols:
            return "No date/time columns found for trend analysis."
        
        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        if not numeric_cols:
            return "No numeric columns found for trend analysis."
        
        answer = "📈 **Trend Analysis:**\n\n"
        
        date_col = date_cols[0]
        try:
            dates = pd.to_datetime(self.df[date_col], errors='coerce')
            
            for val_col in numeric_cols[:3]:
                temp_df = pd.DataFrame({'date': dates, 'value': self.df[val_col]}).dropna()
                monthly = temp_df.groupby(temp_df['date'].dt.to_period('M'))['value'].sum()
                
                if len(monthly) > 1:
                    growth = ((monthly.iloc[-1] - monthly.iloc[0]) / monthly.iloc[0] * 100) if monthly.iloc[0] != 0 else 0
                    trend = "📈 Upward" if growth > 5 else "📉 Downward" if growth < -5 else "➡️ Stable"
                    
                    answer += f"**{val_col}:**\n"
                    answer += f"  Trend: {trend}\n"
                    answer += f"  Overall growth: {growth:.1f}%\n"
                    answer += f"  Best period: {monthly.idxmax()} ({monthly.max():,.2f})\n"
                    answer += f"  Worst period: {monthly.idxmin()} ({monthly.min():,.2f})\n\n"
        except Exception as e:
            answer += f"Could not analyze trends: {e}"
        
        return answer
    
    def _answer_category_question(self, question: str) -> str:
        """Answer questions about categorical data"""
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if not cat_cols:
            return "No categorical columns found in the data."
        
        answer = "📂 **Category Analysis:**\n\n"
        
        for col in cat_cols:
            value_counts = self.df[col].value_counts()
            total = len(self.df)
            
            answer += f"**{col}** ({len(value_counts)} categories):\n"
            for val, count in value_counts.head(5).items():
                pct = round(count / total * 100, 1)
                answer += f"  • {val}: {count:,} ({pct}%)\n"
            answer += "\n"
        
        return answer
    
    def _answer_quality_question(self, question: str) -> str:
        """Answer data quality questions"""
        if self.df is None:
            return "No data loaded."
        
        total_cells = len(self.df) * len(self.df.columns)
        missing_cells = int(self.df.isnull().sum().sum())
        missing_pct = round(missing_cells / total_cells * 100, 2) if total_cells > 0 else 0
        duplicates = int(self.df.duplicated().sum())
        dup_pct = round(duplicates / len(self.df) * 100, 2) if len(self.df) > 0 else 0
        
        # Quality score
        score = 100
        score -= missing_pct * 0.5
        score -= dup_pct * 0.3
        score = max(round(score, 1), 0)
        
        answer = f"🔍 **Data Quality Report:**\n\n"
        answer += f"• **Quality Score:** {score}/100\n"
        answer += f"• **Total Cells:** {total_cells:,}\n"
        answer += f"• **Missing Values:** {missing_cells:,} ({missing_pct}%)\n"
        answer += f"• **Duplicate Rows:** {duplicates:,} ({dup_pct}%)\n\n"
        
        # Columns with most missing values
        missing_by_col = self.df.isnull().sum()
        cols_with_missing = missing_by_col[missing_by_col > 0].sort_values(ascending=False)
        
        if len(cols_with_missing) > 0:
            answer += "**Columns with missing values:**\n"
            for col, count in cols_with_missing.head(10).items():
                pct = round(count / len(self.df) * 100, 1)
                answer += f"  • {col}: {count:,} ({pct}%)\n"
        else:
            answer += "✅ No missing values found!"
        
        return answer
    
    def _answer_summary_question(self, question: str) -> str:
        """Answer summary/overview questions"""
        if self.df is None:
            return "No data loaded."
        
        numeric_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        answer = f"📋 **Data Summary:**\n\n"
        answer += f"This dataset contains **{len(self.df):,} rows** and **{len(self.df.columns)} columns**.\n\n"
        
        if numeric_cols:
            answer += f"**Numeric columns ({len(numeric_cols)}):** {', '.join(numeric_cols)}\n"
            for col in numeric_cols[:5]:
                answer += f"  • {col}: Total={self.df[col].sum():,.2f}, Avg={self.df[col].mean():,.2f}\n"
            answer += "\n"
        
        if cat_cols:
            answer += f"**Categorical columns ({len(cat_cols)}):** {', '.join(cat_cols)}\n"
            for col in cat_cols[:5]:
                answer += f"  • {col}: {self.df[col].nunique()} unique values\n"
            answer += "\n"
        
        # Data quality
        missing = int(self.df.isnull().sum().sum())
        duplicates = int(self.df.duplicated().sum())
        answer += f"**Data Quality:**\n"
        answer += f"  • Missing values: {missing:,}\n"
        answer += f"  • Duplicate rows: {duplicates:,}\n"
        
        return answer
    
    def _answer_general_question(self, question: str, context: str) -> str:
        """Generate a general answer from context"""
        # Find columns mentioned in the question
        q_lower = question.lower()
        mentioned_cols = [col for col in self.df.columns if col.lower() in q_lower]
        
        if mentioned_cols:
            answer = f"📊 **Analysis for: {', '.join(mentioned_cols)}**\n\n"
            for col in mentioned_cols:
                if self.df[col].dtype in ['int64', 'float64']:
                    answer += f"**{col}:**\n"
                    answer += f"  • Total: {self.df[col].sum():,.2f}\n"
                    answer += f"  • Average: {self.df[col].mean():,.2f}\n"
                    answer += f"  • Min-Max: {self.df[col].min():,.2f} to {self.df[col].max():,.2f}\n\n"
                else:
                    answer += f"**{col}:**\n"
                    top_vals = self.df[col].value_counts().head(5)
                    for val, count in top_vals.items():
                        answer += f"  • {val}: {count:,}\n"
                    answer += "\n"
            return answer
        
        # Return context-based answer
        if context:
            return f"Based on your data:\n\n{context}"
        
        return (
            "I can help you understand your data! Try asking about:\n"
            "• KPIs and metrics\n"
            "• Column statistics (mean, sum, min, max)\n"
            "• Data quality (missing values, duplicates)\n"
            "• Correlations between columns\n"
            "• Trends over time\n"
            "• Category breakdowns\n"
            "• Data distribution and outliers"
        )
    
    def get_data_summary(self) -> Dict:
        """Get complete data summary"""
        return {
            'summary': self.data_summary,
            'kpis': self.kpis,
            'documents_count': len(self.data_documents)
        }
