FROM python:3.10.4-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /src/api/

COPY . /src/api/

RUN pip install --upgrade pip && pip install -r requirements.txt

CMD gunicorn config.wsgi:application --bind 0.0.0.0:8000
