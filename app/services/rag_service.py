"""
RAG Query Service - Multi-Translation Bible Assistant
Handles retrieval and generation for Bible study questions across multiple translations
"""

from typing import List, Dict, Optional
import traceback
import json
import os
import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import get_settings

settings = get_settings()


class RAGService:
    """Service for RAG-based Bible study question answering with multiple translations"""
    
    def __init__(self):
        """Initialize the RAG service"""
        print("Initializing Multi-Translation Bible Study RAG Service...")
        
        # HuggingFace embeddings (FREE, runs locally)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print(f"✓ Embeddings initialized: {settings.EMBEDDING_MODEL}")
        
        # Groq LLM (FREE!)
        self.llm = ChatOpenAI(
            model=settings.CHAT_MODEL,
            temperature=settings.TEMPERATURE,
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_API_BASE
        )
        print(f"✓ LLM initialized: {settings.CHAT_MODEL} (Groq - FREE)")
        
        # Translation management
        self.chroma_base_path = Path(settings.CHROMA_DB_PATH)
        self.translations_file = self.chroma_base_path / "translations.json"
        self.current_translation = None
        self.vectorstore = None
        
        # Ensure base directory exists
        self.chroma_base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize translations metadata file if it doesn't exist
        if not self.translations_file.exists():
            self._save_translations_metadata({})
        
        print(f"✓ Translation system initialized: {self.chroma_base_path}")
    
    
    def _load_translations_metadata(self) -> Dict:
        """Load translations metadata from JSON file"""
        try:
            with open(self.translations_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading translations metadata: {e}")
            return {}
    
    
    def _save_translations_metadata(self, metadata: Dict):
        """Save translations metadata to JSON file"""
        try:
            with open(self.translations_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving translations metadata: {e}")
    
    
    def get_available_translations(self) -> List[Dict]:
        """Get list of all available translations"""
        metadata = self._load_translations_metadata()
        
        translations = []
        for translation_id, info in metadata.items():
            translations.append({
                'id': translation_id,
                'name': info.get('name', translation_id),
                'description': info.get('description', ''),
                'created': info.get('created', ''),
                'chunks': info.get('chunks', 0)
            })
        
        return sorted(translations, key=lambda x: x['name'])
    
    
    def create_translation(self, translation_id: str, name: str, description: str = "") -> Dict:
        """Create a new translation collection"""
        try:
            # Validate translation_id (alphanumeric and underscores only)
            if not translation_id.replace('_', '').isalnum():
                return {
                    'success': False,
                    'message': 'Translation ID must contain only letters, numbers, and underscores'
                }
            
            # Check if translation already exists
            metadata = self._load_translations_metadata()
            if translation_id in metadata:
                return {
                    'success': False,
                    'message': f'Translation "{translation_id}" already exists'
                }
            
            # Create directory for this translation
            translation_path = self.chroma_base_path / translation_id
            translation_path.mkdir(parents=True, exist_ok=True)
            
            # Add to metadata
            from datetime import datetime
            metadata[translation_id] = {
                'name': name,
                'description': description,
                'created': datetime.now().isoformat(),
                'chunks': 0
            }
            self._save_translations_metadata(metadata)
            
            print(f"✓ Created translation: {name} ({translation_id})")
            
            return {
                'success': True,
                'message': f'Translation "{name}" created successfully',
                'translation_id': translation_id
            }
            
        except Exception as e:
            print(f"Error creating translation: {e}")
            return {
                'success': False,
                'message': f'Failed to create translation: {str(e)}'
            }
    
    
    def delete_translation(self, translation_id: str) -> Dict:
        """Delete a translation and its database"""
        try:
            # Check if translation exists
            metadata = self._load_translations_metadata()
            if translation_id not in metadata:
                return {
                    'success': False,
                    'message': f'Translation "{translation_id}" not found'
                }
            
            # Delete the directory
            translation_path = self.chroma_base_path / translation_id
            if translation_path.exists():
                shutil.rmtree(translation_path)
            
            # Remove from metadata
            translation_name = metadata[translation_id].get('name', translation_id)
            del metadata[translation_id]
            self._save_translations_metadata(metadata)
            
            # If this was the current translation, clear it
            if self.current_translation == translation_id:
                self.current_translation = None
                self.vectorstore = None
            
            print(f"✓ Deleted translation: {translation_name} ({translation_id})")
            
            return {
                'success': True,
                'message': f'Translation "{translation_name}" deleted successfully'
            }
            
        except Exception as e:
            print(f"Error deleting translation: {e}")
            return {
                'success': False,
                'message': f'Failed to delete translation: {str(e)}'
            }
    
    
    def switch_translation(self, translation_id: str) -> Dict:
        """Switch to a different Bible translation"""
        try:
            # Check if translation exists
            metadata = self._load_translations_metadata()
            if translation_id not in metadata:
                return {
                    'success': False,
                    'message': f'Translation "{translation_id}" not found'
                }
            
            # Initialize vector store for this translation
            translation_path = self.chroma_base_path / translation_id
            
            self.vectorstore = Chroma(
                persist_directory=str(translation_path),
                embedding_function=self.embeddings
            )
            
            self.current_translation = translation_id
            translation_name = metadata[translation_id].get('name', translation_id)
            
            print(f"✓ Switched to translation: {translation_name} ({translation_id})")
            
            return {
                'success': True,
                'message': f'Switched to {translation_name}',
                'translation_id': translation_id,
                'translation_name': translation_name
            }
            
        except Exception as e:
            print(f"Error switching translation: {e}")
            return {
                'success': False,
                'message': f'Failed to switch translation: {str(e)}'
            }
    
    
    def get_current_translation(self) -> Optional[Dict]:
        """Get information about the currently active translation"""
        if not self.current_translation:
            return None
        
        metadata = self._load_translations_metadata()
        if self.current_translation in metadata:
            info = metadata[self.current_translation]
            return {
                'id': self.current_translation,
                'name': info.get('name', self.current_translation),
                'description': info.get('description', ''),
                'chunks': info.get('chunks', 0)
            }
        
        return None
    
    
    def update_translation_chunk_count(self, translation_id: str, chunk_count: int):
        """Update the chunk count for a translation"""
        metadata = self._load_translations_metadata()
        if translation_id in metadata:
            metadata[translation_id]['chunks'] = chunk_count
            self._save_translations_metadata(metadata)
    
    
    def _retrieve_relevant_chunks(self, query: str, k: int = None) -> List[Dict]:
        """Retrieve most relevant Bible translation chunks for a query"""
        if not self.vectorstore:
            return []
        
        if k is None:
            k = settings.RETRIEVAL_K
        
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        retrieved_chunks = []
        for doc, score in results:
            retrieved_chunks.append({
                'content': doc.page_content,
                'score': float(score),
                'metadata': doc.metadata
            })
        
        return retrieved_chunks
    
    
    def _build_rag_prompt(self, query: str, retrieved_chunks: List[Dict]) -> str:
        """Construct prompt with Bible translation context and query"""
        context = "\n\n---\n\n".join([chunk['content'] for chunk in retrieved_chunks])
        
        # Get current translation name
        current_trans = self.get_current_translation()
        translation_name = current_trans['name'] if current_trans else "the Bible"
        
        prompt = f"""You are a knowledgeable and respectful Bible study assistant. You help people explore and understand different Bible translations, their nuances, historical context, and scholarly interpretations.

The user is currently studying from: {translation_name}

INSTRUCTIONS:
- Use ONLY the information from the provided Bible translation context below to answer questions
- Be respectful, scholarly, and neutral when discussing different translations
- Explain translation differences clearly and objectively, noting linguistic and theological nuances
- Reference specific verses, translations, and scholarly perspectives when relevant
- If discussing interpretations, present multiple scholarly viewpoints fairly
- Maintain a reverent and respectful tone when discussing scripture
- Keep responses conversational yet informative - you're helping someone study the Bible
- If the information needed to answer isn't in the context, say "I don't have information about that specific passage in the {translation_name}. Could you tell me more about what you're looking for?"
- Never invent or fabricate biblical information - only use what's provided in the context

BIBLE TRANSLATION CONTEXT ({translation_name}):
{context}

USER'S QUESTION:
{query}

YOUR RESPONSE (as Bible Study Assistant):"""
        
        return prompt
    
    
    def query(self, question: str, k: int = None, include_sources: bool = False) -> Dict:
        """Query the RAG system with a Bible study question"""
        try:
            # Check if a translation is active
            if not self.current_translation or not self.vectorstore:
                return {
                    'success': False,
                    'question': question,
                    'answer': "Please select a Bible translation first before asking questions.",
                    'num_chunks_used': 0,
                    'sources': []
                }
            
            # Retrieve relevant chunks
            retrieved_chunks = self._retrieve_relevant_chunks(question, k)
            
            if not retrieved_chunks:
                current_trans = self.get_current_translation()
                translation_name = current_trans['name'] if current_trans else "this translation"
                
                return {
                    'success': False,
                    'question': question,
                    'answer': f"I couldn't find any relevant information in {translation_name} to answer your question. Could you rephrase or ask about a different passage?",
                    'num_chunks_used': 0,
                    'sources': []
                }
                        
            # Build prompt with context
            prompt = self._build_rag_prompt(question, retrieved_chunks)
            
            # Generate answer using Groq
            response = self.llm.invoke(prompt)
            answer = response.content
            
            result = {
                'success': True,
                'question': question,
                'answer': answer,
                'num_chunks_used': len(retrieved_chunks),
                'translation': self.get_current_translation(),
                'sources': retrieved_chunks if include_sources else []
            }

            return result
            
        except Exception as e:
            print(f"RAG Error: {str(e)}")
            print(f"Traceback:\n{traceback.format_exc()}")
            return {
                'success': False,
                'question': question,
                'answer': f"An error occurred while processing your question. Please try again.",
                'num_chunks_used': 0,
                'error': str(e),
                'sources': []
            }


# Singleton instance
_rag_service = None

def get_rag_service() -> RAGService:
    """Get or create RAG service instance"""
    global _rag_service
    
    if _rag_service is None:
        _rag_service = RAGService()
    
    return _rag_service