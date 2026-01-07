"""
RAG Query Service
Handles retrieval and generation for question answering
"""

import os
from typing import List, Dict

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from app.core.config import get_settings

settings = get_settings()


class RAGService:
    """Service for RAG-based question answering"""
    
    def __init__(self):
        """Initialize the RAG service"""
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        self.llm = ChatOpenAI(
            model=settings.CHAT_MODEL,
            temperature=settings.TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize vector store
        self.vectorstore = Chroma(
            persist_directory=settings.CHROMA_DB_PATH,
            embedding_function=self.embeddings
        )
    
    
    def _retrieve_relevant_chunks(self, query: str, k: int = None) -> List[Dict]:
        """
        Retrieve most relevant document chunks for a query
        
        Args:
            query: User's question
            k: Number of chunks to retrieve (default from settings)
            
        Returns:
            List of relevant document chunks with scores
        """
        if k is None:
            k = settings.RETRIEVAL_K
        
        # Perform similarity search with scores
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        # Format results
        retrieved_chunks = []
        for doc, score in results:
            retrieved_chunks.append({
                'content': doc.page_content,
                'score': float(score),
                'metadata': doc.metadata
            })
        
        return retrieved_chunks
    
    
    def _build_rag_prompt(self, query: str, retrieved_chunks: List[Dict]) -> str:
        """
        Construct prompt with context and query
        
        Args:
            query: User's question
            retrieved_chunks: List of retrieved document chunks
            
        Returns:
            Formatted prompt string
        """
        # Combine all retrieved chunks into context
        context = "\n\n---\n\n".join([chunk['content'] for chunk in retrieved_chunks])
        
        # Build structured prompt
        prompt = f"""You are a helpful assistant that answers questions based on the provided context.

INSTRUCTIONS:
- Use ONLY the information from the context below to answer the question
- If the answer is not in the context, say "I don't have enough information to answer that question."
- Be concise and accurate
- Cite specific parts of the context when relevant

CONTEXT:
{context}

QUESTION: {query}

ANSWER:"""
        
        return prompt
    
    
    def _generate_response(self, prompt: str) -> str:
        """
        Generate answer using LLM
        
        Args:
            prompt: Complete prompt with context and query
            
        Returns:
            Generated response string
        """
        response = self.llm.invoke(prompt)
        return response.content
    
    
    def query(self, question: str, k: int = None, include_sources: bool = True) -> Dict:
        """
        Complete RAG query: Retrieve + Generate
        
        Args:
            question: User's question
            k: Number of chunks to retrieve (default from settings)
            include_sources: Whether to include source chunks in response
            
        Returns:
            Dictionary with answer and metadata
        """
        try:
            # Step 1: Retrieve relevant chunks
            retrieved_chunks = self._retrieve_relevant_chunks(question, k=k)
            
            if not retrieved_chunks:
                return {
                    "success": False,
                    "question": question,
                    "answer": "No relevant information found in the knowledge base.",
                    "sources": [],
                    "num_chunks_used": 0
                }
            
            # Step 2: Build prompt
            rag_prompt = self._build_rag_prompt(question, retrieved_chunks)
            
            # Step 3: Generate answer
            answer = self._generate_response(rag_prompt)
            
            # Prepare response
            response = {
                "success": True,
                "question": question,
                "answer": answer,
                "num_chunks_used": len(retrieved_chunks)
            }
            
            # Include sources if requested
            if include_sources:
                response["sources"] = [
                    {
                        "content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                        "score": chunk["score"],
                        "metadata": chunk["metadata"]
                    }
                    for chunk in retrieved_chunks
                ]
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "question": question,
                "error": str(e),
                "message": f"Failed to process query: {str(e)}"
            }


# Singleton instance
_rag_service = None

def get_rag_service() -> RAGService:
    """Get or create RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service