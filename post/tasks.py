# tasks.py
from celery import shared_task

@shared_task
def add_numbers(a, b):
    if a == 999:
        raise Exception("의도된 실패입니다")
    return a + b
