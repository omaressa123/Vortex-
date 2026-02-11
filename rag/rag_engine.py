import os
import json
import requests
from typing import Any, List, Optional, Dict
import numpy as np

# Import local LLM support
try:
    from utils.local_llm import LocalOllamaLLM, check_ollama_available, get_available_models
    LOCAL_LLM_AVAILABLE = True
except ImportError:
    LOCAL_LLM_AVAILABLE = False
    print("Local LLM not available. Install with: pip install requests")

# Try to import sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    print("✅ Sentence transformers available")
except ImportError as e:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print(f"❌ Sentence transformers not available: {e}")
    print("Install with: pip install sentence-transformers")

class RAGSystem:
    def __init__(self, knowledge_base_path="rag/knowledge_base", api_key=None, use_local=False, local_model="llama3"):
        self.knowledge_base_path = knowledge_base_path
        self.api_key = api_key
        self.use_local = use_local
        self.local_model = local_model
        self.vector_store = None
        self.llm = None
        
        if use_local and LOCAL_LLM_AVAILABLE:
            # Use local LLM - NO API KEY NEEDED!
            print(f"🔹 Using Local LLM: {local_model}")
            if check_ollama_available():
                self.llm = LocalOllamaLLM(model=local_model)
                self._initialize_knowledge_base()
                print("✅ Local RAG System Active!")
            else:
                print("❌ Ollama not running. Please start with: ollama serve")
                self.llm = None
        elif api_key:
            # Use cloud APIs (original logic)
            self._setup_cloud_api(api_key)
        else:
            print("❌ No API key or local LLM configured")
            self.llm = None
    
    def _setup_cloud_api(self, api_key):
        """Setup cloud API (OpenAI/DeepSeek)"""
        # Check for RapidAPI Key format (heuristic: doesn't start with sk- and is long)
        is_openai = api_key.startswith("sk-")
        
        if is_openai:
            try:
                from langchain_community.embeddings import OpenAIEmbeddings
                from langchain_community.chat_models import ChatOpenAI
                os.environ["OPENAI_API_KEY"] = api_key
                self.embeddings = OpenAIEmbeddings()
                self.llm = ChatOpenAI(temperature=0.4, model_name="gpt-3.5-turbo")
                self._initialize_knowledge_base()
            except ImportError:
                print("❌ LangChain components not available for OpenAI")
                self.llm = None
        else:
            # Use DeepSeek RapidAPI
            try:
                from utils.deepseek_llm import ChatDeepSeekRapidAPI
                self.llm = ChatDeepSeekRapidAPI(api_key=api_key)
                # Note: DeepSeek via RapidAPI doesn't provide embeddings in this integration.
                # RAG retrieval will be disabled, but LLM features (analyze_schema) will work.
                print("Using DeepSeek API. RAG Retrieval disabled due to missing Embeddings.")
            except ImportError:
                print("❌ DeepSeek integration not available")
                self.llm = None
    
    def _initialize_knowledge_base(self):
        """Initialize knowledge base with embeddings"""
        try:
            print(f"🔍 Initializing knowledge base from: {self.knowledge_base_path}")
            
            # Load all text files from knowledge base
            documents = []
            if os.path.exists(self.knowledge_base_path):
                for filename in os.listdir(self.knowledge_base_path):
                    if filename.endswith('.txt'):
                        file_path = os.path.join(self.knowledge_base_path, filename)
                        print(f"📄 Loading: {filename}")
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            documents.append(content)
            else:
                print(f"❌ Knowledge base path not found: {self.knowledge_base_path}")
                return
            
            if not documents:
                print("❌ No knowledge base documents found!")
                return
            
            print(f"📚 Loaded {len(documents)} documents")
            
            if self.use_local:
                if SENTENCE_TRANSFORMERS_AVAILABLE:
                    print("🔹 Using sentence transformers for embeddings")
                    # For local LLM, use sentence transformers for embeddings
                    self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')
                    
                    # Create embeddings for all texts
                    print("🔄 Creating embeddings...")
                    embeddings = self.embeddings.encode(documents)
                    
                    # Create simple vector store using numpy
                    self.vector_store = {
                        'documents': documents,
                        'embeddings': embeddings
                    }
                    print(f"✅ Local RAG initialized with {len(documents)} documents")
                else:
                    print("❌ Sentence transformers not available for local RAG")
                    print("Install with: pip install sentence-transformers")
                    self.vector_store = None
            elif hasattr(self, 'embeddings'):
                # Use cloud embeddings if available
                try:
                    print("🔹 Using cloud embeddings")
                    # Simple chunking for cloud embeddings
                    chunk_size = 1000
                    chunks = []
                    for doc in documents:
                        for i in range(0, len(doc), chunk_size):
                            chunks.append(doc[i:i+chunk_size])
                    
                    # Create embeddings
                    print("🔄 Creating cloud embeddings...")
                    embeddings = self.embeddings.embed_documents(chunks)
                    
                    self.vector_store = {
                        'chunks': chunks,
                        'embeddings': embeddings
                    }
                    print(f"✅ Cloud RAG initialized with {len(chunks)} chunks")
                except Exception as e:
                    print(f"❌ Cloud embeddings failed: {e}")
                    self.vector_store = None
            else:
                print("❌ No embeddings available for RAG initialization")
                self.vector_store = None
                
        except Exception as e:
            print(f"❌ Error initializing knowledge base: {e}")
            self.vector_store = None
    
    def retrieve_rules(self, query, k=3):
        """Retrieve relevant rules from knowledge base"""
        if not self.vector_store or not self.embeddings:
            return []
        
        try:
            # Create embedding for query
            query_embedding = self.embeddings.encode([query])
            
            if self.use_local:
                # Local RAG with numpy
                documents = self.vector_store['documents']
                embeddings = self.vector_store['embeddings']
                
                # Calculate similarity
                similarities = np.dot(embeddings, query_embedding.T).flatten()
                
                # Get top k most similar
                top_indices = np.argsort(similarities)[-k:][::-1]
                
                return [documents[i] for i in top_indices]
            else:
                # Cloud RAG
                chunks = self.vector_store['chunks']
                embeddings = self.vector_store['embeddings']
                
                # Calculate similarity
                similarities = np.dot(embeddings, query_embedding[0])
                
                # Get top k most similar
                top_indices = np.argsort(similarities)[-k:][::-1]
                
                return [chunks[i] for i in top_indices]
                
        except Exception as e:
            print(f"Error retrieving rules: {e}")
            return []
    
    def get_decision_support(self, query):
        """Get decision support from RAG system"""
        if not self.llm:
            return "No LLM available for decision support"
        
        try:
            # Retrieve relevant rules
            relevant_rules = self.retrieve_rules(query)
            context = "\n".join(relevant_rules)
            
            # Generate response using LLM
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content="You are a data analysis assistant. Use the provided context to answer questions about data cleaning and analysis."),
                HumanMessage(content=f"Context: {context}\n\nQuestion: {query}")
            ]
            
            result = self.llm._generate(messages)
            return result.generations[0].message.content
            
        except Exception as e:
            return f"Error generating decision support: {str(e)}"
    
    def analyze_schema(self, schema_info, query):
        """Analyze schema with RAG support"""
        if not self.llm:
            return "No LLM available for schema analysis"
        
        try:
            # Get relevant context
            relevant_rules = self.retrieve_rules(query, k=2)
            context = "\n".join(relevant_rules)
            
            # Generate analysis
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content="You are a data analysis expert. Analyze the provided schema and answer questions about it."),
                HumanMessage(content=f"Context: {context}\n\nSchema: {schema_info}\n\nQuestion: {query}")
            ]
            
            result = self.llm._generate(messages)
            return result.generations[0].message.content
            
        except Exception as e:
            return f"Error analyzing schema: {str(e)}"

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)
        
        self.vector_store = FAISS.from_documents(texts, self.embeddings)
        print("Knowledge base initialized successfully.")

    def retrieve_rules(self, query, k=3):
        if not self.vector_store:
            return ["RAG System not initialized (Missing API Key or Documents)."]
        
        docs = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]

    def get_decision_support(self, context, question):
        """
        Decision-support RAG: Returns advice based on rules and context.
        """
        if not self.llm:
            return "RAG System unavailable."

        rules_text = ""
        if self.vector_store:
            rules = self.retrieve_rules(question)
            rules_text = "\n".join(rules)

        prompt = f"""
        You are an intelligent data assistant.
        Context: {context}
        Relevant Rules:
        {rules_text}
        
        Question: {question}
        
        Based on the context and rules, provide a recommendation.
        """
        
        response = self.llm.invoke(prompt)
        return response.content

    def analyze_schema(self, schema_info, query):
        """
        Schema-aware RAG: Understands schema and answers questions.
        """
        if not self.llm:
            return "LLM unavailable."

        prompt = f"""
        You are a schema-aware data assistant.
        Schema Information:
        {schema_info}
        
        User Query: {query}
        
        Provide an answer or insight based on the schema.
        """
        
        response = self.llm.invoke(prompt)
        return response.content
