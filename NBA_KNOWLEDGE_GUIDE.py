#!/usr/bin/env python3
"""
GUIA: Como Alimentar e Usar a Base de Conhecimento NBA

A IA agora tem capacidade de armazenar e usar informações sobre NBA!
Aqui está como usar:

=== 1. VERIFICAR STATUS DA BASE ===

GET /api/nba-knowledge

Retorna:
- Quantos times estão armazenados
- Quantos jogadores
- Quantos padrões descobertos
- Notícias e lesões recentes

Exemplo:
curl "http://localhost:8000/api/nba-knowledge"

Resposta:
{
  "status": "ok",
  "stats": {
    "teams_stored": 30,
    "players_stored": 150,
    "patterns_discovered": 15,
    "news_items": 45
  },
  "relevant_patterns": [...],
  "injury_updates": [...],
  "betting_news": [...]
}


=== 2. POPULAR BASE COM TIMES ===

POST /api/nba-knowledge/populate
{
  "prompt": "teams"
}

Isso vai:
1. Usar Gemini para buscar info de todos os 30 times NBA
2. Armazenar: nome, conferência, divisão, estádio, jogadores-chave
3. Adicionar notas históricas sobre cada time

Resposta:
{
  "status": "ok",
  "category": "teams",
  "stored_count": 30,
  "message": "✅ 30 registros de 'teams' armazenados!"
}


=== 3. POPULAR BASE COM JOGADORES ===

POST /api/nba-knowledge/populate
{
  "prompt": "players"
}

Armazena:
- Top 50 jogadores atuais
- PPG (pontos por jogo)
- Rebounds, Assists
- Status de lesão
- Jersey number, altura, peso


=== 4. DESCOBRIR PADRÕES DE JOGO ===

POST /api/nba-knowledge/populate
{
  "prompt": "patterns"
}

Armazena padrões que afetam apostas:
- B2B (back-to-back) performance
- Home vs Away records
- Conference play patterns
- Novo técnico efeito
- Rest advantage
- Tempo de season (início vs final)


=== 5. OBTER NOTÍCIAS E LESÕES ===

POST /api/nba-knowledge/populate
{
  "prompt": "news"
}

Armazena:
- Lesões de jogadores-chave (CRÍTICO para apostas!)
- Trades e Free Agency
- Mudanças no coaching
- Dinâmicas de time mudando


=== 6. ESTATÍSTICAS DE TIMES ===

POST /api/nba-knowledge/populate
{
  "prompt": "stats"
}

Armazena:
- PPG (Pontos por Jogo)
- PPF (Pontos Permitidos)
- Rebounding strength
- Assists, Turnover rate
- Defensive/Offensive rating


=== COMO A IA USA ESSA INFORMAÇÃO ===

Quando você faz uma aposta, a IA:

1. LÊ o contexto NBA armazenado
2. VÊ estatísticas dos times envolvidos
3. CHECA lesões críticas
4. RECONHECE padrões históricos que aplicam
5. INJETA tudo isso no prompt para Gemini

Exemplo de contexto injetado no Gemini:
---
=== CONTEXTO NBA ===

🏀 Los Angeles Lakers:
  Divisão: Pacific
  Jogadores-chave: LeBron James, Anthony Davis
  Stats: 35W-15L | PPG: 112.4 | PPF: 105.2

🏀 Boston Celtics:
  Divisão: Atlantic
  Jogadores-chave: Jayson Tatum, Derrick White
  Stats: 38W-12L | PPG: 115.8 | PPF: 103.1

📊 Padrões Relevantes:
  B2B Performance: Boston defende bem em noite anterior (>70%)
  Home vs Away: Lakers ganham 60% em casa vs 45% away
  ...

⚠️ Lesões Críticas:
  [Lakers] Derrick Jones Jr em dúvida (tornozelo)
  [Celtics] Holiday descansando propositalmente antes do playoff
---

Com essas informações, Gemini toma decisões MUITO melhores!


=== EXEMPLO PRÁTICO ===

1. Primeira vez que inicia sistema:

POST /api/nba-knowledge/populate {"prompt": "teams"}
POST /api/nba-knowledge/populate {"prompt": "players"}
POST /api/nba-knowledge/populate {"prompt": "patterns"}
POST /api/nba-knowledge/populate {"prompt": "stats"}

2. Diariamente (ou quando tiver notícia importante):

POST /api/nba-knowledge/populate {"prompt": "news"}

3. Verificar se tudo está funcionando:

GET /api/nba-knowledge

4. Fazer apostas - a IA vai considerar tudo isso!


=== DICAS IMPORTANTES ===

✅ FAÇA:
- Popular a base regularmente (pelo menos 1x/semana)
- Atualizar notícias diariamente
- Guardar histórico de padrões para aprender

❌ NÃO FAÇA:
- Confiar em padrão descoberto há 3 meses sem revisar
- Ignorar lesões críticas mesmo que equipe vença normalmente
- Aplicar padrão de time A em time B que não o segue


=== INTEGRAÇÃO COM FEEDBACK LOOP ===

A IA aprende DUPLO:
1. De seus próprios sucessos (feedback loop)
2. Do conhecimento NBA acumulado

Bet WON + Lakers em padrão B2B específico
→ IA aprende: "Lakers em B2B > 70% confiança"

Next game com padrão similar:
→ Bias a favor de Lakers (ajusta odds mentalmente)


=== FUTUROS MELHORAMENTOS ===

Em seguida podemos:
- Análise em tempo real de props (jogador props)
- Integração com live odds
- Detectar value bets automaticamente
- Rastreamento de trends intra-season
- Modelagem de pós-trade performance

Mas por agora: o fundamento está pronto! 🚀
"""

# Este arquivo é apenas documentação - execute as chamadas API via curl/insomnia/postman
