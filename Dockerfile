FROM python:3.12-slim

WORKDIR /opt/prefect

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "prefect", "agent", "start", "-p", "default"] 