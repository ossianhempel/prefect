from prefect import flow, task

@task
def hello_task():
    print("hello from prefect and minio!")

@flow(name="test-flow")
def hello_flow():
    hello_task()

if __name__ == "__main__":
    hello_flow.serve()