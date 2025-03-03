from sqlalchemy import Column, Integer, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from src.config.database import Base

class DadosNotas(Base):
    """
    Modelo da tabela `dados_notas`.

    Campos:
    - id: Identificador único dos dados.
    - requisicao_id: Referência à tabela `requisicoes`.
    - dados: Dados completos da nota fiscal em formato JSON.
    - data_coleta: Data e hora da coleta dos dados.
    """
    __tablename__ = "dados_notas"

    id = Column(Integer, primary_key=True, index=True)
    requisicao_id = Column(Integer, ForeignKey("requisicoes.id"), nullable=False)
    dados = Column(JSON, nullable=False)
    data_coleta = Column(TIMESTAMP, nullable=False, default=func.now())