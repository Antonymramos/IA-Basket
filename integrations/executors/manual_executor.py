"""Manual Executor - Manual betting via web UI."""

from typing import Dict


class ManualExecutor:
    """Executor que mostra recomendação e deixa usuário clicar manualmente."""

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize manual executor.
        
        Args:
            webhook_url: URL de webhook pra notificações (Telegram, Discord, etc)
        """
        self.webhook_url = webhook_url

    async def notify_recommendation(self, oracle_data: Dict) -> bool:
        """
        Envia notificação com recomendação.
        
        Args:
            oracle_data: JSON completo do Oracle
        
        Returns:
            True se notificação foi enviada
        
        TODO:
            - Formatar mensagem clara
            - Enviar pra Telegram/Discord/Email
            - Incluir link com recomendação
        """
        # Exemplo: Telegram
        # message = f"""
        # 🚨 ALERTA Oracle NBA
        # Erro: {oracle_data['diagnostico_saas']['tipo']}
        # Severidade: {oracle_data['diagnostico_saas']['severidade']}
        # Ação recomendada: {oracle_data['comando_cliente']['urgencia']}
        # """
        # await send_telegram(self.webhook_url, message)
        
        return False

    async def get_approval(self, oracle_data: Dict) -> bool:
        """
        Aguarda aprovação manual do usuário.
        
        Args:
            oracle_data: JSON completo
        
        Returns:
            True se usuário aprovou, False caso contrário
        
        TODO:
            - Criar endpoint POST /api/approve
            - Aguardar resposta do cliente
            - Timeout de 5min
        """
        # Placeholder
        return False


if __name__ == "__main__":
    print("🟢 Manual Executor")
    print("   Aguardando implementação de notificações...")
    print("   Configure webhook_url no .env")
