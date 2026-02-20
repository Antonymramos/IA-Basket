#!/usr/bin/env python3
"""
Teste rápido da voz ElevenLabs - Jarvis Premium
"""

import os
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
    print("❌ ELEVENLABS_API_KEY não encontrada no .env")
    exit(1)

print("🎙️ Testando voz premium ElevenLabs...")
print(f"API Key: {ELEVENLABS_API_KEY[:20]}...")

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import play
    
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
    print("\n[JARVIS] Gerando áudio...")
    
    audio = client.generate(
        text="Bom dia, senhor. Jarvis online. Todos os sistemas operacionais. Pronto para receber comandos.",
        voice="Adam",  # Voz britânica masculina
        model="eleven_multilingual_v2"
    )
    
    print("[JARVIS] Reproduzindo...")
    play(audio)
    
    print("\n✅ SUCESSO! Voz premium funcionando!")
    print("Agora execute: python jarvis_assistant_premium.py")
    
except Exception as e:
    print(f"\n❌ Erro: {e}")
    print("\nTentando com biblioteca alternativa...")
    
    try:
        from elevenlabs import generate, save
        import pygame
        
        audio = generate(
            text="Bom dia, senhor. Jarvis online e pronto.",
            voice="Adam",
            api_key=ELEVENLABS_API_KEY
        )
        
        # Salva temporário
        temp_file = "test_jarvis.mp3"
        save(audio, temp_file)
        
        # Toca com pygame
        pygame.mixer.init()
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        import os
        os.remove(temp_file)
        
        print("\n✅ SUCESSO com método alternativo!")
        
    except Exception as e2:
        print(f"\n❌ Erro alternativo: {e2}")
        print("\nVerifique:")
        print("1. API Key está correta")
        print("2. Tem créditos na conta ElevenLabs")
        print("3. Internet conectada")
