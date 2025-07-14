# This file should contain the VectorStore class and related vector DB utilities.
# Move the code from app/vector_store.py here.

from langchain_elasticsearch import ElasticsearchStore
from elasticsearch import Elasticsearch
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

class VectorStore:
    """
    Manages the connection to Elasticsearch and handles document embedding and retrieval.
    """
    def __init__(self, host="localhost", port="9200"):
        self.host = host
        self.port = port
        self.embedding_model = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
        self.client = Elasticsearch(f"http://{self.host}:{self.port}")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self._connect()

    def _connect(self):
        """Establishes a connection to the Elasticsearch server."""
        if not self.client.ping():
            print("Failed to connect to Elasticsearch")
        print("Successfully connected to Elasticsearch.")

    def get_or_create_store(self, index_name: str) -> ElasticsearchStore:
        """
        Gets an ElasticsearchStore instance for the given index.
        """
        return ElasticsearchStore(
            es_connection=self.client,
            index_name=index_name,
            embedding=self.embedding_model
        )

    def add_documents(self, index_name: str, documents: list[str]):
        """
        Embeds and adds documents to the specified Elasticsearch index.
        """
        chunks = self.text_splitter.create_documents(documents)
        store = self.get_or_create_store(index_name)
        store.add_documents(documents=chunks)
        print(f"Successfully added {len(chunks)} chunks to index '{index_name}'.")

    def search(self, index_name: str, query: str, top_k: int = 5) -> list[dict]:
        """
        Searches for the most similar documents in the index based on a text query.
        """
        store = self.get_or_create_store(index_name)
        results = store.similarity_search_with_score(query=query, k=top_k)
        
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "text": doc.page_content,
                "score": score
            })
            
        return formatted_results 