import boto3
from src.config.settings import settings

def get_sqs_client():
    """
    Retorna um cliente SQS configurado.
    """
    return boto3.client("sqs", region_name="sa-east-1")  # Altere para a região correta