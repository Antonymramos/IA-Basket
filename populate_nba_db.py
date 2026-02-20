#!/usr/bin/env python3
"""
Script para popular completamente a base de conhecimento NBA.
Executa uma vez para carregar todos os dados necessários.

Uso: python populate_nba_db.py
"""

import requests
import json
import time
from pathlib import Path

# URL da API (ajuste se necessário)
API_URL = "http://localhost:8000"
ENDPOINTS = {
    "status": f"{API_URL}/api/nba-knowledge",
    "populate": f"{API_URL}/api/nba-knowledge/populate",
}

CATEGORIES_ORDER = [
    ("teams", "Times NBA (30 equipes)"),
    ("stats", "Estatísticas de Times"),
    ("players", "Jogadores (Top 50)"),
    ("patterns", "Padrões de Jogo"),
    ("news", "Notícias e Lesões"),
]


def check_api_status():
    """Verifica se API está rodando."""
    try:
        response = requests.get(f"{API_URL}/api/status", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ API não está respondendo: {e}")
        return False


def get_nba_knowledge_status():
    """Retorna status atual da base."""
    try:
        response = requests.get(ENDPOINTS["status"], timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Erro ao verificar status: {e}")
        return None


def populate_category(category: str) -> bool:
    """Popula uma categoria de dados."""
    print(f"\n📥 Populando {category}...", end=" ")
    
    try:
        payload = {"prompt": category, "objective": category}
        response = requests.post(
            ENDPOINTS["populate"],
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            stored = result.get("stored_count", 0)
            print(f"✅ {stored} registros armazenados!")
            return True
        else:
            print(f"❌ Erro {response.status_code}")
            print(response.text[:200])
            return False
    except requests.Timeout:
        print("❌ Timeout (Gemini demorou muito, tente novamente)")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("🏀 POPULADOR DE BASE NBA - IA Basket")
    print("=" * 60)
    
    # 1. Verificar API
    print("\n1️⃣  Verificando API...")
    if not check_api_status():
        print("\n❌ ERRO: API não está rodando!")
        print("   Execute em outro terminal: python -m uvicorn backend.main:app --reload")
        return
    print("✅ API está online!")
    
    # 2. Verificar status atual
    print("\n2️⃣  Status atual da base:")
    status = get_nba_knowledge_status()
    if status:
        stats = status.get("stats", {})
        print(f"   Teams: {stats.get('teams_stored', 0)}/30")
        print(f"   Players: {stats.get('players_stored', 0)} armazenados")
        print(f"   Patterns: {stats.get('patterns_discovered', 0)} descobertos")
        print(f"   News: {stats.get('news_items', 0)} notícias")
    
    # 3. Populate
    print("\n3️⃣  Populando base de conhecimento NBA...")
    print("    (Cada etapa pode levar 10-30 segundos)")
    
    success_count = 0
    for category, description in CATEGORIES_ORDER:
        print(f"\n   📊 {description}")
        if populate_category(category):
            success_count += 1
            time.sleep(2)  # Pequeno delay entre requisições
        else:
            print(f"      ⚠️  Pulando {category}...")
    
    # 4. Resultado final
    print("\n" + "=" * 60)
    print(f"✅ População completa: {success_count}/{len(CATEGORIES_ORDER)} categorias")
    
    # 5. Status final
    print("\n4️⃣  Status final da base:")
    status = get_nba_knowledge_status()
    if status:
        stats = status.get("stats", {})
        print(f"   ✅ Teams: {stats.get('teams_stored', 0)}/30")
        print(f"   ✅ Players: {stats.get('players_stored', 0)}")
        print(f"   ✅ Patterns: {stats.get('patterns_discovered', 0)}")
        print(f"   ✅ News: {stats.get('news_items', 0)}")
        
        # Mostrar exemplos
        if status.get("relevant_patterns"):
            print("\n   📊 Padrões Descobertos:")
            for pattern in status["relevant_patterns"][:3]:
                print(f"      {pattern}")
        
        if status.get("injury_updates"):
            print("\n   ⚠️  Lesões Críticas:")
            for injury in status["injury_updates"][:2]:
                print(f"      {injury}")
    
    print("\n" + "=" * 60)
    print("🎉 Base de conhecimento NBA pronta para usar!")
    print("   A IA agora tem contexto completo para tomar melhores decisões!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
