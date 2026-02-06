import numpy as np
from typing import Dict, List
import json

print("=" * 80)
print("RAG SYSTEM: VECTOR EMBEDDINGS GENERATION")
print("=" * 80)

# ============================================================================
# STEP 1: COLLECT ALL DATA CONTEXT
# ============================================================================
print("\n📦 STEP 1: Collecting Data Context from Pipeline")
print("-" * 80)

# Gather all available context from upstream blocks
data_context = {
    'data_profile': profile_report,
    'cleaning_summary': cleaning_summary,
    'eda_findings': eda_summary,
    'kpis': kpis
}

print(f"✅ Collected context from 4 sources:")
print(f"  • Data Profile Report: {len(profile_report)} sections")
print(f"  • Cleaning Summary: {len(cleaning_summary['actions'])} actions")
print(f"  • EDA Findings: {len(eda_summary)} analysis sections")
print(f"  • KPIs: {len(kpis)} metrics")

# ============================================================================
# STEP 2: CREATE TEXT CHUNKS FOR EMBEDDING
# ============================================================================
print("\n📝 STEP 2: Creating Text Chunks for Embedding")
print("-" * 80)

text_chunks = []
chunk_metadata = []

# Chunk 1: Dataset Overview & Quality
overview_text = f"""
DATASET OVERVIEW AND QUALITY PROFILE:
- Total Rows: {profile_report['dataset_overview']['total_rows']}
- Total Columns: {profile_report['dataset_overview']['total_columns']}
- Memory Usage: {profile_report['dataset_overview']['memory_usage_mb']} MB
- Duplicate Rows: {profile_report['dataset_overview']['duplicate_rows']}
- Data Types: {len(data_context['data_profile']['data_types']['numeric'])} numeric, {len(data_context['data_profile']['data_types']['categorical'])} categorical, {len(data_context['data_profile']['data_types']['boolean'])} boolean
- Missing Values: {sum(s['missing_count'] for s in profile_report['missing_values'])} total
- Domain: Human Resources / Employee Analytics
"""
text_chunks.append(overview_text.strip())
chunk_metadata.append({'type': 'overview', 'source': 'data_profiling'})

# Chunk 2: Data Cleaning Actions
cleaning_text = f"""
DATA CLEANING ACTIONS PERFORMED:
- Original Shape: {cleaning_summary['original_shape']}
- Final Shape: {cleaning_summary['final_shape']}
- Duplicates Removed: {cleaning_summary['duplicates_removed']}
- Missing Values Handled: {cleaning_summary['missing_values_removed']}
- Outliers Treated: {cleaning_summary['outliers_treated']}
- Type Optimizations: {cleaning_summary['type_optimizations']}
- Actions: {'; '.join(cleaning_summary['actions'])}
"""
text_chunks.append(cleaning_text.strip())
chunk_metadata.append({'type': 'cleaning', 'source': 'intelligent_data_cleaning'})

# Chunk 3: Statistical Distributions
if eda_summary['distribution_insights']:
    dist_text = "STATISTICAL DISTRIBUTION ANALYSIS:\n"
    for col, stats in eda_summary['distribution_insights'].items():
        dist_text += f"- {col}: Normal={stats['is_normal']}, Skewness={stats['skewness']:.2f}, Kurtosis={stats['kurtosis']:.2f}\n"
    text_chunks.append(dist_text.strip())
    chunk_metadata.append({'type': 'distributions', 'source': 'data_profiling'})

# Chunk 4: Correlations
if eda_summary['strong_correlations']:
    corr_text = "CORRELATION FINDINGS:\n"
    for corr in eda_summary['strong_correlations']:
        corr_text += f"- {corr['col1']} ↔ {corr['col2']}: correlation={corr['correlation']:.4f}\n"
    text_chunks.append(corr_text.strip())
    chunk_metadata.append({'type': 'correlations', 'source': 'data_profiling'})

# Chunk 5: Key Performance Indicators
kpi_text = "KEY PERFORMANCE INDICATORS:\n"
for kpi_name, kpi_value in kpis.items():
    kpi_text += f"- {kpi_name}: {kpi_value}\n"
text_chunks.append(kpi_text.strip())
chunk_metadata.append({'type': 'kpis', 'source': 'data_profiling'})

# Chunk 6: Insights and Recommendations
insights_text = f"""
KEY INSIGHTS AND RECOMMENDATIONS:
Insights:
{chr(10).join(f'- {insight}' for insight in eda_summary['insights'])}

Recommendations:
{chr(10).join(f'- {rec}' for rec in profile_report['recommendations'])}
"""
text_chunks.append(insights_text.strip())
chunk_metadata.append({'type': 'insights', 'source': 'data_profiling'})

print(f"✅ Created {len(text_chunks)} text chunks:")
for i, meta in enumerate(chunk_metadata):
    print(f"  {i+1}. {meta['type']} ({meta['source']})")

# ============================================================================
# STEP 3: GENERATE SIMPLE EMBEDDINGS
# ============================================================================
print("\n🧮 STEP 3: Generating Vector Embeddings")
print("-" * 80)

def simple_text_embedding(text: str, dim: int = 384) -> np.ndarray:
    """
    Generate a simple deterministic embedding based on text features.
    In production, use sentence-transformers or OpenAI embeddings.
    """
    # Use text features to create a reproducible embedding
    words = text.lower().split()
    
    # Create deterministic seed from text
    seed = sum(ord(c) for c in text[:100]) % 10000
    np.random.seed(seed)
    
    # Generate base embedding
    embedding = np.random.randn(dim)
    
    # Add text-specific features
    embedding[0] = len(words)  # Word count
    embedding[1] = len(text)   # Character count
    embedding[2] = text.count('.')  # Sentence count proxy
    embedding[3] = sum(1 for w in words if w.isdigit())  # Number count
    
    # Normalize
    embedding = embedding / np.linalg.norm(embedding)
    
    return embedding

# Generate embeddings for all chunks
embeddings = []
for i, chunk in enumerate(text_chunks):
    emb = simple_text_embedding(chunk)
    embeddings.append(emb)
    print(f"  ✅ Chunk {i+1}: Generated {len(emb)}-dimensional embedding")

embeddings_array = np.array(embeddings)

print(f"\n✅ Generated embeddings matrix: {embeddings_array.shape}")

# ============================================================================
# STEP 4: CREATE VECTOR STORE
# ============================================================================
print("\n💾 STEP 4: Creating Vector Store")
print("-" * 80)

vector_store = {
    'embeddings': embeddings_array,
    'chunks': text_chunks,
    'metadata': chunk_metadata,
    'dim': embeddings_array.shape[1],
    'count': len(text_chunks)
}

print(f"✅ Vector store created:")
print(f"  • Dimension: {vector_store['dim']}")
print(f"  • Total Vectors: {vector_store['count']}")
print(f"  • Storage Size: ~{embeddings_array.nbytes / 1024:.2f} KB")

# ============================================================================
# STEP 5: TEST SIMILARITY SEARCH
# ============================================================================
print("\n🔍 STEP 5: Testing Similarity Search")
print("-" * 80)

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def search_similar(query_embedding: np.ndarray, top_k: int = 3) -> List[Dict]:
    """Find most similar chunks to query."""
    similarities = []
    for i, emb in enumerate(embeddings_array):
        sim = cosine_similarity(query_embedding, emb)
        similarities.append({
            'chunk_id': i,
            'similarity': sim,
            'metadata': chunk_metadata[i],
            'text_preview': text_chunks[i][:150] + '...'
        })
    
    # Sort by similarity
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    return similarities[:top_k]

# Test query: "What is the salary distribution?"
test_query = "What is the salary distribution and compensation metrics?"
test_query_embedding = simple_text_embedding(test_query)

print(f"Test Query: '{test_query}'")
print(f"\nTop 3 Most Relevant Chunks:")
results = search_similar(test_query_embedding, top_k=3)

for i, result in enumerate(results, 1):
    print(f"\n  {i}. [{result['metadata']['type']}] (similarity: {result['similarity']:.4f})")
    print(f"     {result['text_preview']}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("✅ VECTOR EMBEDDING SYSTEM READY")
print("=" * 80)
print(f"📊 Embedded {len(text_chunks)} knowledge chunks")
print(f"🧮 Vector dimension: {embeddings_array.shape[1]}")
print(f"💡 Ready for RAG-based LLM integration")
print("\nNext: Connect to LLM for intelligent Q&A and insights generation")