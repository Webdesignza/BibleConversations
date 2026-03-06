"""
Document Processing Service (Translation-Aware)
Handles document upload, parsing, and storage in specific translation collections
FIXED: Restored Bible text parsing with proper metadata
"""

import os
import tempfile
import asyncio
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
from langchain_core.documents import Document

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
        
        # Text splitter for chunking (fallback for non-Bible documents)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Base paths
        self.chroma_base_path = Path(settings.CHROMA_DB_PATH)
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Track processing status (simple in-memory store)
        self.processing_status = {}
        
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
    
    
    def _parse_bible_text(self, documents, filename: str, translation_id: str):
        """
        Parse Bible text and create chunks with proper metadata
        Handles multiple formats including multi-line verses.
        """
        import re
        
        chunks = []
        current_book = None
        current_chapter = None
        
        # Buffer for accumulating multi-line verses
        pending_book = None
        pending_chapter = None
        pending_verse = None
        pending_text = None

        def flush_pending():
            """Save the buffered verse as a chunk"""
            if pending_book and pending_chapter and pending_verse and pending_text:
                chunk = Document(
                    page_content=f"{pending_book} {pending_chapter}:{pending_verse} - {pending_text.strip()}",
                    metadata={
                        'source': filename,
                        'translation_id': translation_id,
                        'book': pending_book,
                        'chapter': pending_chapter,
                        'verse_start': pending_verse,
                        'verse_end': pending_verse
                    }
                )
                chunks.append(chunk)

        for doc in documents:
            lines = doc.page_content.split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check for book header (all caps): "GENESIS", "EXODUS", etc.
                if line.isupper() and len(line.split()) <= 3 and len(line) > 2:
                    potential_book = line.title()
                    if re.match(r'^[A-Za-z0-9\s]+$', potential_book):
                        flush_pending()
                        pending_book = pending_chapter = pending_verse = pending_text = None
                        current_book = potential_book
                        print(f"Found book: {current_book}")
                        continue

                # Check for chapter header: "Chapter 1"
                chapter_match = re.match(r'^Chapter\s+(\d+)$', line, re.IGNORECASE)
                if chapter_match:
                    flush_pending()
                    pending_book = pending_chapter = pending_verse = pending_text = None
                    current_chapter = int(chapter_match.group(1))
                    print(f"Found chapter: {current_book} {current_chapter}")
                    continue

                # Format 1: "Genesis 1:1\tText" (tab separated)
                match = re.match(r'^([A-Za-z0-9\s]+?)\s+(\d+):(\d+)\t(.+)$', line)
                if match:
                    flush_pending()
                    pending_book = match.group(1).strip()
                    pending_chapter = int(match.group(2))
                    pending_verse = int(match.group(3))
                    pending_text = match.group(4).strip()
                    current_book = pending_book
                    current_chapter = pending_chapter
                    continue

                # Format 2: "Genesis 1:1 Text" (space separated)
                match = re.match(r'^([A-Za-z0-9\s]+?)\s+(\d+):(\d+)\s+(.+)$', line)
                if match:
                    flush_pending()
                    pending_book = match.group(1).strip()
                    pending_chapter = int(match.group(2))
                    pending_verse = int(match.group(3))
                    pending_text = match.group(4).strip()
                    current_book = pending_book
                    current_chapter = pending_chapter
                    continue

                # Format 3: ESV style - just verse number: "2 Text"
                if current_book and current_chapter:
                    match = re.match(r'^(\d+)\s+(.+)$', line)
                    if match:
                        flush_pending()
                        pending_book = current_book
                        pending_chapter = current_chapter
                        pending_verse = int(match.group(1))
                        pending_text = match.group(2).strip()
                        continue

                # No verse pattern matched — this is a CONTINUATION line of the previous verse
                if pending_text is not None:
                    pending_text += ' ' + line

        # Don't forget the very last verse
        flush_pending()

        print(f"✓ Parsed {len(chunks)} verses from Bible text")
        return chunks
    
    
    async def _process_in_background(self, temp_path: str, filename: str, 
                                 translation_id: str, job_id: str):
        """Process document in background to avoid timeout"""
        try:
            self.processing_status[job_id] = {
                'status': 'loading',
                'progress': 0,
                'message': 'Loading document...'
            }
            
            # Load document
            loader = self._get_loader_for_file(temp_path)
            documents = loader.load()
            
            self.processing_status[job_id] = {
                'status': 'parsing',
                'progress': 20,
                'message': f'Loaded {len(documents)} document(s), parsing Bible structure...'
            }
            
            # CRITICAL: Parse Bible verses and create structured chunks
            chunks = self._parse_bible_text(documents, filename, translation_id)
            
            if not chunks:
                raise ValueError("Document parsing produced no chunks")
            
            self.processing_status[job_id] = {
                'status': 'embedding',
                'progress': 40,
                'message': f'Parsed {len(chunks)} verses, creating embeddings...'
            }
            
            # Store in translation-specific ChromaDB collection
            translation_path = self.chroma_base_path / translation_id
            translation_path.mkdir(parents=True, exist_ok=True)
            
            # Fix: explicitly set write permissions (Railway filesystem issue)
            import stat
            translation_path.chmod(stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 777
            print(f"✓ Directory permissions set: {oct(translation_path.stat().st_mode)}")
            
            vectorstore = Chroma(
                persist_directory=str(translation_path),
                embedding_function=self.embeddings                
            )
            
            # OPTIMIZATION: Larger batch size to reduce processing time
            batch_size = 500
            total_batches = (len(chunks) - 1) // batch_size + 1
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                # Add documents
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    vectorstore.add_documents, 
                    batch
                )
                
                # Update progress
                progress = 40 + int((batch_num / total_batches) * 50)
                self.processing_status[job_id] = {
                    'status': 'embedding',
                    'progress': progress,
                    'message': f'Processing batch {batch_num}/{total_batches}...'
                }
                
                print(f"Added batch {batch_num}/{total_batches}")
            
            # Get total chunks
            collection = vectorstore._collection
            total_chunks = collection.count()
            
            # Success!
            self.processing_status[job_id] = {
                'status': 'complete',
                'progress': 100,
                'message': f'Successfully indexed {len(chunks)} verses',
                'num_chunks': len(chunks),
                'total_chunks': total_chunks
            }
            
            print(f"✓ Processed {filename}: {len(chunks)} verses indexed in {translation_id}")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error processing document: {str(e)}")
            print(f"Full traceback:\n{error_details}")
            
            self.processing_status[job_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Failed: {str(e)}',
                'error': str(e)
            }
        
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    
    async def process_document(self, file: UploadFile, translation_id: str) -> Dict:
        """
        Process and store a Bible document in a specific translation collection
        Returns immediately with job_id for status tracking
        
        Args:
            file: Uploaded Bible text file
            translation_id: ID of the translation to store in
        
        Returns:
            Dictionary with job_id for tracking progress
        """
        try:
            print(f"Processing file: {file.filename} for translation: {translation_id}")
            
            # Save uploaded file temporarily
            suffix = Path(file.filename).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                content = await file.read()
                tmp.write(content)
                temp_path = tmp.name
            
            print(f"Saved to temp path: {temp_path}")
            
            # Generate job ID
            import uuid
            job_id = str(uuid.uuid4())
            
            # Start background processing
            asyncio.create_task(
                self._process_in_background(temp_path, file.filename, translation_id, job_id)
            )
            
            return {
                'success': True,
                'job_id': job_id,
                'filename': file.filename,
                'translation_id': translation_id,
                'message': 'Upload started. Use job_id to check progress.'
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error starting upload: {str(e)}")
            print(f"Full traceback:\n{error_details}")
            
            return {
                'success': False,
                'filename': file.filename,
                'translation_id': translation_id,
                'error': str(e),
                'message': f'Failed to start upload: {str(e)}'
            }
    
    
    def get_processing_status(self, job_id: str) -> Dict:
        """Get the status of a background processing job"""
        if job_id not in self.processing_status:
            return {
                'status': 'not_found',
                'message': 'Job ID not found'
            }
        
        return self.processing_status[job_id]


# Singleton instance
_document_service = None

def get_document_service() -> DocumentService:
    """Get or create document service instance"""
    global _document_service
    
    if _document_service is None:
        _document_service = DocumentService()
    
    return _document_service