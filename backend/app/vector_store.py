from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType
from sentence_transformers import SentenceTransformer

class VectorStore:
    """
    Manages the connection to Milvus and handles document embedding and retrieval.
    """
    def __init__(self, host="localhost", port="19530"):
        self.host = host
        self.port = port
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self._connect()

    def _connect(self):
        """Establishes a connection to the Milvus server."""
        try:
            connections.connect("default", host=self.host, port=self.port)
            print("Successfully connected to Milvus.")
        except Exception as e:
            print(f"Failed to connect to Milvus: {e}")

    def get_or_create_collection(self, name: str) -> Collection:
        """
        Gets a collection or creates it if it doesn't exist.
        The schema includes a primary key, the original text, and the vector embedding.
        """
        if utility.has_collection(name):
            print(f"Collection '{name}' already exists.")
            return Collection(name)

        print(f"Collection '{name}' not found. Creating new collection...")

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_model.get_sentence_embedding_dimension())
        ]
        schema = CollectionSchema(fields, description=f"{name} collection")
        collection = Collection(name, schema)

        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        print(f"Successfully created collection '{name}' with index.")
        return collection

    def add_documents(self, collection_name: str, documents: list[str]):
        """
        Embeds and adds documents to the specified collection.
        """
        collection = self.get_or_create_collection(collection_name)
        
        # Generate embeddings for the documents
        embeddings = self.embedding_model.encode(documents)
        
        data_to_insert = [
            documents, 
            embeddings 
        ]
        
        result = collection.insert(data_to_insert)
        collection.flush() # Ensure data is written to disk
        print(f"Successfully inserted {len(documents)} documents. Pks: {result.primary_keys}")
        return result

    def search(self, collection_name: str, query: str, top_k: int = 5) -> list[dict]:
        """
        Searches for the most similar documents in the collection based on a text query.
        """
        collection = self.get_or_create_collection(collection_name)
        collection.load()

        query_embedding = self.embedding_model.encode([query])

        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10},
        }

        results = collection.search(
            data=query_embedding,
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text"]
        )

        formatted_results = []
        for hit in results[0]:
            formatted_results.append({
                "id": hit.id,
                "distance": hit.distance,
                "text": hit.entity.get('text')
            })
        
        collection.release()
        return formatted_results
