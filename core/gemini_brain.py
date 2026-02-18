

import google.generativeai as genai
from core.tools_registry import registrar_discrepancia, executar_aposta_live

class GeminiBrain:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=[registrar_discrepancia, executar_aposta_live]
        )
    
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
        
        response = self.model.generate_content(prompt)
        return response