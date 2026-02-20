import google.generativeai as genai
import asyncio
import time
from typing import Optional, Dict, List, Tuple
from core.tools_registry import registrar_discrepancia, executar_aposta_live
from core.brazilian_context import build_brazilian_prompt_section, get_contexto_temporal_brasileiro

class GeminiBrain:
    def __init__(self, api_key, preferred_model=None, ensemble_mode=True, confidence_threshold=0.70, feedback_loop=None, nba_knowledge=None):
        """
        Initialize Gemini Brain with ensemble voting capability and Few-Shot learning.
        
        Args:
            api_key: API key para Gemini
            preferred_model: Modelo preferido (opcional)
            ensemble_mode: Se True, usa múltiplos modelos votando
            confidence_threshold: Score mínimo de confiança para executar (0-1)
            feedback_loop: FeedbackLoop instance para Few-Shot examples (opcional)
            nba_knowledge: NBAKnowledge instance para injetar contexto NBA (opcional)
        """
        genai.configure(api_key=api_key)
        
        self.ensemble_mode = bool(ensemble_mode)
        self.confidence_threshold = float(confidence_threshold)
        self.feedback_loop = feedback_loop  # Para injetar exemplos de sucesso
        self.nba_knowledge = nba_knowledge  # Para injetar contexto NBA
        
        fallback_models = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]

        self.model_names = []
        if preferred_model:
            self.model_names.append(preferred_model)
        self.model_names.extend([name for name in fallback_models if name not in self.model_names])

        self.models = {
            model_name: genai.GenerativeModel(
                model_name=model_name,
                tools=[registrar_discrepancia, executar_aposta_live]
            )
            for model_name in self.model_names
        }
        self.active_model_name = self.model_names[0]
        self.last_ensemble_votes = []
    
    def _build_decision_prompt(self, transmission_data, bet_data, memory_context="") -> str:
        """Constrói prompt estruturado para decisão de aposta com Few-Shot examples e SOTAQUE BRASILEIRO."""
        # Inject Few-Shot examples se disponível
        few_shot_section = ""
        if self.feedback_loop:
            try:
                success_examples = self.feedback_loop.get_success_examples(limit=3)
                if success_examples:
                    few_shot_section = "\n=== EXEMPLOS DE SUCESSO (Few-Shot Learning) ===\n"
                    for i, ex in enumerate(success_examples, 1):
                        few_shot_section += f"""
        Exemplo {i} (✓ GANHOU):
        - Tipo: {ex.get('tipo_pontuacao', 2)}pt
        - EV Score: {ex.get('ev_score', 0):.2f}
        - Consenso: {(ex.get('consensus_strength', 0) * 100):.0f}%
        - Delay: {ex.get('delay_seconds', 0):.1f}s
        → Esta decisão teve ÊXITO. Padrões similares são geralmente acertados."""
                    few_shot_section += "\n"
            except Exception:
                pass  # Se falhar get success examples, continua sem eles
        
        # Injetar contexto cultural brasileiro (GÍRIAS, regionalismos, momento do dia)
        brazilian_section = build_brazilian_prompt_section(transmission_data, bet_data)
        
        # Injetar contexto NBA (estatísticas, padrões, lesões)
        nba_section = ""
        if self.nba_knowledge:
            try:
                # Tenta extrair times do transmission_data (formato pode variar)
                nba_context = self.nba_knowledge.build_nba_context()
                if nba_context:
                    nba_section = f"\n{nba_context}\n"
            except Exception:
                pass  # Se falhar, continua sem contexto NBA
        
        return f"""
        VOCÊ É UM PERITO EM APOSTAS ESPORTIVAS - BRASIL, SÓ!
        
        Tá ligado, aqui a gente não é robô. A gente fala com gírias mesmo,
        entende a vibe do momento, sabe quando tá uma sacanagem,
        quando tá fogo, quando tá maneiro.
        
        === DADOS ATUAIS ===
        Transmissão (timestamp real): {transmission_data}
        Bet Site (Bet365/Bellsports): {bet_data}
        
        === CONTEXTO HISTÓRICO ===
        {memory_context}
        {few_shot_section}
        {brazilian_section}
        {nba_section}
        === ANÁLISE RIGOROSA (CHAIN-OF-THOUGHT) ===
        Passo 1: Calcule diferenças de placar
        - Diferença time A: trans_team_a - bet_team_a
        - Diferença time B: trans_team_b - bet_team_b
        
        Passo 2: Verifique GAPs específicos
        - Procure por GAP de EXATAMENTE 2 ou 3 pontos para UM time
        - Confirme que bet está 5+ segundos desatualizado
        
        Passo 3: Avalie risco de delay
        - Se delay > 8s: somente 3pt com margem clara
        - Se histórico recente tem erros: BLOQUEAR
        
        Passo 4: Tome decisão final
        - Se tudo alinhado: EXECUTAR aposta
        - Se dúvida: REGISTRAR discrepância (segurança > lucro)
        
        === REGRAS DE ROBUSTEZ BRASILEIRA ===
        - NUNCA invente scores além dos fornecidos (tá ligado?)
        - Se há histórico negativo similar: BLOQUEAR (não é sacanagem?)
        - Prefira REGISTRAR DISCREPÂNCIA quando inseguro (grana é sagrada)
        - HIGH CONFIDENCE antes de executar (não vai atrás de qualquer cilada)
        - Se tá complicado demais: MELHOR PERDER 100 NA SEGURANÇA
        
        === RETORNE A DECISÃO ===
        Invoque a ferramenta apropriada baseado na análise acima.
        Fala como brasileiro mesmo - com confiança, gíria e jeito!
        """
    
    def _parse_model_response(self, response, stake: float) -> Dict:
        """Parse uma resposta do modelo em decisão estruturada."""
        if not response or not response.candidates:
            return {"action": "none", "confidence": 0.0}

        for candidate in response.candidates:
            if not candidate.content or not candidate.content.parts:
                continue

            for part in candidate.content.parts:
                if not part.function_call:
                    continue

                function_name = part.function_call.name
                args = dict(part.function_call.args)

                if function_name == "executar_aposta_live":
                    return {
                        "action": "executar_aposta_live",
                        "time_alvo": args.get("time_alvo", "Team A"),
                        "tipo_pontuacao": int(args.get("tipo_pontuacao", 2)),
                        "valor_stake": float(args.get("valor_stake", stake)),
                        "confidence": 0.85,  # Modelo decidiu ao chamar a ferramenta
                    }

                if function_name == "registrar_discrepancia":
                    return {
                        "action": "registrar_discrepancia",
                        "time_alvo": args.get("time_alvo", "Team A"),
                        "tipo_pontuacao": int(args.get("tipo_pontuacao", 0)),
                        "confidence": 0.75,  # Conservador
                    }

        return {"action": "none", "confidence": 0.0}
    
    def _query_model(self, model_name: str, prompt: str, stake: float) -> Dict:
        """Query um modelo específico e retorna decisão estruturada."""
        try:
            response = self.models[model_name].generate_content(prompt, timeout=10)
            decision = self._parse_model_response(response, stake)
            decision["model"] = model_name
            decision["timestamp"] = time.time()
            return decision
        except Exception as exc:
            error_text = str(exc).lower()
            # Se é erro de quota/rate limit, pule este modelo
            if any(token in error_text for token in ["429", "quota", "rate limit", "resource exhausted", "not found", "not supported"]):
                return {"action": "skip", "model": model_name, "error": str(exc)}
            # Se é outro erro, log mas não falhe
            return {"action": "error", "model": model_name, "error": str(exc), "confidence": 0.0}
    
    def analyze_ensemble(self, transmission_data, bet_data, memory_context="", stake=100.0) -> Tuple[Dict, List[Dict]]:
        """
        Analyze usando ENSEMBLE VOTING com múltiplos modelos.
        
        Retorna:
            - decisão final (agregada)
            - histórico de votos de cada modelo
        """
        if not self.ensemble_mode or len(self.model_names) < 2:
            # Fallback para single model se ensemble não ativado
            return self.analyze_single(transmission_data, bet_data, memory_context, stake), []
        
        prompt = self._build_decision_prompt(transmission_data, bet_data, memory_context)
        votes: List[Dict] = []
        
        # Query todos os modelos (até 3)
        ensemble_models = self.model_names[:3]  # Máx 3 modelos
        for model_name in ensemble_models:
            decision = self._query_model(model_name, prompt, stake)
            if decision.get("action") not in ["skip", "error"]:
                votes.append(decision)
        
        self.last_ensemble_votes = votes
        
        # Agregar votos
        final_decision = self._aggregate_votes(votes, stake)
        return final_decision, votes
    
    def _aggregate_votes(self, votes: List[Dict], stake: float) -> Dict:
        """Agrega votos de múltiplos modelos para decisão final."""
        if not votes:
            return {"action": "none", "confidence": 0.0, "ensemble_mode": True, "votes_count": 0}
        
        # Contabilizar ações
        action_votes = {}
        for vote in votes:
            action = vote.get("action", "none")
            if action not in action_votes:
                action_votes[action] = []
            action_votes[action].append(vote)
        
        # Encontrar ação com maior consenso
        best_action = max(action_votes.items(), key=lambda x: len(x[1]))
        action_name, action_voters = best_action
        
        # Calcular confidence
        confidence = len(action_voters) / len(votes) if votes else 0.0
        
        # Se consenso fraco, ser conservador
        if confidence < self.confidence_threshold:
            print(f"[ENSEMBLE] Consenso fraco: {len(action_voters)}/{len(votes)} votaram {action_name} (conf={confidence:.2%})")
            return {
                "action": "registrar_discrepancia",  # Fallback conservador
                "confidence": confidence,
                "ensemble_mode": True,
                "votes_count": len(votes),
                "divergence_reason": f"Consenso fraco: {confidence:.2%} < {self.confidence_threshold:.2%}",
                "votes_breakdown": {k: len(v) for k, v in action_votes.items()}
            }
        
        # Montar resposta final
        if action_name == "executar_aposta_live":
            # Usar valores do primeiro votante
            primary_vote = action_voters[0]
            return {
                "action": "executar_aposta_live",
                "time_alvo": primary_vote.get("time_alvo", "Team A"),
                "tipo_pontuacao": primary_vote.get("tipo_pontuacao", 2),
                "valor_stake": primary_vote.get("valor_stake", stake),
                "confidence": confidence,
                "ensemble_mode": True,
                "votes_count": len(votes),
                "votes_for_action": len(action_voters),
                "consensus_strength": confidence,
            }
        elif action_name == "registrar_discrepancia":
            primary_vote = action_voters[0]
            return {
                "action": "registrar_discrepancia",
                "time_alvo": primary_vote.get("time_alvo", "Team A"),
                "tipo_pontuacao": primary_vote.get("tipo_pontuacao", 0),
                "confidence": confidence,
                "ensemble_mode": True,
                "votes_count": len(votes),
                "votes_for_action": len(action_voters),
                "consensus_strength": confidence,
            }
        else:
            return {
                "action": "none",
                "confidence": 0.0,
                "ensemble_mode": True,
                "votes_count": len(votes),
                "votes_breakdown": {k: len(v) for k, v in action_votes.items()}
            }
    
    def analyze_single(self, transmission_data, bet_data, memory_context="", stake=100.0) -> Dict:
        """Fallback: análise com um único modelo (rápida)."""
        prompt = self._build_decision_prompt(transmission_data, bet_data, memory_context)
        
        last_exception = None
        for model_name in self.model_names:
            try:
                response = self.models[model_name].generate_content(prompt, timeout=10)
                self.active_model_name = model_name
                decision = self._parse_model_response(response, stake)
                decision["model"] = model_name
                decision["ensemble_mode"] = False
                return decision
            except Exception as exc:
                last_exception = exc
                error_text = str(exc).lower()
                if any(token in error_text for token in ["429", "quota", "rate limit", "resource exhausted", "not found", "not supported"]):
                    continue
                raise

        return {
            "action": "gemini_error",
            "error": str(last_exception),
            "ensemble_mode": False
        }

    def suggest_action(self, transmission_data, bet_data, stake, memory_context=""):
        """Wrapper compatível com código antigo - usa ensemble se ativado."""
        try:
            if self.ensemble_mode:
                final_decision, votes = self.analyze_ensemble(transmission_data, bet_data, memory_context, stake)
            else:
                final_decision = self.analyze_single(transmission_data, bet_data, memory_context, stake)
            return final_decision
        except Exception as exc:
            return {
                "action": "gemini_error",
                "error": str(exc),
                "ensemble_mode": self.ensemble_mode
            }