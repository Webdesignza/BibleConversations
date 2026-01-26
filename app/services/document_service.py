"""
Document Processing Service (Translation-Aware)
Handles document upload, parsing, and storage in specific translation collections
"""

import os
import tempfile
from pathlib import Path
from typing import Dict
from fastapi import UploadFile

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader
)
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import get_settings

settings = get_settings()


class DocumentService:
    """Service for processing and storing documents in translation-specific collections"""
    
    def __init__(self):
        """Initialize document service"""
        print("Initializing Document Service...")
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Base paths
        self.chroma_base_path = Path(settings.CHROMA_DB_PATH)
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        print("✓ Document Service initialized")
    
    
    def _get_loader_for_file(self, file_path: str):
        """Get appropriate document loader based on file extension"""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.pdf':
            return PyPDFLoader(file_path)
        
        elif ext in ['.txt', '.md']:
            # Try multiple encodings for text files
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    loader = TextLoader(file_path, encoding=encoding)
                    # Test load to verify encoding works
                    loader.load()
                    return TextLoader(file_path, encoding=encoding)
                except Exception as e:
                    print(f"Failed with {encoding}: {e}")
                    continue
            
            # If all encodings fail, raise error
            raise ValueError(f"Could not load text file with any encoding")
        
        elif ext == '.docx':
            return Docx2txtLoader(file_path)
        
        else:
            raise ValueError(f"Unsupported file type: {ext}. Supported: PDF, TXT, MD, DOCX")
    
    
    async def process_document(self, file: UploadFile, translation_id: str) -> Dict:
        """
        Process and store a document in a specific translation collection
        
        Args:
            file: Uploaded file
            translation_id: ID of the translation to store in
        
        Returns:
            Dictionary with success status and statistics
        """
        temp_path = None
        
        try:
            print(f"Processing file: {file.filename} for translation: {translation_id}")
            
            # Save uploaded file temporarily
            suffix = Path(file.filename).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                content = await file.read()
                tmp.write(content)
                temp_path = tmp.name
            
            print(f"Saved to temp path: {temp_path}")
            
            # Load document
            loader = self._get_loader_for_file(temp_path)
            print(f"Using loader: {type(loader).__name__}")
            
            documents = loader.load()
            print(f"Loaded {len(documents)} document(s)")
            
            if not documents:
                raise ValueError("No content could be extracted from the file")
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)
            print(f"Split into {len(chunks)} chunks")
            
            if not chunks:
                raise ValueError("Document splitting produced no chunks")
            
            # Add metadata
            for chunk in chunks:
                chunk.metadata['source'] = file.filename
                chunk.metadata['translation_id'] = translation_id
            
            # Store in translation-specific ChromaDB collection
            translation_path = self.chroma_base_path / translation_id
            translation_path.mkdir(parents=True, exist_ok=True)
            
            print(f"Storing in: {translation_path}")
            
            vectorstore = Chroma(
                persist_directory=str(translation_path),
                embedding_function=self.embeddings
            )
            
            # Add documents in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                vectorstore.add_documents(batch)
                print(f"Added batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")
            
            # Get total chunks in this translation
            collection = vectorstore._collection
            total_chunks = collection.count()
            
            print(f"✓ Processed {file.filename}: {len(chunks)} chunks added to {translation_id}")
            print(f"Total chunks in {translation_id}: {total_chunks}")
            
            return {
                'success': True,
                'filename': file.filename,
                'translation_id': translation_id,
                'num_chunks': len(chunks),
                'total_chunks': total_chunks,
                'message': f'Successfully added {len(chunks)} chunks to {translation_id}'
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error processing document: {str(e)}")
            print(f"Full traceback:\n{error_details}")
            
            return {
                'success': False,
                'filename': file.filename,
                'translation_id': translation_id,
                'error': str(e),
                'message': f'Failed to process document: {str(e)}'
            }
            
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass


# Singleton instance
_document_service = None

def get_document_service() -> DocumentService:
    """Get or create document service instance"""
    global _document_service
    
    if _document_service is None:
        _document_service = DocumentService()
    
    return _document_service
