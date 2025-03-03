
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from src.utils.selenium_handler import setup_driver
from src.utils.capmonster import resolver_recaptcha 
from src.models.requisicao import Requisicao
from src.models.dados_notas_retorno import DadosDoEmitente, ProdutoEServico, FormaDePagamento, DadosDaNfe, DadosNotaFiscal
from src.utils.logger import logger
import time
import os

def coletar_dados_rj(driver, requisicao: Requisicao, site_url: str):
    """
    Coleta os dados da nota fiscal no site do SEF/SP.

    Parâmetros:
    - driver: Instância do navegador Chrome.
    - requisicao: Requisição a ser processada.
    - site_url: URL do site do SEF/SP.
    """
    try:

        # Configura o navegador
        #driver = setup_driver()

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
        #time.sleep(1)  # Aguarda o carregamento da página
        btn_avancadas = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "details-button"))
        )
        btn_avancadas.click()
        
        # Localiza e clica no botão de consulta
        botao_consultar = driver.find_element(By.ID, "proceed-link")
        botao_consultar.click()
        driver.execute_script("document.body.style.animation = 'none';")
       
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
        campo_chave = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "conteudo_txtChaveAcesso"))
        )
        driver.execute_script("arguments[0].value = arguments[1];", campo_chave, chave_acesso)

        # Localizar chave do site (reCAPTCHA)
        site_key = driver.execute_script("return reCaptchaSiteKey;")
        
        # Resolve o reCAPTCHA
        recaptcha_token = resolver_recaptcha(site_key, site_url)

        # Localiza e preenche o campo do reCAPTCHA
        driver.execute_script(f"document.getElementById('g-recaptcha-response').innerHTML = '{recaptcha_token}'")

        # Verificar se o botão de consulta ainda está desabilitado
        logger.info("Verificando se o botão de consulta está desabilitado...")
        botao_consultar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "conteudo_btnConsultar"))
        )
        if botao_consultar.get_attribute("disabled") == "true":
            logger.info("Botão de consulta ainda está desabilitado. Tentando habilitá-lo...")
            driver.execute_script("arguments[0].removeAttribute('disabled');", botao_consultar)
            driver.execute_script("arguments[0].classList.remove('aspNetDisabled');", botao_consultar)

        # Clicar no botão de consulta
        logger.info("Clicando no botão de consulta...")
        botao_consultar.click()
        Erro_da_site = ""
        try:
            Erro_da_site = driver.find_element(By.ID, "dialog-modal").text
            if "Este número de chave não foi encontrado na base de dados do SEFAZ." in Erro_da_site:
                logger.error("Chave de acesso inválida ou não encontrada na base de dados do SEFAZ.")
                raise Exception("Chave de acesso inválida ou não encontrada na base de dados do SEFAZ.")
            else:
                logger.error(f"Erro no site: {Erro_da_site}")
                raise Exception(f"Erro no site: {Erro_da_site}")
        except Exception as e:
            if Erro_da_site != "" :
                raise Exception(e)

            
        # Aguarda o carregamento da página de resultados
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='conteudo_lblNumeroCfe']"))
        )
        logger.info("Dados da nota fiscal acessados com sucesso")



    except TimeoutException:
        logger.error("Tempo limite excedido ao tentar preencher os campos.")
        raise
    except Exception as e:
        logger.error(f"Erro ao preencher os campos: {e}")
        raise e

def coletar_dados_nota(driver) -> dict:
    try:
        logger.info("Coletando dados da nota fiscal...")
        
        # Extrair dados do emitente
        emitente = extrair_dados_emitente(driver)
        
        # Extrair dados dos produtos
        produtos = extrair_dados_produtos(driver)
        
        # Extrair formas de pagamento
        formas_pagamento = extrair_formas_pagamento(driver)
        
        # Extrair dados gerais da NF-e
        IdCfe = driver.find_element(By.ID, "conteudo_lblIdCfe").text.replace(" ", "")
        numero_extrato = driver.find_element(By.ID, "conteudo_lblNumeroCfe").text
        valor_total = float(driver.find_element(By.ID, "conteudo_lblTotal").text.replace(",", "."))
        data_emissao = driver.find_element(By.ID, "conteudo_lblDataEmissao").text
        
        dados_nfe = DadosDaNfe(
            dataDeEmissao=data_emissao,
            numero=int(numero_extrato),
            valorTotal=valor_total
        )
        
        # Montar o objeto final
        nota_fiscal = DadosNotaFiscal(
            chaveDeAcesso=IdCfe,
            dadosDaNfe=dados_nfe,
            dadosDoEmitente=emitente,
            dadosDosProdutosEServicos=produtos,
            formasDePagamento=formas_pagamento
        )
        
        # Converter para JSON
        return nota_fiscal.__dict__
    
    except Exception as e:
        logger.error(f"Erro ao coletar dados da nota fiscal: {e}")
        raise e

def extrair_dados_emitente(driver):
    try:
        emitente_info = driver.find_element(By.ID, "conteudo_lblNomeEmitente").text
        endereco = driver.find_element(By.ID, "conteudo_lblEnderecoEmintente").text
        bairro = driver.find_element(By.ID, "conteudo_lblBairroEmitente").text
        cep = driver.find_element(By.ID, "conteudo_lblCepEmitente").text
        cnpj = driver.find_element(By.ID, "conteudo_lblCnpjEmitente").text
        ie = driver.find_element(By.ID, "conteudo_lblIeEmitente").text
        municipio = driver.find_element(By.ID, "conteudo_lblMunicipioEmitente").text
        uf = "SP"

        return DadosDoEmitente(
            bairroDistrito=bairro,
            cep=cep,
            cnpj=cnpj,
            endereco=endereco,
            inscricaoEstadual=ie,
            municipio=municipio,
            nomeRazaoSocial=emitente_info,
            uf=uf
        )
    except Exception as e:
        logger.error(f"Erro ao extrair dados do emitente: {e}")
        raise e

def extrair_dados_produtos(driver):
    """
    Extrai dados dos produtos da NF-e.
    Retorna uma lista de objetos ProdutoEServico.

    Parâmetros:
    - driver: Instância do navegador Chrome.

    Retorno:
    Lista de objetos ProdutoEServico.
    """
    try:

        logger.info("Extraindo dados dos produtos...")
        produtos = []
        rows = driver.find_elements(By.XPATH, "//*[@id='tableItens']/tbody/tr")
        for row in rows:
            legenda = row.find_element(By.XPATH, "./td[1]").text
            codigo = row.find_element(By.XPATH, "./td[2]").text
            if codigo != "" and legenda !="Desconto:":
                descricao = row.find_element(By.XPATH, "./td[3]").text
                quantidade = float(row.find_element(By.XPATH, "./td[4]").text.replace(",", "."))
                unidade = row.find_element(By.XPATH, "./td[5]").text
                valorStr = row.find_element(By.XPATH, "./td[6]").text.replace(",", ".").replace("X\n","").replace("X\\n","")
                valor = 0
                if valorStr != "":
                    valor = float(valorStr)
                
                
                    produto = ProdutoEServico(
                        codigo=codigo,
                        descricao=descricao,
                        quantidade=quantidade,
                        unidadeComercial=unidade,
                        valor=valor
                    )
                    produtos.append(produto)
        return produtos
    except Exception as e:
        logger.error(f"Erro ao extrair dados dos produtos: {e}")
        raise e

def extrair_formas_pagamento(driver):
    """
    Extrai dados das formas de pagamento da NF-e.
    Retorna uma lista de objetos FormaDePagamento.
    Parâmetros:
    - driver: Instância do navegador Chrome.
    Retorno:
    Lista de objetos FormaDePagamento.
    """
    try:
        logger.info("Extraindo dados das formas de pagamento...")
        meio = driver.find_element(By.XPATH, "//*[@id='conteudo_DivMeiosPagamento']/div[1]/div[1]").text
        valor = float(driver.find_element(By.XPATH, "//*[@id='conteudo_DivMeiosPagamento']/div[1]/div[2]").text.replace(",", "."))
        troco = float(driver.find_element(By.XPATH, "//*[@id='conteudo_DivMeiosPagamento']/div[2]/div[2]").text.split(" ")[-1].replace(",", "."))
        
        return [FormaDePagamento(meio=meio, valor=valor, valorTroco=troco)]
    except Exception as e:
        logger.error(f"Erro ao extrair dados das formas de pagamento: {e}")
        raise e