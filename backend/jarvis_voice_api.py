"""
API endpoint para servir voz ElevenLabs ao frontend
"""
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

def generate_jarvis_audio(text: str) -> bytes:
    """
    Gera áudio usando ElevenLabs API
    
    Args:
        text: Texto para ser falado pelo Jarvis
        
    Returns:
        Bytes do arquivo MP3
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY não configurada no .env")
    
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
    # Gera áudio
    audio_iterator = client.text_to_speech.convert(
        voice_id=ELEVENLABS_VOICE_ID,
        text=text,
        model_id="eleven_multilingual_v2"
    )
    
    # Coleta chunks em memória
    audio_bytes = b""
    for chunk in audio_iterator:
        if chunk:
            audio_bytes += chunk
    
    return audio_bytes
