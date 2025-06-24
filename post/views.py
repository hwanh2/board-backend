from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Post
from comment.serializers import CommentCreateSerializer, CommentSerializer
from .serializers import PostCreateSerializer, PostSerializer


class PostView(APIView):
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @swagger_auto_schema(
        operation_summary="게시글 목록 조회",
        responses={200: openapi.Response(description="조회 성공", schema=PostSerializer(many=True))}
    )
    def get(self, request):
        posts = Post.objects.all().order_by('-created_at')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="게시글 생성",
        request_body=PostCreateSerializer,
        responses={
            201: openapi.Response(description="생성 성공", schema=PostSerializer),
            400: "잘못된 요청입니다.",
            401: "인증되지 않았습니다."
        }
    )
    def post(self, request):
        serializer = PostCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            post = serializer.save()
            return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="게시글 상세 조회",
        responses={
            200: openapi.Response(description="조회 성공", schema=PostSerializer),
            401: "인증되지 않았습니다.",
            404: "게시글을 찾을 수 없습니다."
        }
    )
    def get(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="게시글 수정",
        request_body=PostCreateSerializer,
        responses={
            200: openapi.Response(description="수정 성공", schema=PostSerializer),
            400: "잘못된 요청입니다.",
            401: "인증되지 않았습니다.",
            403: "작성자가 아닙니다.",
            404: "게시글을 찾을 수 없습니다."
        }
    )
    def put(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        if post.user_id != request.user:
            return Response({"detail": "수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        serializer = PostCreateSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(PostSerializer(post).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="게시글 삭제",
        responses={
            204: "삭제 성공",
            401: "인증되지 않았습니다.",
            403: "작성자가 아닙니다.",
            404: "게시글을 찾을 수 없습니다."
        }
    )
    def delete(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        if post.user_id != request.user:
            return Response({"detail": "삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        post.delete()
        return Response({"detail": "삭제 완료"}, status=status.HTTP_204_NO_CONTENT)


class CommentView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="댓글 생성",
        request_body=CommentCreateSerializer,
        responses={
            201: openapi.Response(description="생성 성공", schema=CommentSerializer),
            400: "잘못된 요청입니다.",
            401: "인증되지 않았습니다.",
            404: "게시글을 찾을 수 없습니다."
        }
    )
    def post(self, request, post_id):  # post_id로 수정
        post = get_object_or_404(Post, pk=post_id)
        serializer = CommentCreateSerializer(data=request.data, context={'request': request, 'post': post})
        if serializer.is_valid():
            comment = serializer.save()
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
