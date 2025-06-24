from django.db import models
from django.conf import settings
from post.models import Post

class Comment(models.Model):
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='user_id',related_name='comments')
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE, db_column='post_id',related_name='comments')

    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comment'

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.title}'
