"""
Voice Narration Engine - Motor de narração inteligente integrado ao Communication Engine
Responsável por:
- Narrar briefings, recomendações e alertas via TTS
- Adaptar tom de voz ao contexto (alerta crítico vs oportunidade)
- Priorizar mensagens importantes
- Integração com ElevenLabs e pyttsx3
"""

import threading
import time
import queue
from typing import Dict, Any, Optional
from pathlib import Path

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("⚠️ pyttsx3 não disponível - narração offline desabilitada")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class VoiceNarrationEngine:
    """Motor de narração de voz integrado ao sistema de comunicação"""

    def __init__(self, use_premium: bool = False, elevenlabs_api_key: Optional[str] = None):
        self.use_premium = use_premium
        self.elevenlabs_api_key = elevenlabs_api_key
        self.queue = queue.Queue(maxsize=50)
        self.running = False
        self.thread = None
        
        # Inicializar pyttsx3 offline
        if PYTTSX3_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 160)
                self.tts_engine.setProperty('volume', 0.9)
            except Exception as e:
                print(f"Erro ao inicializar pyttsx3: {e}")
                self.tts_engine = None
        else:
            self.tts_engine = None

    def start(self):
        """Inicia thread de narração em background"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._narration_loop, daemon=True)
        self.thread.start()
        print("🔊 Voice Narration Engine iniciado")

    def stop(self):
        """Para thread de narração"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("🔇 Voice Narration Engine parado")

    def _narration_loop(self):
        """Loop principal de narração"""
        while self.running:
            try:
                # Pegar mensagem da fila (timeout de 1s)
                message = self.queue.get(timeout=1)
                
                # Narrar
                self._speak(message["text"], message.get("priority", "normal"))
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Erro no loop de narração: {e}")
                time.sleep(0.5)

    def _speak(self, text: str, priority: str = "normal"):
        """Narra texto via TTS"""
        if not text.strip():
            return

        # ElevenLabs premium (se configurado)
        if self.use_premium and self.elevenlabs_api_key and REQUESTS_AVAILABLE:
            try:
                self._speak_elevenlabs(text, priority)
                return
            except Exception as e:
                print(f"Erro ElevenLabs: {e}, fallback para pyttsx3")

        # pyttsx3 offline fallback
        if self.tts_engine:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"Erro pyttsx3: {e}")

    def _speak_elevenlabs(self, text: str, priority: str):
        """Narra via ElevenLabs API"""
        url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
        
        # Ajustar voice settings por prioridade
        stability = 0.6 if priority == "critical" else 0.5
        similarity = 0.8
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key,
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity,
            }
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Salvar áudio temporário e tocar
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                f.write(response.content)
                audio_path = f.name
            
            # Tocar áudio (usar playsound ou outra lib)
            try:
                import playsound
                playsound.playsound(audio_path)
            except Exception:
                print(f"⚠️ Áudio salvo em {audio_path}, mas não é possível tocar")
            finally:
                try:
                    os.remove(audio_path)
                except Exception:
                    pass
        else:
            raise Exception(f"ElevenLabs retornou {response.status_code}")

    # ============================================
    # PUBLIC METHODS - Adicionar mensagens à fila
    # ============================================

    def narrate_briefing(self, briefing_text: str):
        """Narra briefing do Jarvis"""
        # Resumir briefing para não ficar muito longo
        lines = briefing_text.split("\n")
        summary = "\n".join(lines[:5])  # Primeiras 5 linhas
        
        self.queue.put({
            "text": f"Briefing de inteligência. {summary}",
            "priority": "normal"
        })

    def narrate_recommendation(self, team_a: str, team_b: str, confidence: int):
        """Narra recomendação de aposta"""
        confidence_text = "alta confiança" if confidence >= 75 else "moderada confiança"
        
        text = f"Oportunidade detectada. {team_a} versus {team_b}. {confidence_text}."
        
        self.queue.put({
            "text": text,
            "priority": "high" if confidence >= 75 else "normal"
        })

    def narrate_alert(self, alert_text: str, is_critical: bool = False):
        """Narra alerta de risco ou Safe Mode"""
        priority = "critical" if is_critical else "high"
        
        self.queue.put({
            "text": alert_text,
            "priority": priority
        })

    def narrate_immediate_feedback(self, event: str, message: str, narration: Optional[str] = None):
        """Narra feedback imediato de DETECTADO, APOSTOU, BLOQUEADO"""
        if narration:
            self.queue.put({
                "text": narration,
                "priority": "normal" if event == "DETECTADO" else "high"
            })

    def narrate_pattern_insight(self, insight_text: str):
        """Narra insight de padrão descoberto"""
        self.queue.put({
            "text": f"Padrão descoberto. {insight_text}",
            "priority": "normal"
        })

    def narrate_weekly_summary(self, summary_text: str):
        """Narra resumo semanal"""
        # Pegar só as primeiras linhas
        lines = summary_text.split("\n")
        summary = "\n".join(lines[:4])
        
        self.queue.put({
            "text": f"Resumo semanal. {summary}",
            "priority": "normal"
        })

    def narrate_custom(self, text: str, priority: str = "normal"):
        """Narra texto customizado"""
        self.queue.put({
            "text": text,
            "priority": priority
        })

    def get_queue_size(self) -> int:
        """Retorna tamanho da fila de narração"""
        return self.queue.qsize()

    def clear_queue(self):
        """Limpa fila de narração"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
