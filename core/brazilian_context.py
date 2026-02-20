#!/usr/bin/env python3
"""
Contexto Cultural Brasileiro para enriquecer análise de apostas.
Injeta gírias, regionalismos e padrões de comportamento brasileiro na IA.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

# Dicionário de GÍRIAS e EXPRESSÕES muito brasileiras pro Gemini entender melhor
GIRIAS_APOSTA = {
    "tá ligado": "você está atento, percebeu o padrão",
    "já era": "a oportunidade passou, perdeu a chance",
    "se tá complicado": "as coisas estão difíceis, o risco aumentou",
    "tá inchadão": "o mercado está inflado, não confio",
    "bora": "vamos, hora de agir rápido",
    "sacanagem": "foi um erro óbvio, devia ter visto",
    "tá fogo": "situação está quente, tá tudo acontecendo agora",
    "tá caro": "o preço/risco não vale",
    "grana": "dinheiro em risco",
    "fica esperto": "preste atenção, isso é importante",
    "bolado": "frustrado, viu uma oportunidade ruim",
    "tá maneiro": "está bom, está funcionando",
    "que cilada": "armadilha óbvia, não caia",
    "tá quente demais": "o risco está muito alto",
    "na lata": "na prática, no real",
    "de primeira": "de cara, óbvio",
    "se vira": "acha uma solução criativa",
}

# Regionalismos por REGIÃO do BRASIL
REGIONALISMOS = {
    "nordeste": {
        "tá véio": "está bom, está ok",
        "tá desafiador": "está difícil",
        "ânimo": "vamos, bora",
        "ó a oportunidade, ó!": "aí vem a chance que esperávamos",
    },
    "rio": {
        "tá cabuloso": "está arriscado demais",
        "que cilada": "que armadilha",
        "tá massa": "está bom",
        "tá malandro": "está espertinho, astuto",
    },
    "sao_paulo": {
        "tá ligado": "você viu",
        "coisa de louco": "risco absurdo",
        "não vem com frufru": "não complique, direto ao ponto",
        "se tá fogo": "a situação está crítica",
    },
    "sul": {
        "tá blá": "está chato, monótono",
        "tchê": "ó, ouve aí",
        "tá zika": "tá ruim",
        "bah": "puxa, caramba",
    },
}

# EVENTOS CULTURAIS que afetam comportamento de apostadores brasileiros
EVENTOS_CULTURAIS = {
    "carnaval": "fevereiro - apostadores menos focados, padrões erráticos",
    "copa": "junho/julho - todos apostam, picos de volume gigantescos",
    "black_friday": "novembro - promo pra grana em apostas, não confia em odds",
    "ano_novo": "dezembro/janeiro - momento d'ânimo, mais risco que o normal",
    "feriado_prolongado": "emocional, apostadores menos racionais",
}

# HORÁRIOS PICOS DE APOSTAS em Brasil (timezone BR)
HORARIOS_BRASIL = {
    "madrugada": (0, 6, "tá de insônia, apostador night"),
    "manhã": (6, 12, "acordou, checando as oportunidades"),
    "tarde": (12, 18, "horário TOP - todo mundo apostando"),
    "noite": (18, 24, "balada/futebol, foco nas apostas é menor"),
}


def get_girias_contextualizadas(transmission_data: str, bet_data: str) -> str:
    """
    Analisa contexto das apostas e retorna explicação em GÍRIAS brasileiras.
    Ajuda Gemini a entender melhor o "sotaque" do contexto.
    """
    linhas = []
    
    # Se scores estão muito afastados
    if "100" in str(transmission_data) or "105" in str(transmission_data):
        linhas.append("Placar tá inchadão demais pra confiar, tá ligado?")
    
    # Se bet está desatualizado
    if "delay" in str(bet_data).lower() or "lag" in str(bet_data).lower():
        linhas.append("Bet tá atrasada, já era a chance de ouro.")
    
    # Gap detectado
    if "2" in str(transmission_data) or "3" in str(transmission_data):
        linhas.append("Ó a oportunidade! Tá fogo agora, bora rápido!")
    
    return " | ".join(linhas) if linhas else "Tá normal por enquanto, fica esperto."


def get_contexto_temporal_brasileiro() -> str:
    """
    Retorna contexto cultural + horário em português brasileiro.
    Gemini entende melhor a vibe da aposta neste momento.
    """
    agora = datetime.now()
    hora = agora.hour
    dia_semana = {
        0: "segunda (foco máximo)",
        1: "terça (dia comum)",
        2: "quarta (rotina)",
        3: "quinta (quinta-feira)",
        4: "sexta (pita do fim de semana)",
        5: "sábado (caótico, todo mundo apostando)",
        6: "domingo (futebol BR, volume gigante)",
    }.get(agora.weekday(), "semana")
    
    # Identifica período do dia
    periodo_info = ""
    for periodo, (inicio, fim, descricao) in HORARIOS_BRASIL.items():
        if inicio <= hora < fim:
            periodo_info = f"{periodo.upper()} ({descricao})"
            break
    
    # Detecta se é evento cultural importante
    mes = agora.month
    evento_descricao = ""
    if mes == 2:
        evento_descricao = " [CARNAVAL próximo - apostadores loucos]"
    elif mes in (6, 7):
        evento_descricao = " [COPA - volume absurdo de apostas]"
    elif mes == 11:
        evento_descricao = " [BLACK FRIDAY - ofertas falsas]"
    
    return f"""
    === CONTEXTO CULTURAL BRASIL ===
    Agora é {dia_semana}
    Horário: {periodo_info}
    Momento: {agora.strftime('%H:%M:%S')}{evento_descricao}
    
    Dica cultural: Neste momento, o padrão de apostador brasileiro é {
        "ir dormir, tá com sono" if hora < 6
        else "checando as oportunidades, tá acordado" if hora < 12
        else "tá apostando de verdade, volume máximo" if hora < 18
        else "mais relaxado, futebol na TV"
    }
    """


def get_explicacao_girias() -> str:
    """
    Retorna um resumo das GÍRIAS mais importantes pro Gemini aprender.
    Isso ajuda ele a entender melhor o jeito brasileiro de falar sobre apostas.
    """
    linhas = ["=== GÍRIAS BRASILEIRAS PRAS APOSTAS ==="]
    
    for giria, significado in list(GIRIAS_APOSTA.items())[:8]:  # Top 8
        linhas.append(f"• '{giria}' = {significado}")
    
    linhas.append("")
    linhas.append("=== EVENTOS CULTURAIS QUE MEXEM COM APOSTADOR ===")
    for evento, descricao in list(EVENTOS_CULTURAIS.items())[:5]:
        linhas.append(f"• {evento.replace('_', ' ').upper()}: {descricao}")
    
    return "\n".join(linhas)


async def enrich_analysis_with_gemini(
    gemini_brain,
    transmission_data: str,
    bet_data: str,
) -> str:
    """
    Usa GEMINI para gerar análise em "sotaque brasileiro".
    Retorna prompt enriquecido com insights culturais brasileiros.
    """
    girias_relevantes = get_girias_contextualizadas(transmission_data, bet_data)
    contexto_temporal = get_contexto_temporal_brasileiro()
    explicacao = get_explicacao_girias()
    
    prompt_enriquecimento = f"""
    Você é um apostador EXPERIENTE dos trópicos, tá ligado? 
    
    Analise NESTA HORA:
    {girias_relevantes}
    
    {contexto_temporal}
    
    {explicacao}
    
    Baseado nisso, qual é o "feeling" brasileiro da situação agora?
    - Tá uma sacanagem (armadilha óbvia)?
    - Tá fogo (super urgente)?
    - Tá maneiro (pode confiar)?
    - Tá caro (não compensa)?
    
    Fale em português brasileiro real, com gírias mesmo!
    """
    
    # Se gemini_brain disponível, usa pra enriquecimento
    # Se não, retorna análise baseada em regras (fallback)
    try:
        if gemini_brain and hasattr(gemini_brain, 'models'):
            for model_name in gemini_brain.model_names[:1]:  # Só primeiro modelo (rápido)
                try:
                    response = gemini_brain.models[model_name].generate_content(
                        prompt_enriquecimento,
                        timeout=5
                    )
                    if response and response.text:
                        return f"[SOTAQUE BR] {response.text[:200]}"
                except Exception:
                    pass  # Fallback se gemini falhar
        
        # Fallback sem Gemini
        return f"""[SOTAQUE BR]
        {girias_relevantes}
        {contexto_temporal}
        """
    except Exception as e:
        return f"Erro no sotaque BR: {str(e)}"


def build_brazilian_prompt_section(transmission_data: str, bet_data: str) -> str:
    """
    Retorna seção pré-pronta para injetar no prompt do Gemini.
    Toda em português com gírias e jeito brasileiro.
    """
    return f"""
    === ANÁLISE COM SOTAQUE BRASILEIRO ===
    
    Tá ligado, aqui no Brasil a gente fala claro:
    
    {get_girias_contextualizadas(transmission_data, bet_data)}
    
    {get_contexto_temporal_brasileiro()}
    
    Lembre: Se tá muito complicado, tá uma sacanagem, ou tá demorando demais,
    a gente tira o pé do acelerador. Melhor perder 100 na segurança do que 
    arriscar a grana toda por uma chance pequena. É coisa de gente sábia.
    """
