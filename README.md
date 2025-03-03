# API de Processamento de Notas Fiscais (RPA)

Esta API é responsável por receber requisições de enriquecimento de notas fiscais, processar os dados no site do SEFAZ e retornar os resultados via callback.

## Requisitos

- Python 3.8+
- PostgreSQL
- AWS SQS
- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy
- psycopg2-binary
- Boto3
- Python-dotenv
- Pydantic-settings
- selenium
- undetected-chromedriver
- setuptools

## Instalação
1. iniciar a env:
```bash
python -m venv venv  #Criar ambiente virtual com nome de "venv"
.\venv\Scripts\activate  #Ativar o "venv". Executar sempre que for utilizar o ambiente
```

2. Clone o repositório:

```bash
   git clone https://github.com/seu-usuario/api-rpa.git
   cd api-rpa
```

3. Crie um ambiente virtual e instale as dependências:

```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    pip install -r requirements.txt
```
4. Configure as variáveis de ambiente:
    Crie um arquivo .env na raiz do projeto com as seguintes variáveis:

```env
    DATABASE_URL=postgresql://postgres:sua_senha@db-paperoff-rpa.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com:5432/RPA
    AWS_SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/sua-fila
```

5. Execute a aplicação:
```bash
    uvicorn main:app --reload
```
* Apos executar acessar com o endpoint **http://127.0.0.1:8000/teste**

## Endpoints

1. Solicitação de Enriquecimento
    * Método: POST

    * URL: /create

    * Descrição: Recebe a chave da nota fiscal, estado e URL de callback para iniciar o processo de enriquecimento.

    * Corpo da Requisição:
    ```json
    {
        "accessKey": "35241111317530001075590009014621746736973705",
        "estado": "SP",
        "callbackUrl": "https://api-prd.brmalls.com.br/enrichment-callback/order-enrichment/invoice",
        "extraOptions": {
            "forceDelay": true,
            "shopping": "SVL"
        }
    }
    ```

    * Resposta:
    ```json
    {
        "id": 1,
        "status": "Aguardando",
        "message": "Requisição recebida e adicionada à fila."
    }
    ```
2. Consulta de Dados Enriquecidos
    * Método: GET

    * URL: /read/:accessKey

    * Descrição: Retorna os dados da nota fiscal enriquecida.

    * Resposta:
    ```json
    {
        "id": 1,
        "accessKey": "35241111317530001075590009014621746736973705",
        "estado": "SP",
        "status": "Concluído",
        "tempo_total_processamento": 1200,
        "tempo_acesso_sefaz": 300,
        "tempo_resolucao_captcha": 500,
        "tempo_coleta_dados": 400,
        "dados": {
            "chaveDeAcesso": "35241111317530001075590009014621746736973705",
            "dadosDaNfe": {
            "dataDeEmissao": "05/11/2024 13:41:03",
            "valorTotal": 22.95
            },
            "dadosDoEmitente": {
            "cnpj": "11.317.530/0010-75",
            "nomeRazaoSocial": "VIRTUS COMERCIO DE ALIMENTOS LTDA"
            }
        }
    }
    ```

## Estrutura do Projeto

* **main.py**: Ponto de entrada da aplicação.
* **src/config/**: Configurações do projeto (banco de dados, variáveis de ambiente).
* **src/models/**: Modelos de dados (SQLAlchemy).
* **src/schemas/**: Esquemas de validação (Pydantic).
* **src/routes/**: Rotas da API.
* **src/services/**: Lógica de negócio.
* **src/utils/**: Utilitários (logger, SQS handler).
* **tests/**: Testes automatizados.

## Testes
Para executar os testes, use o comando:

```bash
    pytest tests/
```

## Contribuição

1. Faça um fork do repositório.

2. Crie uma branch para sua feature (**git checkout -b feature/nova-feature**).

3. Commit suas alterações (**git commit -m 'Adiciona nova feature'**).

4. Push para a branch (**git push origin feature/nova-feature**).

5. Abra um Pull Request.

 

---

### **2. Documentação Interna do Código**

Aqui estão exemplos de como a documentação interna será estruturada no código:

#### **Exemplo 1: Modelo `Requisicao` (`src/models/requisicao.py`)**
```python
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
```

#### **Exemplo 1: Modelo `Requisicao` (`src/models/requisicao.py`)**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.schemas.requisicao import RequisicaoCreate
from src.services.requisicao import criar_requisicao
from src.config.database import get_db

router = APIRouter()

@router.post("/create", response_model=RequisicaoCreate)
def criar_requisicao_endpoint(requisicao: RequisicaoCreate, db: Session = Depends(get_db)):
    """
    Endpoint para criar uma nova requisição de enriquecimento.

    Parâmetros:
    - requisicao: Dados da requisição (accessKey, estado, callbackUrl, extraOptions).
    - db: Sessão do banco de dados.

    Retorna:
    - Requisição criada com status "Aguardando".
    """
    try:
        return criar_requisicao(db, requisicao)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```