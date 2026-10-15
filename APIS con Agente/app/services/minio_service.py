import os
import io
import boto3
import json
from botocore.client import Config
from botocore.exceptions import ClientError
from app.core.config import settings

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.minio_endpoint,
    aws_access_key_id=settings.minio_user,
    aws_secret_access_key=settings.minio_password,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1"
)

def aplicar_politica_publica(bucket_name: str):
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicRead",
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
            }
        ]
    }
    try:
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
    except Exception as e:
        print(f"Aviso al aplicar politica publica en {bucket_name}: {e}")

def asegurar_bucket(bucket_name: str = settings.bucket_tickets):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError:
        try:
            s3_client.create_bucket(Bucket=bucket_name)
        except Exception as e:
            print(f"Aviso al verificar o crear bucket {bucket_name}: {e}")
    aplicar_politica_publica(bucket_name)

def subir_ticket_imagen(buffer_bytes: bytes, filename: str) -> str:
    asegurar_bucket(settings.bucket_tickets)
    s3_client.upload_fileobj(
        io.BytesIO(buffer_bytes),
        settings.bucket_tickets,
        filename,
        ExtraArgs={"ContentType": "image/png"}
    )
    return f"{settings.minio_endpoint}/{settings.bucket_tickets}/{filename}"

def descargar_ticket_bytes(filename: str) -> bytes:
    buf = io.BytesIO()
    s3_client.download_fileobj(settings.bucket_tickets, filename, buf)
    buf.seek(0)
    return buf.getvalue()
