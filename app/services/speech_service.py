"""
Speech Service
Text-to-speech using Edge TTS (Microsoft Edge's TTS - Free!)
"""

import edge_tts


class SpeechService:
    """Service for text-to-speech conversion using Edge TTS"""
    
    def __init__(self):
        """Initialize Edge TTS service"""
        pass
    
    async def text_to_speech(
        self, 
        text: str, 
        voice: str = "en-US-JennyNeural",
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> bytes:
        """
        Convert text to speech using Edge TTS (async)
        
        Args:
            text: Text to convert to speech
            voice: Voice name (e.g., 'en-US-JennyNeural')
            rate: Speaking rate (-50% to +100%, default "+0%")
            pitch: Pitch adjustment (-50Hz to +50Hz, default "+0Hz")
            
        Returns:
            Audio bytes (MP3 format)
        """
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch
        )
        
        # Collect audio chunks
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        
        return b"".join(audio_chunks)


# Singleton
_speech_service = None

def get_speech_service() -> SpeechService:
    """Get or create speech service instance"""
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechService()
    return _speech_service