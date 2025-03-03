
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from src.utils.selenium_handler import setup_driver
from src.utils.capmonster import resolver_recaptcha 
from src.models.requisicao import Requisicao
from src.models.dados_notas_retorno import DadosDoEmitente, ProdutoEServico, FormaDePagamento, DadosDaNfe, DadosNotaFiscal, DadosDoDestinatario
from src.utils.logger import logger
import time
import os

def coletar_dados_sp_65(driver, requisicao: Requisicao, site_url: str):
    """
    Coleta os dados da nota fiscal no site do SEF/SP.

    Parâmetros:
    - driver: Instância do navegador Chrome.
    - requisicao: Requisição a ser processada.
    - site_url: URL do site do SEF/SP.
    """
    try:
        inicio = time.time()  # Tempo inicial
        # Configura o navegador
        #driver = setup_driver()

        # Acessa o site do SEFAZ
        acessar_site_sefaz(driver, site_url)

        # Preenche os campos e consulta a nota fiscal
        preencher_campos(driver, requisicao.access_key, site_url, requisicao)

        # Coleta os dados da nota fiscal
        inicio = time.time()  # Tempo inicial
        dados_nota = coletar_dados_nota(driver, inicio, requisicao)
        fim = time.time()     # Tempo final
        tempo_coletar_dados_nota = (fim - inicio) * 1000
        requisicao.tempo_coleta_dados = tempo_coletar_dados_nota
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
        btn_avancadas = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "ConteudoPrincipal"))
        )

    except Exception as e:
        logger.error(f"Erro ao acessar o site do SEFAZ: {e}")
        raise e

def preencher_campos(driver, chave_acesso: str, site_url: str, requisicao: Requisicao):
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
        # campo_chave = WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.ID, "Conteudo_txtChaveAcesso"))
        # )
        # driver.execute_script("arguments[0].value = arguments[1];", campo_chave, chave_acesso)
        driver.execute_script(f"document.getElementById('Conteudo_txtChaveAcesso').value = '{chave_acesso}'")


        # Localizar chave do site (reCAPTCHA)
        #site_key = driver.execute_script("return reCaptchaSiteKey;")
        recaptcha_element = driver.find_element(By.CSS_SELECTOR, 'div.g-recaptcha')
        site_key = recaptcha_element.get_attribute('data-sitekey')
        

        inicio = time.time()  # Tempo inicial
        # Resolve o reCAPTCHA
        recaptcha_token = resolver_recaptcha(site_key, site_url)
        fim = time.time()     # Tempo final
        TempoDeResolver_recaptcha = (fim - inicio) * 1000
        requisicao.tempo_resolucao_captcha = TempoDeResolver_recaptcha


        # Localiza e preenche o campo do reCAPTCHA
        driver.execute_script(f"document.getElementById('g-recaptcha-response').innerHTML = '{recaptcha_token}'")

        # Verificar se o botão de consulta ainda está desabilitado
        logger.info("Verificando se o botão de consulta está desabilitado...")
        botao_consultar = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "Conteudo_btnConsultaResumida"))
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
            Erro_da_site = driver.find_element(By.ID, "spnErroMaster").text
            if "Chave de Acesso inválida. Verifique a digitação das informações." in Erro_da_site:
                logger.error("Chave de acesso inválida ou não encontrada na base de dados do SEFAZ.")
                raise Exception("Chave de acesso inválida ou não encontrada na base de dados do SEFAZ.")
            else:
                logger.error(f"Erro no site: {Erro_da_site}")
                raise Exception(f"Erro no site: {Erro_da_site}")
        except Exception as e:
            if Erro_da_site != "" :
                raise Exception(e)

        driver.execute_script("javascript:__doPostBack('btnVisualizarAbas','')")

        # Aguarda o carregamento da página de resultados
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='pnlDadosNFCeId']"))
        )
        logger.info("Dados da nota fiscal acessados com sucesso")



    except TimeoutException:
        logger.error("Tempo limite excedido ao tentar preencher os campos.")
        raise
    except Exception as e:
        logger.error(f"Erro ao preencher os campos: {e}")
        raise e

def coletar_dados_nota(driver, inicio, requisicao: Requisicao) -> dict:
    try:
        logger.info("Coletando dados da nota fiscal...")
        try:
            driver.execute_script("document.getElementById('Conteudo_pnlNFe_tabEmitente').removeAttribute('style');")
            driver.execute_script("document.getElementById('Conteudo_pnlNFe_tabDestinatario').removeAttribute('style');")
            driver.execute_script("document.getElementById('Conteudo_pnlNFe_tabProdServ').removeAttribute('style');")
            driver.execute_script("document.getElementById('Conteudo_pnlNFe_tabTotais').removeAttribute('style');")
            driver.execute_script("document.getElementById('Conteudo_pnlNFe_tabTransporte').removeAttribute('style');")
            driver.execute_script("document.getElementById('Conteudo_pnlNFe_tabCobranca').removeAttribute('style');")
            driver.execute_script("document.getElementById('Conteudo_pnlNFe_tabInfAdic').removeAttribute('style');")
            driver.execute_script("document.getElementById('Conteudo_pnlNFe_tabAvulsa').removeAttribute('style');")
            
        except Exception as e:
            logger.error(f"Erro ao remover estilos das abas: {e}")
            raise e


        # Extrair dados do emitente
        emitente = extrair_dados_emitente(driver)
        
        # Extrair dados dos produtos
        produtos = extrair_dados_produtos(driver)
        
        # Extrair formas de pagamento
        formas_pagamento = extrair_formas_pagamento(driver)

        # Extrair dados do destinatario
        cpf = driver.find_element(By.XPATH, "//legend[text() = 'Dados do Destinatário']/..//label[contains(.,'CPF')]/../span").text
        dadosDoDestinatario = DadosDoDestinatario(
            cpf=cpf.replace('.', '').replace('-', '')
        )
        
        # Extrair dados gerais da NF-e
        chaveDeAcesso = driver.find_element(By.XPATH, "//*[@id='pnlDadosNFCeId']/table/tbody/tr[2]/td[1]").text.replace(" ", "").replace(".", "").replace("/", "").replace("-", "")
        numero_extrato = driver.find_element(By.XPATH, smallXpath("Dados da NF-e", "Número")).text.replace(".", "")
        valor_total = driver.find_element(By.XPATH, smallXpath("Totais", "Valor Total da NFe")).text.replace(".", "").replace(",", ".")
        data_emissao = driver.find_element(By.XPATH, smallXpath("Dados da NF-e", "Data de Emissão")).text
        dataSaidaEntrada = driver.find_element(By.XPATH, "//legend[text() = 'Dados da NF-e']/..//label[contains(.,'Data Saída/Entrada')]/../span").text
        modelo = driver.find_element(By.XPATH, smallXpath("Dados da NF-e", "Modelo")).text
        serie = driver.find_element(By.XPATH, smallXpath("Dados da NF-e", "Série")).text

        dados_nfe = DadosDaNfe(
            dataDeEmissao=data_emissao,
            dataSaidaEntrada=dataSaidaEntrada,
            modelo=int(modelo),
            numero=int(numero_extrato),
            serie=int(serie),
            valorTotal=float(valor_total)
        )

        fim = time.time()     # Tempo final
        # Calculando o tempo em milissegundos
        
        tempo_execucao_ms = (fim - inicio) * 1000
        TempoDeCaptura = tempo_execucao_ms
        requisicao.tempo_acesso_sefaz = tempo_execucao_ms
        # Montar o objeto final
        nota_fiscal = DadosNotaFiscal(
            chaveDeAcesso=chaveDeAcesso,
            TempoDeCaptura=TempoDeCaptura,
            dadosDaNfe=dados_nfe,
            dadosDoDestinatario=dadosDoDestinatario,
            dadosDoEmitente=emitente,
            dadosDosProdutosEServicos=produtos,
            formasDePagamento=formas_pagamento
        )
        
        # Converter para JSON
        return nota_fiscal.__dict__
    
    except Exception as e:
        logger.error(f"Erro ao coletar dados da nota fiscal: {e}")
        raise e

def smallXpath(legend: str, label: str):
    # //legend[text() = 'Totais']/..//label[text() = 'Valor Total da NFe']/../span
    return f"//legend[text() = '{legend}']/..//label[text() = '{label}']/../span"

def extrair_dados_emitente(driver):
    try:
        emitente_info = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Nome / Razão Social")).text
        ie = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Inscrição Estadual")).text
        endereco = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Endereço")).text.replace('-','').lstrip().rstrip()
        bairro = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Bairro / Distrito")).text
        cep = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "CEP")).text
        cnpj = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "CNPJ")).text.replace('-','').replace('.','').replace('/','')
        municipio = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Município")).text.split("-")[1]
        uf = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "UF")).text
        cnae = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "CNAE Fiscal")).text
        codigoRegimeTributario = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Código de Regime Tributário")).text
        inscricaoEstadualDoSubstitutoTributario = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Inscrição Estadual do Substituto Tributário")).text
        inscricaoMunicipal = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Inscrição Municipal")).text
        municipioIcms = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Município da Ocorrência do Fato Gerador do ICMS")).text
        nomeFantasia = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Nome Fantasia")).text
        pais = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "País")).text.split("-")[1]
        telefone = driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Telefone")).text
        
        return DadosDoEmitente(
            bairroDistrito=bairro,
            cep=cep,
            cnpj=cnpj,
            endereco=endereco,
            inscricaoEstadual=ie,
            municipio=municipio.lstrip(),
            nomeRazaoSocial=emitente_info,
            uf=uf,
            cnae=cnae,
            codigoRegimeTributario=codigoRegimeTributario.split('-')[1].lstrip(),
            inscricaoEstadualDoSubstitutoTributario=inscricaoEstadualDoSubstitutoTributario,
            inscricaoMunicipal=inscricaoMunicipal,
            municipioIcms=municipioIcms,
            nomeFantasia=nomeFantasia,
            pais=pais.lstrip(),
            telefone=telefone
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
        rows = driver.find_elements(By.XPATH, "//*[@id='Prod']/fieldset/div/table[@class='toggle box']")
        contar_itens = 0
        for row in rows:
            
            rowsDetalhes = driver.find_elements(By.XPATH, "//*[@id='Prod']/fieldset/div/table[@class='toggable box']")[contar_itens]
            driver.execute_script("arguments[0].removeAttribute('style');", rowsDetalhes)
            codigo = WebDriverWait(rowsDetalhes, 10).until(
                EC.presence_of_element_located((By.XPATH, ".//label[text() = 'Código do Produto']/../span"))
            ).text
            codigoCest = rowsDetalhes.find_element(By.XPATH, ".//label[text() = 'Código CEST']/../span").text
            descricao = row.find_element(By.XPATH, "./tbody/tr/td[@class='fixo-prod-serv-descricao']/span").text
            quantidade = row.find_element(By.XPATH, "./tbody/tr/td[@class='fixo-prod-serv-qtd']/span").text.replace(".", "").replace(",", ".")
            unidade = row.find_element(By.XPATH, "./tbody/tr/td[@class='fixo-prod-serv-uc']/span").text
            valorStr = row.find_element(By.XPATH, "./tbody/tr/td[@class='fixo-prod-serv-vb']/span").text.replace(".", "").replace(",", ".").replace("X\n","").replace("X\\n","")
            codigoEanComercial = rowsDetalhes.find_element(By.XPATH, ".//label[text() = 'Código EAN Comercial']/../span").text
            codigoEanTributavel = rowsDetalhes.find_element(By.XPATH, ".//label[text() = 'Código EAN Tributável']/../span").text
            codigoNcm = rowsDetalhes.find_element(By.XPATH, ".//label[text() = 'Código NCM']/../span").text
            valorDesconto = rowsDetalhes.find_element(By.XPATH, ".//label[text() = 'Valor do Desconto']/../span").text.replace(".", "").replace(",", ".").replace("X\n","").replace("X\\n","")
            valor = 0
            if valorDesconto=='':
                valorDesconto = '0'
            if valorStr != "":
                produto = ProdutoEServico(
                    codigo=codigo,
                    codigoCest=codigoCest,
                    codigoEanComercial=codigoEanComercial,
                    codigoEanTributavel=codigoEanTributavel,
                    codigoNcm=codigoNcm,
                    descricao=descricao,
                    quantidade=float(quantidade),
                    unidadeComercial=unidade,
                    valor=float(valorStr),
                    valorDesconto=float(valorDesconto)
                )
                produtos.append(produto)
            contar_itens = contar_itens+1 
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
        pagamentos = []
        trocoObj = driver.find_element(By.XPATH, "//label[contains(.,'Troco')]/../../../../../../../..")
        # Remove a style do troco para ele não ficar oculto
        driver.execute_script("arguments[0].removeAttribute('style');", trocoObj)
        contar_itens = 0

        # Processa cada linha da tabela de pagamentos
        rows = driver.find_elements(By.XPATH, "//*[@id='Cobranca']/fieldset/table[@class='toggle box']")
        for row in rows:
            try:
                logger.info(f"Processando pagamento: {row.text}")
                rowsDetalhes = driver.find_elements(By.XPATH, "//*[@id='Cobranca']/fieldset/table[@class='toggable box']")[contar_itens]
                driver.execute_script("arguments[0].removeAttribute('style');", rowsDetalhes)
                # Extrai dados do pagamento
                forma = row.find_element(By.XPATH, "./tbody/tr/td[1]/span").text
                meio = row.find_element(By.XPATH, "./tbody/tr/td[2]/span").text.split("-")[1].lstrip()
                valorStr = row.find_element(By.XPATH, "./tbody/tr/td[3]/span").text.replace(".", "").replace(",", ".")
                valor = float(valorStr)
                trocoStr = rowsDetalhes.find_element(By.XPATH, ".//label[contains(.,'Troco')]/../../../tr[4]/td/span").text.replace(".", "").replace(",", ".")
                troco = float(trocoStr)
                valor = 0
                # Adiciona o pagamento à lista
                if valorStr != "":
                    valor = float(valorStr)

                    pagamento = FormaDePagamento(
                        forma=forma,
                        meio=meio,
                        valor=valor,
                        valorTroco=troco
                    )
                    pagamentos.append(pagamento)

            except Exception as e:
                logger.error(f"Erro ao processar pagamento: {e}")
        return pagamentos
    except Exception as e:
        logger.error(f"Erro ao extrair dados das formas de pagamento: {e}")
        raise e