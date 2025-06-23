from django.urls import path
from .views import *

urlpatterns = [
    path('', LoginView.as_view(), name='login'),
]