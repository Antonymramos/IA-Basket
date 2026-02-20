#!/usr/bin/env python3
"""
JARVIS - Assistente com WAKE WORD usando bibliotecas sem compilação
Alternativa ao PyAudio: usa sounddevice + vosk para detecção offline
"""

import os
import sys
import time
import re
import webbrowser
import subprocess
import requests
import unicodedata
import threading
from queue import Empty
from datetime import datetime
from urllib.parse import quote
from pathlib import Path

try:
    import sounddevice as sd
    import numpy as np
    import pyttsx3
    from dotenv import load_dotenv
    import vosk
    import queue
    import json
except ImportError:
    print("Instalando dependências sem compilação...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "sounddevice", "numpy", "pyttsx3", "python-dotenv", "elevenlabs",
                          "vosk", "requests"])
    print("\nAgora baixando modelo de reconhecimento de voz offline...")
    print("Execute novamente o script.")
    sys.exit(0)

load_dotenv()

API_BASE = "http://localhost:8000"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "vosk-model-small-pt-0.3")
SCRIPT_DIR = Path(__file__).resolve().parent


def normalize_pt_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = ''.join(
        ch for ch in unicodedata.normalize('NFD', text)
        if unicodedata.category(ch) != 'Mn'
    )
    return ' '.join(text.split())


def strip_wake_words(text: str) -> str:
    wake_words = {"jarvis", "jarve", "jarves", "jarviz", "jarvi", "jarbis", "gervis", "jarvins"}
    noise_tokens = {"ja", "jardim", "jazz", "jar", "jarv", "vos", "voce", "vo"}
    verb_tokens = {
        "abrir", "abre", "abra", "abri",
        "iniciar", "inicia", "ligar", "liga",
        "parar", "pausar", "stop", "status",
        "situacao", "lucro", "resultado", "relatorio",
        "buscar", "busca", "pesquisa", "analisar",
    }
    tokens = [tok for tok in (text or "").split() if tok not in wake_words]

    # Remove ruídos iniciais quando há um verbo de comando logo depois.
    max_strip = 2
    while tokens and max_strip > 0:
        ahead = tokens[1:3]
        if tokens[0] in noise_tokens and any(tok in verb_tokens for tok in ahead):
            tokens.pop(0)
            max_strip -= 1
            continue
        if tokens[0] in wake_words:
            tokens.pop(0)
            max_strip -= 1
            continue
        break

    return " ".join(tokens).strip()


def has_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def has_any_word(text: str, words: list[str]) -> bool:
    return any(has_word(text, word) for word in words)


def list_search_roots(include_drives: bool = True) -> list[str]:
    roots = []
    home = os.path.expanduser("~")
    for sub in ["Desktop", "Documents", "Downloads"]:
        path = os.path.join(home, sub)
        if os.path.isdir(path):
            roots.append(path)
    if include_drives:
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.isdir(drive):
                roots.append(drive)
    return roots


def match_folder_name(name: str, tokens: list[str]) -> bool:
    normalized = normalize_pt_text(name)
    return all(tok in normalized for tok in tokens)


def find_folder(tokens: list[str], roots: list[str], max_dirs: int = 30000, max_seconds: int = 20):
    if not tokens or not roots:
        return None, "invalid"
    start = time.time()
    scanned = 0
    skip = {
        "$recycle.bin",
        "system volume information",
        "windows",
        "program files",
        "program files (x86)",
        "appdata",
        "temp",
        "tmp",
    }
    for root in roots:
        for dirpath, dirnames, _ in os.walk(root):
            scanned += 1
            if scanned >= max_dirs or (time.time() - start) > max_seconds:
                return None, "timeout"

            dirnames[:] = [d for d in dirnames if normalize_pt_text(d) not in skip]
            for d in dirnames:
                if match_folder_name(d, tokens):
                    return os.path.join(dirpath, d), "found"
    return None, "not_found"


def open_search_in_explorer(query: str, location: str) -> None:
    if not query:
        return
    loc = location or os.path.expanduser("~")
    uri = f"search-ms:query={quote(query)}&crumb=location:{loc}"
    subprocess.Popen(["explorer.exe", uri])

class JarvisVoice:
    def __init__(self):
        self.use_premium = False
        self.setup_premium_voice()
        self.engine = pyttsx3.init()
        self.setup_voice()

    def setup_premium_voice(self):
        if not ELEVENLABS_API_KEY:
            print("[VOZ] ElevenLabs não configurado. Usando Windows TTS.")
            return
        try:
            from elevenlabs.client import ElevenLabs
            self.elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            self.use_premium = True
            print("[VOZ] ElevenLabs Premium ativo ✅")
        except Exception as e:
            print(f"[VOZ] ElevenLabs indisponível: {e}")
            self.use_premium = False
        
    def setup_voice(self):
        """Configura voz masculina grave em PT-BR"""
        voices = self.engine.getProperty('voices')
        
        pt_voices = [v for v in voices if 'portuguese' in v.name.lower() or 'pt-br' in v.id.lower() or 'daniel' in v.name.lower() or 'antonio' in v.name.lower()]
        
        if pt_voices:
            target_voice = pt_voices[0]
            print(f"[VOZ] Usando: {target_voice.name}")
        else:
            target_voice = voices[0]
            print(f"[VOZ] PT-BR não encontrado. Usando: {target_voice.name}")
        
        self.engine.setProperty('voice', target_voice.id)
        self.engine.setProperty('rate', 140)
        self.engine.setProperty('volume', 0.9)
    
    def speak(self, text):
        print(f"[JARVIS] {text}")
        if self.use_premium:
            try:
                audio_iterator = self.elevenlabs_client.text_to_speech.convert(
                    voice_id=ELEVENLABS_VOICE_ID,
                    text=text,
                    model_id="eleven_multilingual_v2",
                    output_format="pcm_24000"
                )

                pcm_bytes = b""
                for chunk in audio_iterator:
                    if chunk:
                        pcm_bytes += chunk

                samples = np.frombuffer(pcm_bytes, dtype=np.int16)
                sd.play(samples, samplerate=24000)
                sd.wait()
                return
            except Exception as e:
                print(f"[VOZ] Falha premium, fallback Windows TTS: {e}")

        self.engine.say(text)
        self.engine.runAndWait()


class WakeWordDetector:
    def __init__(self, model_path=VOSK_MODEL_PATH):
        """Detector de wake word usando Vosk (offline)"""
        resolved_path = Path(model_path)
        if not resolved_path.is_absolute():
            resolved_path = SCRIPT_DIR / resolved_path
        default_path = SCRIPT_DIR / "vosk-model-small-pt-0.3"
        if not resolved_path.exists() and default_path.exists():
            resolved_path = default_path
        self.model_path = str(resolved_path)
        self.model = None
        self.q = queue.Queue()
        self.sample_rate = 16000
        self.input_device = None
        self.input_gain = float(os.getenv("JARVIS_MIC_GAIN", "2.0"))
        self.silence_seconds = float(os.getenv("JARVIS_SILENCE_SECONDS", "1.2"))
        self.min_confidence = float(os.getenv("JARVIS_MIN_CONFIDENCE", "0.55"))
        
        # Download modelo se não existir
        if not os.path.exists(self.model_path):
            print(f"[WAKE] Modelo nao encontrado em: {self.model_path}")
            self.download_model()
            fallback_path = SCRIPT_DIR / "vosk-model-small-pt-0.3"
            if fallback_path.exists():
                self.model_path = str(fallback_path)
        
        try:
            self.model = vosk.Model(self.model_path)
            print(f"[WAKE] Modelo carregado: {self.model_path}")
            self.setup_input_device()
            self.optimize_input_device()
            self.check_microphone_signal()
        except Exception as e:
            print(f"[ERRO] Modelo Vosk: {e}")
            print(f"[ERRO] Caminho do modelo: {self.model_path}")
            print("Execute: python download_vosk_model.py")

    def measure_input_level(self, device_index, seconds=0.35):
        """Mede nível médio de áudio de um dispositivo de entrada"""
        try:
            audio = sd.rec(
                int(self.sample_rate * seconds),
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                device=device_index
            )
            sd.wait()
            return float(np.abs(audio).mean())
        except Exception:
            return 0.0

    def optimize_input_device(self):
        """Quando sinal está baixo, tenta achar automaticamente outro microfone melhor"""
        if self.input_device is None:
            return
        try:
            current_level = self.measure_input_level(self.input_device, seconds=0.35)
            devices = list(sd.query_devices())

            # Candidatos: só entradas válidas, ignorando mapeadores genéricos
            reject_tokens = ["mapeador", "mapper", "driver de captura", "primary sound capture driver"]
            candidates = []
            for i, dev in enumerate(devices):
                name = str(dev.get("name", "")).lower()
                if dev.get("max_input_channels", 0) <= 0:
                    continue
                if any(t in name for t in reject_tokens):
                    continue
                candidates.append(i)

            best_device = self.input_device
            best_level = current_level

            for idx in candidates:
                lvl = self.measure_input_level(idx, seconds=0.25)
                if lvl > best_level:
                    best_level = lvl
                    best_device = idx

            current_name = str(devices[self.input_device]["name"]).strip().lower()
            best_name = str(devices[best_device]["name"]).strip().lower()

            if best_device != self.input_device and best_name == current_name:
                return

            if best_device != self.input_device and best_level > (current_level + 1.0):
                old_name = devices[self.input_device]["name"]
                new_name = devices[best_device]["name"]
                print(f"[MIC] Trocando dispositivo por maior sinal: {self.input_device} ({old_name}) -> {best_device} ({new_name})")
                self.input_device = best_device
        except Exception as e:
            print(f"[MIC] Falha ao otimizar dispositivo: {e}")

    def listen_for_trigger_or_direct_command(self):
        """Escuta wake word OU comando direto (fallback para não ficar travado no 'Jarvis')."""
        if not self.model:
            return None, None

        wake_variants = ["jarvis", "jarves", "jarviz", "jarvi", "jarve", "gervis", "jarvins", "jardim", "jazz"]
        direct_tokens = [
            "iniciar", "inicia", "ligar", "liga", "parar", "pausar", "stop", "status",
            "situacao", "situação", "lucro", "resultado", "relatorio", "relatório",
            "abrir", "abre", "painel", "bet365", "bet", "aposta", "auto",
            "erro", "erros", "diagnostico", "diagnóstico", "pesquisa", "buscar", "nba",
            "procurar", "encontrar", "localizar", "pasta", "projeto", "diretorio", "diretório"
        ]

        try:
            self.clear_queue()
            rec = vosk.KaldiRecognizer(self.model, self.sample_rate)
            rec.SetWords(True)
            rec.SetPartialWords(True)

            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=4000,
                dtype='int16',
                channels=1,
                device=self.input_device,
                callback=self.audio_callback,
            ):
                while True:
                    try:
                        data = self.q.get(timeout=1)
                    except Empty:
                        continue

                    accepted = rec.AcceptWaveform(data)
                    if accepted:
                        text = json.loads(rec.Result()).get("text", "")
                    else:
                        text = json.loads(rec.PartialResult()).get("partial", "")

                    if not text:
                        continue

                    normalized = normalize_pt_text(text)
                    if has_any_word(normalized, wake_variants):
                        print(f"[WAKE] Detectado: {text}")
                        return "wake", text

                    if has_any_word(normalized, direct_tokens):
                        print(f"[TRIGGER] Comando direto detectado: {text}")
                        return "direct", text
        except Exception as e:
            print(f"[ERRO] Trigger/Comando: {e}")
            return None, None

    def setup_input_device(self):
        """Seleciona microfone de entrada de forma robusta"""
        try:
            forced = os.getenv("JARVIS_MIC_DEVICE")
            if forced and forced.isdigit():
                self.input_device = int(forced)
                dev = sd.query_devices(self.input_device)
                print(f"[MIC] Forçado via JARVIS_MIC_DEVICE={self.input_device}: {dev['name']}")
                return

            default_in = None
            default_device = sd.default.device
            if isinstance(default_device, (list, tuple)) and len(default_device) > 0:
                default_in = default_device[0]
            elif isinstance(default_device, int):
                default_in = default_device

            devices = list(sd.query_devices())

            if default_in is not None and int(default_in) >= 0:
                default_dev = devices[default_in]
                if default_dev.get("max_input_channels", 0) > 0:
                    self.input_device = default_in
                    print(f"[MIC] Usando default input {default_in}: {default_dev['name']}")
                    return

            preferred_tokens = ["microfone", "microphone", "headset", "kofire", "usb"]
            reject_tokens = ["mapeador", "mapper", "driver de captura", "primary sound capture driver"]

            for i, dev in enumerate(devices):
                name = str(dev.get("name", "")).lower()
                if any(t in name for t in reject_tokens):
                    continue
                if dev.get("max_input_channels", 0) > 0 and any(t in name for t in preferred_tokens):
                    self.input_device = i
                    print(f"[MIC] Selecionado automaticamente {i}: {dev['name']}")
                    return

            for i, dev in enumerate(devices):
                name = str(dev.get("name", "")).lower()
                if any(t in name for t in reject_tokens):
                    continue
                if dev.get("max_input_channels", 0) > 0:
                    self.input_device = i
                    print(f"[MIC] Fallback de entrada {i}: {dev['name']}")
                    return

            print("[MIC] Nenhum dispositivo de entrada encontrado.")
        except Exception as e:
            print(f"[MIC] Falha ao selecionar dispositivo: {e}")

    def check_microphone_signal(self):
        """Teste rápido para validar se há sinal no microfone"""
        if self.input_device is None:
            return
        try:
            print("[MIC] Testando sinal por 1 segundo...")
            audio = sd.rec(
                int(self.sample_rate * 1.0),
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                device=self.input_device
            )
            sd.wait()
            level = float(np.abs(audio).mean())
            boosted_level = level * self.input_gain
            print(f"[MIC] Nível médio de sinal: {level:.2f} | ganho: x{self.input_gain:.1f} | efetivo: {boosted_level:.2f}")
            if boosted_level < 3:
                self.input_gain = min(self.input_gain + 2.0, 6.0)
                print(f"[MIC] Sinal muito baixo. Ajustando ganho para x{self.input_gain:.1f}.")
            elif boosted_level < 6:
                self.input_gain = min(self.input_gain + 1.0, 4.0)
                print(f"[MIC] Sinal baixo. Ajustando ganho para x{self.input_gain:.1f}.")
        except Exception as e:
            print(f"[MIC] Não foi possível testar sinal: {e}")
    
    def download_model(self):
        """Download modelo PT-BR pequeno"""
        print("[DOWNLOAD] Baixando modelo de voz PT-BR (50MB)...")
        print("Isso leva ~2 minutos, aguarde...")
        
        import urllib.request
        import zipfile
        
        url = "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
        zip_path = str(SCRIPT_DIR / "vosk-model.zip")
        
        try:
            urllib.request.urlretrieve(url, zip_path)
            print("[DOWNLOAD] Extraindo...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(str(SCRIPT_DIR))
            os.remove(zip_path)
            print("[DOWNLOAD] Modelo instalado!")
        except Exception as e:
            print(f"[ERRO] Download: {e}")
            print("Baixe manualmente: https://alphacephei.com/vosk/models")
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback para captura de áudio"""
        if status:
            print(status)
        try:
            samples = np.frombuffer(bytes(indata), dtype=np.int16).astype(np.float32)
            if self.input_gain != 1.0:
                samples = np.clip(samples * self.input_gain, -32768, 32767)
            self.q.put(samples.astype(np.int16).tobytes())
        except Exception:
            self.q.put(bytes(indata))

    def clear_queue(self):
        """Limpa buffer de áudio pendente"""
        try:
            while not self.q.empty():
                self.q.get_nowait()
        except Exception:
            pass
    
    def listen_for_wake_word(self):
        """Escuta por 'jarvis'"""
        if not self.model:
            return False
        
        try:
            self.clear_queue()
            wake_variants = ["jarvis", "jarves", "jarviz", "gervis", "jarvins"]
            wake_grammar = '["jarvis", "jarves", "jarviz", "gervis", "jarvins"]'
            rec = vosk.KaldiRecognizer(self.model, self.sample_rate, wake_grammar)
            rec.SetWords(True)
            rec.SetPartialWords(True)
            
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=4000, dtype='int16',
                                   channels=1, device=self.input_device, callback=self.audio_callback):
                
                while True:
                    try:
                        data = self.q.get(timeout=1)
                    except Empty:
                        continue

                    accepted = rec.AcceptWaveform(data)
                    if accepted:
                        result = json.loads(rec.Result())
                        text = result.get('text', '').lower()

                        if any(w in text for w in wake_variants):
                            print(f"[WAKE] Detectado: {text}")
                            return True
                    else:
                        partial = json.loads(rec.PartialResult()).get('partial', '').lower()
                        if partial and any(w in partial for w in wake_variants):
                            print(f"[WAKE] Detectado (parcial): {partial}")
                            return True
        except Exception as e:
            print(f"[ERRO] Escuta: {e}")
            return False
    
    def listen_command(self):
        """Captura comando completo"""
        if not self.model:
            return None
        
        try:
            self.clear_queue()
            rec = vosk.KaldiRecognizer(self.model, self.sample_rate)
            rec.SetWords(True)
            rec.SetPartialWords(True)
            
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=4000, dtype='int16',
                                   channels=1, device=self.input_device, callback=self.audio_callback):
                
                print("[COMANDO] Escutando (8 segundos)...")
                start_time = time.time()
                last_voice_time = start_time
                full_text = []
                latest_partial = ""
                final_payload = None
                
                while time.time() - start_time < 8:
                    try:
                        data = self.q.get(timeout=1)
                    except Empty:
                        continue

                    accepted = rec.AcceptWaveform(data)
                    if accepted:
                        result = json.loads(rec.Result())
                        final_payload = result
                        text = result.get('text', '')
                        if text:
                            full_text.append(text)
                            last_voice_time = time.time()
                    else:
                        partial = json.loads(rec.PartialResult()).get('partial', '').strip()
                        if partial and partial != latest_partial:
                            latest_partial = partial
                            last_voice_time = time.time()

                    if full_text and (time.time() - last_voice_time) > self.silence_seconds:
                        break

                # Captura texto final reconhecido (muito importante no Vosk)
                final_result = json.loads(rec.FinalResult())
                final_payload = final_payload or final_result
                final_text = final_result.get('text', '')
                if final_text:
                    full_text.append(final_text)
                elif latest_partial:
                    full_text.append(latest_partial)
                
                command = ' '.join(full_text)
                command = ' '.join(command.split()).strip()
                if final_payload and final_payload.get("result"):
                    confs = [w.get("conf", 0) for w in final_payload.get("result", []) if w.get("conf") is not None]
                    if confs and (sum(confs) / len(confs)) < self.min_confidence:
                        print("[ASR] Confiança baixa, descartando comando.")
                        return None
                if command:
                    print(f"[ASR] Texto capturado: {command}")
                return command if command else None
                
        except Exception as e:
            print(f"[ERRO] Comando: {e}")
            return None


class JarvisAssistant:
    def __init__(self, use_wake_word=True):
        self.voice = JarvisVoice()
        self.use_wake_word = use_wake_word
        self.wake_detector = WakeWordDetector()
        
    def call_api(self, endpoint, method="GET", data=None):
        """Chama API do Hoops Jarvis"""
        try:
            url = f"{API_BASE}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=5)
            
            if response.ok:
                return response.json()
        except Exception as e:
            print(f"[ERRO] API {endpoint}: {e}")
        return None
    
    def execute_command(self, command):
        """Executa comando"""
        if not command:
            return
        
        cmd = normalize_pt_text(command)
        cmd = strip_wake_words(cmd)
        print(f"[COMANDO NORMALIZADO] {cmd}")

        # Primeiro, usa o parser oficial do backend (mesma regra do frontend)
        backend_voice = self.call_api("/api/voice/command", "POST", {"text": cmd})
        if backend_voice and backend_voice.get("status") in ["ok", "noop"]:
            action = (backend_voice.get("action") or {}).get("action", "noop")
            if action == "start":
                self.voice.speak("Sistema iniciado.")
                return
            if action == "stop":
                self.voice.speak("Sistema pausado.")
                return
            if action == "set_auto_bet":
                enabled = (backend_voice.get("action") or {}).get("enabled", False)
                self.voice.speak("Aposta automática ativada." if enabled else "Aposta automática desativada.")
                return
            if action == "select_game":
                game = (backend_voice.get("action") or {}).get("game", "")
                self.voice.speak(f"Jogo selecionado: {game}." if game else "Jogo selecionado.")
                return
            if action == "open_errors_panel":
                webbrowser.open("http://localhost:8000/#erros")
                self.voice.speak("Abrindo painel dos erros da bet.")
                return
            if action == "knowledge_query":
                answer = (backend_voice.get("knowledge_response") or "").strip()
                if answer:
                    short_answer = answer.split("\n")[0][:220]
                    self.voice.speak(short_answer)
                else:
                    self.voice.speak("Consulta concluída, mas sem resposta objetiva.")
                return
        
        # Controle sistema
        if has_any_word(cmd, ["iniciar", "inicia", "start", "ligar", "liga"]):
            result = self.call_api("/api/control/start", "POST")
            if result is not None:
                self.voice.speak("Sistema iniciado.")
            else:
                self.voice.speak("Nao consegui conectar ao backend para iniciar.")
            return
        
        if has_any_word(cmd, ["parar", "pausar", "stop", "desligar"]):
            result = self.call_api("/api/control/stop", "POST")
            if result is not None:
                self.voice.speak("Sistema pausado.")
            else:
                self.voice.speak("Nao consegui conectar ao backend para parar.")
            return
        
        if has_any_word(cmd, ["status", "situacao"]):
            status = self.call_api("/api/status")
            if status:
                running = "rodando" if status.get('running') else "parado"
                self.voice.speak(f"Sistema {running}.")
                return
        
        if has_any_word(cmd, ["lucro", "resultado", "relatorio"]):
            report = self.call_api("/api/report")
            if report:
                total = report.get('total_bets', 0)
                self.voice.speak(f"{total} apostas hoje.")
                return
        
        # Abrir apps
        if has_any_word(cmd, ["abra", "abrir", "abre", "abri"]):
            if has_word(cmd, "painel"):
                webbrowser.open("http://localhost:8000")
                self.voice.speak("Abrindo painel.")
                return

            if has_word(cmd, "erro") or has_word(cmd, "erros"):
                webbrowser.open("http://localhost:8000/#erros")
                self.voice.speak("Abrindo painel dos erros.")
                return
            
            if has_any_word(cmd, ["bet365", "bet", "betty", "bete", "beti"]):
                webbrowser.open("https://www.bet365.com")
                self.voice.speak("Abrindo Bet365.")
                return

            if has_any_word(cmd, ["nba", "basquete", "basket"]):
                webbrowser.open("https://www.nba.com/schedule")
                self.voice.speak("Abrindo últimos jogos da NBA.")
                return

            # Fallback: abrir painel principal se não houver destino explícito.
            webbrowser.open("http://localhost:8000")
            self.voice.speak("Abrindo painel principal.")
            return

        # Comandos utilitários no PC
        if has_any_word(cmd, ["abrir", "abre"]) and has_any_word(cmd, ["projeto", "pasta"]):
            project_path = os.getcwd()
            os.startfile(project_path)
            self.voice.speak("Abrindo pasta do projeto.")
            return

        if has_any_word(cmd, ["procurar", "encontrar", "localizar"]) and has_any_word(
            cmd, ["pasta", "projeto", "diretorio", "diretorio"]
        ):
            target = ""
            match = re.search(r"(pasta|projeto|diretorio)\s+(.+)$", cmd)
            if match:
                target = match.group(2).strip()
            if not target and has_word(cmd, "ia") and has_word(cmd, "basket"):
                target = "ia basket"

            if not target:
                self.voice.speak("Qual pasta voce quer procurar?")
                return

            tokens = normalize_pt_text(target).split()
            roots = list_search_roots(include_drives=True)
            found, status = find_folder(tokens, roots)
            if found:
                os.startfile(found)
                self.voice.speak(f"Pasta encontrada: {os.path.basename(found)}.")
            else:
                open_search_in_explorer(target, roots[0] if roots else "C:\\")
                self.voice.speak("Nao encontrei rapido. Abri o Explorer com a busca.")
            return

        if has_any_word(cmd, ["iniciar", "abre"]) and has_any_word(cmd, ["backend", "api"]):
            try:
                subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--reload"])
                self.voice.speak("Backend iniciado.")
            except Exception:
                self.voice.speak("Não consegui iniciar o backend agora.")
            return
        
        self.voice.speak("Comando não reconhecido.")
    
    def _start_monitoring_thread(self):
        """Inicia thread de monitoramento de transmissão vs bet"""
        def monitor_transmission_bet():
            last_desync_ids = set()
            last_pending_ids = set()
            
            while True:
                try:
                    time.sleep(30)  # Verifica a cada 30 segundos
                    
                    status = self.call_api("/api/transmission-bet-status?minutes=60")
                    if not status:
                        continue
                    
                    # Alertar sobre DESYNC novos
                    desync_events = status.get("desync", {}).get("recent_events", [])
                    for evt in desync_events:
                        evt_id = f"{evt.get('signal_id')}_{evt.get('ts')}"
                        if evt_id not in last_desync_ids:
                            last_desync_ids.add(evt_id)
                            t_a, t_b = evt.get("t_a", 0), evt.get("t_b", 0)
                            b_a, b_b = evt.get("b_a", 0), evt.get("b_b", 0)
                            diff_a, diff_b = evt.get("diff_a", 0), evt.get("diff_b", 0)
                            
                            alert = f"Desincronização detectada. Transmissão: {t_a} a {t_b}. Bet: {b_a} a {b_b}. Diferença: {diff_a} e {diff_b}."
                            print(f"[ALERTA] {alert}")
                            # Não fala para não interrumpir commands, apenas loga
                    
                    # Alertar sobre DELAY_PENDING (atrasos)
                    pending_events = status.get("delay", {}).get("pending_events", [])
                    for evt in pending_events:
                        evt_id = f"{evt.get('signal_id')}_{evt.get('ts')}"
                        if evt_id not in last_pending_ids:
                            last_pending_ids.add(evt_id)
                            age = evt.get("age_seconds", 0)
                            threshold = evt.get("threshold", 0)
                            
                            if age > threshold:
                                alert = f"Alerta: Aposta atrasada. Idade do sinal: {age:.1f} segundos, limite: {threshold:.1f} segundos."
                                print(f"[ALERTA DELAY] {alert}")
                                # Fala o alerta de atraso crítico
                                if age > threshold + 2:  # Apenas se for significativamente atrasado
                                    self.voice.speak(alert)
                    
                    # Mostrar estatísticas de delay se disponível
                    delay_info = status.get("delay", {})
                    if delay_info.get("samples_count", 0) > 0:
                        avg_lag = delay_info.get("avg_lag_seconds", 0)
                        if avg_lag > 0:
                            print(f"[DELAY STATÍSTICAS] Lag médio: {avg_lag:.2f}s, Amostra #{delay_info['samples_count']}")
                
                except Exception as e:
                    print(f"[ERRO MONITORAMENTO] {e}")
        
        thread = threading.Thread(target=monitor_transmission_bet, daemon=True)
        thread.start()
        print("[INFO] Thread de monitoramento transmissão/bet iniciada.")
    
    def run_wake_word_mode(self):
        """Modo com wake word"""
        self.voice.speak("Jarvis online. Aguardando comando.")
        
        while True:
            try:
                print("[WAKE] Aguardando 'Jarvis'...")

                trigger_type, heard_text = self.wake_detector.listen_for_trigger_or_direct_command()

                if trigger_type == "wake":
                    self.voice.speak("Sim, senhor.")
                    time.sleep(0.25)
                    
                    command = self.wake_detector.listen_command()
                    
                    if command:
                        print(f"[COMANDO] {command}")
                        
                        if "desligar jarvis" in command.lower():
                            self.voice.speak("Encerrando.")
                            break
                        
                        self.execute_command(command)
                    else:
                        self.voice.speak("Não compreendi.")

                elif trigger_type == "direct" and heard_text:
                    print(f"[COMANDO DIRETO] {heard_text}")
                    command = self.wake_detector.listen_command()
                    if command:
                        self.execute_command(command)
                    else:
                        self.execute_command(heard_text)
            
            except KeyboardInterrupt:
                self.voice.speak("Assistente encerrado.")
                break
    
    def run_text_mode(self):
        """Modo texto"""
        self.voice.speak("Assistente web online.")
        
        print("\n[COMANDOS]")
        print("- iniciar / parar")
        print("- status / lucro")
        print("- abra painel / abra bet365")
        print("- sair\n")
        
        while True:
            try:
                command = input("> ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['sair', 'exit']:
                    self.voice.speak("Encerrando.")
                    break
                
                self.execute_command(command)
            
            except KeyboardInterrupt:
                break
    
    def run(self):
        """Inicia assistente"""
        # Inicia thread de monitoramento de transmissão/bet
        self._start_monitoring_thread()
        
        if not self.wake_detector or not self.wake_detector.model:
            print("[INFO] Modo texto (wake word não disponível)")
            self.run_text_mode()
            return

        if self.use_wake_word:
            self.run_wake_word_mode()
            return

        # Modo direto: não exige falar "Jarvis"
        self.voice.speak("Assistente online. Fale o comando.")
        while True:
            try:
                trigger_type, heard_text = self.wake_detector.listen_for_trigger_or_direct_command()
                if trigger_type in ["direct", "wake"]:
                    print(f"[COMANDO] {heard_text}")
                    command = self.wake_detector.listen_command()
                    if command:
                        self.execute_command(command)
                    else:
                        self.execute_command(heard_text)
            except KeyboardInterrupt:
                self.voice.speak("Assistente encerrado.")
                break


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║         JARVIS - Assistente com Wake Word Offline          ║
║           (Sem PyAudio - Sem compilação C++)               ║
╚════════════════════════════════════════════════════════════╝

[TECNOLOGIA]
- sounddevice (áudio sem compilação)
- vosk (reconhecimento offline PT-BR)
- pyttsx3 (voz resposta)

""")
    
    try:
        # Tenta modo wake word, fallback para texto
        assistant = JarvisAssistant(use_wake_word=False)
        assistant.run()
    except Exception as e:
        print(f"\n[ERRO] {e}")
        print("\nUsando modo texto simplificado...")
        time.sleep(2)
        assistant = JarvisAssistant(use_wake_word=False)
        assistant.run()
