import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from src.utils.logger import logger
import time
import os

def setup_driver():
    """
    Configura e retorna uma instância do navegador Chrome.

    Retorna:
    - driver: Instância do navegador Chrome.
    """
    try:
        # Configurações do Chrome
        options = uc.ChromeOptions()
        #options.add_argument("--no-sandbox")  # Evita alguns erros de permissão
        #options.add_argument("--disable-dev-shm-usage")  # Evita problemas de memória
        #options.add_argument("--headless")  # Executa em modo headless (sem interface gráfica)

        # Inicializa o navegador
        driver = uc.Chrome(options=options)
        driver.maximize_window()
        #driver.minimize_window()
        return driver

    except Exception as e:
        logger.error(f"Erro ao configurar o navegador: {e}")
        raise e
