# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /auditlog

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "main.py", "run", "--host=0.0.0.0"]