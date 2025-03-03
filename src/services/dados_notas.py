from fastapi import HTTPException
from sqlalchemy.orm import Session
from src.models.dados_notas import DadosNotas
from src.schemas.dados_notas import DadosNotasResponse

def obter_dados_notas(db: Session, requisicao_id: int):
    """
    Obtém os dados de uma nota fiscal pelo ID da requisição.

    Parâmetros:
    - db: Sessão do banco de dados.
    - requisicao_id: ID da requisição.

    Retorna:
    - Dados da nota fiscal.
    """
    dados_notas = db.query(DadosNotas).filter(DadosNotas.requisicao_id == requisicao_id).first()
    if not dados_notas:
        raise HTTPException(status_code=404, detail="Dados da nota fiscal não encontrados")
    return dados_notas