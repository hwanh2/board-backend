FROM python:3.10

ENV PYTHONUNBUFFERED 1

WORKDIR /Board-Backend

COPY ./requirements.txt /requirements.txt

RUN pip install --upgrade -r /requirements.txt

RUN pip install GitPython

COPY . ./

RUN python manage.py collectstatic --noinput

