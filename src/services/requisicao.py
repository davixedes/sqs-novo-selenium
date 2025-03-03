from sqlalchemy.orm import Session
from src.models.requisicao import Requisicao
from src.schemas.requisicao import RequisicaoCreate, RequisicaoResponse
from datetime import datetime

def criar_requisicao(db: Session, requisicao: RequisicaoCreate):
    """
    Cria uma nova requisição no banco de dados.

    Parâmetros:
    - db: Sessão do banco de dados.
    - requisicao: Dados da requisição.

    Retorna:
    - Requisição criada.
    """
    db_requisicao = Requisicao(
        access_key=requisicao.accessKey,
        estado=requisicao.estado,
        callback_url=requisicao.callbackUrl,
        shopping=requisicao.extraOptions.get("shopping") if requisicao.extraOptions else None,
        force_delay=requisicao.extraOptions.get("forceDelay") if requisicao.extraOptions else False
    )
    db.add(db_requisicao)
    db.commit()
    db.refresh(db_requisicao)

    # Converte o objeto SQLAlchemy para o esquema Pydantic
    return RequisicaoResponse(
        id=db_requisicao.id,
        accessKey=db_requisicao.access_key,
        estado=db_requisicao.estado,
        status=db_requisicao.status,
        data_criacao=db_requisicao.data_criacao.isoformat()  # Converte datetime para string
    )

from datetime import datetime


def consultar_requisicao(db: Session, data_inicial: str, data_final: str):
    """
    Consulta requisições no banco de dados com status "Erro" dentro de um intervalo de datas.

    Parâmetros:
    - db: Sessão do banco de dados.
    - data_inicial: Data inicial no formato "DD/MM/YYYY HH:MM:SS".
    - data_final: Data final no formato "DD/MM/YYYY HH:MM:SS".

    Retorna:
    - Lista de requisições encontradas.
    """

    # Converte as datas de string para datetime
    try:
        dt_inicial = datetime.strptime(data_inicial, "%d/%m/%Y %H:%M:%S")
        dt_final = datetime.strptime(data_final, "%d/%m/%Y %H:%M:%S")
    except ValueError:
        raise ValueError("Formato de data inválido. Use 'DD/MM/YYYY HH:MM:SS'.")

    # Consulta no banco de dados
    requisicoes = (
        db.query(Requisicao)
        .filter(Requisicao.status == "Erro")
        .filter(Requisicao.data_atualizacao >= dt_inicial)
        .filter(Requisicao.data_atualizacao <= dt_final)
        .all()
    )

    # Retorna a lista de respostas formatadas
    return [
        RequisicaoResponse(
            id=req.id,
            accessKey=req.access_key,
            estado=req.estado,
            status=req.status,
            data_criacao=req.data_criacao.isoformat(),
            data_atualizacao=req.data_atualizacao.isoformat(),
            contador_tentativas=req.contador_tentativas,
            shopping=req.shopping,
            force_delay=req.force_delay,
            observacao=req.observacao,
            tempo_total_processamento=req.tempo_total_processamento,
            tempo_acesso_sefaz=req.tempo_acesso_sefaz,
            tempo_resolucao_captcha=req.tempo_resolucao_captcha,
            tempo_coleta_dados=req.tempo_coleta_dados,
            erro=req.erro
        )
        for req in requisicoes
    ]
