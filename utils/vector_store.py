"""
Vector store: Handles semantic search using embeddings.
Uses ChromaDB for storing and searching vector embeddings.
"""
import chromadb
import uuid
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from utils.config import Config

class VectorStore:
    """Manages vector embeddings and semantic search"""
    
    def __init__(self):
        # Initialize embedding model
        print(f"Loading embedding model: {Config.EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=Config.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"Vector store initialized. Collection size: {self.collection.count()}")
    
    def add_documents(self, chunks: List[Dict]):
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of document chunks with text and metadata
        """
        if not chunks:
            print("No chunks to add")
            return
        
        print(f"Adding {len(chunks)} chunks to vector store...")
        
        # Prepare data for ChromaDB
        texts = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        # FIX: Use unique IDs based on source filename + chunk index
        # This prevents new uploads from overwriting existing ones
        ids = [
            f"{chunk['metadata'].get('source', 'unknown')}_{chunk['chunk_index']}_{uuid.uuid4().hex[:8]}"
            for chunk in chunks
        ]
        
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        ).tolist()
        
        # Add to ChromaDB
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Successfully added {len(chunks)} chunks")
    
    def search(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Semantic search for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant document chunks with scores
        """
        if top_k is None:
            top_k = Config.TOP_K_RESULTS

        # Don't search if collection is empty
        if self.collection.count() == 0:
            return []

        # Clamp top_k to collection size to avoid ChromaDB errors
        top_k = min(top_k, self.collection.count())
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True
        ).tolist()
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        search_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                result = {
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': 1 - results['distances'][0][i],
                    'id': results['ids'][0][i]
                }
                search_results.append(result)
        
        return search_results
    
    def clear(self):
        """Clear all documents from the vector store"""
        try:
            self.client.delete_collection("documents")
            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            print("Vector store cleared")
        except Exception as e:
            print(f"Error clearing vector store: {str(e)}")
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        return {
            'total_documents': self.collection.count(),
            'embedding_model': Config.EMBEDDING_MODEL
        }