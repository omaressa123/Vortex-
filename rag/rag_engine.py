import os
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import CharacterTextSplitter
from utils.deepseek_llm import ChatDeepSeekRapidAPI

class RAGSystem:
    def __init__(self, knowledge_base_path="rag/knowledge_base", api_key=None):
        self.knowledge_base_path = knowledge_base_path
        self.api_key = api_key
        self.vector_store = None
        self.llm = None
        
        if self.api_key:
            # Check for RapidAPI Key format (heuristic: doesn't start with sk- and is long)
            is_openai = self.api_key.startswith("sk-")
            
            if is_openai:
                os.environ["OPENAI_API_KEY"] = self.api_key
                self.embeddings = OpenAIEmbeddings()
                self.llm = ChatOpenAI(temperature=0.4, model_name="gpt-3.5-turbo")
                self._initialize_knowledge_base()
            else:
                # Use DeepSeek RapidAPI
                self.llm = ChatDeepSeekRapidAPI(api_key=self.api_key)
                # Note: DeepSeek via RapidAPI doesn't provide embeddings in this integration.
                # RAG retrieval will be disabled, but LLM features (analyze_schema) will work.
                print("Using DeepSeek API. RAG Retrieval disabled due to missing Embeddings.")

    def _initialize_knowledge_base(self):
        documents = []
        if not os.path.exists(self.knowledge_base_path):
            print(f"Warning: Knowledge base path {self.knowledge_base_path} not found.")
            return

        for filename in os.listdir(self.knowledge_base_path):
            if filename.endswith(".txt"):
                file_path = os.path.join(self.knowledge_base_path, filename)
                loader = TextLoader(file_path)
                documents.extend(loader.load())
        
        if not documents:
            print("No documents found in knowledge base.")
            return

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
