"""
Document processor: Loads and chunks documents for semantic search.
Supports PDF, DOCX, and TXT files.
REVISED: Swapped PyPDF2 → PyMuPDF (fitz) for better text extraction.
"""
import os
from typing import List, Dict
from pathlib import Path
import fitz  # PyMuPDF — replaces PyPDF2
import docx
from langchain.text_splitter import RecursiveCharacterTextSplitter
from utils.config import Config

class DocumentProcessor:
    """Processes documents and splits them into chunks"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_document(self, file_path: str) -> str:
        """
        Load a document and extract its text content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text content
        """
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            return self._load_pdf(file_path)
        elif file_extension == '.docx':
            return self._load_docx(file_path)
        elif file_extension == '.txt':
            return self._load_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    def _load_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF using PyMuPDF.
        Better than PyPDF2 for modern PDFs, scanned docs, and complex layouts.
        """
        doc = fitz.open(file_path)
        text = ""
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            if page_text.strip():  # skip blank pages
                text += f"\n[Page {page_num + 1}]\n{page_text}"
        doc.close()
        return text
    
    def _load_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    
    def _load_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into chunks for embedding.
        
        Args:
            text: Text content to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunks with metadata
        """
        chunks = self.text_splitter.split_text(text)
        
        result = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                'text': chunk,
                'chunk_index': i,
                'metadata': metadata or {}
            }
            result.append(chunk_data)
        
        return result
    
    def process_document(self, file_path: str) -> List[Dict]:
        """
        Process a single document: load and chunk it.
        
        Args:
            file_path: Path to the document
            
        Returns:
            List of text chunks with metadata
        """
        text = self.load_document(file_path)
        
        metadata = {
            'source': os.path.basename(file_path),
            'file_path': file_path
        }
        
        chunks = self.chunk_text(text, metadata)
        return chunks
    
    def process_directory(self, directory_path: str) -> List[Dict]:
        """
        Process all documents in a directory.
        
        Args:
            directory_path: Path to directory containing documents
            
        Returns:
            List of all text chunks from all documents
        """
        all_chunks = []
        supported_extensions = ['.pdf', '.docx', '.txt']
        
        for file_name in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file_name)
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension in supported_extensions:
                try:
                    print(f"Processing: {file_name}")
                    chunks = self.process_document(file_path)
                    all_chunks.extend(chunks)
                    print(f"  -> Created {len(chunks)} chunks")
                except Exception as e:
                    print(f"  -> Error processing {file_name}: {str(e)}")
        
        return all_chunks