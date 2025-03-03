from pydantic import BaseModel
from datetime import datetime

class DadosNotasResponse(BaseModel):
    """
    Esquema para resposta dos dados de notas fiscais.

    Campos:
    - id: Identificador único dos dados.
    - requisicao_id: Referência à tabela `requisicoes`.
    - dados: Dados completos da nota fiscal em formato JSON.
    - data_coleta: Data e hora da coleta dos dados.
    """
    id: int
    requisicao_id: int
    dados: dict
    data_coleta: datetime

    class Config:
        from_attributes = True  # Habilita a conversão de objetos ORM para Pydantic