# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster
WORKDIR /bot
COPY requirements.txt requirements.txt
COPY . .
RUN pip3 install -r requirements.txt
CMD [ "python3", "-m" , "main", "--host=0.0.0.0"]