from celery import shared_task
import time

@shared_task
def add_numbers(a, b):
    print(f" {a} + {b} = {a + b}")
    time.sleep(1)  # 비동기 테스트용
    return a + b