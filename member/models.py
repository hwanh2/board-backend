from django.db import models

class Member(models.Model):
    name = models.CharField(max_length=20)
    password = models.CharField(max_length=100)

    class Meta:
        db_table = 'member'