
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from src.utils.selenium_handler import setup_driver
from src.utils.capmonster import resolver_recaptcha 
from src.models.requisicao import Requisicao
from src.utils.logger import logger
import time
import os

def coletar_dados_teste(driver, requisicao: Requisicao, site_url: str):
    """

    """
    try:

        # Configura o navegador
        driver = setup_driver()

        # Acessa o site do SEFAZ
        acessar_site_sefaz(driver, site_url)

        # Preenche os campos e consulta a nota fiscal
        preencher_campos(driver, requisicao.access_key, site_url)

        # Coleta os dados da nota fiscal
        dados_nota = coletar_dados_nota(driver)

        return dados_nota
        
    
    except TimeoutException:
        logger.error("Tempo excedido para encontrar a nota fiscal.")
        raise Exception("Tempo excedido para encontrar a nota fiscal.")
    except WebDriverException as e:
        logger.error(f"Erro ao acessar o site do SEF/SP: {e}")
        raise e
    except Exception as e:
        logger.error(f"Erro desconhecido: {e}")
        raise e
    finally:
        if driver:
            driver.quit()  # Fecha o navegador após o processamento
            # Salva o driver para uso posterior
            driver_path = os.path.join(os.getcwd(), "driver.chromedriver")
            os.rename(driver_path, os.path.join(os.getcwd(), f"driver_{time.time()}.chromedriver"))
            raise Exception("Erro ao acessar o site do SEF/SP.")
        # TODO: Implementar o tratamento de erros específicos   

def acessar_site_sefaz(driver, url: str):
    """
    Acessa o site do SEFAZ.

    Parâmetros:
    - driver: Instância do navegador Chrome.
    - url: URL do site do SEFAZ.
    """
    try:
        logger.info(f"Acessando o site do SEFAZ: {url}")
        driver.get(url)
       
    except Exception as e:
        logger.error(f"Erro ao acessar o site do SEFAZ: {e}")
        raise e

def preencher_campos(driver, chave_acesso: str, site_url: str):

    """
    Preenche os campos no site do SEFAZ.
    Parâmetros:
    - driver: Instância do navegador Chrome.
    - chave_acesso: Chave de acesso da nota fiscal.
    - recaptcha_token: Token do reCAPTCHA resolvido.
    """
    try:
        

        logger.info("Preenchendo os campos no site do SEFAZ...")
        
        # Localiza e preenche o campo da chave de acesso
        campo_chave = WebDriverWait(driver, 100).until(
            EC.presence_of_element_located((By.ID, "conteudo_txtChaveAcesso"))
        )
        campo_chave.clear()
        campo_chave.send_keys(chave_acesso)
        
        # Resolve o reCAPTCHA
        # Localizar chave do site (reCAPTCHA)
        site_key = driver.execute_script("return reCaptchaSiteKey;")
        
        # Resolve o reCAPTCHA
        recaptcha_token = resolver_recaptcha(site_key, site_url)

        # Alternar para o iframe que contém o reCAPTCHA
        iframe = driver.find_element(By.CSS_SELECTOR, "iframe[title='reCAPTCHA']")
        driver.switch_to.frame(iframe)
        
        # Localiza e preenche o campo do reCAPTCHA
        campo_recaptcha = driver.find_element(By.ID, "recaptcha-token")
        driver.execute_script(f"arguments[0].value = '{recaptcha_token}';", campo_recaptcha)
        
        # Volta ao conteúdo principal da página
        driver.switch_to.default_content()
        
        # Clica no botão de consulta
        botao_consultar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "conteudo_btnConsultar"))
        )
        botao_consultar.click()
        
        # Aguarda o carregamento da página de resultados
        WebDriverWait(driver, 100).until(
            EC.presence_of_element_located((By.ID, "conteudo_lblNumeroExtrato"))
        )


    except TimeoutException:
        logger.error("Tempo limite excedido ao tentar preencher os campos.")
        raise Exception("Tempo limite excedido ao tentar preencher os campos.")
    except WebDriverException as e:
        logger.error(f"Erro ao acessar o site do SEF/SP: {e}")
        raise e
    except Exception as e:
        logger.error(f"Erro desconhecido: {e}")
        raise e
    finally:
        # TODO: Implementar o tratamento de erros específicos
        pass

  






def coletar_dados_nota(driver) -> dict:
    """
    Coleta os dados da nota fiscal no site do SEFAZ.

    Parâmetros:
    - driver: Instância do navegador Chrome.

    Retorna:
    - Dados da nota fiscal em formato JSON.
    """
    try:
        logger.info("Coletando dados da nota fiscal...")

        # Exemplo de coleta de dados (ajuste conforme a estrutura do site do SEFAZ)
        numero_extrato = driver.find_element(By.ID, "conteudo_lblNumeroExtrato").text
        valor_total = driver.find_element(By.ID, "conteudo_lblValorTotal").text
        emitente = driver.find_element(By.ID, "conteudo_lblEmitente").text

        dados_nota = {
            "numeroExtrato": numero_extrato,
            "valorTotal": valor_total,
            "emitente": emitente
        }

        return dados_nota

    except Exception as e:
        logger.error(f"Erro ao coletar dados da nota fiscal: {e}")
        raise e