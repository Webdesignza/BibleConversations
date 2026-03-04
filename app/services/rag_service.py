"""
RAG Query Service - Multi-Translation Bible Assistant
Handles retrieval and generation for Bible study questions across multiple translations
UPDATED: Single unified verse retrieval function for both modes
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
    
    # Will check if JSON file exists and load it, otherwise create an empty one
    def _load_translations_metadata(self) -> Dict:
        """Load translations metadata from JSON file"""
        metadata_file = self.chroma_base_path / "translations.json"
        
        # Create empty metadata file if it doesn't exist
        if not metadata_file.exists():
            print("⚠️ translations.json not found, creating empty metadata")
            self.chroma_base_path.mkdir(parents=True, exist_ok=True)
            with open(metadata_file, 'w') as f:
                json.dump({}, f)
            return {}
        
        try:
            with open(metadata_file, 'r') as f:
                content = f.read().strip()
                
                # Handle empty file
                if not content:
                    print("⚠️ translations.json is empty, initializing")
                    with open(metadata_file, 'w') as fw:
                        json.dump({}, fw)
                    return {}
                
                return json.loads(content)
                
        except json.JSONDecodeError as e:
            print(f"⚠️ Invalid JSON in translations.json: {e}")
            print(f"Content: {content[:100]}")  # Show first 100 chars
            # Backup corrupted file and create new one
            backup_file = self.chroma_base_path / "translations.json.backup"
            with open(backup_file, 'w') as f:
                f.write(content)
            with open(metadata_file, 'w') as f:
                json.dump({}, f)
            return {}
            
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
        """Get list of available Bible translations"""
        try:
            metadata = self._load_translations_metadata()
            
            translations = []
            for trans_id, info in metadata.items():
                translation_path = self.chroma_base_path / trans_id
                
                # Check if ChromaDB has actual data
                actual_chunks = 0
                has_data = False
                
                if translation_path.exists():
                    try:
                        from chromadb import PersistentClient
                        client = PersistentClient(path=str(translation_path))
                        collections = client.list_collections()
                        
                        if collections and len(collections) > 0:
                            actual_chunks = collections[0].count()
                            has_data = actual_chunks > 0
                    except Exception as e:
                        print(f"⚠️ Error checking {trans_id}: {e}")
                
                # Include translation regardless of data status
                translations.append({
                    'id': trans_id,
                    'name': info.get('name', trans_id),
                    'description': info.get('description', ''),
                    'chunks': actual_chunks,  # Show 0 if no data
                    'has_data': has_data,     # Flag for UI
                    'created': info.get('created', '')
                })
            
            return translations
            
        except Exception as e:
            print(f"Error loading translations: {e}")
            return []
        
    
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
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error creating translation: {e}")
            print(f"Full traceback:\n{error_trace}")
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
        print(f"\n{'='*60}")
        print(f"SWITCH TRANSLATION CALLED: {translation_id}")
        print(f"{'='*60}")
        
        try:
            # Check if translation exists
            metadata = self._load_translations_metadata()
            print(f"Loaded metadata: {list(metadata.keys())}")
            
            if translation_id not in metadata:
                print(f"❌ Translation {translation_id} not found in metadata")
                return {
                    'success': False,
                    'message': f'Translation "{translation_id}" not found'
                }
            
            # Initialize vector store for this translation
            translation_path = self.chroma_base_path / translation_id
            print(f"Translation path: {translation_path}")
            print(f"Path exists: {translation_path.exists()}")
            
            # USE SIMPLE persist_directory APPROACH (like Charlotte and previous version)
            print(f"Creating Chroma with persist_directory...")
            self.vectorstore = Chroma(
                persist_directory=str(translation_path),
                embedding_function=self.embeddings
            )
            print("✓ Chroma wrapper created")
            
            self.current_translation = translation_id
            translation_name = metadata[translation_id].get('name', translation_id)
            
            print(f"✓ Successfully switched to: {translation_name}")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'message': f'Switched to {translation_name}',
                'translation_id': translation_id,
                'translation_name': translation_name
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"\n❌ ERROR IN SWITCH_TRANSLATION:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"\nFull traceback:\n{error_trace}")
            print(f"{'='*60}\n")
            
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
        
        CRITICAL: Distinguishes between "John 1:1" (Gospel) and "1 John 1:1" (Epistle)
        """
        
        # Patterns for Bible references (in order of specificity)
        # IMPORTANT: Numbered books MUST be matched first to avoid confusion
        patterns = [
            # "1 John 2:5" or "2 Corinthians 3:16" (numbered books with colon) - MUST BE FIRST
            r'\b([1-3]\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(\d+):(\d+)(?:-(\d+))?',
            
            # "1 John 2 verse 5" (numbered books natural language)
            r'\b([1-3]\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:chapter\s+)?(\d+)\s+verse\s+(\d+)(?:\s+to\s+(\d+))?',
            
            # "John 3:16" or "John 3:16-18" (standard format with colon, NO leading number)
            r'\b(?<!\d\s)([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(\d+):(\d+)(?:-(\d+))?',
            
            # "John 3 verse 16" or "John chapter 3 verse 16" (natural language, NO leading number)
            r'\b(?<!\d\s)([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:chapter\s+)?(\d+)\s+verse\s+(\d+)(?:\s+to\s+(\d+))?',
            
            # "John 3 verses 16 to 18" (plural verses)
            r'\b([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:chapter\s+)?(\d+)\s+verses\s+(\d+)(?:\s+to\s+)?(\d+)?',
            
            # "John 3 16" (space-separated)
            r'\b([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(\d+)\s+(\d+)(?:-(\d+))?(?:\s|$)',
            
            # "John 10" (whole chapter)
            r'\b([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:chapter\s+)?(\d+)(?:\s|$)(?![\d:])',
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
                
                print(f"📖 Extracted verse reference: {reference}")
                print(f"   Book: '{book}', Chapter: {chapter}, Verses: {verse_start}-{verse_end}")
                
                return {
                    'book': book,
                    'chapter': chapter,
                    'verse_start': verse_start,
                    'verse_end': verse_end,
                    'reference': reference
                }
        
        print(f"⚠️ Could not extract verse reference from: '{query}'")
        return None

    
    def _get_book_variations(self, book_name: str) -> List[str]:
        """
        Generate all possible variations of a book name for robust searching
        NOTE: May not be needed with semantic search, but kept for future use
        """
        variations = [book_name]
        
        # Add "Gospel of X" and "X's Gospel" for gospels
        gospel_names = ['Matthew', 'Mark', 'Luke', 'John']
        if book_name in gospel_names:
            variations.extend([
                f"Gospel of {book_name}",
                f"{book_name}'s Gospel",
                f"The Gospel According to {book_name}"
            ])
        
        # Handle Psalm/Psalms
        book_lower = book_name.lower()
        if book_lower == 'psalm':
            variations.extend(['Psalms', 'Psalm', 'The Psalms'])
        elif book_lower == 'psalms':
            variations.extend(['Psalm', 'Psalms', 'The Psalms'])
        
        # Handle plural/singular for other books
        elif book_lower.endswith('s') and book_lower not in ['psalms']:
            variations.append(book_name[:-1])  # Try singular
        else:
            variations.append(book_name + 's')  # Try plural
        
        # Handle numbered books (1 John, 2 Corinthians, etc.)
        if book_name[0].isdigit():
            # "1 John" -> "First John", "I John"
            num_map = {'1': ['First', 'I'], '2': ['Second', 'II'], '3': ['Third', 'III']}
            digit = book_name[0]
            rest = book_name[1:].strip()
            if digit in num_map:
                for word_num in num_map[digit]:
                    variations.append(f"{word_num} {rest}")
        
        return variations
    
    
    def _retrieve_verse_from_translation(self, translation_id: str, verse_ref: Dict, 
                                         k: int = None) -> List[Dict]:
        """
        Retrieve verses from a DIFFERENT translation (comparison mode)
        Uses simple persist_directory approach + post-filtering for accuracy
        """
        print(f"\n--- Retrieving from {translation_id}: {verse_ref['reference']} ---")
        
        if k is None:
            k = settings.RETRIEVAL_K
        
        try:
            # Get translation path
            translation_path = self.chroma_base_path / translation_id
            
            # SIMPLE APPROACH: Use persist_directory like Charlotte
            vectorstore = Chroma(
                persist_directory=str(translation_path),
                embedding_function=self.embeddings
            )
            
            # Simple semantic search with the verse reference
            print(f"  Searching with query: {verse_ref['reference']}")
            results = vectorstore.similarity_search_with_score(
                verse_ref['reference'], 
                k=k * 10  # Get more results to filter from
            )
            
            # POST-FILTER: Only keep chunks that actually match the verse we want
            filtered_chunks = []
            for doc, score in results:
                meta = doc.metadata
                
                # Check if this chunk contains the verse we're looking for
                doc_book = meta.get('book', '').lower()
                doc_chapter = meta.get('chapter', -1)
                doc_verse_start = meta.get('verse_start', -1)
                doc_verse_end = meta.get('verse_end', doc_verse_start)
                
                target_book = verse_ref['book'].lower()
                target_chapter = verse_ref['chapter']
                target_verse_start = verse_ref['verse_start']
                target_verse_end = verse_ref['verse_end']
                
                # Check if book matches (handle variations)
                book_matches = (
                    doc_book == target_book or
                    f"gospel of {target_book}" in doc_book or
                    target_book in doc_book
                )
                
                # Check if chapter and verse match
                chapter_matches = (doc_chapter == target_chapter)
                verse_matches = (
                    doc_verse_start >= target_verse_start and
                    doc_verse_start <= target_verse_end
                )
                
                if book_matches and chapter_matches and verse_matches:
                    filtered_chunks.append({
                        'content': doc.page_content,
                        'score': float(score),
                        'metadata': doc.metadata
                    })
                    print(f"    ✓ Match: {meta.get('book')} {doc_chapter}:{doc_verse_start}")
                else:
                    print(f"    ✗ Skip: {meta.get('book')} {doc_chapter}:{doc_verse_start} (doesn't match)")
            
            # Sort by verse number
            filtered_chunks.sort(key=lambda x: x['metadata'].get('verse_start', 0))
            
            print(f"✓ Retrieved {len(filtered_chunks)} matching chunks (filtered from {len(results)} total)")
            return filtered_chunks
            
        except Exception as e:
            print(f"❌ ERROR retrieving from {translation_id}:")
            print(f"   {e}")
            import traceback
            print(traceback.format_exc())
            return []
    
    
    def _books_match(self, doc_book: str, target_book: str) -> bool:
        """
        Robust book name matching that handles variations across translations.
        E.g. 'john' matches 'john', 'gospel of john', but NOT '1 john' or '2 john'
        """
        doc_book = doc_book.lower().strip()
        target_book = target_book.lower().strip()

        # Direct match
        if doc_book == target_book:
            return True

        # Target is a numbered book (e.g. "1 john") — require exact or very close match only
        if target_book[0].isdigit():
            return doc_book == target_book or doc_book.startswith(target_book)

        # Target is NOT numbered (e.g. "john") — make sure doc_book is also not numbered
        # This prevents "john" matching "1 john", "2 john", "3 john"
        if doc_book and doc_book[0].isdigit():
            return False

        # Allow "gospel of john" -> matches "john"
        # Strip common prefixes
        prefixes = ['gospel of ', 'the gospel of ', 'the book of ', 'book of ']
        clean_doc = doc_book
        for prefix in prefixes:
            if clean_doc.startswith(prefix):
                clean_doc = clean_doc[len(prefix):]
                break

        clean_target = target_book
        for prefix in prefixes:
            if clean_target.startswith(prefix):
                clean_target = clean_target[len(prefix):]
                break

        return clean_doc == clean_target or clean_doc.startswith(clean_target)


    def _get_smart_k(self, query: str, verse_ref: dict = None) -> int:
        """
        Automatically determine how many chunks to retrieve based on query type:
        - Single verse (John 3:16) → 1
        - Verse range (Proverbs 1:1-14) → number of verses in range
        - Theme/concept (what does Bible say about sin) → 5
        """
        if verse_ref:
            verse_start = verse_ref.get('verse_start', 1)
            verse_end = verse_ref.get('verse_end', verse_start)
            
            # Whole chapter requested (verse_end = 999)
            if verse_end == 999:
                return 50  # Get up to 50 verses for whole chapter
            
            # Verse range (e.g. 1-14 = 14 verses)
            num_verses = verse_end - verse_start + 1
            if num_verses > 1:
                return num_verses  # Return exactly as many as requested
            
            # Single verse
            return 1
        
        # No verse reference = concept/theme query → return multiple verses
        return 5


    def _retrieve_relevant_chunks(self, query: str, k: int = None) -> List[Dict]:
        """
        Retrieve relevant chunks using semantic search + smart filtering.
        k from widget is ignored for verse queries — smart k is used instead.
        """
        if not self.vectorstore:
            return []

        print(f"🔍 Searching for: '{query}'")

        # Extract verse reference if present
        verse_ref = self._extract_verse_reference(query)

        # Override k with smart detection
        smart_k = self._get_smart_k(query, verse_ref)
        print(f"  📊 Smart k={smart_k} ({'verse range' if verse_ref and verse_ref.get('verse_end', 1) > verse_ref.get('verse_start', 1) else 'single verse' if verse_ref else 'concept/theme'} query)")

        if verse_ref:
            print(f"  📍 Looking for: {verse_ref['book']} {verse_ref['chapter']}:{verse_ref['verse_start']}-{verse_ref['verse_end']}")

            specific_query = f"{verse_ref['book']} {verse_ref['chapter']}:{verse_ref['verse_start']}"
            search_k = 100  # Always cast wide net

            results = self.vectorstore.similarity_search_with_score(specific_query, k=search_k)

            exact_matches = []
            close_matches = []

            for doc, score in results:
                meta = doc.metadata
                doc_book = meta.get('book', '').lower()
                doc_chapter = meta.get('chapter', -1)
                doc_verse = meta.get('verse_start', -1)

                target_book = verse_ref['book'].lower()

                book_matches = self._books_match(doc_book, target_book)
                chapter_matches = (doc_chapter == verse_ref['chapter'])
                verse_matches = (verse_ref['verse_start'] <= doc_verse <= verse_ref['verse_end'])

                print(f"    🔎 {meta.get('book')} {doc_chapter}:{doc_verse} | book:{book_matches} ch:{chapter_matches} v:{verse_matches}")

                if book_matches and chapter_matches and verse_matches:
                    exact_matches.append((doc, score))
                    print(f"      ✓ EXACT MATCH!")
                elif book_matches and chapter_matches:
                    close_matches.append((doc, score))
                    print(f"      ~ CLOSE MATCH (right book+chapter, wrong verse)")

            if exact_matches:
                # Sort by verse number so they come out in order
                exact_matches.sort(key=lambda x: x[0].metadata.get('verse_start', 0))
                print(f"  ✅ Using {min(len(exact_matches), smart_k)} exact matches")
                results_to_use = exact_matches[:smart_k]
            elif close_matches:
                close_matches.sort(key=lambda x: x[0].metadata.get('verse_start', 0))
                print(f"  ⚠️ Using 1 close match (right chapter, wrong verse)")
                results_to_use = close_matches[:1]
            else:
                print(f"  ⚠️ No matches found")
                results_to_use = []

            retrieved_chunks = []
            for doc, score in results_to_use:
                retrieved_chunks.append({
                    'content': doc.page_content,
                    'score': float(score),
                    'metadata': doc.metadata
                })

        else:
            # Concept/theme query — semantic search, return smart_k results
            results = self.vectorstore.similarity_search_with_score(query, k=search_k if False else 50)
            retrieved_chunks = []
            for i, (doc, score) in enumerate(results[:smart_k]):
                meta = doc.metadata
                book = meta.get('book', 'NO_BOOK')
                chapter = meta.get('chapter', 'NO_CH')
                verse_start = meta.get('verse_start', 'NO_V')
                print(f"  Result {i+1}: {book} {chapter}:{verse_start} (score={score:.3f})")
                retrieved_chunks.append({
                    'content': doc.page_content,
                    'score': float(score),
                    'metadata': doc.metadata
                })

        print(f"✓ Retrieved {len(retrieved_chunks)} chunks")
        return retrieved_chunks
    
    
    def _build_rag_prompt(self, query: str, retrieved_chunks: List[Dict]) -> str:
        """Construct prompt - forces LLM to only use retrieved text, never memory"""
        
        # Build context with explicit verse labels
        context_parts = []
        for chunk in retrieved_chunks:
            meta = chunk.get('metadata', {})
            book = meta.get('book', '')
            chapter = meta.get('chapter', '')
            verse = meta.get('verse_start', '')
            label = f"[{book} {chapter}:{verse}]" if book and chapter and verse else "[verse]"
            context_parts.append(f"{label} {chunk['content']}")
        
        context = "\n".join(context_parts)

        current_trans = self.get_current_translation()
        translation_name = current_trans['name'] if current_trans else "the Bible"

        prompt = f"""You are a Bible verse lookup tool. You ONLY output what is written in the RETRIEVED TEXT below.

    Translation: {translation_name}

    RETRIEVED TEXT:
    {context}

    USER REQUEST: {query}

    STRICT RULES - READ CAREFULLY:
    1. ONLY quote the text shown in RETRIEVED TEXT above
    2. NEVER use your training knowledge or memory to provide Bible verses
    3. NEVER substitute a different verse if the requested one is in the RETRIEVED TEXT
    4. The RETRIEVED TEXT is the authoritative source - trust it completely
    5. Start your response with the exact verse reference (e.g. "Proverbs 22:12 says:")
    6. Then quote ONLY the text from RETRIEVED TEXT - word for word
    7. Do not add commentary, context or explanation
    8. If RETRIEVED TEXT is empty, say: "I could not retrieve that verse. Please try again."

    IMPORTANT: The RETRIEVED TEXT above contains the correct verse. Use it exactly as shown. Do not replace it with a different verse from memory.

    RESPONSE:"""

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
            
            # Retrieve relevant chunks (now uses unified function)
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
        SIMPLE: Switch to each translation, retrieve chunks, display directly in table
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
            
            # CRITICAL: Use the same k as single mode
            if k is None:
                k = settings.RETRIEVAL_K
            
            print(f"📖 Comparing across {len(translation_ids)} translations (k={k})")
            
            # Store the original translation to restore later
            original_translation = self.current_translation
            original_vectorstore = self.vectorstore
            
            comparisons = []
            
            # Loop through each translation
            for trans_id in translation_ids:
                print(f"\n--- Processing {trans_id} ---")
                
                # SWITCH to this translation (EXACTLY like single mode does)
                translation_path = self.chroma_base_path / trans_id
                self.vectorstore = Chroma(
                    persist_directory=str(translation_path),
                    embedding_function=self.embeddings
                )
                self.current_translation = trans_id
                
                # Call the EXACT SAME function that single mode uses WITH SAME k
                chunks = self._retrieve_relevant_chunks(question, k=k)
                
                trans_info = metadata[trans_id]
                comparisons.append({
                    'translation_id': trans_id,
                    'translation_name': trans_info.get('name', trans_id),
                    'chunks': chunks,
                    'num_chunks': len(chunks),
                    'has_results': len(chunks) > 0
                })
            
            # Restore original translation
            self.current_translation = original_translation
            self.vectorstore = original_vectorstore
            
            # BUILD TABLE DIRECTLY - No AI needed!
            table_html = self._build_comparison_table_direct(question, comparisons)
            
            # Simple spoken summary
            trans_names = [c['translation_name'] for c in comparisons]
            found_count = sum(1 for c in comparisons if c['has_results'])
            
            if found_count == len(comparisons):
                analysis = f"Here's {question} from all {len(comparisons)} translations."
            elif found_count > 0:
                analysis = f"Found {question} in {found_count} of {len(comparisons)} translations."
            else:
                analysis = f"Could not find {question} in any of the selected translations."
            
            return {
                'success': True,
                'question': question,
                'analysis': analysis,
                'table_html': table_html,
                'comparisons': comparisons,
                'num_translations': len(comparisons)
            }
                
        except Exception as e:
            # Restore original translation on error
            if original_translation and original_vectorstore:
                self.current_translation = original_translation
                self.vectorstore = original_vectorstore
            
            print(f"Comparison Error: {str(e)}")
            print(f"Traceback:\n{traceback.format_exc()}")
            return {
                'success': False,
                'question': question,
                'error': str(e),
                'comparisons': []
            }
    
    
    def _build_comparison_table_direct(self, question: str, comparisons: List[Dict]) -> str:
        """Build comparison table directly from retrieved chunks - mobile friendly"""
        
        headers = ['Passage'] + [c['translation_name'] for c in comparisons]
        
        table_html = '<table class="comparison-table">\n<thead>\n<tr>\n'
        for header in headers:
            table_html += f'<th>{header}</th>\n'
        table_html += '</tr>\n</thead>\n<tbody>\n<tr>\n'
        
        # Passage cell
        table_html += f'<td>{question}</td>\n'
        
        # Translation cells - ADD style to force full text display
        for comp in comparisons:
            label = comp['translation_name']
            if comp['chunks']:
                text = ' '.join([chunk['content'] for chunk in comp['chunks']])
                table_html += f'<td data-label="{label}" style="white-space: normal; word-wrap: break-word; overflow: visible; max-width: none;">{text}</td>\n'
            else:
                table_html += f'<td data-label="{label}" style="white-space: normal; word-wrap: break-word;">Not found</td>\n'
        
        table_html += '</tr>\n</tbody>\n</table>'
        
        return table_html
    
    
    def _build_comparison_prompt(self, question: str, comparisons: List[Dict]) -> str:
        """Build prompt for comparing multiple translations with table format"""
        
        # Format each translation's text - INCLUDE ALL
        translation_texts = []
        all_trans_names = []
        
        for comp in comparisons:
            trans_name = comp['translation_name']
            all_trans_names.append(trans_name)
            
            # ALWAYS include the translation with its chunks
            if comp['chunks']:
                context = "\n".join([chunk['content'] for chunk in comp['chunks']])
                translation_texts.append(f"=== {trans_name} ===\n{context}")
            else:
                translation_texts.append(f"=== {trans_name} ===\n(No text retrieved)")
        
        combined_context = "\n\n".join(translation_texts)
        
        prompt = f"""You are comparing Bible translations. You MUST provide your response in this EXACT format:

[SPOKEN]: Brief summary here

[TABLE]: HTML table here

USER'S QUESTION:
{question}

BIBLE TEXT FROM EACH TRANSLATION:
{combined_context}

CRITICAL INSTRUCTIONS:
1. Use ONLY the text shown above for each translation
2. If a translation shows "(No text retrieved)", put "Not found" in that cell
3. If a translation has text, use that EXACT text in the table
4. DO NOT add explanations or interpretations - just show what each translation says
5. Create ONE row for the passage requested

PART 1 - SPOKEN SUMMARY:
Start with "[SPOKEN]:" then write 1-2 sentences comparing what you see.

PART 2 - HTML TABLE:
Start with "[TABLE]:" then create this table:

<table class="comparison-table">
<tr>
<th>Passage</th>
{chr(10).join(f'<th>{name}</th>' for name in all_trans_names)}
</tr>
<tr>
<td>{question}</td>
{chr(10).join(f'<td>[text from {name} or "Not found"]</td>' for name in all_trans_names)}
</tr>
</table>

YOUR RESPONSE (must include both [SPOKEN]: and [TABLE]: with ALL {len(all_trans_names)} translations):"""
        
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