import boto3
from botocore.client import Config
import os

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
    endpoint_url=os.getenv("MINIO_ENDPOINT"),
    config=Config(signature_version="s3v4"),
)

# test listing buckets
print(s3.list_buckets())
