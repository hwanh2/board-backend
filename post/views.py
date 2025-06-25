from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

from comment.models import Comment
from .models import Post
from comment.serializers import CommentCreateSerializer, CommentSerializer
from .serializers import PostCreateSerializer, PostSerializer, PostCommentSummarySerializer
from .tasks import add_numbers, get_post_summary, get_comment_summary


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
    

class TestSuccessView(APIView):
    permission_classes = [AllowAny] 
    
    @swagger_auto_schema(
        operation_summary="비동기 덧셈 요청",
        operation_description="post_id와 10을 더하는 비동기 작업을 큐에 등록합니다.",
        manual_parameters=[
            openapi.Parameter(
                name='post_id',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                description='더할 기준이 되는 post ID',
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="작업 등록 성공",
                examples={
                    "application/json": {
                        "message": "비동기 덧셈 작업이 큐에 들어갔습니다. (post_id=3)",
                        "task_id": "1e89f378-932b-472e-a332-1c16d4aa6a0b"
                    }
                }
            )
        }
    )
    def get(self, request, post_id):
        result = add_numbers.delay(post_id, 10)
        return Response({
            "message": f"비동기 덧셈 작업이 큐에 들어갔습니다. (post_id={post_id})",
            "task_id": result.id
        })

class TestFailView(APIView):

    @swagger_auto_schema(
        operation_description="강제로 비동기 작업을 큐에 넣어 테스트 실패를 유발합니다.",
        responses={
            200: openapi.Response(
                description="작업이 큐에 들어갔습니다.",
                examples={
                    "application/json": {
                        "message": "비동기 덧셈 작업이 큐에 들어갔습니다. (post_id=1)",
                        "task_id": "b5d8bfc4-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                    }
                }
            )
        }
    )
    def get(self, request, post_id: int):
        result = add_numbers.delay(post_id, 10)
        return Response({
            "message": f"비동기 덧셈 작업이 큐에 들어갔습니다. (post_id={post_id})",
            "task_id": result.id
        }, status=status.HTTP_200_OK)

class PostSummaryView(APIView):
    permission_classes = []  # 인증 없이 접근 가능

    @swagger_auto_schema(
        operation_summary="게시글 및 댓글 요약",
        operation_description="게시글 내용과 댓글을 AI가 요약한 결과를 반환합니다.",
        responses={
            200: openapi.Response(
                description="요약 성공",
                schema=PostCommentSummarySerializer
            ),
            404: "게시글이 존재하지 않습니다.",
            500: "내부 서버 오류"
        }
    )
    def get(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "게시글이 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)

        comments = Comment.objects.filter(post_id=post_id).order_by("created_at")

        try:
            post_summary = get_post_summary(post)
            comment_summary = get_comment_summary(comments)

            response_data = {
                "post_summary": post_summary,
                "comment_summary": comment_summary
            }

            serializer = PostCommentSummarySerializer(response_data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)