"""
Pydantic Models/Schemas
Request and response models for API endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ============================================================================
# DOCUMENT/UPLOAD SCHEMAS
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """Response after uploading a document"""
    success: bool
    filename: str
    num_documents: Optional[int] = None
    num_chunks: Optional[int] = None
    message: str
    error: Optional[str] = None


class VectorStoreStatsResponse(BaseModel):
    """Response for vector store statistics"""
    success: bool
    total_chunks: Optional[int] = None
    embedding_model: Optional[str] = None
    db_path: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# CHAT/QUERY SCHEMAS
# ============================================================================

class ChatRequest(BaseModel):
    """Request for chat/query endpoint"""
    question: str = Field(..., description="User's question", min_length=1)
    k: Optional[int] = Field(None, description="Number of chunks to retrieve", ge=1, le=10)
    include_sources: Optional[bool] = Field(True, description="Include source chunks in response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is this document about?",
                "k": 3,
                "include_sources": True
            }
        }


class SourceChunk(BaseModel):
    """Source chunk information"""
    content: str
    score: float
    metadata: Dict[str, Any]


class ChatResponse(BaseModel):
    """Response from chat/query endpoint"""
    success: bool
    question: str
    answer: str
    num_chunks_used: int
    sources: Optional[List[SourceChunk]] = None
    error: Optional[str] = None
    message: Optional[str] = None


# ============================================================================
# VOICE/SPEECH SCHEMAS
# ============================================================================

class TTSRequest(BaseModel):
    """Request model for text-to-speech"""
    text: str = Field(..., description="Text to convert to speech", min_length=1)
    voice: str = Field("en-US-JennyNeural", description="Voice name for TTS")
    rate: str = Field("+0%", description="Speech rate adjustment")
    pitch: str = Field("+0Hz", description="Pitch adjustment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, how can I help you today?",
                "voice": "en-US-JennyNeural",
                "rate": "+0%",
                "pitch": "+0Hz"
            }
        }


class VoiceQueryResponse(BaseModel):
    """Response for voice query (includes transcription)"""
    success: bool
    transcribed_question: Optional[str] = None
    answer: Optional[str] = None
    num_chunks_used: Optional[int] = None
    sources: Optional[List[SourceChunk]] = None
    error: Optional[str] = None
    message: Optional[str] = None


# ============================================================================
# HEALTH CHECK SCHEMAS
# ============================================================================

class HealthResponse(BaseModel):
    """Response for health check endpoint"""
    status: str
    message: str
    vector_store_status: str
    total_chunks: Optional[int] = None