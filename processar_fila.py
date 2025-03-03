from src.config.database import get_db
from src.services.processamento import processar_fila_sqs

if __name__ == "__main__":
    db = next(get_db())
    processar_fila_sqs(db)