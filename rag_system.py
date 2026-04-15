"""
RAG System: Main application that ties everything together.
Combines document processing, vector search, and LLM generation.
NOW WITH CONVERSATION HISTORY!
"""
from typing import List, Dict, Optional
from datetime import datetime
import json
import os
from utils.config import Config
from utils.document_processor import DocumentProcessor
from utils.vector_store import VectorStore
from utils.llm_interface import LLMInterface

class RAGSystem:
    """Main RAG (Retrieval-Augmented Generation) system with conversation tracking"""
    
    def __init__(self):
        """Initialize all components of the RAG system"""
        print("Initializing RAG System...")
        
        # Validate configuration
        Config.validate()
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.llm = LLMInterface()
        
        # Conversation history storage
        self.conversations = {}  # {session_id: {messages: [], created_at: datetime}}
        self.history_file = './data/conversation_history.json'
        
        # Load existing conversations
        self._load_conversations()
        
        print("RAG System ready!")
    
    def _load_conversations(self):
        """Load conversation history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.conversations = data
                print(f"Loaded {len(self.conversations)} conversation(s)")
        except Exception as e:
            print(f"Could not load conversation history: {e}")
    
    def _save_conversations(self):
        """Save conversation history to file"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump(self.conversations, f, indent=2)
        except Exception as e:
            print(f"Could not save conversation history: {e}")
    
    def create_session(self, session_id: str = None) -> str:
        """
        Create a new conversation session.
        
        Args:
            session_id: Optional custom session ID
            
        Returns:
            Session ID
        """
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.conversations[session_id] = {
            'messages': [],
            'created_at': datetime.now().isoformat(),
            'title': 'New Conversation'
        }
        self._save_conversations()
        return session_id
    
    def get_conversation(self, session_id: str) -> Optional[Dict]:
        """Get a conversation by session ID"""
        return self.conversations.get(session_id)
    
    def list_conversations(self) -> List[Dict]:
        """List all conversations with metadata"""
        conversations = []
        for session_id, data in self.conversations.items():
            conversations.append({
                'session_id': session_id,
                'title': data.get('title', 'Untitled'),
                'created_at': data.get('created_at'),
                'message_count': len(data.get('messages', []))
            })
        return sorted(conversations, key=lambda x: x['created_at'], reverse=True)
    
    def delete_conversation(self, session_id: str):
        """Delete a conversation"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            self._save_conversations()
    
    def clear_all_conversations(self):
        """Clear all conversation history"""
        self.conversations = {}
        self._save_conversations()
    
    def index_documents(self, directory_path: str = None):
        """
        Process and index documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents.
                           Uses Config.DOCUMENTS_DIR if not provided.
        """
        if directory_path is None:
            directory_path = Config.DOCUMENTS_DIR
        
        print(f"\n{'='*50}")
        print(f"Indexing documents from: {directory_path}")
        print(f"{'='*50}\n")
        
        # Process all documents in the directory
        chunks = self.document_processor.process_directory(directory_path)
        
        if not chunks:
            print("\nNo documents found to index!")
            return
        
        print(f"\nTotal chunks created: {len(chunks)}")
        
        # Add to vector store
        self.vector_store.add_documents(chunks)
        
        print("\n✓ Indexing complete!")
    
    def index_single_document(self, file_path: str):
        """
        Process and index a single document.
        
        Args:
            file_path: Path to the document file
        """
        print(f"\nIndexing document: {file_path}")
        
        chunks = self.document_processor.process_document(file_path)
        
        if chunks:
            self.vector_store.add_documents(chunks)
            print(f"✓ Indexed {len(chunks)} chunks")
        else:
            print("No chunks created from document")
    
    def query(
        self,
        question: str,
        session_id: str = None,
        top_k: int = None,
        return_sources: bool = True,
        use_history: bool = True
    ) -> Dict:
        """
        Query the RAG system with a question.
        
        Args:
            question: User's question
            session_id: Conversation session ID
            top_k: Number of relevant documents to retrieve
            return_sources: Whether to return source documents
            use_history: Whether to use conversation history
            
        Returns:
            Dictionary containing answer, sources, and session info
        """
        print(f"\nQuery: {question}")
        
        # Create session if needed
        if session_id is None:
            session_id = self.create_session()
        elif session_id not in self.conversations:
            self.create_session(session_id)
        
        # Step 1: Retrieve relevant documents
        print("  → Searching knowledge base...")
        relevant_docs = self.vector_store.search(question, top_k)
        
        if not relevant_docs:
            answer = "I couldn't find any relevant information in the knowledge base to answer your question."
            self._add_to_history(session_id, question, answer, [])
            return {
                'answer': answer,
                'sources': [],
                'session_id': session_id
            }
        
        print(f"  → Found {len(relevant_docs)} relevant documents")
        
        # Step 2: Get conversation history for context
        conversation_history = None
        if use_history and session_id in self.conversations:
            # Convert to format expected by LLM
            messages = self.conversations[session_id]['messages']
            if messages:
                conversation_history = []
                for msg in messages[-6:]:  # Last 3 exchanges (6 messages)
                    conversation_history.append({
                        'role': 'user',
                        'content': msg['question']
                    })
                    conversation_history.append({
                        'role': 'assistant',
                        'content': msg['answer']
                    })
        
        # Step 3: Generate response using LLM
        print("  → Generating answer...")
        answer = self.llm.generate_response(
            question,
            relevant_docs,
            conversation_history
        )
        
        # Update conversation title if it's the first message
        if len(self.conversations[session_id]['messages']) == 0:
            self.conversations[session_id]['title'] = question[:50] + ('...' if len(question) > 50 else '')
        
        # Add to conversation history
        self._add_to_history(session_id, question, answer, relevant_docs)
        
        # Prepare response
        response = {
            'answer': answer,
            'session_id': session_id
        }
        
        if return_sources:
            response['sources'] = [
                {
                    'text': doc['text'][:200] + "...",  # Preview
                    'source': doc['metadata'].get('source', 'Unknown'),
                    'relevance': doc['score']
                }
                for doc in relevant_docs
            ]
        
        return response
    
    def _add_to_history(self, session_id: str, question: str, answer: str, sources: List[Dict]):
        """Add a Q&A pair to conversation history"""
        if session_id not in self.conversations:
            self.create_session(session_id)
        
        self.conversations[session_id]['messages'].append({
            'question': question,
            'answer': answer,
            'sources': [s['metadata'].get('source', 'Unknown') for s in sources],
            'timestamp': datetime.now().isoformat()
        })
        self._save_conversations()
    
    def export_conversation(self, session_id: str, format: str = 'txt') -> str:
        """
        Export a conversation to text or markdown.
        
        Args:
            session_id: Session to export
            format: 'txt' or 'md'
            
        Returns:
            Formatted conversation string
        """
        if session_id not in self.conversations:
            return "Conversation not found"
        
        conversation = self.conversations[session_id]
        title = conversation.get('title', 'Untitled')
        created = conversation.get('created_at', 'Unknown')
        
        if format == 'md':
            output = f"# {title}\n\n"
            output += f"**Created:** {created}\n\n"
            output += "---\n\n"
            
            for i, msg in enumerate(conversation['messages'], 1):
                output += f"### Question {i}\n{msg['question']}\n\n"
                output += f"### Answer {i}\n{msg['answer']}\n\n"
                if msg.get('sources'):
                    output += f"**Sources:** {', '.join(msg['sources'])}\n\n"
                output += "---\n\n"
        else:
            output = f"{title}\n"
            output += f"Created: {created}\n"
            output += "="*50 + "\n\n"
            
            for i, msg in enumerate(conversation['messages'], 1):
                output += f"Q{i}: {msg['question']}\n"
                output += f"A{i}: {msg['answer']}\n"
                if msg.get('sources'):
                    output += f"Sources: {', '.join(msg['sources'])}\n"
                output += "\n" + "-"*50 + "\n\n"
        
        return output
    
    def clear_index(self):
        """Clear all indexed documents"""
        print("\nClearing index...")
        self.vector_store.clear()
        print("✓ Index cleared")
    
    def get_stats(self) -> Dict:
        """Get system statistics"""
        stats = self.vector_store.get_stats()
        stats['llm_provider'] = Config.LLM_PROVIDER
        stats['llm_model'] = Config.LLM_MODEL
        stats['total_conversations'] = len(self.conversations)
        return stats
    
    def chat_without_rag(self, message: str) -> str:
        """
        Simple chat without RAG (for comparison/testing).
        
        Args:
            message: User message
            
        Returns:
            LLM response
        """
        return self.llm.simple_chat(message)


# Example usage
if __name__ == "__main__":
    # Initialize system
    rag = RAGSystem()
    
    # Index documents
    rag.index_documents()
    
    # Create a conversation session
    session_id = rag.create_session()
    print(f"\nSession ID: {session_id}")
    
    # Example queries with conversation history
    queries = [
        "What is machine learning?",
        "Can you explain that in simpler terms?",  # Uses context from previous answer
        "What are some applications of it?",  # "it" refers to machine learning
    ]
    
    for query in queries:
        result = rag.query(query, session_id=session_id)
        print(f"\n{'='*60}")
        print(f"Q: {query}")
        print(f"{'='*60}")
        print(f"A: {result['answer']}")
    
    # Export conversation
    export = rag.export_conversation(session_id, format='md')
    print("\n" + export)