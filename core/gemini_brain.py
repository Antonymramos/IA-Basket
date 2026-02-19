

import google.generativeai as genai
from core.tools_registry import registrar_discrepancia, executar_aposta_live

class GeminiBrain:
    def __init__(self, api_key, preferred_model=None):
        genai.configure(api_key=api_key)
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
    
    def analyze(self, transmission_data, bet_data):
        """
        Analyze the data from transmission and bet sources
        Returns the tool call if arbitrage opportunity detected
        """
        prompt = f"""
        Você é um agente de arbitragem esportiva de alta velocidade.
        Receba os dados da transmissão ao vivo e da casa de apostas.
        
        Transmissão: {transmission_data}
        Bet: {bet_data}
        
        Se o placar da transmissão for maior (diferença de 2 ou 3 pontos para um time) 
        e o placar da bet estiver desatualizado, invoque imediatamente a ferramenta 
        de aposta no time que pontuou. Caso contrário, registre a discrepância.
        
        Retorne apenas a chamada da ferramenta, sem textos adicionais.
        """
        
        last_exception = None
        for model_name in self.model_names:
            try:
                response = self.models[model_name].generate_content(prompt)
                self.active_model_name = model_name
                return response
            except Exception as exc:
                last_exception = exc
                error_text = str(exc).lower()
                if "not found" in error_text or "not supported" in error_text:
                    continue
                raise

        raise RuntimeError(f"Nenhum modelo Gemini disponível. Último erro: {last_exception}")

    def suggest_action(self, transmission_data, bet_data, stake):
        try:
            response = self.analyze(transmission_data, bet_data)
        except Exception as exc:
            return {
                "action": "gemini_error",
                "error": str(exc),
            }

        if not response or not response.candidates:
            return {"action": "none"}

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
                    }

                if function_name == "registrar_discrepancia":
                    return {
                        "action": "registrar_discrepancia",
                        "time_alvo": args.get("time_alvo", "Team A"),
                        "tipo_pontuacao": int(args.get("tipo_pontuacao", 0)),
                    }

        return {"action": "none"}