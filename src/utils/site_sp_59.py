# modelo 59 modificado
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

def coletar_dados_sp_59(driver, requisicao: Requisicao, site_url: str):
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
        campo_chave = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "conteudo_txtChaveAcesso"))
        )
        driver.execute_script("arguments[0].value = arguments[1];", campo_chave, chave_acesso)

        # Localizar chave do site (reCAPTCHA)
        site_key = driver.execute_script("return reCaptchaSiteKey;")
        
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

            

        logger.info("Verificando se o botão de detalhes está desabilitado...")
        botao_detalhes = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='conteudo_btnDetalhe']"))
        )
        botao_detalhes.click()

        logger.info("Verificando se o conteudo de detalhes foi carregado corretamente...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='conteudo_tabCfe']"))
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

        # Extrair dados do emitente
        emitente = extrair_dados_emitente(driver)
        
        # Extrair dados dos produtos
        produtos = extrair_dados_produtos(driver)
        
        

        # Extrair dados do destinatario
        botao_tabDestinatario = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='conteudo_tabDestinatario']"))
        )
        botao_tabDestinatario.click()
        cpf = getXpath(driver, smallXpath("Dados do Destinatário", "CNPJ / CPF"))
        dadosDoDestinatario = DadosDoDestinatario(
            cpf=tratarTexto(cpf)
        )
        
        # Extrair formas de pagamento
        formas_pagamento = extrair_formas_pagamento(driver)

        # Extrair dados gerais da NF-e
        chaveDeAcesso = getXpath(driver, "//*[@id='conteudo_lblChaveAcesso']")
        numero_extrato = getXpath(driver, "//*[@id='conteudo_lblNumeroCfe']")
        
        data_emissao = getXpath(driver, "//*[@id='conteudo_lblDataEmissao']", 'N')
        dataSaidaEntrada = ''#driver.find_element(By.XPATH, "//legend[text() = 'Dados da NF-e']/..//label[contains(.,'Data Saída/Entrada')]/../span").text
        modelo = '59' #driver.find_element(By.XPATH, smallXpath("Dados da NF-e", "Modelo")).text
        serie = '0' #driver.find_element(By.XPATH, smallXpath("Dados da NF-e", "Série")).text
        valor_total = getXpath(driver, smallXpath("Totais", "Valor Total do CF-e"))

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
    # //legend[text() = 'Emitente']/..//span[text() = 'Nome / Razão Social:']/../../span
    #return f"//legend[text() = '{legend}']/..//span[text() = '{label}:']/../../span" 
    return f"//legend[text() = '{legend}']/..//span[contains(.,'{label}:')]/../../span"

def tratarTexto(texto: str):
    texto = texto.replace('\n','').replace('\r','').replace('\t','').replace('  ',' ').strip().lstrip().rstrip().replace('.','').replace(',','.').replace('/','').replace('-','').replace('Não Informado','').replace("X\n","").replace("X\\n","")
    return texto
def getXpath(elemento, ElementoXPATH, tratar = 'S'):
    stringElemento = ''
    try:
        #logger.info(f"Buscando o elemento {elemento} pelo XPath {ElementoXPATH}...")
        stringElemento = elemento.find_element(By.XPATH, ElementoXPATH).text
    except TimeoutException:
        logger.error("Tempo limite excedido ao tentar buscar o elemento pelo XPath.")
    except Exception as e:
        logger.error(f"Erro ao buscar o elemento {elemento} pelo XPath {ElementoXPATH}: {e}")
    finally:
        if (tratar=='S'):
            return tratarTexto(stringElemento)
        else:
            return stringElemento

def extrair_dados_emitente(driver):
    try:
        logger.info("Extraindo dados do emitente...")

        botao_detalhes = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='conteudo_tabEmitente']"))
        )
        botao_detalhes.click()
        emitente_info = getXpath(driver, smallXpath("Dados do Emitente", "Nome / Razão Social"))
        ie = getXpath(driver, smallXpath("Dados do Emitente", "Inscrição Estadual"))
        endereco = getXpath(driver, smallXpath("Dados do Emitente", "Endereço"))
        bairro = getXpath(driver, smallXpath("Dados do Emitente", "Bairro / Distrito"))
        cep = getXpath(driver, smallXpath("Dados do Emitente", "CEP"))
        cnpj = getXpath(driver, smallXpath("Dados do Emitente", "CNPJ"))
        municipio = getXpath(driver, smallXpath("Dados do Emitente", "Município"))
        uf = getXpath(driver, smallXpath("Dados do Emitente", "UF"))
        cnae = '' #driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "CNAE Fiscal")).text
        codigoRegimeTributario = getXpath(driver, smallXpath("Dados do Emitente", "Código do Regime Tributário"))
        inscricaoEstadualDoSubstitutoTributario = getXpath(driver, smallXpath("Dados do Emitente", "Inscrição Estadual do Substituto Tributário"))
        inscricaoMunicipal = getXpath(driver, smallXpath("Dados do Emitente", "Inscrição Municipal"))
        municipioIcms = '' #driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Município da Ocorrência do Fato Gerador do ICMS")).text
        nomeFantasia = getXpath(driver, smallXpath("Dados do Emitente", "Nome Fantasia"))
        pais = '' #driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "País")).text.split("-")[1]
        telefone = '' #driver.find_element(By.XPATH, smallXpath("Dados do Emitente", "Telefone")).text
        
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
            codigoRegimeTributario=codigoRegimeTributario,
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
        botao_tabProdutoServico = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='conteudo_tabProdutoServico']"))
        )
        botao_tabProdutoServico.click()
        rows = driver.find_elements(By.XPATH, "//*[@id='conteudo_grvProdutosServicos']/tbody/tr[not(contains(@style, 'background-color:#999999'))]")
        contRows = 0
        #rows_count = len(rows)
        for row in rows:
            codigo = getXpath(driver, f"//span[@id='conteudo_grvProdutosServicos_lblProdutoServicoCodigoProduto_{contRows}']")
            codigoCest = getXpath(driver, f"//span[@id='conteudo_grvProdutosServicos_lblProdutoServicoObservacaoFisco_{contRows}']")
            if 'Cod CEST ' in codigoCest:
                codigoCest = tratarTexto(codigoCest.replace('Cod CEST ',''))
            else:
                codigoCest = ''
            
            descricao = getXpath(driver, f"//span[@id='conteudo_grvProdutosServicos_lblProdutoServicoDesc_{contRows}']")
            quantidade = getXpath(driver, f"//span[@id='conteudo_grvProdutosServicos_lblProdutoServicoQtd_{contRows}']")
            unidade = getXpath(driver, f"//span[@id='conteudo_grvProdutosServicos_lblProdutoServicoUnit_{contRows}']")
            valorStr = getXpath(driver, f"//span[@id='conteudo_grvProdutosServicos_lblProdutoServicoIcmsValorLiquidoItem_{contRows}']")
            codigoEanComercial = '' #row.find_element(By.XPATH, f".//span[@id='conteudo_grvProdutosServicos_lblProdutoServicoCodigoProduto_{contRows}']").text
            codigoEanTributavel = '' #row.find_element(By.XPATH, f".//span[@id='conteudo_grvProdutosServicos_lblProdutoServicoCodigoProduto_{contRows}']").text
            codigoNcm = getXpath(driver, f"//span[@id='conteudo_grvProdutosServicos_lblProdutoServicoNcm_{contRows}']")
            valorDesconto = getXpath(driver, f"//span[@id='conteudo_grvProdutosServicos_lblProdutoServicoValorDesconto_{contRows}']")
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
                contRows = contRows+1
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
        pagamentos = []
        botao_tabTotais = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='conteudo_tabTotais']"))
        )
        botao_tabTotais.click()
        contRows = 0
        # Processa cada linha da tabela de pagamentos
        rows = driver.find_elements(By.XPATH, "//*[@id='conteudo_grvMeiosPagamento']/tbody/tr/td/span/../..")
        for row in rows:
            try:
                logger.info(f"Processando pagamento: {row.text}")
                # Extrai dados do pagamento
                forma = '' #row.find_element(By.XPATH, ".//*[@id='conteudo_grvMeiosPagamento_lblMeiosPagamentoCodigoMeioPagamento_0']").text
                meio = getXpath(driver, f"//*[@id='conteudo_grvMeiosPagamento_lblMeiosPagamentoCodigoMeioPagamento_{contRows}']")
                valorStr = getXpath(driver, f"//*[@id='conteudo_grvMeiosPagamento_lblMeiosPagamentoValorMeioPagamento_{contRows}']")
                valor = float(valorStr)
                trocoStr = getXpath(row,  "//span[text() = 'Valor do Troco:']/../../span")
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
        contRows=contRows+1
        return pagamentos
    except Exception as e:
        logger.error(f"Erro ao extrair dados das formas de pagamento: {e}")
        raise e