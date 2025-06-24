from django.urls import path
from .views import *

urlpatterns = [
    path('<int:board_id>', CommentView.as_view(), name='comment_list_create'),
]