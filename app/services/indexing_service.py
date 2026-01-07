"""
Document Indexing Service
Handles document loading, chunking, embedding, and storage in ChromaDB
"""

import os
from typing import List, Dict
from pathlib import Path

from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from app.core.config import get_settings

settings = get_settings()


class IndexingService:
    """Service for processing and indexing documents"""
    
    def __init__(self):
        """Initialize the indexing service"""
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Ensure chroma_db directory exists
        os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
    
    
    def _load_document(self, file_path: str):
        """
        Load document based on file type
        
        Args:
            file_path: Path to the document
            
        Returns:
            Loaded documents
            
        Raises:
            ValueError: If file type is not supported
        """
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_extension == '.txt':
            loader = TextLoader(file_path)
        elif file_extension == '.md':
            loader = UnstructuredMarkdownLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        return loader.load()
    
    
    def process_document(self, file_path: str) -> Dict:
        """
        Complete document processing pipeline
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with processing results and statistics
        """
        try:
            # Step 1: Load document
            docs = self._load_document(file_path)
            
            # Step 2: Chunk documents
            chunks = self.text_splitter.split_documents(docs)
            
            # Step 3: Create/load vector store and add documents
            vectorstore = Chroma(
                persist_directory=settings.CHROMA_DB_PATH,
                embedding_function=self.embeddings
            )
            
            # Add chunks to vector store
            vectorstore.add_documents(chunks)
            
            # Get filename for tracking
            filename = Path(file_path).name
            
            return {
                "success": True,
                "filename": filename,
                "num_documents": len(docs),
                "num_chunks": len(chunks),
                "message": f"Successfully processed {filename}: {len(chunks)} chunks added to vector store"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to process document: {str(e)}"
            }
    
    
    def get_vectorstore_stats(self) -> Dict:
        """
        Get statistics about the vector store
        
        Returns:
            Dictionary with vector store statistics
        """
        try:
            vectorstore = Chroma(
                persist_directory=settings.CHROMA_DB_PATH,
                embedding_function=self.embeddings
            )
            
            # Get collection info
            collection = vectorstore._collection
            total_chunks = collection.count()
            
            return {
                "success": True,
                "total_chunks": total_chunks,
                "embedding_model": settings.EMBEDDING_MODEL,
                "db_path": settings.CHROMA_DB_PATH
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve vector store statistics"
            }


# Singleton instance
_indexing_service = None

def get_indexing_service() -> IndexingService:
    """Get or create indexing service instance"""
    global _indexing_service
    if _indexing_service is None:
        _indexing_service = IndexingService()
    return _indexing_service