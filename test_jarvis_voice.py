#!/usr/bin/env python3
"""
Teste SIMPLES da voz ElevenLabs - Salva MP3 e reproduz
"""

import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

print("🎙️ Testando voz ElevenLabs...")
print(f"Voice ID: {VOICE_ID}\n")

texto = "Bom dia, senhor. Jarvis online. Todos os sistemas operacionais."

try:
    from elevenlabs.client import ElevenLabs
    
    print("[JARVIS] Conectando à API ElevenLabs...")
    client = ElevenLabs(api_key=API_KEY)
    
    print("[JARVIS] Gerando áudio...")
    
    # Gera áudio
    audio_iterator = client.text_to_speech.convert(
        voice_id=VOICE_ID,
        text=texto,
        model_id="eleven_multilingual_v2"
    )
    
    # Salva em arquivo
    print("[JARVIS] Salvando áudio...")
    with open("jarvis_voice.mp3", "wb") as f:
        for chunk in audio_iterator:
            if chunk:
                f.write(chunk)
    
    print("[JARVIS] Áudio salvo em: jarvis_voice.mp3")
    
    # Tenta reproduzir com pygame
    try:
        import pygame
        
        print("[JARVIS] Reproduzindo...")
        pygame.mixer.init()
        pygame.mixer.music.load("jarvis_voice.mp3")
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        print("\n✅ SUCESSO! Voz premium ElevenLabs funcionando!")
        print("🎬 Qualidade cinematográfica!")
        print("\nArquivo salvo: jarvis_voice.mp3")
        print("Ouça para confirmar a qualidade da voz!")
        
    except ImportError:
        print("\n⚠️ pygame não disponível")
        print("✅ Áudio gerado com sucesso: jarvis_voice.mp3")
        print("Abra o arquivo para ouvir!")
        
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
