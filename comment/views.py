from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Comment
from post.models import Post
from .serializers import CommentCreateSerializer, CommentSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


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
    def put(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)

        if comment.user_id != request.user:
            return Response({"detail": "수정 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

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
    def delete(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)

        if comment.user_id != request.user:
            return Response({"detail": "삭제 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)