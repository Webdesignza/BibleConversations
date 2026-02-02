"""
RAG Query Service - Multi-Translation Bible Assistant
Handles retrieval and generation for Bible study questions across multiple translations
UPDATED: Completely unbiased, text-only responses + Smart Translation Comparison
"""

from typing import List, Dict, Optional
import traceback
import json
import os
import re
import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from groq import Groq

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
        
        # Groq LLM (FREE!) - Direct SDK, no OpenAI wrapper
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
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
    
   
    def _extract_verse_reference(self, query: str) -> Optional[Dict[str, any]]:
        """
        Extract exact Bible reference from query
        Handles multiple formats:
        - "John 3:16" (standard)
        - "John 3 verse 16" (natural language)
        - "John chapter 3 verse 16" (verbose)
        - "1 John 2:5" (numbered books)
        """
        
        # Patterns for Bible references (in order of specificity)
        patterns = [
            # "John 3:16" or "John 3:16-18" (standard format with colon)
            r'(\d?\s*[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(\d+):(\d+)(?:-(\d+))?',
            
            # "John 3 verse 16" or "John chapter 3 verse 16" (natural language)
            r'(\d?\s*[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:chapter\s+)?(\d+)\s+verse\s+(\d+)(?:\s+to\s+(\d+))?',
            
            # "John 3 verses 16 to 18" (plural verses)
            r'(\d?\s*[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:chapter\s+)?(\d+)\s+verses\s+(\d+)(?:\s+to\s+)?(\d+)?',
            
            # "John 3 16" (space-separated)
            r'(\d?\s*[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(\d+)\s+(\d+)(?:-(\d+))?(?:\s|$)',
            
            # "John 10" (whole chapter)
            r'(\d?\s*[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:chapter\s+)?(\d+)(?:\s|$)(?![\d:])',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                groups = match.groups()
                book = groups[0].strip()
                chapter = int(groups[1])
                
                if len(groups) >= 3 and groups[2]:
                    # Specific verse(s)
                    verse_start = int(groups[2])
                    verse_end = int(groups[3]) if len(groups) >= 4 and groups[3] else verse_start
                else:
                    # Whole chapter requested
                    verse_start = 1
                    verse_end = 999  # Get all verses in chapter
                
                reference = f"{book} {chapter}:{verse_start}"
                if verse_end != verse_start and verse_end != 999:
                    reference += f"-{verse_end}"
                
                print(f"🔍 Extracted verse reference: {reference}")
                
                return {
                    'book': book,
                    'chapter': chapter,
                    'verse_start': verse_start,
                    'verse_end': verse_end,
                    'reference': reference
                }
        
        print(f"⚠️ Could not extract verse reference from: '{query}'")
        return None

    
    def _retrieve_relevant_chunks(self, query: str, k: int = None) -> List[Dict]:
        """Retrieve most relevant Bible chunks - with exact verse matching"""
        if not self.vectorstore:
            return []
        
        if k is None:
            k = settings.RETRIEVAL_K
        
        # Try to extract exact verse reference
        verse_ref = self._extract_verse_reference(query)
        
        if verse_ref:
            print(f"Searching for exact reference: {verse_ref['reference']}")
            
            book_variations = [
                verse_ref['book'],
                f"Gospel of {verse_ref['book']}",
                f"{verse_ref['book']}'s Gospel",
                verse_ref['book'].lower(),
                verse_ref['book'].title(),
            ]
            
            filtered_results = []
            
            for book_name in book_variations:
                try:
                    # Search with book and chapter filter
                    results = self.vectorstore.similarity_search(
                        verse_ref['reference'],
                        k=k * 5,
                        filter={
                            "$and": [
                                {"book": {"$eq": book_name}},
                                {"chapter": {"$eq": verse_ref['chapter']}}
                            ]
                        }
                    )
                    
                    if results:
                        print(f"✓ Found {len(results)} matches with book name: {book_name}")
                        
                        # CRITICAL FIX: Only include verses that EXACTLY match the range
                        for doc in results:
                            doc_verse_start = doc.metadata.get('verse_start', 0)
                            doc_verse_end = doc.metadata.get('verse_end', doc_verse_start)
                            
                            # MUST be within the exact range, no partial overlaps
                            if (doc_verse_start >= verse_ref['verse_start'] and 
                                doc_verse_start <= verse_ref['verse_end'] and
                                doc_verse_end >= verse_ref['verse_start'] and 
                                doc_verse_end <= verse_ref['verse_end']):
                                filtered_results.append((doc, 1.0))
                        
                        if filtered_results:
                            break
                
                except Exception as e:
                    print(f"Filter search failed for '{book_name}': {e}")
                    continue
            
            if filtered_results:
                print(f"✓ Found {len(filtered_results)} exact matches")
                # Sort by verse start AND limit to exact requested verses
                filtered_results.sort(key=lambda x: x[0].metadata.get('verse_start', 0))
                
                # CRITICAL: Only return verses in the exact range
                exact_matches = []
                for doc, score in filtered_results:
                    v_start = doc.metadata.get('verse_start', 0)
                    if verse_ref['verse_start'] <= v_start <= verse_ref['verse_end']:
                        exact_matches.append((doc, score))
                
                results = exact_matches[:k] if exact_matches else filtered_results[:k]
            else:
                print(f"✗ No exact matches found, trying semantic search")
                results = self.vectorstore.similarity_search_with_score(query, k=k)
        else:
            print("Using semantic search (no exact reference found)")
            results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        retrieved_chunks = []
        for item in results:
            if isinstance(item, tuple):
                doc, score = item
            else:
                doc, score = item, 1.0
            
            retrieved_chunks.append({
                'content': doc.page_content,
                'score': float(score),
                'metadata': doc.metadata
            })
        
        return retrieved_chunks
    
    
    def _build_rag_prompt(self, query: str, retrieved_chunks: List[Dict]) -> str:
        """Construct prompt with Bible translation context and query - COMPLETELY UNBIASED"""
        context = "\n\n---\n\n".join([chunk['content'] for chunk in retrieved_chunks])
        
        # Get current translation name
        current_trans = self.get_current_translation()
        translation_name = current_trans['name'] if current_trans else "the Bible"
        
        prompt = f"""You are a Bible reference assistant. Your role is to provide ONLY what is written in the biblical text, without interpretation, opinion, or theological commentary.

The user is currently reading from: {translation_name}

STRICT INSTRUCTIONS:
1. ONLY quote or paraphrase what is explicitly written in the provided Bible text below
2. DO NOT add theological interpretations, doctrinal explanations, or personal opinions
3. DO NOT explain what verses "mean" - only state what they literally say
4. If asked for interpretation or meaning, respond: "I provide only what the text says. For interpretation, please consult a pastor, theologian, or Bible study guide."
5. If comparing translations, ONLY note the different wording used - do not explain which is "better" or "more accurate"
6. If the text doesn't contain the answer, say: "I don't see that specific information in the {translation_name} passages I have access to."
7. When citing passages, use natural verse ranges (e.g., "John 3:16-18" instead of "verse 16, verse 17, verse 18")
8. For consecutive verses, introduce ONCE with the verse range at the beginning (e.g., "John 3 verses 16 to 18 say:") then read the text smoothly without repeating "verse 16", "verse 17" for each one
9. Read the biblical text naturally and conversationally - avoid robotic verse-by-verse announcements
10. If asked about context (historical, cultural), only provide it if it's explicitly mentioned in the biblical text itself

BIBLE TEXT FROM {translation_name}:
{context}

USER'S QUESTION:
{query}

YOUR RESPONSE (Bible text only, no interpretation, natural verse ranges):"""
        
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
            
            # Generate answer using Groq directly
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=settings.CHAT_MODEL,
                temperature=settings.TEMPERATURE,
            )
            
            answer = chat_completion.choices[0].message.content
            
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
    
    
    def compare_translations(self, question: str, translation_ids: List[str], k: int = None) -> Dict:
        """
        Compare the same passage across multiple Bible translations
        NOW HANDLES BOTH: Specific verse requests AND topical searches
        """
        try:
            if not translation_ids or len(translation_ids) < 2:
                return {
                    'success': False,
                    'question': question,
                    'error': 'Please select at least 2 translations to compare',
                    'comparisons': []
                }
            
            # Check all translations exist
            metadata = self._load_translations_metadata()
            for trans_id in translation_ids:
                if trans_id not in metadata:
                    return {
                        'success': False,
                        'question': question,
                        'error': f'Translation "{trans_id}" not found',
                        'comparisons': []
                    }
            
            if k is None:
                k = settings.RETRIEVAL_K
            
            # Check if this is a specific verse request or topical search
            verse_ref = self._extract_verse_reference(question)
            
            if verse_ref:
                # SPECIFIC VERSE: Fetch the SAME verse from all translations
                print(f"📖 Specific verse comparison: {verse_ref['reference']}")
                return self._compare_specific_verses(question, translation_ids, verse_ref, k, metadata)
            else:
                # TOPICAL SEARCH: Find verses in ONE translation, then fetch same verses from others
                print(f"🔍 Topical comparison for: {question}")
                return self._compare_topical_search(question, translation_ids, k, metadata)
                
        except Exception as e:
            print(f"Comparison Error: {str(e)}")
            print(f"Traceback:\n{traceback.format_exc()}")
            return {
                'success': False,
                'question': question,
                'error': str(e),
                'comparisons': []
            }
    
    
    def _compare_specific_verses(self, question: str, translation_ids: List[str], 
                                 verse_ref: Dict, k: int, metadata: Dict) -> Dict:
        """Compare a specific verse/passage across translations"""
        comparisons = []
        
        for trans_id in translation_ids:
            try:
                # Load translation's vector store
                translation_path = self.chroma_base_path / trans_id
                vectorstore = Chroma(
                    persist_directory=str(translation_path),
                    embedding_function=self.embeddings
                )
                
                # Search for the SPECIFIC verse using metadata filter
                book_variations = [
                    verse_ref['book'],
                    f"Gospel of {verse_ref['book']}",
                    f"{verse_ref['book']}'s Gospel",
                ]
                
                retrieved_chunks = []
                for book_name in book_variations:
                    try:
                        results = vectorstore.similarity_search(
                            verse_ref['reference'],
                            k=k * 3,
                            filter={
                                "$and": [
                                    {"book": {"$eq": book_name}},
                                    {"chapter": {"$eq": verse_ref['chapter']}}
                                ]
                            }
                        )
                        
                        # Filter to exact verse range
                        for doc in results:
                            doc_v_start = doc.metadata.get('verse_start', 0)
                            doc_v_end = doc.metadata.get('verse_end', doc_v_start)
                            
                            if (doc_v_start >= verse_ref['verse_start'] and 
                                doc_v_start <= verse_ref['verse_end']):
                                retrieved_chunks.append({
                                    'content': doc.page_content,
                                    'score': 1.0,
                                    'metadata': doc.metadata
                                })
                        
                        if retrieved_chunks:
                            break
                            
                    except Exception as e:
                        continue
                
                trans_info = metadata[trans_id]
                comparisons.append({
                    'translation_id': trans_id,
                    'translation_name': trans_info.get('name', trans_id),
                    'chunks': retrieved_chunks,
                    'num_chunks': len(retrieved_chunks),
                    'has_results': len(retrieved_chunks) > 0
                })
                
                print(f"✓ {trans_info.get('name', trans_id)}: Found {len(retrieved_chunks)} chunks")
                
            except Exception as e:
                print(f"❌ Error retrieving {trans_id}: {e}")
                comparisons.append({
                    'translation_id': trans_id,
                    'translation_name': metadata.get(trans_id, {}).get('name', trans_id),
                    'chunks': [],
                    'num_chunks': 0,
                    'has_results': False,
                    'error': str(e)
                })
        
        # Generate comparison
        comparison_prompt = self._build_comparison_prompt(question, comparisons)
        chat_completion = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": comparison_prompt}],
            model=settings.CHAT_MODEL,
            temperature=settings.TEMPERATURE,
        )
        
        full_response = chat_completion.choices[0].message.content
        
        # Parse response
        spoken_text, table_html = self._parse_comparison_response(full_response)
        
        return {
            'success': True,
            'question': question,
            'analysis': spoken_text,
            'table_html': table_html,
            'comparisons': comparisons,
            'num_translations': len(comparisons)
        }
    
    
    def _compare_topical_search(self, question: str, translation_ids: List[str], 
                                k: int, metadata: Dict) -> Dict:
        """
        Compare topical search across translations
        Strategy: Search in first translation, extract verse refs, fetch from all
        """
        
        # Step 1: Do semantic search in FIRST translation to find relevant verses
        first_trans_id = translation_ids[0]
        translation_path = self.chroma_base_path / first_trans_id
        vectorstore = Chroma(
            persist_directory=str(translation_path),
            embedding_function=self.embeddings
        )
        
        # Get relevant verses from first translation
        results = vectorstore.similarity_search_with_score(question, k=min(k, 3))
        
        if not results:
            return {
                'success': False,
                'question': question,
                'error': 'Could not find relevant passages for comparison',
                'comparisons': []
            }
        
        # Step 2: Extract verse references from results
        verse_references = []
        for doc, score in results:
            meta = doc.metadata
            if 'book' in meta and 'chapter' in meta and 'verse_start' in meta:
                verse_ref = {
                    'book': meta['book'],
                    'chapter': meta['chapter'],
                    'verse_start': meta['verse_start'],
                    'verse_end': meta.get('verse_end', meta['verse_start']),
                    'reference': f"{meta['book']} {meta['chapter']}:{meta['verse_start']}"
                }
                if verse_ref['verse_end'] != verse_ref['verse_start']:
                    verse_ref['reference'] += f"-{verse_ref['verse_end']}"
                verse_references.append(verse_ref)
        
        print(f"📚 Found {len(verse_references)} relevant passages to compare")
        
        # Step 3: Fetch these SAME verses from ALL translations
        all_comparisons = []
        
        for verse_ref in verse_references:
            verse_comparison = {
                'reference': verse_ref['reference'],
                'translations': {}
            }
            
            for trans_id in translation_ids:
                trans_path = self.chroma_base_path / trans_id
                vectorstore = Chroma(
                    persist_directory=str(trans_path),
                    embedding_function=self.embeddings
                )
                
                # Search for this specific verse
                book_variations = [
                    verse_ref['book'],
                    f"Gospel of {verse_ref['book']}",
                    f"{verse_ref['book']}'s Gospel",
                ]
                
                found_content = None
                for book_name in book_variations:
                    try:
                        results = vectorstore.similarity_search(
                            verse_ref['reference'],
                            k=5,
                            filter={
                                "$and": [
                                    {"book": {"$eq": book_name}},
                                    {"chapter": {"$eq": verse_ref['chapter']}}
                                ]
                            }
                        )
                        
                        for doc in results:
                            doc_v_start = doc.metadata.get('verse_start', 0)
                            if verse_ref['verse_start'] <= doc_v_start <= verse_ref['verse_end']:
                                found_content = doc.page_content
                                break
                        
                        if found_content:
                            break
                    except:
                        continue
                
                verse_comparison['translations'][trans_id] = {
                    'name': metadata[trans_id].get('name', trans_id),
                    'content': found_content or "Not found"
                }
            
            all_comparisons.append(verse_comparison)
        
        # Step 4: Build special prompt for multiple verse comparison
        comparison_prompt = self._build_topical_comparison_prompt(question, all_comparisons, translation_ids, metadata)
        
        chat_completion = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": comparison_prompt}],
            model=settings.CHAT_MODEL,
            temperature=settings.TEMPERATURE,
        )
        
        full_response = chat_completion.choices[0].message.content
        spoken_text, table_html = self._parse_comparison_response(full_response)
        
        return {
            'success': True,
            'question': question,
            'analysis': spoken_text,
            'table_html': table_html,
            'comparisons': all_comparisons,
            'num_translations': len(translation_ids)
        }
    
    
    def _build_comparison_prompt(self, question: str, comparisons: List[Dict]) -> str:
        """Build prompt for comparing multiple translations with table format"""
        
        # Format each translation's text
        translation_texts = []
        for comp in comparisons:
            trans_name = comp['translation_name']
            
            if comp.get('has_results', True) and comp['chunks']:
                context = "\n".join([chunk['content'] for chunk in comp['chunks']])
                translation_texts.append(f"=== {trans_name} ===\n{context}")
            else:
                # Include even if no results found
                translation_texts.append(f"=== {trans_name} ===\n(No matching passage found)")
        
        combined_context = "\n\n".join(translation_texts)
        
        # Get translation names for the table - INCLUDE ALL
        trans_names = [comp['translation_name'] for comp in comparisons]
        
        prompt = f"""You are comparing Bible translations. You MUST provide your response in this EXACT format:

[SPOKEN]: Brief summary here

[TABLE]: HTML table here

USER'S QUESTION:
{question}

BIBLE TEXT FROM EACH TRANSLATION:
{combined_context}

PART 1 - SPOKEN SUMMARY:
Start with "[SPOKEN]:" then write a brief 2-3 sentence summary.
If some translations don't have the passage, mention this in your summary.

PART 2 - HTML TABLE:
Start with "[TABLE]:" then create an HTML table showing ALL {len(trans_names)} translations side-by-side.

Requirements:
- Use <table class="comparison-table">
- First column header: "Passage"
- Column headers for ALL translations: {', '.join(trans_names)}
- If a translation doesn't have the passage, put "Not found" in that cell
- Each row shows: verse reference | text from each translation

CRITICAL: You MUST include columns for ALL {len(trans_names)} translations: {', '.join(trans_names)}

YOUR RESPONSE (must have both parts and all {len(trans_names)} translation columns):"""
        
        return prompt
    
    
    def _build_topical_comparison_prompt(self, question: str, all_comparisons: List[Dict], 
                                         translation_ids: List[str], metadata: Dict) -> str:
        """Build prompt for topical comparison with multiple verses"""
        
        trans_names = [metadata[tid].get('name', tid) for tid in translation_ids]
        
        # Format the context
        context_parts = []
        for verse_comp in all_comparisons:
            ref = verse_comp['reference']
            context_parts.append(f"\n=== {ref} ===")
            for trans_id in translation_ids:
                trans_name = verse_comp['translations'][trans_id]['name']
                content = verse_comp['translations'][trans_id]['content']
                context_parts.append(f"{trans_name}: {content}")
        
        combined_context = "\n".join(context_parts)
        
        prompt = f"""You are comparing Bible translations for a topical question. You MUST provide your response in this EXACT format:

[SPOKEN]: Brief summary here

[TABLE]: HTML table here

USER'S QUESTION:
{question}

RELEVANT PASSAGES FROM EACH TRANSLATION:
{combined_context}

PART 1 - SPOKEN SUMMARY:
Start with "[SPOKEN]:" then write a 2-3 sentence summary explaining how the translations address this topic.

PART 2 - HTML TABLE:
Start with "[TABLE]:" then create an HTML table with these specifications:
- Use <table class="comparison-table">
- First column header: "Passage"
- Other column headers: {', '.join(trans_names)}
- One row per verse reference
- Show text from each translation (or "Not found")

Example structure:
[TABLE]:
<table class="comparison-table">
<tr>
<th>Passage</th>
<th>{trans_names[0]}</th>
<th>{trans_names[1]}</th>
{f'<th>{trans_names[2]}</th>' if len(trans_names) > 2 else ''}
</tr>
<tr>
<td>John 3:16</td>
<td>For God so loved...</td>
<td>For God so loved...</td>
{f'<td>For God so loved...</td>' if len(trans_names) > 2 else ''}
</tr>
</table>

YOUR RESPONSE (must have both [SPOKEN]: and [TABLE]:):"""
        
        return prompt
    
    
    def _parse_comparison_response(self, full_response: str) -> tuple:
        """Parse AI response into spoken and table parts"""
        spoken_text = ""
        table_html = ""
        
        if "[SPOKEN]:" in full_response and "[TABLE]:" in full_response:
            parts = full_response.split("[TABLE]:")
            spoken_text = parts[0].replace("[SPOKEN]:", "").strip()
            table_html = parts[1].strip()
        else:
            spoken_text = full_response
            table_html = ""
        
        return spoken_text, table_html


# Singleton instance
_rag_service = None

def get_rag_service() -> RAGService:
    """Get or create RAG service instance"""
    global _rag_service
    
    if _rag_service is None:
        _rag_service = RAGService()
    
    return _rag_service