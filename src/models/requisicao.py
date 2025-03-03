from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Text, BigInteger
from sqlalchemy.sql import func
from src.config.database import Base

class Requisicao(Base):
    """
    Modelo da tabela `requisicoes`.

    Campos:
    - id: Identificador único da requisição.
    - access_key: Chave da nota fiscal.
    - estado: Estado da nota fiscal (ex.: SP, RJ).
    - callback_url: URL de callback para retorno dos dados.
    - status: Status da requisição (ex.: "Aguardando", "Processando", "Concluído").
    - data_criacao: Data e hora da criação da requisição.
    - data_atualizacao: Data e hora da última atualização.
    - contador_tentativas: Número de tentativas de processamento.
    - shopping: Identificação do cliente (ex.: "SVL").
    - force_delay: Indica se o processamento deve ter um atraso forçado.
    - observacao: Log de erros ou mensagens relevantes.
    - tempo_total_processamento: Tempo total de processamento em milissegundos.
    - tempo_acesso_sefaz: Tempo para acessar o site do SEFAZ em milissegundos.
    - tempo_resolucao_captcha: Tempo para resolver o reCAPTCHA em milissegundos.
    - tempo_coleta_dados: Tempo para coletar os dados da nota fiscal em milissegundos.
    - erro: Mensagem de erro, se houver.
    """
    __tablename__ = "requisicoes"

    id = Column(Integer, primary_key=True, index=True)
    access_key = Column(String(50), nullable=False)
    estado = Column(String(2), nullable=False)
    callback_url = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="Aguardando")
    data_criacao = Column(TIMESTAMP, nullable=False, default=func.now())
    data_atualizacao = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())
    contador_tentativas = Column(Integer, nullable=False, default=0)
    shopping = Column(String(50))
    force_delay = Column(Boolean, default=False)
    observacao = Column(Text)
    tempo_total_processamento = Column(BigInteger)
    tempo_acesso_sefaz = Column(BigInteger)
    tempo_resolucao_captcha = Column(BigInteger)
    tempo_coleta_dados = Column(BigInteger)
    erro = Column(Text)