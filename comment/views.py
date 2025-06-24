from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Comment
from post.models import Post
from .serializers import CommentCreateSerializer, CommentSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class CommentView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="댓글 목록 조회",
        responses={
            200: openapi.Response(description="조회 성공", schema=CommentSerializer(many=True)),
            404: "게시글을 찾을 수 없습니다."
        }
    )
    def get(self, request, board_id): # 해당 게시글의 댓글 목록 조회
        post = get_object_or_404(Post, pk=board_id)
        comments = post.comments.all().order_by('-created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
    def post(self, request, board_id): # 해당 게시글에 댓글 생성
        post = get_object_or_404(Post, pk=board_id)
        serializer = CommentCreateSerializer(data=request.data, context={'request': request, 'post': post})
        if serializer.is_valid():
            comment = serializer.save()
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ---------------------------------------------------------------------------------------------------------

class CommentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="댓글 수정",
        request_body=CommentCreateSerializer,
        responses={
            200: openapi.Response(description="수정 성공", schema=CommentSerializer),
            400: "잘못된 요청입니다.",
            401: "인증되지 않았습니다.",
            403: "수정 권한이 없습니다.",
            404: "댓글을 찾을 수 없습니다."
        }
    )
    def put(self, request, board_id, comment_id): # 댓글 수정
        # 게시글 존재 확인
        post = get_object_or_404(Post, pk=board_id)
        # 댓글 존재 확인
        comment = get_object_or_404(Comment, pk=comment_id, post_id=post)

        # 작성자 본인인지 확인
        if comment.user_id != request.user:
            return Response({"detail": "수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        # 수정
        serializer = CommentCreateSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(CommentSerializer(comment).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="댓글 삭제",
        responses={
            204: "삭제 성공",
            401: "인증되지 않았습니다.",
            403: "삭제 권한이 없습니다.",
            404: "댓글을 찾을 수 없습니다.",
        }
    )
    def delete(self, request, board_id, comment_id):
        post = get_object_or_404(Post, pk=board_id)
        comment = get_object_or_404(Comment, pk=comment_id, post_id=post)

        if comment.user_id != request.user:
            return Response({"detail": "삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)