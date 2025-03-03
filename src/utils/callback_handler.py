import requests
from src.utils.logger import logger

def enviar_callback(callback_url: str, dados_nota: dict):
    """
    Envia os dados processados para o URL de callback.

    Parâmetros:
    - callback_url: URL de callback para onde os dados serão enviados.
    - dados_nota: Dados da nota fiscal em formato JSON.
    """
    try:
        logger.info(f"Enviando callback para {callback_url}...")

        # Envia os dados para o callback URL
        response = requests.post(callback_url, json=dados_nota)
        
        # Verifica se o envio foi bem-sucedido
        if response.status_code == 200:
            logger.info("Callback enviado com sucesso.")
        else:
            logger.error(f"Erro ao enviar callback: {response.status_code} - {response.text}")
            raise Exception(f"Erro ao enviar callback: {response.status_code} - {response.text}")

    except Exception as e:
        logger.error(f"Erro ao enviar callback: {e}")
        raise e