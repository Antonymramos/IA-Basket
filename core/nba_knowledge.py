#!/usr/bin/env python3
"""
NBA Knowledge Base - Alimenta a IA com informações sobre NBA da internet.
Usa Gemini para buscar estatísticas, padrões, histórico e armazena no banco de dados.
"""

from __future__ import annotations

import sqlite3
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any


class NBAKnowledge:
    """Gerencia base de conhecimento sobre NBA armazenada em banco de dados."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection
    
    def _init_db(self) -> None:
        """Cria tabelas para armazenar conhecimento NBA."""
        with self._connect() as connection:
            # Tabela: Informações sobre times
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS nba_teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    team_name TEXT UNIQUE,
                    city TEXT,
                    conference TEXT,
                    division TEXT,
                    last_season_record TEXT,
                    home_court TEXT,
                    key_players TEXT,
                    historical_notes TEXT,
                    updated_at REAL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_nba_teams_name ON nba_teams(team_name)"
            )
            
            # Tabela: Estatísticas de times (PPF, PPG, etc)
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS nba_team_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    team_name TEXT NOT NULL,
                    season TEXT,
                    wins INTEGER,
                    losses INTEGER,
                    win_percentage REAL,
                    ppg REAL,
                    ppf REAL,
                    rebounding REAL,
                    ast_per_game REAL,
                    turnover_rate REAL,
                    defense_rating REAL,
                    offensive_rating REAL,
                    notes TEXT
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_nba_team_stats ON nba_team_stats(team_name, season)"
            )
            
            # Tabela: Padrões de jogo (trends)
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS nba_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    pattern_name TEXT,
                    description TEXT,
                    relevant_teams TEXT,
                    impact_on_scoring INTEGER,
                    betting_edge TEXT,
                    reliability_score REAL,
                    last_observed REAL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_nba_patterns_name ON nba_patterns(pattern_name)"
            )
            
            # Tabela: Informações sobre jogadores
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS nba_players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    player_name TEXT UNIQUE,
                    team TEXT,
                    position TEXT,
                    jersey_number INTEGER,
                    height TEXT,
                    weight INTEGER,
                    ppg REAL,
                    rpg REAL,
                    apg REAL,
                    injury_status TEXT,
                    season_stats TEXT,
                    career_highlights TEXT
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_nba_players_name ON nba_players(player_name)"
            )
            
            # Tabela: Notícias e eventos importantes
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS nba_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    date TEXT,
                    team TEXT,
                    headline TEXT,
                    impact TEXT,
                    relevant_to_betting BOOLEAN,
                    injury_update BOOLEAN
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_nba_news_date ON nba_news(date)"
            )
            
            connection.commit()
    
    def store_team_info(
        self,
        team_name: str,
        city: str,
        conference: str,
        division: str,
        last_season_record: str,
        home_court: str,
        key_players: str,
        historical_notes: str = "",
    ) -> None:
        """Armazena informações sobre um time NBA."""
        with self._connect() as connection:
            try:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO nba_teams 
                    (ts, team_name, city, conference, division, last_season_record, home_court, key_players, historical_notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        time.time(),
                        team_name,
                        city,
                        conference,
                        division,
                        last_season_record,
                        home_court,
                        key_players,
                        historical_notes,
                        time.time(),
                    ),
                )
                connection.commit()
            except Exception as e:
                print(f"Erro ao armazenar info do time {team_name}: {e}")
    
    def store_team_stats(
        self,
        team_name: str,
        season: str,
        wins: int,
        losses: int,
        ppg: float,
        ppf: float,
        rebounding: float,
        ast_per_game: float,
        turnover_rate: float = 0,
        defense_rating: float = 0,
        offensive_rating: float = 0,
    ) -> None:
        """Armazena estatísticas de um time."""
        with self._connect() as connection:
            win_pct = wins / (wins + losses) if (wins + losses) > 0 else 0
            connection.execute(
                """
                INSERT INTO nba_team_stats 
                (ts, team_name, season, wins, losses, win_percentage, ppg, ppf, rebounding, ast_per_game, turnover_rate, defense_rating, offensive_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    team_name,
                    season,
                    wins,
                    losses,
                    win_pct,
                    ppg,
                    ppf,
                    rebounding,
                    ast_per_game,
                    turnover_rate,
                    defense_rating,
                    offensive_rating,
                ),
            )
            connection.commit()
    
    def store_pattern(
        self,
        pattern_name: str,
        description: str,
        relevant_teams: str,
        impact_on_scoring: int,
        betting_edge: str,
        reliability_score: float = 0.5,
    ) -> None:
        """Armazena um padrão de jogo NBA descoberto."""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO nba_patterns
                (ts, pattern_name, description, relevant_teams, impact_on_scoring, betting_edge, reliability_score, last_observed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    pattern_name,
                    description,
                    relevant_teams,
                    impact_on_scoring,
                    betting_edge,
                    reliability_score,
                    time.time(),
                ),
            )
            connection.commit()
    
    def store_player_info(
        self,
        player_name: str,
        team: str,
        position: str,
        jersey_number: int,
        height: str,
        weight: int,
        ppg: float,
        rpg: float,
        apg: float,
        injury_status: str = "Saudável",
        season_stats: str = "",
        career_highlights: str = "",
    ) -> None:
        """Armazena informações sobre um jogador."""
        with self._connect() as connection:
            try:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO nba_players
                    (ts, player_name, team, position, jersey_number, height, weight, ppg, rpg, apg, injury_status, season_stats, career_highlights)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        time.time(),
                        player_name,
                        team,
                        position,
                        jersey_number,
                        height,
                        weight,
                        ppg,
                        rpg,
                        apg,
                        injury_status,
                        season_stats,
                        career_highlights,
                    ),
                )
                connection.commit()
            except Exception as e:
                print(f"Erro ao armazenar info do jogador {player_name}: {e}")
    
    def store_news(
        self,
        date: str,
        team: str,
        headline: str,
        impact: str,
        relevant_to_betting: bool = False,
        injury_update: bool = False,
    ) -> None:
        """Armazena notícias e eventos importantes da NBA."""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO nba_news
                (ts, date, team, headline, impact, relevant_to_betting, injury_update)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (time.time(), date, team, headline, impact, relevant_to_betting, injury_update),
            )
            connection.commit()
    
    def get_team_info(self, team_name: str) -> Dict[str, Any]:
        """Retorna informações armazenadas sobre um time."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM nba_teams WHERE team_name = ?",
                (team_name,),
            ).fetchone()
        
        if not row:
            return {}
        
        return {
            "team_name": row["team_name"],
            "city": row["city"],
            "conference": row["conference"],
            "division": row["division"],
            "last_season_record": row["last_season_record"],
            "home_court": row["home_court"],
            "key_players": row["key_players"],
            "historical_notes": row["historical_notes"],
        }
    
    def get_team_stats(self, team_name: str, season: str = None) -> List[Dict]:
        """Retorna estatísticas de um time, filtradas por temporada se indicado."""
        with self._connect() as connection:
            if season:
                rows = connection.execute(
                    "SELECT * FROM nba_team_stats WHERE team_name = ? AND season = ? ORDER BY ts DESC LIMIT 1",
                    (team_name, season),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM nba_team_stats WHERE team_name = ? ORDER BY ts DESC LIMIT 5",
                    (team_name,),
                ).fetchall()
        
        return [
            {
                "team_name": row["team_name"],
                "season": row["season"],
                "wins": row["wins"],
                "losses": row["losses"],
                "ppg": row["ppg"],
                "ppf": row["ppf"],
                "win_pct": f"{row['win_percentage']:.1%}",
            }
            for row in rows
        ]
    
    def get_relevant_patterns(self, num_patterns: int = 5) -> List[str]:
        """Retorna padrões relevantes para apostar."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT pattern_name, description, betting_edge, reliability_score
                FROM nba_patterns
                ORDER BY reliability_score DESC, last_observed DESC
                LIMIT ?
                """,
                (num_patterns,),
            ).fetchall()
        
        patterns = []
        for row in rows:
            patterns.append(
                f"📊 {row['pattern_name']}: {row['description']} "
                f"(Edge: {row['betting_edge']}, Confiança: {row['reliability_score']:.0%})"
            )
        
        return patterns
    
    def get_injury_updates(self) -> List[str]:
        """Retorna notícias de lesões que podem afetar apostas."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT team, headline, impact, date
                FROM nba_news
                WHERE injury_update = 1
                ORDER BY ts DESC
                LIMIT 10
                """,
            ).fetchall()
        
        updates = []
        for row in rows:
            updates.append(f"⚠️ [{row['team']}] {row['headline']} - {row['impact']}")
        
        return updates
    
    def get_betting_relevant_news(self) -> List[str]:
        """Retorna notícias relevantes para apostas."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT team, headline, impact, date
                FROM nba_news
                WHERE relevant_to_betting = 1
                ORDER BY ts DESC
                LIMIT 8
                """,
            ).fetchall()
        
        news = []
        for row in rows:
            news.append(f"📰 [{row['team']}] {row['headline']}")
        
        return news
    
    def build_nba_context(self, team_a: str = None, team_b: str = None) -> str:
        """Constrói contexto NBA para injetar no prompt do Gemini."""
        lines = ["=== CONTEXTO NBA ==="]
        
        # Info dos times se fornecidos
        if team_a:
            info_a = self.get_team_info(team_a)
            stats_a = self.get_team_stats(team_a)
            if info_a:
                lines.append(f"\n🏀 {team_a}:")
                lines.append(f"  Divisão: {info_a.get('division', 'N/A')}")
                lines.append(f"  Jogadores-chave: {info_a.get('key_players', 'N/A')}")
                if stats_a:
                    lines.append(
                        f"  Stats: {stats_a[0]['wins']}W-{stats_a[0]['losses']}L | "
                        f"PPG: {stats_a[0]['ppg']:.1f} | PPF: {stats_a[0]['ppf']:.1f}"
                    )
        
        if team_b:
            info_b = self.get_team_info(team_b)
            stats_b = self.get_team_stats(team_b)
            if info_b:
                lines.append(f"\n🏀 {team_b}:")
                lines.append(f"  Divisão: {info_b.get('division', 'N/A')}")
                lines.append(f"  Jogadores-chave: {info_b.get('key_players', 'N/A')}")
                if stats_b:
                    lines.append(
                        f"  Stats: {stats_b[0]['wins']}W-{stats_b[0]['losses']}L | "
                        f"PPG: {stats_b[0]['ppg']:.1f} | PPF: {stats_b[0]['ppf']:.1f}"
                    )
        
        # Padrões relevantes
        patterns = self.get_relevant_patterns(3)
        if patterns:
            lines.append("\n📊 Padrões Relevantes:")
            for pattern in patterns:
                lines.append(f"  {pattern}")
        
        # Lesões críticas
        injuries = self.get_injury_updates()
        if injuries:
            lines.append("\n⚠️ Lesões Críticas:")
            for injury in injuries[:3]:
                lines.append(f"  {injury}")
        
        # Notícias de aposta
        news = self.get_betting_relevant_news()
        if news:
            lines.append("\n📰 Notícias de Aposta:")
            for item in news[:3]:
                lines.append(f"  {item}")
        
        return "\n".join(lines)


async def fetch_nba_data_from_gemini(gemini_api_key: str, prompt: str, timeout: int = 15) -> str:
    """
    Usa Gemini para buscar informações sobre NBA da internet.
    Retorna informações estruturadas que podem ser armazenadas no BD.
    """
    import google.generativeai as genai
    
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt, timeout=timeout)
        
        if response and response.text:
            return response.text
        return ""
    except Exception as e:
        print(f"Erro ao buscar dados NBA via Gemini: {e}")
        return ""


def build_nba_population_prompt(category: str = "teams") -> str:
    """Constrói prompt para Gemini completar base de conhecimento NBA."""
    
    if category == "teams":
        return """
        Lista os 30 times da NBA (2025-2026 season) com:
        - Nome da cidade e time
        - Conferência e Divisão
        - Recorde da temporada anterior (wins-losses)
        - Estádio/Arena
        - 3-4 jogadores-chave principais
        
        Formato: JSON array com campos: team_name, city, conference, division, 
        last_season_record, home_court, key_players, historical_notes
        
        Retorne APENAS JSON válido, sem explicação.
        """
    
    elif category == "stats":
        return """
        Retorne estatísticas NBA 2024-2025 season:
        - PPG (Pontos por Jogo)
        - PPF (Pontos Permitidos por Jogo)
        - Rebounding
        - Assists por jogo
        - Win percentage
        
        Para cada time NBA, em formato JSON:
        {team_name, season, wins, losses, ppg, ppf, rebounding, ast_per_game, defense_rating, offensive_rating}
        
        Retorne APENAS JSON array válido.
        """
    
    elif category == "patterns":
        return """
        Padrões de jogo NBA que afetam resultados de apostas:
        
        Liste 10-15 padrões importantes como:
        - B2B (back-to-back) performance
        - Home vs Away records
        - Conference play
        - Rodada final de temporada (trading deadline efeito)
        - Novo técnico no time
        - Rest vs No rest advantage
        
        Formato JSON: {pattern_name, description, relevant_teams, impact_on_scoring, betting_edge, reliability_score}
        
        Retorne APENAS JSON array.
        """
    
    elif category == "players":
        return """
        Top 50 jogadores NBA 2025 com:
        - Nome, Team, Position
        - PPG, RPG, APG
        - Jersey Number, Height, Weight
        - Status de lesão
        - Destaques de carreira
        
        Formato JSON: {player_name, team, position, jersey_number, height, weight, ppg, rpg, apg, injury_status}
        
        Retorne APENAS JSON array.
        """
    
    elif category == "news":
        return """
        Notícias recentes de NBA (últimas 2 semanas) que afetam apostas:
        - Lesões de jogadores-chave
        - Trades ou Free Agency
        - Técnico/FO changes
        - Dinâmica de times mudando
        
        Formato: {date, team, headline, impact, relevant_to_betting, injury_update}
        
        Retorne APENAS JSON array.
        """
    
    return "Retorne informações sobre NBA em formato JSON."
