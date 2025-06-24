from rest_framework import serializers
from .models import Comment

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content']

    def create(self, validated_data):
        user = self.context['request'].user
        post = self.context['post']
        return Comment.objects.create(user_id=user, post_id=post, **validated_data)


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'content', 'user_id', 'created_at', 'updated_at']
