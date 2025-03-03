from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict

class RequisicaoCreate(BaseModel):
    """
    Esquema para criação de uma nova requisição de enriquecimento.

    Campos:
    - accessKey: Chave da nota fiscal.
    - estado: Estado da nota fiscal (ex.: SP, RJ).
    - callbackUrl: URL de callback para retorno dos dados.
    - extraOptions: Opções adicionais (forceDelay, shopping).
    """
    accessKey: str
    estado: str
    callbackUrl: str
    extraOptions: Optional[Dict[str, str | bool]] = None

class RequisicaoResponse(BaseModel):
    """
    Esquema para resposta de uma requisição de enriquecimento.

    Campos:
    - id: Identificador único da requisição.
    - accessKey: Chave da nota fiscal.
    - estado: Estado da nota fiscal.
    - status: Status da requisição.
    - data_criacao: Data e hora da criação da requisição (em formato string).
    """
    id: int
    accessKey: str = Field(alias="access_key")  # Mapeia o campo access_key do SQLAlchemy para accessKey
    estado: str
    status: str
    data_criacao: str  # Agora espera uma string

    class Config:
        from_attributes = True  # Habilita a conversão de objetos ORM para Pydantic
        populate_by_name = True  # Permite o uso de alias (accessKey -> access_key)