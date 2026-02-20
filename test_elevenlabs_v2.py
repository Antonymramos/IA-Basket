#!/usr/bin/env python3
"""
Teste da voz ElevenLabs - Usando API v2.36
"""

import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

if not API_KEY:
    print("❌ ELEVENLABS_API_KEY não encontrada no .env")
    exit(1)

print("🎙️ Testando voz ElevenLabs v2.36...")
print(f"API Key: {API_KEY[:24]}...")
print(f"Voice ID: {VOICE_ID}")

texto = "Bom dia, senhor. Jarvis online. Todos os sistemas operacionais."

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import play
    
    print("\n[JARVIS] Criando cliente...")
    client = ElevenLabs(api_key=API_KEY)
    
    print("[JARVIS] Gerando áudio...")
    
    # API correta v2.36: client.text_to_speech.convert()
    audio = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        text=texto,
        model_id="eleven_multilingual_v2"
    )
    
    print("[JARVIS] Reproduzindo...")
    play(audio)
    
    print("\n✅ VOZ PREMIUM FUNCIONANDO!")
    print("🎬 Esta é a voz de qualidade cinematográfica do Jarvis!")
    
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n🔧 Tentando salvar em arquivo...")
    
    try:
        from elevenlabs.client import ElevenLabs
        import pygame
        
        client = ElevenLabs(api_key=API_KEY)
        
        audio_iterator = client.text_to_speech.convert(
            voice_id=VOICE_ID,
            text=texto,
            model_id="eleven_multilingual_v2"
        )
        
        # Salva áudio
        with open("jarvis_test.mp3", "wb") as f:
            for chunk in audio_iterator:
                if chunk:
                    f.write(chunk)
        
        print("[JARVIS] Reproduzindo com pygame...")
        pygame.mixer.init()
        pygame.mixer.music.load("jarvis_test.mp3")
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        print("\n✅ VOZ PREMIUM FUNCIONANDO (método arquivo)!")
        
    except Exception as e2:
        print(f"\n❌ Erro: {e2}")
        import traceback
        traceback.print_exc()
