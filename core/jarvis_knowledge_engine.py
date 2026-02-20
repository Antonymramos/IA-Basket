#!/usr/bin/env python3
"""
Jarvis Knowledge Engine - Motor de conhecimento autônomo para o assistente.
Integra NBA knowledge, feedback loop, análise de padrões e busca na internet.
Jarvis consulta isso para tomar decisões MUITO mais inteligentes.
"""

from __future__ import annotations

import sqlite3
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

from core.communication_engine import CommunicationEngine


class JarvisKnowledgeEngine:
    """Motor que alimenta o Jarvis com conhecimento agregado."""
    
    def __init__(
        self,
        analytics_db: str,
        feedback_db: str,
        nba_db: str,
    ):
        self.analytics_db = analytics_db
        self.feedback_db = feedback_db
        self.nba_db = nba_db
    
    def _connect(self, db_path: str) -> sqlite3.Connection:
        connection = sqlite3.connect(db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection
    
    def get_current_betting_intelligence(self, minutes: int = 120) -> Dict[str, Any]:
        """
        Retorna inteligência completa sobre apostas atual para o Jarvis usar.
        Integra: odds, padrões, lesões, estatísticas, histórico pessoal.
        """
        window_start = time.time() - (minutes * 60)
        
        intelligence = {
            "timestamp": datetime.now().isoformat(),
            "window_minutes": minutes,
            "market_analysis": self._analyze_market(window_start),
            "personal_performance": self._get_personal_performance(window_start),
            "nba_context": self._get_nba_context(),
            "risk_assessment": self._assess_current_risk(window_start),
            "pattern_recognition": self._recognize_patterns(window_start),
            "recommendations": self._generate_recommendations(window_start),
        }
        
        return intelligence
    
    def _analyze_market(self, window_start: float) -> Dict[str, Any]:
        """Analisa mercado de apostas: o que está acontecendo."""
        try:
            with self._connect(self.analytics_db) as connection:
                # Contar eventos de aposta
                detected = connection.execute(
                    "SELECT COUNT(*) as c FROM events WHERE ts >= ? AND event_name = 'DETECTADO'",
                    (window_start,),
                ).fetchone()["c"]
                
                apostou = connection.execute(
                    "SELECT COUNT(*) as c FROM events WHERE ts >= ? AND event_name = 'APOSTOU'",
                    (window_start,),
                ).fetchone()["c"]
                
                bloqueado = connection.execute(
                    "SELECT COUNT(*) as c FROM events WHERE ts >= ? AND event_name = 'BLOQUEADO'",
                    (window_start,),
                ).fetchone()["c"]
                
                expirou = connection.execute(
                    "SELECT COUNT(*) as c FROM events WHERE ts >= ? AND event_name = 'EXPIROU'",
                    (window_start,),
                ).fetchone()["c"]
                
                # Taxa de sucesso
                success_rate = (apostou / detected * 100) if detected > 0 else 0
                block_rate = (bloqueado / detected * 100) if detected > 0 else 0
                
                return {
                    "opportunities_detected": detected,
                    "bets_executed": apostou,
                    "success_rate_pct": round(success_rate, 1),
                    "blocked_pct": round(block_rate, 1),
                    "expired_pct": round((expirou / detected * 100) if detected > 0 else 0, 1),
                    "market_heat": "HOT" if apostou > 5 else "WARM" if apostou > 2 else "COLD",
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_personal_performance(self, window_start: float) -> Dict[str, Any]:
        """Desempenho pessoal: quanto você está ganhando/perdendo."""
        try:
            with self._connect(self.feedback_db) as connection:
                # Stats gerais
                total = connection.execute(
                    "SELECT COUNT(*) as c FROM bet_results WHERE ts >= ?",
                    (window_start,),
                ).fetchone()["c"]
                
                won = connection.execute(
                    "SELECT COUNT(*) as c FROM bet_results WHERE ts >= ? AND result_status = 'WON'",
                    (window_start,),
                ).fetchone()["c"]
                
                lost = connection.execute(
                    "SELECT COUNT(*) as c FROM bet_results WHERE ts >= ? AND result_status = 'LOST'",
                    (window_start,),
                ).fetchone()["c"]
                
                # Lucro esperado (EV-weighted)
                profit = connection.execute(
                    """
                    SELECT 
                        SUM(CASE WHEN result_status = 'WON' THEN ev_score * stake ELSE -stake END) as total
                    FROM bet_results
                    WHERE ts >= ?
                    """,
                    (window_start,),
                ).fetchone()["total"] or 0.0
                
                # Melhor tipo
                best_type = connection.execute(
                    """
                    SELECT tipo_pontuacao, 
                           SUM(CASE WHEN result_status = 'WON' THEN 1 ELSE 0 END) as wins,
                           COUNT(*) as total
                    FROM bet_results
                    WHERE ts >= ?
                    GROUP BY tipo_pontuacao
                    ORDER BY (wins * 1.0 / total) DESC
                    LIMIT 1
                    """,
                    (window_start,),
                ).fetchone()
                
                return {
                    "total_bets": total,
                    "wins": won,
                    "losses": lost,
                    "win_rate_pct": round((won / total * 100) if total > 0 else 0, 1),
                    "expected_profit": round(profit, 2),
                    "best_performing_type": f"{best_type['tipo_pontuacao']}pt ({best_type['wins']}/{best_type['total']})" if best_type else "Sem dados",
                    "confidence": "HIGH" if won / max(1, total) > 0.6 else "MEDIUM" if won / max(1, total) > 0.45 else "LOW",
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_nba_context(self) -> Dict[str, Any]:
        """Contexto NBA: lesões críticas, padrões, notícias."""
        try:
            with self._connect(self.nba_db) as connection:
                # Lesões críticas
                injuries = connection.execute(
                    "SELECT team, headline, impact FROM nba_news WHERE injury_update = 1 ORDER BY ts DESC LIMIT 5"
                ).fetchall()
                
                # Padrões importantes
                patterns = connection.execute(
                    "SELECT pattern_name, betting_edge, reliability_score FROM nba_patterns ORDER BY reliability_score DESC LIMIT 3"
                ).fetchall()
                
                # Notícias de aposta
                news = connection.execute(
                    "SELECT team, headline FROM nba_news WHERE relevant_to_betting = 1 ORDER BY ts DESC LIMIT 3"
                ).fetchall()
                
                return {
                    "critical_injuries": [
                        f"{i['team']}: {i['headline']}" for i in injuries
                    ],
                    "key_patterns": [
                        f"{p['pattern_name']} (Edge: {p['betting_edge']}, Confiança: {p['reliability_score']:.0%})" 
                        for p in patterns
                    ],
                    "betting_news": [
                        f"{n['team']}: {n['headline']}" for n in news
                    ],
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _assess_current_risk(self, window_start: float) -> Dict[str, Any]:
        """Avalia risco atual do mercado."""
        try:
            with self._connect(self.analytics_db) as connection:
                # Erros recentes
                errors = connection.execute(
                    "SELECT COUNT(*) as c FROM events WHERE ts >= ? AND event_name IN ('ERROR', 'GEMINI_ERROR')",
                    (window_start,),
                ).fetchone()["c"]
                
                # Safe mode ativo?
                safe_mode = connection.execute(
                    "SELECT COUNT(*) as c FROM events WHERE ts >= ? AND event_name = 'SAFE_MODE_ENABLED'",
                    (window_start,),
                ).fetchone()["c"]
                
                # Taxa de bloqueio (pode indicar instabilidade)
                blocked = connection.execute(
                    "SELECT COUNT(*) as c FROM events WHERE ts >= ? AND event_name = 'BLOQUEADO'",
                    (window_start,),
                ).fetchone()["c"]
                
                detected = connection.execute(
                    "SELECT COUNT(*) as c FROM events WHERE ts >= ? AND event_name = 'DETECTADO'",
                    (window_start,),
                ).fetchone()["c"]
                
                block_rate = (blocked / detected * 100) if detected > 0 else 0
                
                return {
                    "recent_errors": errors,
                    "safe_mode_active": bool(safe_mode),
                    "block_rate_pct": round(block_rate, 1),
                    "risk_level": "CRITICAL" if safe_mode or errors > 3 else "HIGH" if block_rate > 50 else "MEDIUM" if block_rate > 25 else "LOW",
                    "recommendation": "PAUSE APOSTAS" if safe_mode or errors > 3 else "PROCEDA COM CAUTELA" if block_rate > 50 else "NORMAL",
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _recognize_patterns(self, window_start: float) -> Dict[str, Any]:
        """Reconhece padrões de sucesso e falha."""
        try:
            with self._connect(self.feedback_db) as connection:
                # Horário do dia com mais sucesso
                best_hour = connection.execute(
                    """
                    SELECT strftime('%H', datetime(ts, 'unixepoch')) as hora,
                           SUM(CASE WHEN result_status = 'WON' THEN 1 ELSE 0 END) as wins,
                           COUNT(*) as total
                    FROM bet_results
                    WHERE ts >= ?
                    GROUP BY hora
                    ORDER BY (wins * 1.0 / total) DESC
                    LIMIT 1
                    """,
                    (window_start,),
                ).fetchone()
                
                # Tipo de jogo com mais sucesso
                best_game_type = connection.execute(
                    """
                    SELECT tipo_pontuacao,
                           SUM(CASE WHEN result_status = 'WON' THEN 1 ELSE 0 END) as wins,
                           COUNT(*) as total
                    FROM bet_results
                    WHERE ts >= ?
                    GROUP BY tipo_pontuacao
                    ORDER BY (wins * 1.0 / total) DESC
                    LIMIT 1
                    """,
                    (window_start,),
                ).fetchone()
                
                return {
                    "best_hour": f"{best_hour['hora']}:00" if best_hour else "Sem dados",
                    "best_hour_accuracy": f"{(best_hour['wins'] / best_hour['total'] * 100):.1f}%" if best_hour and best_hour['total'] > 0 else "N/A",
                    "best_game_type": f"{best_game_type['tipo_pontuacao']}pt" if best_game_type else "N/A",
                    "best_game_accuracy": f"{(best_game_type['wins'] / best_game_type['total'] * 100):.1f}%" if best_game_type and best_game_type['total'] > 0 else "N/A",
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_recommendations(self, window_start: float) -> List[str]:
        """Gera recomendações baseadas em tudo que sabe."""
        recommendations = []
        
        try:
            perf = self._get_personal_performance(window_start)
            risk = self._assess_current_risk(window_start)
            patterns = self._recognize_patterns(window_start)
            
            # Baseado em performance
            if perf.get("win_rate_pct", 0) > 60:
                recommendations.append("✅ CONFIANÇA ALTA: Você está em boa forma, continue com estratégia atual")
            elif perf.get("win_rate_pct", 0) < 40:
                recommendations.append("⚠️ REVISAR ESTRATÉGIA: Taxa de acerto abaixo de 40%, considere pausa")
            
            # Baseado em risco
            if risk.get("safe_mode_active"):
                recommendations.append("🛑 SAFE MODE ATIVO: Sistema detectou instabilidade, não faça apostas por enquanto")
            
            # Baseado em padrões
            if patterns.get("best_hour") != "Sem dados":
                recommendations.append(f"📊 PADRÃO DESCOBERTO: Você joga melhor em {patterns['best_hour']} (acurácia {patterns['best_hour_accuracy']})")
            
            # Baseado em mercado
            market = self._analyze_market(window_start)
            if market.get("market_heat") == "HOT":
                recommendations.append("🔥 MERCADO QUENTE: Muitas oportunidades sendo detectadas")
            elif market.get("market_heat") == "COLD":
                recommendations.append("❄️ MERCADO FRIO: Poucas oportunidades, seja seletivo")
            
            # NBA insights
            nba = self._get_nba_context()
            if nba.get("critical_injuries"):
                recommendations.append(f"⚠️ LESÃO CRÍTICA: {nba['critical_injuries'][0]}")
            
        except Exception as e:
            recommendations.append(f"Erro ao gerar recomendações: {str(e)}")
        
        return recommendations if recommendations else ["💡 Sem recomendações específicas no momento"]
    
    def get_jarvis_briefing(self) -> str:
        """
        Retorna briefing completo para o Jarvis apresentar ao usuário.
        Tudo resumido, pronto para falar.
        """
        intelligence = self.get_current_betting_intelligence()
        
        briefing_lines = [
            "=== RELATÓRIO INTELIGENTE DO JARVIS ===",
            f"Atualizado em: {intelligence['timestamp']}",
            "",
            "📊 MERCADO:",
            f"  • Oportunidades detectadas: {intelligence['market_analysis'].get('opportunities_detected', 0)}",
            f"  • Apostas executadas: {intelligence['market_analysis'].get('bets_executed', 0)}",
            f"  • Taxa de sucesso: {intelligence['market_analysis'].get('success_rate_pct', 0)}%",
            f"  • Temperatura: {intelligence['market_analysis'].get('market_heat', 'N/A')}",
            "",
            "💰 SEU DESEMPENHO:",
            f"  • Total de apostas: {intelligence['personal_performance'].get('total_bets', 0)}",
            f"  • Ganhos: {intelligence['personal_performance'].get('wins', 0)} | Perdas: {intelligence['personal_performance'].get('losses', 0)}",
            f"  • Taxa de acerto: {intelligence['personal_performance'].get('win_rate_pct', 0)}%",
            f"  • Lucro esperado: R$ {intelligence['personal_performance'].get('expected_profit', 0)}",
            f"  • Confiança: {intelligence['personal_performance'].get('confidence', 'N/A')}",
            "",
            "🏀 CONTEXTO NBA:",
        ]
        
        for injury in intelligence['nba_context'].get('critical_injuries', [])[:2]:
            briefing_lines.append(f"  ⚠️ {injury}")
        
        briefing_lines.extend([
            "",
            "🎯 PADRÕES DESCOBERTOS:",
        ])
        
        for pattern in intelligence['pattern_recognition'].items():
            if pattern[0] not in ['error']:
                briefing_lines.append(f"  • {pattern[0]}: {pattern[1]}")
        
        briefing_lines.extend([
            "",
            "⚡ NÍVEL DE RISCO:",
            f"  • Status: {intelligence['risk_assessment'].get('risk_level', 'N/A')}",
            f"  • Recomendação: {intelligence['risk_assessment'].get('recommendation', 'N/A')}",
            "",
            "💡 RECOMENDAÇÕES:",
        ])
        
        for rec in intelligence['recommendations']:
            briefing_lines.append(f"  {rec}")
        
        return "\n".join(briefing_lines)
    
    def get_betting_suggestion(self, team_a: str, team_b: str) -> Dict[str, Any]:
        """
        Retorna sugestão completa de aposta para o Jarvis apresentar.
        Integra tudo: odds, padrões, histórico pessoal, saúde dos times.
        """
        perf = self._get_personal_performance(time.time() - 30*24*3600)  # Últimos 30 dias
        nba = self._get_nba_context()
        risk = self._assess_current_risk(time.time() - 2*3600)  # Últimas 2h
        
        return {
            "teams": f"{team_a} vs {team_b}",
            "personal_stats": perf,
            "nba_context": nba,
            "risk_assessment": risk,
            "confidence_score": 0.0,  # Será calculado por Gemini
            "recommendation": "ANALISAR COM CUIDADO" if risk['risk_level'] in ['HIGH', 'CRITICAL'] else "PROCEDER",
            "factors_to_consider": [
                f"Seu histórico recente: {perf['win_rate_pct']}% de taxa de acerto",
                f"Lesões críticas: {len(nba.get('critical_injuries', []))} times afetados",
                f"Risco atual: {risk['risk_level']}",
                f"Melhor hora para apostar: {self._recognize_patterns(time.time() - 7*24*3600).get('best_hour')}",
            ],
        }

    # ============================================
    # ENHANCED COMMUNICATION METHODS
    # ============================================

    def get_betting_suggestion_explained(
        self, team_a: str, team_b: str, confidence: float = 0.70
    ) -> Dict[str, Any]:
        """
        Retorna sugestão de aposta COM explicações narrativas completas
        Diferente de get_betting_suggestion() que é técnico.
        """
        comm = CommunicationEngine()
        suggestion = self.get_betting_suggestion(team_a, team_b)
        
        # Extrair componentes
        intel = self.get_current_betting_intelligence(minutes=120)
        market = intel.get("market_analysis", {})
        perf = intel.get("personal_performance", {})
        nba = intel.get("nba_context", {})
        risk = intel.get("risk_assessment", {})
        patterns = intel.get("pattern_recognition", {})

        # Build explanation narrative
        reasons = [
            comm.explain_market_analysis(market),
            comm.explain_personal_performance(perf),
            comm.explain_nba_context(nba),
        ]

        factors = {
            "market_health": 0.15 if market.get("executed_rate", 0) > 0.7 else -0.10,
            "personal_form": 0.20 if perf.get("win_rate", 0) > 0.60 else -0.10,
            "nba_injuries": 0.10 if not nba.get("injury_updates", []) else -0.15,
            "risk_level": -0.25 if risk.get("risk_level") == "HIGH" else 0.05,
        }

        return comm.build_recommendation(
            team_a, team_b, confidence, factors, reasons
        )

    def get_pattern_insights(self) -> Dict[str, Any]:
        """
        Retorna insights sobre padrões descobertos com narrativa
        """
        comm = CommunicationEngine()
        window_start = time.time() - 30 * 24 * 3600  # Últimos 30 dias

        patterns = self._recognize_patterns(window_start)

        return {
            "best_hour": patterns.get("best_hour"),
            "best_hour_description": comm._describe_hour(patterns.get("best_hour", 0)),
            "best_game_type": patterns.get("best_game_type"),
            "success_rate": patterns.get("game_type_success_rate", 0),
            "narrative": comm.explain_pattern_recognition(patterns),
            "recommendation": (
                f"Aproveite as oportunidades às {comm._describe_hour(patterns.get('best_hour', 0))} "
                f"com apostas em {patterns.get('best_game_type', 'N/A')}pt"
            ),
        }

    def get_decision_breakdown(
        self, team_a: str, team_b: str, confidence: float = 0.70
    ) -> Dict[str, Any]:
        """
        Quebra a decisão em componentes com impacto individual explicado
        Mostra EXATAMENTE por que cada fator importa
        """
        comm = CommunicationEngine()
        intel = self.get_current_betting_intelligence(minutes=120)

        market = intel.get("market_analysis", {})
        perf = intel.get("personal_performance", {})
        nba = intel.get("nba_context", {})
        risk = intel.get("risk_assessment", {})

        # Calcular impacto individual de cada componente
        components = {
            "market_analysis": 0.15 if market.get("executed_rate", 0) > 0.7 else -0.10,
            "personal_performance": 0.25 if perf.get("win_rate", 0) > 0.60 else -0.15,
            "nba_context": 0.15 if not nba.get("injury_updates", []) else -0.10,
            "risk_assessment": -0.10 if risk.get("risk_level") == "HIGH" else 0.05,
            "pattern_recognition": 0.10,
        }

        return comm.build_decision_breakdown(team_a, team_b, components, confidence)

    def get_weekly_performance(self) -> Dict[str, Any]:
        """
        Retorna resumo semanal que comunica aprendizado e progresso
        """
        comm = CommunicationEngine()
        window_start = time.time() - 7 * 24 * 3600  # Últimos 7 dias

        try:
            conn = self._connect(self.feedback_db)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT 
                    SUM(CASE WHEN result_status = 'WON' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result_status = 'LOST' THEN 1 ELSE 0 END) as losses,
                    COUNT(*) as total
                FROM bet_results
                WHERE timestamp >= ?
                """,
                (window_start,),
            )
            row = cursor.fetchone()
            wins = row[0] or 0
            losses = row[1] or 0
            total = row[2] or 1

            win_rate = wins / max(total, 1)

            # Buscar semana anterior para comparação
            window_start_prev = time.time() - 14 * 24 * 3600
            window_end_prev = time.time() - 7 * 24 * 3600

            cursor.execute(
                """
                SELECT 
                    SUM(CASE WHEN result_status = 'WON' THEN 1 ELSE 0 END) as wins,
                    COUNT(*) as total
                FROM bet_results
                WHERE timestamp >= ? AND timestamp < ?
                """,
                (window_start_prev, window_end_prev),
            )
            row_prev = cursor.fetchone()
            wins_prev = row_prev[0] or 0
            total_prev = row_prev[1] or 1
            win_rate_prev = wins_prev / max(total_prev, 1)

            accuracy_change = (win_rate - win_rate_prev) * 100

            conn.close()

            performance = {
                "wins": wins,
                "losses": losses,
                "win_rate": win_rate,
                "new_patterns_discovered": 2,  # Placeholder
                "accuracy_change_percent": accuracy_change,
                "best_sequence": 3,  # Placeholder
            }

            return {
                "summary": comm.build_weekly_summary(performance),
                "performance": performance,
            }

        except Exception as e:
            return {
                "summary": f"Erro ao gerar resumo semanal: {str(e)}",
                "performance": {},
            }

    def format_immediate_feedback(
        self, event: str, team_a: str, team_b: str, metadata: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """
        Formata feedback imediato para eventos de apostas
        DETECTADO, APOSTOU, BLOQUEADO
        """
        comm = CommunicationEngine()
        metadata = metadata or {}

        if event == "DETECTADO":
            return comm.format_detection_feedback(
                team_a,
                team_b,
                metadata.get("game_type", "2"),
                metadata.get("ev_score", 0),
                metadata.get("consensus_strength", 0.5),
            )

        elif event == "APOSTOU":
            return comm.format_execution_feedback(
                team_a, team_b, metadata.get("delay_seconds", 0)
            )

        elif event == "BLOQUEADO":
            return comm.format_block_feedback(
                team_a,
                team_b,
                metadata.get("reason", "unknown"),
                metadata.get("current_errors", 0),
            )

        return {"event": event, "emoji": "❓", "message": "Evento desconhecido"}

    def answer_question(self, question: str) -> str:
        """
        Responde perguntas do usuário sobre o sistema
        """
        comm = CommunicationEngine()
        intel = self.get_current_betting_intelligence()

        context = {
            "win_rate": intel.get("personal_performance", {}).get("win_rate", 0),
            "best_hour": intel.get("pattern_recognition", {}).get("best_hour"),
        }

        return comm.answer_question(question, context)


def build_jarvis_knowledge_endpoint(
    analytics_db: str,
    feedback_db: str,
    nba_db: str,
) -> JarvisKnowledgeEngine:
    """Factory para criar engine de conhecimento do Jarvis."""
    return JarvisKnowledgeEngine(analytics_db, feedback_db, nba_db)
