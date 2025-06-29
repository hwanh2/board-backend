from rest_framework import serializers
from .models import Comment
from django.contrib.auth import get_user_model
User = get_user_model()


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content']

    def create(self, validated_data):
        user = self.context['request'].user
        post = self.context['post']
        return Comment.objects.create(user_id=user, post_id=post, **validated_data)

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class CommentSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(source='user_id', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'content', 'user', 'created_at', 'updated_at']

class CommentSummarySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user_id.username')

    class Meta:
        model = Comment
        fields = ['username', 'content']