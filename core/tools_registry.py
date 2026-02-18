#!/usr/bin/env python3
"""
Tools Registry - Function definitions for Gemini function calling
"""

def registrar_discrepancia(time_alvo: str, tipo_pontuacao: int, transmissao_score: dict, bet_score: dict):
    """
    Registra uma discrepância detectada entre transmissão e bet
    """
    print(f"Discrepância registrada: {time_alvo} pontuou {tipo_pontuacao} pontos")
    print(f"Transmissão: {transmissao_score}")
    print(f"Bet: {bet_score}")
    # Aqui poderia salvar em um banco de dados ou log
    return {"status": "registrado"}

def executar_aposta_live(time_alvo: str, tipo_pontuacao: int, valor_stake: float):
    """
    Executa uma aposta ao vivo baseada na discrepância detectada
    """
    print(f"Executando aposta: {time_alvo}, {tipo_pontuacao} pontos, stake: {valor_stake}")
    # Chamar o executor de aposta
    from action_layer.bet_executor import BetExecutor
    executor = BetExecutor()
    return executor.execute_bet(time_alvo, tipo_pontuacao, valor_stake)