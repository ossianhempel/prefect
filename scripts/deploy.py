import os
from prefect_aws import S3Bucket, MinIOCredentials


# load minio credentials
minio_credentials = MinIOCredentials.load("minio-creds")

# recreate s3 bucket block
s3_block = S3Bucket(
    bucket_name="flows",
    credentials=minio_credentials,
    endpoint_url=os.getenv("MINIO_ENDPOINT"),  # add endpoint explicitly
)
s3_block.save(name="minio-bucket", overwrite=True)
