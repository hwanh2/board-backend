from django.urls import path
from .views import *

urlpatterns = [
    path('', PostView.as_view(), name='post_list_create'),
    path('<int:post_id>', PostDetailView.as_view(), name='post_detail'),
    path('<int:post_id>/comments', CommentView.as_view(), name='comment_create'),
    path('<int:post_id>/test-success', TestSuccessView.as_view(), name='test_success'),
    path('<int:post_id>/test-fail', TestFailView.as_view(), name='test_fail'),
]