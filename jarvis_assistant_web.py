#!/usr/bin/env python3
"""
JARVIS Assistant - Versão Web Simplificada (SEM microfone)
Usa comandos de texto via API web para testar sem PyAudio
"""

import requests
import pyttsx3
import os
import sys
import time
from dotenv import load_dotenv
import openai

load_dotenv()

API_BASE = "http://localhost:8000"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class JarvisVoice:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.setup_voice()
        
    def setup_voice(self):
        """Configura voz masculina grave em PT-BR"""
        voices = self.engine.getProperty('voices')
        
        # Busca melhor voz PT-BR masculina
        pt_voices = [v for v in voices if 'portuguese' in v.name.lower() or 'pt-br' in v.id.lower()]
        male_voices = [v for v in voices if any(x in v.name.lower() for x in ['daniel', 'antonio', 'male', 'masculino'])]
        
        target_voice = None
        if pt_voices:
            target_voice = pt_voices[0]
            print(f"[VOZ] Usando voz PT-BR: {target_voice.name}")
        elif male_voices:
            target_voice = male_voices[0]
            print(f"[VOZ] Usando voz masculina: {target_voice.name}")
        else:
            target_voice = voices[0]
            print(f"[VOZ] Usando voz padrão: {target_voice.name}")
        
        self.engine.setProperty('voice', target_voice.id)
        self.engine.setProperty('rate', 140)
        self.engine.setProperty('volume', 0.9)
        
        print("\n=== VOZES DISPONÍVEIS ===")
        for i, voice in enumerate(voices):
            print(f"{i}: {voice.name} | {voice.id}")
        print("=" * 60 + "\n")
    
    def speak(self, text):
        """Fala texto com voz configurada"""
        print(f"[JARVIS] {text}")
        self.engine.say(text)
        self.engine.runAndWait()


class JarvisWebAssistant:
    def __init__(self):
        self.voice = JarvisVoice()
        
    def call_api(self, endpoint, method="GET", data=None):
        """Chama API do sistema Hoops Jarvis"""
        try:
            url = f"{API_BASE}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=5)
            else:
                return None
            
            if response.ok:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"[ERRO] API call {endpoint}: {e}")
            return None
    
    def execute_command(self, command):
        """Executa comando de texto"""
        cmd_lower = command.lower()
        
        # Comandos do sistema
        if "iniciar" in cmd_lower or "start" in cmd_lower:
            self.call_api("/api/control/start", "POST")
            self.voice.speak("Sistema iniciado.")
            return
        
        if "parar" in cmd_lower or "stop" in cmd_lower:
            self.call_api("/api/control/stop", "POST")
            self.voice.speak("Sistema pausado.")
            return
        
        if "status" in cmd_lower:
            status = self.call_api("/api/status")
            if status:
                running = "rodando" if status.get('running') else "parado"
                autobet = "ativa" if status.get('auto_bet_enabled') else "desativada"
                self.voice.speak(f"Sistema {running}. Aposta automática {autobet}.")
                return
        
        if "lucro" in cmd_lower or "resultado" in cmd_lower:
            report = self.call_api("/api/report")
            if report:
                total = report.get('total_bets', 0)
                blocked = report.get('blocked_bets', 0)
                self.voice.speak(f"{total} apostas processadas. {blocked} bloqueadas.")
                return
        
        self.voice.speak("Comando não reconhecido.")
    
    def run(self):
        """Loop de comandos de texto"""
        self.voice.speak("Jarvis Web online. Digite comandos ou 'sair' para encerrar.")
        
        print("\n[COMANDOS DISPONÍVEIS]")
        print("- iniciar")
        print("- parar")
        print("- status")
        print("- lucro")
        print("- sair")
        print("")
        
        while True:
            try:
                command = input("\n> ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['sair', 'exit', 'quit']:
                    self.voice.speak("Encerrando assistente.")
                    break
                
                self.execute_command(command)
                
            except KeyboardInterrupt:
                self.voice.speak("Assistente encerrado.")
                break
            except Exception as e:
                print(f"[ERRO] {e}")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║    JARVIS Web - Assistente Simplificado (sem microfone)    ║
╚════════════════════════════════════════════════════════════╝

[INFO] Esta versão usa comandos de TEXTO em vez de voz.
[INFO] Para versão completa com microfone, instale PyAudio.

Iniciando...
""")
    
    try:
        assistant = JarvisWebAssistant()
        assistant.run()
    except Exception as e:
        print(f"\n[ERRO FATAL] {e}")
