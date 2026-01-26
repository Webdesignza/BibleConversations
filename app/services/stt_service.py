"""
Speech-to-Text Service using Groq Whisper API
"""

from groq import Groq
from app.core.config import get_settings
from typing import Optional
import os

settings = get_settings()

class STTService:
    """Service for speech-to-text conversion using Groq Whisper API"""
    
    def __init__(self):
        """Initialize Groq Whisper client"""
        print("Initializing Groq Whisper API...")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        print("✓ Groq Whisper ready!")
        
        # Context prompt helps with domain-specific vocabulary
        self.context_prompt = """
        This conversation is about GainSkills, an online training company.
        They offer CodeQuest (gamified coding platform), AI Interview Coach, and AWS certification training.
        Common topics: courses, certificates, enrollment, learning, training, education, skills development.
        """
    
    def transcribe_audio(self, audio_file_path: str, language: str = "en") -> dict:
        """
        Transcribe audio file to text using Groq Whisper API
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (default: 'en')
        
        Returns:
            Dictionary with transcription result
        """
        try:
            # Read audio file
            with open(audio_file_path, "rb") as audio_file:
                # Transcribe with Groq Whisper
                transcription = self.client.audio.transcriptions.create(
                    file=(os.path.basename(audio_file_path), audio_file.read()),
                    model="whisper-large-v3-turbo",  # Best model, still FREE
                    language=language,
                    prompt=self.context_prompt,  # Helps with domain vocabulary
                    temperature=0.0,  # Most consistent results
                    response_format="verbose_json"  # Get detailed info
                )
            
            # Extract text
            text = transcription.text.strip() if hasattr(transcription, 'text') else str(transcription).strip()
            
            # Post-process common mistakes
            text = self.fix_common_mistakes(text)
            
            return {
                "success": True,
                "text": text,
                "language": language
            }
            
        except Exception as e:
            print(f"STT Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    def fix_common_mistakes(self, text: str) -> str:
        """Fix commonly misheard domain-specific terms"""
        import re
        
        corrections = {
            # GainSkills variations
            "gang skills": "GainSkills",
            "gain skills": "GainSkills",
            "games skills": "GainSkills",
            "gaines skills": "GainSkills",
            "game skills": "GainSkills",
            
            # CodeQuest variations
            "code quest": "CodeQuest",
            "coat quest": "CodeQuest",
            "cold quest": "CodeQuest",
            "code price": "CodeQuest",
            
            # AI Interview Coach
            "ai interview coach": "AI Interview Coach",
            "interview coach": "AI Interview Coach",
        }
        
        result = text
        for wrong, correct in corrections.items():
            result = re.sub(re.escape(wrong), correct, result, flags=re.IGNORECASE)
        
        return result


# Singleton
_stt_service: Optional[STTService] = None

def get_stt_service() -> STTService:
    """Get or create STT service instance"""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service