from django.urls import path
from .views import *

urlpatterns = [
    path('<int:comment_id>', CommentDetailView.as_view(), name='comment_datail'),
]