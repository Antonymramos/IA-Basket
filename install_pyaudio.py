#!/usr/bin/env python3
"""
Instalador automático de PyAudio para Windows
Detecta versão do Python e baixa wheel pré-compilado
"""

import sys
import subprocess
import urllib.request
import os
import platform

def get_python_version():
    """Retorna versão do Python no formato cpXXX"""
    major = sys.version_info.major
    minor = sys.version_info.minor
    return f"cp{major}{minor}"

def get_platform():
    """Retorna plataforma (32 ou 64 bits)"""
    is_64bits = sys.maxsize > 2**32
    return "win_amd64" if is_64bits else "win32"

def download_pyaudio():
    """Baixa PyAudio wheel apropriado"""
    py_version = get_python_version()
    platform_str = get_platform()
    
    print(f"[INFO] Python: {sys.version}")
    print(f"[INFO] Versão detectada: {py_version}")
    print(f"[INFO] Plataforma: {platform_str}")
    print()
    
    # URLs de repositórios com PyAudio pré-compilado
    urls = [
        # Repositório principal (Gohlke - UCI)
        f"https://download.lfd.uci.edu/pythonlibs/archived/PyAudio-0.2.14-{py_version}-{py_version}-{platform_str}.whl",
        # Repositório alternativo
        f"https://github.com/intxcc/pyaudio_portaudio/releases/download/v0.2.14/PyAudio-0.2.14-{py_version}-{py_version}-{platform_str}.whl",
    ]
    
    wheel_filename = f"PyAudio-0.2.14-{py_version}-{py_version}-{platform_str}.whl"
    
    print(f"[1/3] Tentando baixar: {wheel_filename}")
    print()
    
    for url in urls:
        try:
            print(f"Tentando URL: {url}")
            urllib.request.urlretrieve(url, wheel_filename)
            print(f"✅ Download concluído: {wheel_filename}")
            return wheel_filename
        except Exception as e:
            print(f"❌ Falhou: {e}")
            continue
    
    return None

def install_wheel(wheel_path):
    """Instala wheel do PyAudio"""
    print()
    print(f"[2/3] Instalando {wheel_path}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", wheel_path])
        print("✅ PyAudio instalado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao instalar: {e}")
        return False

def cleanup(wheel_path):
    """Remove arquivo wheel temporário"""
    try:
        if os.path.exists(wheel_path):
            os.remove(wheel_path)
            print(f"[3/3] Arquivo temporário removido: {wheel_path}")
    except Exception:
        pass

def manual_instructions():
    """Mostra instruções manuais caso automático falhe"""
    py_version = get_python_version()
    platform_str = get_platform()
    
    print()
    print("=" * 70)
    print("❌ INSTALAÇÃO AUTOMÁTICA FALHOU")
    print("=" * 70)
    print()
    print("OPÇÃO 1: Baixar manualmente")
    print("-" * 70)
    print("1. Acesse: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
    print(f"2. Procure e baixe: PyAudio-0.2.14-{py_version}-{py_version}-{platform_str}.whl")
    print("3. Execute: pip install caminho\\para\\arquivo.whl")
    print()
    print("OPÇÃO 2: Usar repositório GitHub")
    print("-" * 70)
    print("1. Acesse: https://github.com/intxcc/pyaudio_portaudio/releases")
    print("2. Baixe versão compatível")
    print("3. Execute: pip install arquivo.whl")
    print()
    print("OPÇÃO 3: Usar assistente SEM microfone")
    print("-" * 70)
    print("Execute: python jarvis_assistant_web.py")
    print("(Comandos via texto, respostas via voz)")
    print()
    print("=" * 70)

def test_pyaudio():
    """Testa se PyAudio foi instalado corretamente"""
    print()
    print("[TESTE] Verificando instalação do PyAudio...")
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        print(f"✅ PyAudio funcionando! Versão: {pyaudio.__version__}")
        print(f"✅ Dispositivos de áudio detectados: {p.get_device_count()}")
        p.terminate()
        return True
    except ImportError:
        print("❌ PyAudio não está instalado")
        return False
    except Exception as e:
        print(f"⚠️ PyAudio instalado mas com erro: {e}")
        return False

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║        Instalador Automático de PyAudio (Windows)          ║
╚════════════════════════════════════════════════════════════╝
""")
    
    # Verifica se já está instalado
    if test_pyaudio():
        print()
        print("✅ PyAudio já está instalado e funcionando!")
        print("Execute agora: python jarvis_assistant.py")
        sys.exit(0)
    
    # Tenta download automático
    wheel_path = download_pyaudio()
    
    if wheel_path:
        # Tenta instalar
        if install_wheel(wheel_path):
            cleanup(wheel_path)
            test_pyaudio()
            print()
            print("=" * 70)
            print("✅ INSTALAÇÃO CONCLUÍDA!")
            print("=" * 70)
            print()
            print("Próximo passo: python jarvis_assistant.py")
            print()
        else:
            cleanup(wheel_path)
            manual_instructions()
    else:
        manual_instructions()
