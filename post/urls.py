from django.urls import path
from .views import *

urlpatterns = [
    path('', PostView.as_view(), name='post_list_create'),
    path('<int:post_id>', PostDetailView.as_view(), name='post_detail'),
    
]