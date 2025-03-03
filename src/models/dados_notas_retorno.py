from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DadosDaNfe:
    dataDeEmissao: str
    dataSaidaEntrada: Optional[str] = None
    modelo: int = 0
    numero: int = 0
    serie: int = 0
    valorTotal: float = 0.0

@dataclass
class DadosDoDestinatario:
    cpf: Optional[str] = None

@dataclass
class DadosDoEmitente:
    bairroDistrito: str
    cep: str
    cnpj: str  # Argumento obrigatório movido antes de argumentos com valores padrão
    endereco: str
    inscricaoEstadual: str
    municipio: str
    nomeRazaoSocial: str
    uf: str
    cnae: Optional[str] = None  # Argumento com valor padrão mantido após argumentos obrigatórios
    codigoRegimeTributario: str = "Regime Normal"
    inscricaoEstadualDoSubstitutoTributario: Optional[str] = None
    inscricaoMunicipal: Optional[str] = None
    municipioIcms: Optional[str] = None
    nomeFantasia: str = "Não Informado"
    pais: str = "1058 - Brasil"
    telefone: Optional[str] = None

@dataclass
class ProdutoEServico:
    codigo: str
    codigoCest: Optional[str] = None
    codigoEanComercial: str = ""
    codigoEanTributavel: Optional[str] = None
    codigoNcm: Optional[str] = None
    descricao: str = ""
    numero: int = 0
    quantidade: float = 0.0
    unidadeComercial: str = ""
    valor: float = 0.0
    valorDesconto: float = 0.0

@dataclass
class FormaDePagamento:
    forma: Optional[str] = None
    meio: str = ""
    valor: float = 0.0
    valorTroco: float = 0.0

@dataclass
class DadosNotaFiscal:
    chaveDeAcesso: str
    TempoDeCaptura: Optional[str] = None
    dadosDaNfe: DadosDaNfe = field(default_factory=DadosDaNfe)
    dadosDoDestinatario: DadosDoDestinatario = field(default_factory=DadosDoDestinatario)
    dadosDoEmitente: DadosDoEmitente = field(default_factory=DadosDoEmitente)
    dadosDosProdutosEServicos: List[ProdutoEServico] = field(default_factory=list)
    formasDePagamento: List[FormaDePagamento] = field(default_factory=list)