import requests
import time
from src.config.settings import settings
from src.utils.logger import logger

def resolver_recaptcha(site_key: str, site_url: str) -> str:
    """
    Resolve o reCAPTCHA usando a API do CapMonster.

    Parâmetros:
    - site_key: Chave do site (reCAPTCHA).
    - site_url: URL do site onde o reCAPTCHA está presente.

    Retorna:
    - Token do reCAPTCHA resolvido.
    """
    try:
        # Cria a tarefa no CapMonster
        payload = {
            'clientKey': settings.CAPMONSTER_CLIENT_KEY,
            'task': {
                'type': 'NoCaptchaTaskProxyless',
                'websiteKey': site_key,
                'websiteURL': site_url
            }
        }
        response = requests.post(f'{settings.CAPMONSTER_ENDPOINT}/createTask', json=payload)
        response.raise_for_status()

        task_data = response.json()
        if task_data.get('errorId') != 0:
            logger.error(f"Erro ao criar tarefa no CapMonster: {task_data.get('errorDescription')}")
            raise Exception(task_data.get('errorDescription'))

        task_id = task_data.get('taskId')
        logger.info(f"Tarefa criada no CapMonster. Task ID: {task_id}")

        # Obtém o resultado da tarefa
        while True:
            params = {'clientKey': settings.CAPMONSTER_CLIENT_KEY, 'taskId': task_id}
            response = requests.post(f'{settings.CAPMONSTER_ENDPOINT}/getTaskResult', json=params)
            response.raise_for_status()

            result_data = response.json()
            if result_data['status'] == 'ready':
                logger.info("reCAPTCHA resolvido com sucesso.")
                return result_data['solution']['gRecaptchaResponse']
            elif result_data['status'] == 'processing':
                logger.info("Aguardando resolução do reCAPTCHA...")
                time.sleep(5)
            else:
                logger.error(f"Erro ao resolver reCAPTCHA: {result_data.get('errorDescription')}")
                raise Exception(result_data.get('errorDescription'))

    except Exception as e:
        logger.error(f"Erro ao resolver reCAPTCHA: {e}")
        raise e