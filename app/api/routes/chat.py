from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from app.core.security import verify_api_key
from app.services.rag_service import get_rag_service
from app.services.speech_service import get_speech_service
from app.services.stt_service import get_stt_service
from app.models.schemas import ChatRequest, ChatResponse, TTSRequest
from typing import List
from pydantic import BaseModel
import traceback
import tempfile
import os

router = APIRouter()


# Request model for translation comparison
class CompareRequest(BaseModel):
    """Request model for translation comparison"""
    question: str
    translation_ids: List[str]  # e.g., ["kjv", "niv", "esv"]
    k: int = 3
    include_chunks: bool = False


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """Chat endpoint for question answering"""
    try:
        rag_service = get_rag_service()
        result = rag_service.query(
            question=request.question,
            k=request.k,
            include_sources=request.include_sources
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@router.post("/stt")
async def speech_to_text(
    audio: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Convert speech audio to text using Groq Whisper
    
    Args:
        audio: Audio file (WAV, MP3, WEBM, etc.)
    
    Returns:
        Transcribed text
    """
    # Save uploaded audio to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Get STT service and transcribe
        stt_service = get_stt_service()
        result = stt_service.transcribe_audio(tmp_path)
        
        return result
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"STT failed: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Convert text to speech using Edge TTS
    
    Args:
        request: TTSRequest with text, voice, rate, pitch
    
    Returns:
        Audio file (MP3)
    """
    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        speech_service = get_speech_service()
        audio_bytes = await speech_service.text_to_speech(
            request.text, 
            request.voice, 
            request.rate, 
            request.pitch
        )
        
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.post("/compare")
async def compare_translations(
    request: CompareRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Compare the same Bible passage across multiple translations
    
    Example request:
    {
        "question": "What does John 3:16 say?",
        "translation_ids": ["kjv", "niv", "esv"],
        "k": 3,
        "include_chunks": false
    }
    """
    try:
        rag_service = get_rag_service()
        
        result = rag_service.compare_translations(
            question=request.question,
            translation_ids=request.translation_ids,
            k=request.k
        )
        
        # Optionally remove chunks to reduce response size
        if not request.include_chunks and result.get('success'):
            for comparison in result.get('comparisons', []):
                comparison.pop('chunks', None)
        
        return result
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )