from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # 기본적으로 username, password, email 등 포함됨
    # 필요한 경우 추가 필드를 여기에 정의
    # 예: profile_image = models.URLField(null=True, blank=True)

    class Meta:
        db_table = 'user'  # 테이블 이름을 'user'로 지정
