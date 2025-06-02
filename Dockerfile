FROM python:3.11-slim

COPY . .

RUN pip install -r requirements.txt


CMD [ "uvicorn", "fast_api:app", "--host", "0.0.0.0", "--port", "80" ]