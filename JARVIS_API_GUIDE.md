# Jarvis Knowledge Engine - API Guide

## Overview

The **Jarvis Knowledge Engine** is a unified intelligence aggregation system that synthesizes information from multiple sources:
- **Personal Betting Performance** (from feedback loop)
- **Market Activity Analysis** (from analytics events)
- **NBA Intelligence** (teams, players, lesions, patterns)
- **Brazilian Cultural Context** (gírias, regionalismos, temporal patterns)

This creates a complete briefing for decision-making and autonomous advisory.

---

## 3 New API Endpoints

### 1. **GET /api/jarvis/briefing**
Returns a human-readable formatted briefing of all system intelligence.

**Parameters:**
- `minutes` (optional, default=120): Time window in minutes to analyze

**Example:**
```bash
curl -X GET "http://localhost:8000/api/jarvis/briefing?minutes=120"
```

**Response:**
```json
{
  "status": "ok",
  "brief_type": "formatted_text",
  "briefing": "🎯 JARVIS BRIEFING\n=================\n\n📊 MARKET ANALYSIS\n─────────────────\nDetected: 45 signals\nExecuted: 38 bets (84.4%)\nBlocked: 7 (15.6%)\n\n🏀 PERSONAL PERFORMANCE\n───────────────────────\nTotal Wins: 28/38 (73.7%)\nEV Profit: +$245.80\nAvg Confidence: 78%\n\n🏆 NBA INTELLIGENCE\n───────────────────\nInjury Alert: LeBron James (LAL) - Recovery week\nKey Pattern: Lakers 73% win @ home vs East\nTrending: Strong consensus on Celtics tomorrow\n\n⚠️ RISK ASSESSMENT\n──────────────────\nSafe Mode Events: 2 (last 2h)\nBlock Rate: 15.6% (normal)\nLast Error: 3.5h ago\n\n🎲 PATTERN RECOGNITION\n──────────────────────\nBest Hour: 19:00-21:00 (local)\nBest Game Type: 2pt spreads\nSuccess Rate (Weak Consensus): 65%\n\n💡 RECOMMENDATIONS\n──────────────────\n1. Wait for evening games (19:00+) - higher edge\n2. Focus on strong consensus signals (>75%)\n3. Monitor LeBron status updates - affects LAL odds\n4. 2pt spreads showing better EV today",
  "generated_at": "2025-01-15T14:23:45.123456"
}
```

---

### 2. **GET /api/jarvis/intelligence**
Returns the complete intelligence in structured JSON format.

**Parameters:**
- `minutes` (optional, default=120): Time window in minutes to analyze

**Example:**
```bash
curl -X GET "http://localhost:8000/api/jarvis/intelligence?minutes=120"
```

**Response:**
```json
{
  "status": "ok",
  "intelligence": {
    "market_analysis": {
      "detected_signals": 45,
      "executed_bets": 38,
      "execution_rate": 0.844,
      "blocked_signals": 7,
      "block_rate": 0.156
    },
    "personal_performance": {
      "total_bets": 38,
      "wins": 28,
      "losses": 10,
      "win_rate": 0.737,
      "ev_profit": 245.80,
      "avg_confidence": 0.78
    },
    "nba_context": {
      "injury_alerts": [
        {
          "player": "LeBron James",
          "team": "LAL",
          "status": "Recovery week",
          "impact": "high"
        }
      ],
      "relevant_patterns": [
        {
          "pattern": "Lakers 73% win @ home vs East",
          "reliability": 0.85,
          "betting_edge": "Favor LAL spreads"
        }
      ],
      "news_highlights": ["Strong consensus on Celtics tomorrow"]
    },
    "risk_assessment": {
      "safe_mode_events_2h": 2,
      "block_rate": 0.156,
      "last_error_minutes_ago": 210,
      "risk_level": "normal"
    },
    "pattern_recognition": {
      "best_hour": "19:00-21:00",
      "best_game_type": "2pt spreads",
      "weak_consensus_success_rate": 0.65
    },
    "recommendations": [
      "Wait for evening games (19:00+) - higher edge",
      "Focus on strong consensus signals (>75%)",
      "Monitor LeBron status updates",
      "2pt spreads showing better EV today"
    ]
  },
  "generated_at": "2025-01-15T14:23:45.123456"
}
```

---

### 3. **POST /api/jarvis/suggest-bet**
Provides a detailed betting suggestion based on complete system intelligence.

**Request Body:**
```json
{
  "team_a": "Lakers",
  "team_b": "Celtics"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/jarvis/suggest-bet" \
  -H "Content-Type: application/json" \
  -d '{"team_a": "Lakers", "team_b": "Celtics"}'
```

**Response:**
```json
{
  "status": "ok",
  "suggestion": {
    "matchup": "Lakers vs Celtics",
    "personal_stats": {
      "vs_lakers_record": "6 wins, 2 losses (75% win rate)",
      "vs_celtics_record": "4 wins, 1 loss (80% win rate)",
      "avg_ev_vs_lakers": 2.45,
      "avg_ev_vs_celtics": 2.78
    },
    "nba_context": {
      "lakers_status": "LeBron James in recovery week - affects team execution",
      "celtics_status": "Full roster healthy",
      "historical_matchup": "66% Celtics win when both healthy",
      "home_advantage": "If at Celtics TD: +3-5 pt advantage"
    },
    "risk_assessment": {
      "current_risk_level": "medium",
      "consecutive_losses": "None recently",
      "safe_mode_warnings": 0,
      "confidence_factors": ["Strong recent win streak", "Good historical record vs both"]
    },
    "recommendation": {
      "preferred_bet": "Celtics straight (due to LeBron absence + home advantage)",
      "confidence": "78%",
      "suggested_stake": "Standard (normal EV found)",
      "edge_reason": "Celtics healthy roster + LeBron recovery = +value",
      "risk_mitigation": "Monitor LeBron status until tip-off"
    }
  },
  "generated_at": "2025-01-15T14:23:45.123456"
}
```

---

## Integration Points

### 1. **Backend (main.py)**
All 3 endpoints are now available in FastAPI, starting at line ~1152.

### 2. **Frontend (app.js)**
New React states and fetch functions:
- `jarvisBriefing`: Stores briefing response
- `jarvisIntel`: Stores intelligence response
- `fetchJarvisBriefing()`: Fetches briefing (refreshes every 2s)
- `fetchJarvisIntelligence()`: Fetches intelligence (refreshes every 2s)

A new **"🧠 Jarvis Briefing"** card is displayed in the dashboard showing the formatted briefing.

### 3. **Core Engine (core/jarvis_knowledge_engine.py)**
The `JarvisKnowledgeEngine` class aggregates:
- `FeedbackLoop` (bet accuracy, success examples)
- `NBAKnowledge` (teams, players, lesions, patterns)
- `BrazilianContext` (gírias, temporal patterns)
- `AnalyticsContext` (market events: detected, executed, blocked)

---

## Data Flow

```
┌─────────────────────────────────────────────────────────┐
│         INTERNAL DATA SOURCES                          │
├─────────────────────────────────────────────────────────┤
│ • analytics.db      (Market: detected, executed, blocked) │
│ • feedback_loop.db  (Performance: wins, losses, EV)      │
│ • nba_knowledge.db  (Teams, players, lesions, patterns)  │
│ • brazilian_context (Gírias, peak hours, seasonality)   │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│    JARVIS KNOWLEDGE ENGINE                              │
│    (core/jarvis_knowledge_engine.py)                     │
├─────────────────────────────────────────────────────────┤
│ • Analyzes market (4 metrics)                           │
│ • Pulls personal performance (6 metrics)                │
│ • Aggregates NBA context (3 modules)                    │
│ • Assesses risk (4 metrics)                             │
│ • Recognizes patterns (3 temporal/type)                 │
│ • Generates recommendations (4-6 items)                 │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│         API ENDPOINTS (main.py)                         │
├─────────────────────────────────────────────────────────┤
│ • GET  /api/jarvis/briefing         (formatted text)    │
│ • GET  /api/jarvis/intelligence     (full JSON)         │
│ • POST /api/jarvis/suggest-bet      (context for pair)  │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│         FRONTENDS                                       │
├─────────────────────────────────────────────────────────┤
│ • Web Dashboard (app.js - briefing card)                │
│ • Autonomous Voice Assistant (jarvis_assistant_offline) │
│ • External Integrations (betting apps, chat bots)       │
└─────────────────────────────────────────────────────────┘
```

---

## Usage Examples

### Example 1: Get Daily Briefing
```python
import requests

response = requests.get("http://localhost:8000/api/jarvis/briefing?minutes=1440")
briefing = response.json()['briefing']
print(briefing)
# Output: Formatted briefing text with all metrics
```

### Example 2: Get Intelligence for Decision
```python
response = requests.get("http://localhost:8000/api/jarvis/intelligence?minutes=120")
intel = response.json()['intelligence']

if intel['risk_assessment']['risk_level'] == 'low':
    print(f"Safe time to bet: Win rate = {intel['personal_performance']['win_rate']*100}%")
```

### Example 3: Suggest Bet Before Placing
```python
response = requests.post(
    "http://localhost:8000/api/jarvis/suggest-bet",
    json={"team_a": "Lakers", "team_b": "Nets"}
)
suggestion = response.json()['suggestion']
print(f"Recommendation: {suggestion['recommendation']['preferred_bet']}")
print(f"Confidence: {suggestion['recommendation']['confidence']}")
```

---

## Autonomous Integration (Future)

### Jarvis Assistant Offline
The `jarvis_assistant_offline.py` can be updated to:
1. Call `GET /api/jarvis/briefing` every 30 minutes
2. Detect high-confidence opportunities
3. Auto-narrate recommendations via voice TTS
4. Monitor real-time NBA updates

### Real-Time Monitoring
Implement scheduled tasks:
- **Hourly**: Fetch fresh NBA data via Gemini
- **Every 5 min**: Check for high-confidence signals
- **On event**: Alert via email/SMS if recommended bet appears

---

## Database Tables Used

### analytics.db
- **events** table: Records all signals (DETECTADO, APOSTOU, BLOQUEADO, ENSEMBLE_CONSENSUS, SAFE_MODE_*)

### feedback_loop.db
- **bet_results** table: 
  - signal_id, tipo_pontuacao, stake, ev_score, consensus_strength
  - result_status (WON, LOST, EXPIRED, ERROR)
  - timestamp

### nba_knowledge.db
- **nba_teams**: team_name, city, conference, division, key_players
- **nba_team_stats**: team, ppg, apg, rpg, fg_percent, ...
- **nba_players**: player_name, team, position, ppg, rpg, apg, injury_status
- **nba_patterns**: pattern_name, relevant_teams, impact_on_scoring, betting_edge
- **nba_news**: date, team, headline, injury_update, relevant_to_betting

---

## Performance Notes

- **Briefing generation**: ~200-500ms (SQLite queries + aggregation)
- **Intelligence JSON**: ~300-800ms (full data fetch + structure)
- **Bet suggestion**: ~400-1s (personalized analysis + context matching)
- **Frontend refresh**: Every 2 seconds (batched API calls)

For better performance with high-frequency updates, consider:
1. Caching briefing for 30s between updates
2. Running aggregation on background thread
3. Using Redis for hot metrics (market_analysis)

---

## Test the Endpoints

```bash
# Quick test all endpoints
curl -X GET "http://localhost:8000/api/jarvis/briefing"
curl -X GET "http://localhost:8000/api/jarvis/intelligence"
curl -X POST "http://localhost:8000/api/jarvis/suggest-bet" \
  -H "Content-Type: application/json" \
  -d '{"team_a": "Lakers", "team_b": "Celtics"}'
```

---

**Created**: Phase 6 - Jarvis Knowledge Engine Integration  
**Status**: ✅ API endpoints complete, frontend integrated, ready for autonomous advisory
