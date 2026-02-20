#!/usr/bin/env python3
"""
JARVIS - Assistente de voz desktop para operação multi-conta de arbitragem
Integrado com o sistema Hoops Jarvis
"""

import os
import sys
import threading
import time
import webbrowser
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# Importações de voz
try:
    import speech_recognition as sr
    import pyttsx3
    from dotenv import load_dotenv
    import openai
except ImportError:
    print("Instalando dependências necessárias...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "SpeechRecognition", "pyttsx3", "python-dotenv", 
                          "openai", "PyAudio", "pywhatkit"])
    import speech_recognition as sr
    import pyttsx3
    from dotenv import load_dotenv
    import openai

load_dotenv()

# Configurações
API_BASE = "http://localhost:8000"
WAKE_WORDS = ["jarvis", "jarviz", "gervis"]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Sistema de voz
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
        self.engine.setProperty('rate', 140)  # Lento e imponente
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


class JarvisAssistant:
    def __init__(self):
        self.voice = JarvisVoice()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening = False
        self.history = []
        
        # Ajusta sensibilidade do microfone
        with self.microphone as source:
            print("[INIT] Calibrando microfone para ruído ambiente...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        
        print("[INIT] JARVIS Desktop inicializado")
        
    def listen_for_wake_word(self):
        """Escuta continuamente por wake word"""
        with self.microphone as source:
            print("[ESCUTA] Aguardando 'Jarvis'...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                text = self.recognizer.recognize_google(audio, language="pt-BR").lower()
                
                if any(wake in text for wake in WAKE_WORDS):
                    return True
                    
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"[ERRO] Escuta wake word: {e}")
        
        return False
    
    def listen_command(self):
        """Captura comando completo após wake word"""
        self.voice.speak("Sim, senhor.")
        
        with self.microphone as source:
            print("[COMANDO] Escutando comando...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                command = self.recognizer.recognize_google(audio, language="pt-BR")
                print(f"[COMANDO] Reconhecido: {command}")
                return command
            except sr.UnknownValueError:
                self.voice.speak("Não compreendi. Repita, por favor.")
                return None
            except Exception as e:
                print(f"[ERRO] Captura comando: {e}")
                self.voice.speak("Erro ao capturar comando.")
                return None
    
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
    
    def get_gpt_response(self, command):
        """Obtém resposta contextual do GPT-4o-mini"""
        if not OPENAI_API_KEY:
            return None
        
        try:
            # Contexto do sistema
            status = self.call_api("/api/status")
            report = self.call_api("/api/report")
            
            context = f"""Você é JARVIS, assistente de arbitragem esportiva.
Sistema: Hoops Jarvis (arbitragem de apostas ao vivo em basquete)
Status atual: {'Rodando' if status.get('running') else 'Parado'}
Auto-bet: {'Ativo' if status.get('auto_bet_enabled') else 'Desativo'}
"""
            if report:
                context += f"Apostas hoje: {report.get('total_bets', 0)}\n"
                context += f"Bloqueadas: {report.get('blocked_bets', 0)}\n"
            
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": command}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERRO] GPT: {e}")
            return None
    
    def execute_command(self, command):
        """Executa comando reconhecido"""
        cmd_lower = command.lower()
        
        # Comandos do sistema Hoops Jarvis
        if "iniciar" in cmd_lower or "ligar" in cmd_lower or "start" in cmd_lower:
            if "bot" in cmd_lower or "sistema" in cmd_lower:
                self.call_api("/api/control/start", "POST")
                self.voice.speak("Sistema de arbitragem iniciado.")
                return
        
        if "parar" in cmd_lower or "desligar" in cmd_lower or "stop" in cmd_lower:
            if "bot" in cmd_lower or "sistema" in cmd_lower:
                self.call_api("/api/control/stop", "POST")
                self.voice.speak("Sistema pausado.")
                return
        
        if "auto" in cmd_lower and "bet" in cmd_lower:
            enable = "ativ" in cmd_lower or "lig" in cmd_lower
            self.call_api("/api/control/auto-bet", "POST", {"enabled": enable})
            self.voice.speak(f"Aposta automática {'ativada' if enable else 'desativada'}.")
            return
        
        # Status e relatórios
        if any(x in cmd_lower for x in ["status", "situação", "como está"]):
            status = self.call_api("/api/status")
            if status:
                running = "rodando" if status.get('running') else "parado"
                autobet = "ativa" if status.get('auto_bet_enabled') else "desativada"
                self.voice.speak(f"Sistema {running}. Aposta automática {autobet}.")
                return
        
        if "lucro" in cmd_lower or "ganho" in cmd_lower or "resultado" in cmd_lower:
            report = self.call_api("/api/report")
            if report:
                total = report.get('total_bets', 0)
                blocked = report.get('blocked_bets', 0)
                self.voice.speak(f"{total} apostas processadas hoje. {blocked} bloqueadas.")
                return
        
        if "quantas apostas" in cmd_lower or "número de apostas" in cmd_lower:
            report = self.call_api("/api/report")
            if report:
                total = report.get('total_bets', 0)
                self.voice.speak(f"{total} apostas no total.")
                return
        
        # Abrir aplicativos/sites
        if "abra" in cmd_lower or "abrir" in cmd_lower:
            if "painel" in cmd_lower or "dashboard" in cmd_lower or "hoops" in cmd_lower:
                webbrowser.open("http://localhost:8000")
                self.voice.speak("Abrindo painel de controle.")
                return
            
            if "bet365" in cmd_lower:
                # Suporte multi-conta
                if "conta 2" in cmd_lower or "segunda conta" in cmd_lower:
                    webbrowser.open_new_tab("https://www.bet365.com")
                elif "conta 3" in cmd_lower or "terceira conta" in cmd_lower:
                    webbrowser.open_new_tab("https://www.bet365.com")
                else:
                    webbrowser.open("https://www.bet365.com")
                self.voice.speak("Abrindo Bet365.")
                return
            
            if "chrome" in cmd_lower:
                subprocess.Popen(["start", "chrome"], shell=True)
                self.voice.speak("Abrindo Chrome.")
                return
            
            if "vscode" in cmd_lower or "code" in cmd_lower:
                subprocess.Popen(["code", "."], shell=True)
                self.voice.speak("Abrindo Visual Studio Code.")
                return
        
        # Hora e data
        if "que horas" in cmd_lower or "hora" in cmd_lower:
            now = datetime.now()
            hour_str = now.strftime("%H horas e %M minutos")
            self.voice.speak(f"São {hour_str}.")
            return
        
        if "que dia" in cmd_lower or "data" in cmd_lower:
            now = datetime.now()
            date_str = now.strftime("%d de %B de %Y")
            self.voice.speak(f"Hoje é {date_str}.")
            return
        
        # Comando geral via GPT
        if OPENAI_API_KEY:
            response = self.get_gpt_response(command)
            if response:
                self.voice.speak(response)
                return
        
        # Fallback
        self.voice.speak("Comando não reconhecido. Posso ajudar com controle do sistema, status, abrir aplicativos ou responder perguntas.")
    
    def run(self):
        """Loop principal do assistente"""
        self.voice.speak("Jarvis online, senhor. Pronto para operação multi-conta.")
        
        while True:
            try:
                # Escuta wake word
                if self.listen_for_wake_word():
                    # Captura comando
                    command = self.listen_command()
                    
                    if command:
                        # Comandos de shutdown
                        if "desligar jarvis" in command.lower() or "encerrar assistente" in command.lower():
                            self.voice.speak("Encerrando assistente. Até logo, senhor.")
                            break
                        
                        # Executa comando
                        self.execute_command(command)
                
            except KeyboardInterrupt:
                self.voice.speak("Assistente encerrado.")
                break
            except Exception as e:
                print(f"[ERRO] Loop principal: {e}")
                time.sleep(1)


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║         JARVIS - Assistente Desktop de Arbitragem          ║
║              Hoops Jarvis Multi-Conta System               ║
╚════════════════════════════════════════════════════════════╝

[REQUISITOS]
1. Instale PyAudio: pip install pipwin && pipwin install pyaudio
2. Configure OPENAI_API_KEY no arquivo .env (opcional)
3. Sistema Hoops Jarvis deve estar rodando em localhost:8000

[COMANDOS SUPORTADOS]
- "Jarvis, inicie o bot"
- "Jarvis, qual o status?"
- "Jarvis, qual o lucro hoje?"
- "Jarvis, abra a Bet365 conta 2"
- "Jarvis, abra o painel"
- "Jarvis, que horas são?"
- "Jarvis, [qualquer pergunta]"

[ATALHOS]
- Ctrl+C para sair
- "Desligar Jarvis" via voz

Iniciando em 3 segundos...
""")
    
    time.sleep(3)
    
    try:
        assistant = JarvisAssistant()
        assistant.run()
    except Exception as e:
        print(f"\n[ERRO FATAL] {e}")
        print("\nVerifique se:")
        print("1. PyAudio está instalado: pip install pipwin && pipwin install pyaudio")
        print("2. Microfone está conectado e permitido")
        print("3. Sistema Hoops Jarvis está rodando")
