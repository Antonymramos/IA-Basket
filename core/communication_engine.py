"""
Communication Engine - Motor de Comunicação Inteligente para Jarvis
Responsável por:
- Traduzir decisões técnicas em linguagem natural
- Explicar recomendações com narrativa clara
- Adaptar tom e estilo ao contexto
- Aplicar gírias/regionalismos brasileiros
- Estruturar feedback imediato e significativo
"""

import sqlite3
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum

from core.brazilian_context import (
    GIRIAS_APOSTA,
    REGIONALISMOS,
    EVENTOS_CULTURAIS,
    HORARIOS_BRASIL,
    get_girias_contextualizadas,
    get_contexto_temporal_brasileiro,
)


class ConfidenceLevel(Enum):
    """Níveis de confiança com emojis e descrições"""
    VERY_HIGH = ("muito_alta", "🟢 Muito Confiante", 0.80)
    HIGH = ("alta", "🟢 Confiante", 0.65)
    MODERATE = ("moderada", "🟡 Moderadamente Confiante", 0.50)
    LOW = ("baixa", "🔴 Baixa Confiança", 0.35)
    VERY_LOW = ("muito_baixa", "🔴 Muito baixa confiança", 0.0)

    def get_level(confidence_score: float) -> "ConfidenceLevel":
        """Classifica score em nível de confiança"""
        if confidence_score >= 0.80:
            return ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.65:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 0.50:
            return ConfidenceLevel.MODERATE
        elif confidence_score >= 0.35:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW


class CommunicationEngine:
    """Motor de comunicação que traduz decisões técnicas em linguagem natural"""

    def __init__(self):
        self.brazilian_girias = GIRIAS_APOSTA
        self.regionalismos = REGIONALISMOS
        self.cultural_events = EVENTOS_CULTURAIS
        self.peak_hours = HORARIOS_BRASIL

    # ============================================
    # FORMAT & CONFIDENCE
    # ============================================

    def format_confidence(self, confidence_score: float) -> Dict[str, Any]:
        """
        Converte score técnico em percentual legível e descrição
        Ex: 0.78 → "78% | 🟢 Confiante"
        """
        level = ConfidenceLevel.get_level(confidence_score)
        emoji, description, min_threshold = level.value

        return {
            "percentage": int(confidence_score * 100),
            "level": level.value[0],
            "emoji": emoji,
            "description": description,
            "full_text": f"{int(confidence_score * 100)}% {description}",
            "is_positive": confidence_score >= 0.50,
        }

    # ============================================
    # EXPLANATION CHAINS
    # ============================================

    def explain_market_analysis(self, analysis: Dict[str, Any]) -> str:
        """
        Explica análise de mercado em português natural
        """
        detected = analysis.get("detected_rate", 0)
        executed = analysis.get("executed_rate", 0)
        blocked = analysis.get("blocked_rate", 0)

        if detected < 0.1:
            return "🔍 Mercado muito calmo - poucas oportunidades detectadas."

        if blocked > 0.3:
            return (
                f"⚠️ Mercado instável - {int(blocked * 100)}% das apostas foram bloqueadas por risco."
            )

        if executed > 0.7:
            return "✅ Mercado saudável - a maioria das apostas foram executadas com sucesso."

        return (
            f"📊 Mercado ativo - {int(detected * 100)} sinais detectados, "
            f"{int(executed * 100)} executados."
        )

    def explain_personal_performance(self, performance: Dict[str, Any]) -> str:
        """
        Explica performance pessoal em narrativa motivadora
        """
        win_rate = performance.get("win_rate", 0)
        wins = performance.get("wins", 0)
        losses = performance.get("losses", 0)
        profit = performance.get("expected_profit", 0)

        if wins == 0:
            return "📈 Começando a jornada com Jarvis... Primeira aposta definirá o caminho!"

        streak_analysis = "positiva" if win_rate >= 0.60 else "recuperação"

        giria = self.brazilian_girias.get(
            "boa_sequencia", "na boca do gol"
        ) if win_rate >= 0.70 else "numa sequência interessante"

        return (
            f"🏆 Performance: {wins}W-{losses}L ({int(win_rate * 100)}%) {giria}\n"
            f"   Lucro esperado: R$ {profit:.2f} | Tendência: {streak_analysis.upper()}"
        )

    def explain_nba_context(self, nba_context: Dict[str, Any]) -> str:
        """
        Explica contexto NBA - lesões, padrões, notícias
        """
        injuries = nba_context.get("injury_updates", [])
        patterns = nba_context.get("relevant_patterns", [])
        news = nba_context.get("relevant_news", [])

        lines = []

        if injuries:
            lines.append(f"🏥 Lesões: {', '.join(injuries[:2])}")

        if patterns:
            best_pattern = patterns[0] if patterns else None
            if best_pattern:
                lines.append(f"📊 Padrão: {best_pattern.get('description', 'N/A')}")

        if news:
            lines.append(f"📰 Última notícia: {news[0].get('headline', '')[:60]}...")

        if not lines:
            lines.append("🏀 Contexto NBA estável - sem grandes mudanças.")

        return "\n   ".join(lines)

    def explain_risk_assessment(self, risk: Dict[str, Any]) -> str:
        """
        Explica avaliação de risco em termos claros
        """
        error_rate = risk.get("error_rate", 0)
        blocked_rate = risk.get("blocked_rate", 0)
        safe_mode = risk.get("safe_mode_active", False)

        if safe_mode:
            return "🛡️ SAFE MODE ATIVO - Sistema em mode conservador após sequência de erros."

        if error_rate > 0.3:
            return "⚠️ RISCO ELEVADO - Muitos erros recentes. Considere aguardar."

        if blocked_rate > 0.2:
            return f"🚫 {int(blocked_rate * 100)}% de bloqueios - Risco moderado, proceda com cuidado."

        return "✅ Risco controlado - Sistema operando normalmente."

    def explain_pattern_recognition(self, patterns: Dict[str, Any]) -> str:
        """
        Explica padrões descobertos de forma narrativa
        """
        best_hour = patterns.get("best_hour", None)
        best_game_type = patterns.get("best_game_type", None)

        lines = []

        if best_hour:
            lines.append(f"🕐 Melhor hora: {self._describe_hour(best_hour)}")

        if best_game_type:
            success_rate = patterns.get("game_type_success_rate", 0)
            lines.append(
                f"🎯 {best_game_type}pt: {int(success_rate * 100)}% acerto"
            )

        if not lines:
            lines.append("📊 Padrões ainda estão se formando...")

        return " | ".join(lines)

    def _describe_hour(self, hour: int) -> str:
        """Descreve uma hora do dia naturalmente"""
        hourly_context = HORARIOS_BRASIL.get(hour, {})
        description = hourly_context.get("description", f"{hour}h")
        return f"{description} ({hour}h)"

    # ============================================
    # RECOMMENDATIONS WITH NARRATIVES
    # ============================================

    def build_recommendation(
        self,
        team_a: str,
        team_b: str,
        confidence: float,
        factors: Dict[str, float],
        reasons: List[str],
    ) -> Dict[str, Any]:
        """
        Constrói uma recomendação completa com narrativa
        Ex: "Lakers vs Celtics: Aposte em Lakers com 78% de confiança porque..."
        """
        confidence_info = self.format_confidence(confidence)

        recommendation_text = (
            f"🎯 {team_a.upper()} vs {team_b.upper()}\n"
            f"{confidence_info['full_text']}\n\n"
            f"Por quê:\n"
        )

        # Adicionar razões numeradas
        for idx, reason in enumerate(reasons[:3], 1):
            recommendation_text += f"{idx}. {reason}\n"

        # Adicionar análise de fatores
        positive_factors = [k for k, v in factors.items() if v > 0]
        negative_factors = [k for k, v in factors.items() if v < 0]

        if positive_factors:
            recommendation_text += f"\n✅ A favor: {', '.join(positive_factors)}"

        if negative_factors:
            recommendation_text += f"\n⚠️ Contra: {', '.join(negative_factors)}"

        return {
            "team_a": team_a,
            "team_b": team_b,
            "recommendation": f"Apostar em {team_a}",
            "confidence": confidence_info,
            "narrative": recommendation_text,
            "factors": factors,
            "reasons": reasons,
        }

    # ============================================
    # IMMEDIATE FEEDBACK (Event-based)
    # ============================================

    def format_detection_feedback(
        self,
        team_a: str,
        team_b: str,
        game_type: str,
        ev_score: float,
        consensus_strength: float,
    ) -> Dict[str, str]:
        """
        Feedback imediato quando aposta é DETECTADA
        """
        emoji = "✅"
        confidence_info = self.format_confidence(consensus_strength)

        message = (
            f"{emoji} DETECTADA: {team_a} vs {team_b} ({game_type}pt)\n"
            f"   EV Score: {ev_score:.2f}\n"
            f"   Confiança Ensemble: {confidence_info['full_text']}"
        )

        return {
            "event": "DETECTADO",
            "emoji": emoji,
            "message": message,
            "narration": f"Aposta detectada em {team_a}. Confiança: {confidence_info['percentage']} por cento.",
        }

    def format_execution_feedback(
        self, team_a: str, team_b: str, delay_seconds: float
    ) -> Dict[str, str]:
        """
        Feedback quando aposta é EXECUTADA
        """
        emoji = "🎉"

        if delay_seconds < 1:
            emoji = "⚡"
            speed = "ultra-rápido"
        elif delay_seconds < 5:
            speed = "rápido"
        else:
            speed = f"em ${delay_seconds:.1f}s"

        message = f"{emoji} EXECUTADA: {team_a} vs {team_b} ({speed})"

        return {
            "event": "APOSTOU",
            "emoji": emoji,
            "message": message,
            "narration": f"Aposta executada {speed} em {team_a}.",
        }

    def format_block_feedback(
        self, team_a: str, team_b: str, reason: str, current_errors: int = 0
    ) -> Dict[str, str]:
        """
        Feedback quando aposta é BLOQUEADA
        """
        emoji = "🚫"

        reason_text = {
            "safe_mode": f"Safe Mode ativo ({current_errors} erros seguidos)",
            "high_risk": "Risco muito alto detectado",
            "low_consensus": "Baixa consenso no ensemble",
            "market_unstable": "Mercado instável",
        }.get(reason, reason)

        message = f"{emoji} BLOQUEADA: {team_a} vs {team_b}\n   Motivo: {reason_text}"

        return {
            "event": "BLOQUEADO",
            "emoji": emoji,
            "message": message,
            "narration": f"Aposta bloqueada. {reason_text}.",
        }

    # ============================================
    # CONTEXTUAL MESSAGING
    # ============================================

    def get_context_greeting(self) -> str:
        """Greeting que varia por hora do dia"""
        now = datetime.datetime.now()
        hour = now.hour

        if 5 <= hour < 12:
            return "🌅 Bom dia! Vamos analisar as oportunidades de hoje?"
        elif 12 <= hour < 18:
            return "☀️ Boa tarde! Qual o melhor movimento agora?"
        elif 18 <= hour < 21:
            return "🌆 Boa noite! Hora dos melhores jogos..."
        else:
            return "🌙 Boa madrugada! Analisando padrões da noite..."

    def get_day_context(self) -> str:
        """Contexto especial por dia da semana"""
        now = datetime.datetime.now()
        day_name = now.strftime("%A").lower()

        day_messages = {
            "monday": "📅 Segunda-feira: começando a semana certo...",
            "tuesday": "📅 Terça-feira: momentum nos jogos!",
            "wednesday": "📅 Quarta-feira: meio da semana, apostas mais previsíveis",
            "thursday": "📅 Quinta-feira: jogos importantes começam!",
            "friday": "📅 Sexta-feira: fim de semana chegando, alta volatilidade!",
            "saturday": "📅 Sábado: jogos bombados! Máxima atenção!",
            "sunday": "📅 Domingo: encerrando a semana... grandes finais!",
        }

        return day_messages.get(day_name, "📅 Vamos lá!")

    # ============================================
    # WEEKLY PERFORMANCE NARRATIVE
    # ============================================

    def build_weekly_summary(self, performance: Dict[str, Any]) -> str:
        """
        Resumo semanal que comunica aprendizado e progresso
        """
        wins = performance.get("wins", 0)
        losses = performance.get("losses", 0)
        win_rate = performance.get("win_rate", 0)
        new_patterns = performance.get("new_patterns_discovered", 0)
        accuracy_change = performance.get("accuracy_change_percent", 0)
        best_sequence = performance.get("best_sequence", 0)

        summary = f"📊 RESUMO SEMANAL\n{'=' * 40}\n"
        summary += f"Resultado: {wins}W - {losses}L ({int(win_rate * 100)}%)\n"

        if accuracy_change > 0:
            summary += (
                f"📈 Acurácia melhorou {accuracy_change:.1f}% esta semana!\n"
            )
        elif accuracy_change < 0:
            summary += f"📉 Acurácia baixou {abs(accuracy_change):.1f}% - vamos recuperar!\n"

        if new_patterns:
            summary += f"🎯 {new_patterns} padrão(ões) novo(s) descoberto(s)!\n"

        if best_sequence:
            summary += (
                f"🔥 Melhor sequência: {best_sequence} ganhos seguidos!\n"
            )

        summary += f"\nPróxima semana: continue acompanhando os padrões! 🚀"

        return summary

    # ============================================
    # DECISION BREAKDOWN (For Transparency)
    # ============================================

    def build_decision_breakdown(
        self,
        team_a: str,
        team_b: str,
        components: Dict[str, float],
        final_confidence: float,
    ) -> Dict[str, Any]:
        """
        Quebra cada componente da decisão com impacto individual
        Mostra ao usuário exatamente por que cada factor importa
        """
        breakdown = {
            "matchup": f"{team_a} vs {team_b}",
            "final_confidence": self.format_confidence(final_confidence),
            "components": [],
        }

        # Ordenar por impacto absoluto
        sorted_components = sorted(
            components.items(), key=lambda x: abs(x[1]), reverse=True
        )

        for component_name, impact in sorted_components:
            # Formatar nome do componente
            formatted_name = {
                "market_analysis": "Análise de Mercado",
                "personal_performance": "Performance Pessoal",
                "nba_context": "Contexto NBA",
                "risk_assessment": "Avaliação de Risco",
                "pattern_recognition": "Reconhecimento de Padrões",
            }.get(component_name, component_name.replace("_", " ").title())

            # Descrição do impacto
            if impact > 0.2:
                impact_desc = "+++Muito positivo"
                emoji = "✅"
            elif impact > 0.1:
                impact_desc = "++Positivo"
                emoji = "✅"
            elif impact > 0:
                impact_desc = "+Levemente positivo"
                emoji = "👍"
            elif impact > -0.1:
                impact_desc = "-Levemente negativo"
                emoji = "⚠️"
            elif impact > -0.2:
                impact_desc = "--Negativo"
                emoji = "❌"
            else:
                impact_desc = "---Muito negativo"
                emoji = "❌"

            breakdown["components"].append(
                {
                    "name": formatted_name,
                    "impact": round(impact, 3),
                    "percentage_contribution": f"{abs(impact) * 100:.1f}%",
                    "description": impact_desc,
                    "emoji": emoji,
                }
            )

        return breakdown

    # ============================================
    # INTERACTIVE Q&A
    # ============================================

    def answer_question(self, question: str, context: Dict[str, Any]) -> str:
        """
        Responde perguntas do usuário de forma contextual
        """
        question_lower = question.lower()

        # Perguntas sobre histórico
        if "melhor" in question_lower and "hora" in question_lower:
            best_hour = context.get("best_hour", None)
            if best_hour:
                return f"🕐 Sua melhor hora é {self._describe_hour(best_hour)}"
            return "📊 Ainda não temos padrão identificado de horário."

        # Perguntas sobre desempenho
        if "como" in question_lower and "desempenho" in question_lower:
            win_rate = context.get("win_rate", 0)
            return (
                f"📊 Sua taxa de acerto esta semana: {int(win_rate * 100)}%\n"
                f"Continue assim! 💪"
            )

        # Perguntas sobre bloqueios
        if "bloqueou" in question_lower or "por que" in question_lower:
            return (
                "🚫 Bloquei a aposta para proteger seu patrimônio.\n"
                "O mercado estava muito instável ou muitos erros foram detectados."
            )

        # Default
        return (
            "🤖 Entendi sua pergunta! Aqui está o que observo:\n"
            "Para mais detalhes, consulte os endpoints de inteligência."
        )
