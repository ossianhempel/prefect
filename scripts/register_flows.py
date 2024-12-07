import os
from prefect import Flow
from prefect.storage import S3
from prefect_aws import MinIOCredentials

minio_credentials_block = MinIOCredentials.load("flows-storage")

flows_dir = "./flows"
s3_bucket = "flows"

for file in os.listdir(flows_dir):
    if file.endswith(".py"):
        flow_name = file.split(".")[0]
        flow_file = os.path.join(flows_dir, file)

        # dynamically load flow from file
        with open(flow_file) as f:
            exec(f.read())

        # check if flow exists in globals
        if "flow" in globals():
            flow.storage = S3(bucket=s3_bucket, key=f"flows/{file}")
            flow.register(project_name="my-prefect-project")
