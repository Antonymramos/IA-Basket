#!/usr/bin/env python3
"""Quick test script for Oracle NBA API."""

import json
import sys
import time

import requests

BASE_URL = "http://127.0.0.1:8001"


def test_status():
    try:
        resp = requests.get(f"{BASE_URL}/api/status", timeout=5)
        resp.raise_for_status()
        print("✅ /api/status")
        print(json.dumps(resp.json(), indent=2))
        return True
    except Exception as e:
        print(f"❌ /api/status: {e}")
        return False


def test_analyze():
    try:
        payload = {
            "video_live": {"placar": "93-85", "tempo": "Q1 05:03"},
            "bet365": {
                "placar_geral": "91-85",
                "tempo_bet": "Q1 05:03",
                "linhas": ["Q05:03 R$L Mag 2pts 1.40 ✓REGISTROU"],
            },
            "system": {"status_stream": "OK"},
        }
        resp = requests.post(
            f"{BASE_URL}/api/oracle/analyze", json=payload, timeout=10
        )
        resp.raise_for_status()
        print("\n✅ /api/oracle/analyze")
        data = resp.json()
        print(f"  Erro detectado: {data['diagnostico_saas']['erro_detectado']}")
        print(f"  Tipo: {data['diagnostico_saas']['tipo']}")
        print(f"  Severidade: {data['diagnostico_saas']['severidade']}")
        return True
    except Exception as e:
        print(f"❌ /api/oracle/analyze: {e}")
        return False


def test_latest():
    try:
        resp = requests.get(f"{BASE_URL}/api/oracle/latest", timeout=5)
        resp.raise_for_status()
        print("\n✅ /api/oracle/latest")
        data = resp.json()
        if data.get("latest"):
            print(f"  Com dados: {data['latest']['diagnostico_saas']['tipo']}")
        else:
            print("  (Vazio - nenhuma ingestão ainda)")
        return True
    except Exception as e:
        print(f"❌ /api/oracle/latest: {e}")
        return False


def test_debug_routes():
    try:
        resp = requests.get(f"{BASE_URL}/api/debug/routes", timeout=5)
        resp.raise_for_status()
        print("\n✅ /api/debug/routes")
        data = resp.json()
        routes = data.get("routes", [])
        print(f"  Total de rotas: {len(routes)}")
        for r in routes:
            if r.get("path", "").startswith("/api/oracle"):
                print(f"    - {r['path']}")
        return True
    except Exception as e:
        print(f"❌ /api/debug/routes: {e}")
        return False


def main():
    print(f"Testando Oracle NBA API em {BASE_URL}\n")
    print("Ps: Certifique que o servidor está rodando:\n")
    print("  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001\n")

    results = [
        test_status(),
        test_analyze(),
        test_latest(),
        test_debug_routes(),
    ]

    print()
    if all(results):
        print("✅ Todos os testes passaram!")
        return 0
    else:
        print(f"❌ {sum(not r for r in results)} teste(s) falharam")
        return 1


if __name__ == "__main__":
    sys.exit(main())
