FROM python:3.10.4-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /api

COPY requirements.txt /api

RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

COPY . /api

RUN python manage.py makemigrations && python manage.py migrate
RUN python manage.py collectstatic
