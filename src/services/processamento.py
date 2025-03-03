from sqlalchemy.orm import Session  # Adicione esta linha
import time
import boto3
from src.models.requisicao import Requisicao
from src.models.dados_notas import DadosNotas
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.sqs_handler import get_sqs_client
import json  
from src.utils.selenium_handler import setup_driver
from src.utils.site_sp_59 import coletar_dados_sp_59  
from src.utils.site_sp_65 import coletar_dados_sp_65
from src.utils.site_rj import coletar_dados_rj
from src.utils.site_teste import coletar_dados_teste  
from src.utils.callback_handler import enviar_callback

def processar_fila_sqs(db: Session):
    """
    Monitora a fila SQS e processa cada requisição.
    """
    sqs = get_sqs_client()
    queue_url = settings.AWS_SQS_QUEUE_URL

    try:
        # Verifica se a fila existe
        sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["All"])
    except Exception as e:
        logger.error(f"Erro ao acessar a fila SQS: {e}")
        return

    while True:
        try:
            # Recebe mensagens da fila SQS
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20
            )

            if "Messages" in response:
                for message in response["Messages"]:
                    # Processa a mensagem
                    processar_mensagem(db, message)
                    # Remove a mensagem da fila após o processamento
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message["ReceiptHandle"]
                    )
            else:
                logger.info("Nenhuma mensagem na fila SQS. Aguardando...")

        except Exception as e:
            logger.error(f"Erro ao processar a fila SQS: {e}")
            time.sleep(10)  # Aguarda 10 segundos antes de tentar novamente

def processar_mensagem(db: Session, message: dict):
    """
    Processa uma mensagem da fila SQS.

    Parâmetros:
    - db: Sessão do banco de dados.
    - message: Mensagem recebida da fila SQS.
    """
    try:
        inicio = time.time()  # Tempo inicial
        # Converte o corpo da mensagem de string JSON para um dicionário Python
        body = json.loads(message["Body"])
        requisicao_id = int(body["requisicao_id"])

        # Obtém a requisição do banco de dados
        requisicao = db.query(Requisicao).filter(Requisicao.id == requisicao_id).first()
        if not requisicao:
            logger.error(f"Requisição {requisicao_id} não encontrada no banco de dados.")
            return

        # Atualiza o status da requisição para "Processando"
        requisicao.status = "Processando"
        db.commit()
        dados_nota = {}

        # Coleta os dados da nota fiscal
        # Tenta coletar os dados da nota fiscal até 3 tentativas
        tentativas = 0
        maximoDeTentativas = 5
        while tentativas < maximoDeTentativas:
            tentativas = tentativas + 1
            try:
                dados_nota = coletar_dados_nota(requisicao)
                break
            except Exception as e:
                logger.error(f"Erro ao coletar dados da requisição {requisicao_id}: {e}")
                if tentativas < maximoDeTentativas:
                    continue
                else:
                    raise Exception(f"Número de tentativas excedido para coletar dados da requisição. {e}")
            

        # Serializa os dados da nota fiscal
        dados_nota_serializavel = serializar_objeto(dados_nota)
        
        # Salva os dados no banco de dados
        db_dados_notas = DadosNotas(
            requisicao_id=requisicao.id,
            dados=dados_nota_serializavel
        )
        db.add(db_dados_notas)
        db.commit()

        fim = time.time()     # Tempo final
        tempo_execucao_ms = (fim - inicio) * 1000
        TempoDeprocessamento= tempo_execucao_ms
        # Atualiza o status da requisição para "Concluído"
        requisicao.tempo_total_processamento = TempoDeprocessamento
        requisicao.contador_tentativas = tentativas
        requisicao.status = "Concluído"
        db.commit()

        # Adiciona a chave de acesso aos dados da nota fiscal
        dados_nota["chaveDeAcesso"] = requisicao.access_key

        # Envia o callback
        #if requisicao.callback_url != '':
            #enviar_callback(requisicao.callback_url, dados_nota_serializavel)


    except Exception as e:
        logger.error(f"Erro ao processar a mensagem: {e}")
        # Atualiza o status da requisição para "Erro"
        if requisicao:
            requisicao.status = "Erro"
            requisicao.erro = str(e)
            db.commit()
    finally:
        db.close()  # Fecha a sessão após o processamento

def coletar_dados_nota(requisicao: Requisicao) -> dict:
    """
    Coleta os dados da nota fiscal no site do SEFAZ.

    Parâmetros:
    - requisicao: Requisição a ser processada.

    Retorna:
    - Dados da nota fiscal em formato JSON.
    """
    driver = None
    try:
        logger.info(f"Coletando dados da nota fiscal para a requisição {requisicao.id}...")


        site_url_sp_59 = "https://satsp.fazenda.sp.gov.br/COMSAT/Public/ConsultaPublica/ConsultaPublicaCfe.aspx"
        site_url_sp_65 = "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica"
        site_url_rj = "https://consultadfe.fazenda.rj.gov.br/consultaDFe/paginas/consultaChaveAcesso.faces"
        site_url_teste = "https://2captcha.com/pt/demo/recaptcha-v2-callback"
        estado = requisicao.estado
        driver = setup_driver()  # Inicializa o driver do Selenium
        # Configura os timeouts
        driver.set_page_load_timeout(30)  # Timeout para carregamento de página
        driver.implicitly_wait(2)  # Timeout implícito para busca de elementos
        driver.set_script_timeout(20)  # Timeout para execução de scripts
        #requisicao.access_key = '35240107063149000169650010000010351999099759'
        # Coleta os dados da nota fiscal
        match estado:
            case 'RJ':
                dados_nota = coletar_dados_rj(driver, requisicao, site_url_rj)
            case 'SP':
                tipo_nota = identificar_tipo_documento(requisicao.access_key)
                if tipo_nota == 'CF-e SAT':
                    dados_nota = coletar_dados_sp_59(driver, requisicao, site_url_sp_59)
                elif tipo_nota == 'NFC-e':
                    dados_nota = coletar_dados_sp_65(driver, requisicao, site_url_sp_65)
                elif tipo_nota == 'NF-e':
                    raise Exception("Tipo de nota indisponivel")
                else:
                    raise Exception("Tipo de nota desconhecida")
            case 'TT':
                return {} #dados_nota = coletar_dados_teste(driver, requisicao, site_url_teste)
        return dados_nota

    except Exception as e:
        logger.error(f"Erro ao coletar dados da nota fiscal: {e}")
        raise e

    finally:
        if driver:
            driver.quit()  # Fecha o navegador após o processamento

def serializar_objeto(obj):
    """
    Converte um objeto personalizado em um dicionário serializável.
    
    Parâmetros:
    - obj: Objeto a ser serializado.
    
    Retorna:
    - Dicionário serializável do objeto.
    """
    # Tenta converter o objeto em um dicionário usando o método to_dict()
    # Caso o método não seja disponível, tenta converter os atributos do objeto em um dicionário
    # Caso o objeto seja um dicionário, tenta converter os valores dos seus itens em um dicionário
    # Caso o objeto seja uma lista ou tupla, tenta converter cada item em um dicionário
    # Caso o objeto seja um tipo primitivo ou None, simplesmente retorna o valor
    # Caso o objeto seja um outro tipo de objeto, tenta converter seus atributos em um dicionário
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    elif isinstance(obj, dict):
        return {key: serializar_objeto(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serializar_objeto(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    else:
        # Se o objeto não for serializável, tenta converter seus atributos em um dicionário
        return {key: serializar_objeto(value) for key, value in obj.__dict__.items()}

def identificar_tipo_documento(chave):
    """
    Identifica o tipo de documento fiscal a partir da chave de acesso de 44 dígitos.

    Retorna:
        - "NFC-e" para Nota Fiscal do Consumidor Eletrônica (modelo 65).
        - "CF-e SAT" para Cupom Fiscal Eletrônico via SAT (modelo 59, exclusivo de SP).
        - "NF-e" para Nota Fiscal Eletrônica (modelo 55).
        - "Desconhecido" caso o formato não corresponda.
    """
    if not isinstance(chave, str) or not chave.isdigit():
        return "Erro: A chave deve conter apenas números."
    
    if len(chave) != 44:
        return "Erro: A chave deve ter exatamente 44 dígitos."

    modelo_fiscal = chave[20:22]  # Modelo do documento

    if modelo_fiscal == "65":
        return "NFC-e"  # Nota Fiscal do Consumidor Eletrônica
    elif modelo_fiscal == "59":
        return "CF-e SAT"  # Cupom Fiscal Eletrônico via SAT
    elif modelo_fiscal == "55":
        return "NF-e"  # Nota Fiscal Eletrônica
    else:
        return "Desconhecido"