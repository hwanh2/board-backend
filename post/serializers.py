from rest_framework import serializers
from .models import Post
from comment.serializers import CommentSerializer

class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['title', 'content']  # user는 직접 할당하므로 생략

    def create(self, validated_data):
        user = self.context['request'].user
        return Post.objects.create(user_id=user, **validated_data)


class PostSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'user_id', 'created_at','updated_at','comments']