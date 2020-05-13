from django.db import models

# Create your models here.

class User(models.Model):
    user_ID = models.CharField(max_length = 50) # 사용자 ID
    user_password = models.CharField(max_length = 50) # 사용자 비밀번호
    user_name = models.CharField(max_length = 50) # 사용자 이름
    user_birth = models.DateField() # 생년월일

