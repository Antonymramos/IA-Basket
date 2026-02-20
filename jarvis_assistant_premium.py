#!/usr/bin/env python3
"""
JARVIS Premium - Assistente com as MELHORES vozes possíveis
Suporta: ElevenLabs, Azure TTS, Google TTS, Windows Premium
"""

import os
import sys
import time
import webbrowser
import subprocess
import requests
from datetime import datetime
from pathlib import Path

try:
    import speech_recognition as sr
    import pyttsx3
    from dotenv import load_dotenv
except ImportError:
    print("Instalando dependências...")
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                          "SpeechRecognition", "pyttsx3", "python-dotenv",
                          "pygame", "PyAudio"])
    import speech_recognition as sr
    import pyttsx3
    from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8000"

# Configurações de vozes premium
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Adam (British)

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION = os.getenv("AZURE_SPEECH_REGION", "eastus")

GOOGLE_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


class JarvisPremiumVoice:
    """Sistema de voz com múltiplas engines e fallback automático"""
    
    def __init__(self):
        self.engine_priority = []
        self.current_engine = None
        self.temp_audio_dir = Path("temp_audio")
        self.temp_audio_dir.mkdir(exist_ok=True)
        
        self.detect_available_engines()
        self.select_best_engine()
    
    def detect_available_engines(self):
        """Detecta engines disponíveis em ordem de qualidade"""
        
        # 1. ElevenLabs (melhor)
        if ELEVENLABS_API_KEY:
            try:
                import elevenlabs
                self.engine_priority.append(("elevenlabs", "ElevenLabs Premium"))
                print("✅ ElevenLabs detectado (MELHOR QUALIDADE)")
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "elevenlabs"])
                import elevenlabs
                self.engine_priority.append(("elevenlabs", "ElevenLabs Premium"))
                print("✅ ElevenLabs instalado e detectado")
        
        # 2. Azure TTS
        if AZURE_SPEECH_KEY:
            try:
                import azure.cognitiveservices.speech as speechsdk
                self.engine_priority.append(("azure", "Azure Neural TTS"))
                print("✅ Azure TTS detectado")
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "azure-cognitiveservices-speech"])
                import azure.cognitiveservices.speech as speechsdk
                self.engine_priority.append(("azure", "Azure Neural TTS"))
        
        # 3. Google Cloud TTS
        if GOOGLE_CREDENTIALS and Path(GOOGLE_CREDENTIALS).exists():
            try:
                from google.cloud import texttospeech
                self.engine_priority.append(("google", "Google WaveNet TTS"))
                print("✅ Google Cloud TTS detectado")
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "google-cloud-texttospeech"])
                from google.cloud import texttospeech
                self.engine_priority.append(("google", "Google WaveNet TTS"))
        
        # 4. Windows Premium (sempre disponível como fallback)
        self.engine_priority.append(("pyttsx3", "Windows TTS"))
        print("✅ Windows TTS disponível (fallback)")
    
    def select_best_engine(self):
        """Seleciona engine de maior qualidade disponível"""
        if self.engine_priority:
            engine_name, engine_label = self.engine_priority[0]
            self.current_engine = engine_name
            print(f"\n🎙️ VOZ SELECIONADA: {engine_label}\n")
            
            if engine_name == "pyttsx3":
                self.setup_pyttsx3()
    
    def setup_pyttsx3(self):
        """Configura pyttsx3 com melhor voz Windows disponível"""
        self.tts_engine = pyttsx3.init()
        voices = self.tts_engine.getProperty('voices')
        
        print("\n=== VOZES WINDOWS DISPONÍVEIS ===")
        for i, voice in enumerate(voices):
            gender = "M" if "male" in voice.name.lower() or any(x in voice.name.lower() for x in ["daniel", "antonio", "mark", "guy", "david"]) else "F"
            print(f"{i}: [{gender}] {voice.name}")
        print("=" * 50 + "\n")
        
        # Busca vozes masculinas graves em ordem de preferência
        priority_voices = [
            # PT-BR masculinas
            lambda v: "daniel" in v.name.lower(),
            lambda v: "antonio" in v.name.lower(),
            # EN masculinas graves
            lambda v: "guy" in v.name.lower(),
            lambda v: "mark" in v.name.lower(),
            lambda v: "david" in v.name.lower(),
            # Qualquer masculina PT
            lambda v: ("portuguese" in v.name.lower() or "pt-br" in v.id.lower()) and "male" in v.name.lower(),
            # Qualquer masculina EN
            lambda v: "male" in v.name.lower() and "english" in v.name.lower(),
            # Primeira masculina
            lambda v: "male" in v.name.lower(),
        ]
        
        selected_voice = None
        for check in priority_voices:
            for voice in voices:
                if check(voice):
                    selected_voice = voice
                    break
            if selected_voice:
                break
        
        if not selected_voice:
            selected_voice = voices[0]
        
        print(f"🎤 VOZ WINDOWS: {selected_voice.name}")
        self.tts_engine.setProperty('voice', selected_voice.id)
        self.tts_engine.setProperty('rate', 135)  # Mais lento = mais grave
        self.tts_engine.setProperty('volume', 0.95)
    
    def speak_elevenlabs(self, text):
        """Usa ElevenLabs (MELHOR qualidade) - API v2.36"""
        try:
            from elevenlabs.client import ElevenLabs
            
            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            
            # Gera áudio usando API v2.36
            audio_iterator = client.text_to_speech.convert(
                voice_id=ELEVENLABS_VOICE_ID,
                text=text,
                model_id="eleven_multilingual_v2"
            )
            
            # Salva em arquivo temporário
            temp_file = self.temp_audio_dir / "jarvis_temp.mp3"
            with open(temp_file, 'wb') as f:
                for chunk in audio_iterator:
                    if chunk:
                        f.write(chunk)
            
            # Reproduz com pygame (mais confiável que playsound)
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(str(temp_file))
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                temp_file.unlink()
            except ImportError:
                # Fallback para playsound se pygame não disponível
                playsound(str(temp_file))
                temp_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"❌ ElevenLabs falhou: {e}")
            print("   Tentando próxima engine...")
            return False
    
    def speak_azure(self, text):
        """Usa Azure TTS"""
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            speech_config = speechsdk.SpeechConfig(
                subscription=AZURE_SPEECH_KEY,
                region=AZURE_REGION
            )
            speech_config.speech_synthesis_voice_name = "en-US-GuyNeural"
            
            temp_file = self.temp_audio_dir / "jarvis_temp.wav"
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(temp_file))
            
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                try:
                    import pygame
                    pygame.mixer.init()
                    pygame.mixer.music.load(str(temp_file))
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                except ImportError:
                    from playsound import playsound
                    playsound(str(temp_file))
                temp_file.unlink()
                return True
            else:
                print(f"❌ Azure falhou: {result.reason}")
                return False
                
        except Exception as e:
            print(f"❌ Azure falhou: {e}")
            return False
    
    def speak_google(self, text):
        """Usa Google Cloud TTS"""
        try:
            from google.cloud import texttospeech
            
            client = texttospeech.TextToSpeechClient()
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Wavenet-D",
                ssml_gender=texttospeech.SsmlVoiceGender.MALE
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.9,
                pitch=-2.0
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            temp_file = self.temp_audio_dir / "jarvis_temp.mp3"
            with open(temp_file, "wb") as f:
                f.write(response.audio_content)
            
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(str(temp_file))
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            except ImportError:
                from playsound import playsound
                playsound(str(temp_file))
            temp_file.unlink()
            return True
            
        except Exception as e:
            print(f"❌ Google falhou: {e}")
            return False
    
    def speak_pyttsx3(self, text):
        """Fallback para pyttsx3"""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            return True
        except Exception as e:
            print(f"❌ pyttsx3 falhou: {e}")
            return False
    
    def speak(self, text):
        """Fala usando melhor engine disponível com fallback"""
        print(f"[JARVIS] {text}")
        
        # Tenta engines em ordem de prioridade
        for engine_name, engine_label in self.engine_priority:
            if engine_name == "elevenlabs":
                if self.speak_elevenlabs(text):
                    return
            elif engine_name == "azure":
                if self.speak_azure(text):
                    return
            elif engine_name == "google":
                if self.speak_google(text):
                    return
            elif engine_name == "pyttsx3":
                if self.speak_pyttsx3(text):
                    return
        
        print("❌ Todas engines de voz falharam!")


class JarvisAssistant:
    def __init__(self):
        self.voice = JarvisPremiumVoice()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        with self.microphone as source:
            print("[CALIBRAÇÃO] Ajustando para ruído ambiente...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        
        print("[INICIALIZAÇÃO] JARVIS Premium pronto!\n")
    
    def listen_for_wake_word(self):
        """Escuta wake word 'Jarvis'"""
        with self.microphone as source:
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                text = self.recognizer.recognize_google(audio, language="pt-BR").lower()
                
                if any(wake in text for wake in ["jarvis", "jarviz", "gervis"]):
                    return True
                    
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                pass
            except Exception as e:
                print(f"[ERRO] {e}")
        
        return False
    
    def listen_command(self):
        """Captura comando"""
        self.voice.speak("Sim, senhor.")
        
        with self.microphone as source:
            print("[ESCUTANDO] Aguardando comando...")
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                command = self.recognizer.recognize_google(audio, language="pt-BR")
                print(f"[COMANDO] {command}")
                return command
            except sr.UnknownValueError:
                self.voice.speak("Não compreendi.")
                return None
            except Exception as e:
                print(f"[ERRO] {e}")
                return None
    
    def call_api(self, endpoint, method="GET", data=None):
        """Chama API Hoops Jarvis"""
        try:
            url = f"{API_BASE}{endpoint}"
            response = requests.get(url, timeout=5) if method == "GET" else requests.post(url, json=data, timeout=5)
            return response.json() if response.ok else None
        except Exception as e:
            print(f"[API ERRO] {e}")
            return None
    
    def execute_command(self, command):
        """Executa comando"""
        if not command:
            return
        
        cmd = command.lower()
        
        # Comandos sistema
        if "iniciar" in cmd or "start" in cmd:
            self.call_api("/api/control/start", "POST")
            self.voice.speak("Sistema de arbitragem iniciado, senhor.")
            return
        
        if "parar" in cmd or "stop" in cmd:
            self.call_api("/api/control/stop", "POST")
            self.voice.speak("Monitoramento pausado.")
            return
        
        if "status" in cmd:
            status = self.call_api("/api/status")
            if status:
                state = "operacional" if status.get('running') else "em standby"
                self.voice.speak(f"Sistema {state}, senhor.")
                return
        
        if "lucro" in cmd or "resultado" in cmd:
            report = self.call_api("/api/report")
            if report:
                total = report.get('total_bets', 0)
                self.voice.speak(f"{total} operações processadas até o momento.")
                return
        
        if "abra" in cmd or "abrir" in cmd:
            if "painel" in cmd:
                webbrowser.open("http://localhost:8000")
                self.voice.speak("Abrindo painel de controle.")
                return
            if "bet365" in cmd:
                webbrowser.open("https://www.bet365.com")
                self.voice.speak("Abrindo plataforma Bet365.")
                return
        
        self.voice.speak("Comando não reconhecido, senhor.")
    
    def run(self):
        """Loop principal"""
        self.voice.speak("Jarvis online senhor. Todos os sistemas operacionais. Pronto para receber comandos.")
        
        while True:
            try:
                print("\n[AGUARDANDO] Diga 'Jarvis'...")
                
                if self.listen_for_wake_word():
                    command = self.listen_command()
                    
                    if command and "desligar jarvis" in command.lower():
                        self.voice.speak("Encerrando sistemas. Até logo, senhor.")
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
║              JARVIS PREMIUM - Iron Man Edition             ║
║         Melhor qualidade de voz possível disponível        ║
╚════════════════════════════════════════════════════════════╝

[REQUISITOS]
1. Visual C++ Build Tools instalado
2. PyAudio funcionando
3. Opcional: API keys para vozes premium (.env)

[VOZES SUPORTADAS]
⭐⭐⭐⭐⭐ ElevenLabs (igual ao filme!)
⭐⭐⭐⭐   Azure Neural TTS
⭐⭐⭐⭐   Google WaveNet
⭐⭐⭐     Windows Premium

Iniciando...
""")
    
    time.sleep(2)
    
    try:
        assistant = JarvisAssistant()
        assistant.run()
    except Exception as e:
        print(f"\n[ERRO FATAL] {e}")
        print("\nVerifique:")
        print("1. Visual C++ Build Tools instalado")
        print("2. PyAudio: pip install PyAudio")
        print("3. Microfone conectado e permitido")
