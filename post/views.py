from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from celery import chord

from .models import Post
from comment.models import Comment
from comment.serializers import CommentCreateSerializer, CommentSerializer, CommentSummarySerializer
from .serializers import PostCreateSerializer, PostSerializer, PostCommentSummarySerializer
from .tasks import add_numbers, get_post_summary, get_comment_summary, collect_post_and_comment_summaries
from django.http import StreamingHttpResponse
import requests
import openai
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

def call_openai_api_stream(prompt):
    api_url = "https://api.openai.com/v1/chat/completions"
    api_key = settings.OPENAI_API_KEY

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",  # 정확한 모델 이름으로 변경
        "messages": [
            {"role": "system", "content": "당신은 일반 사용자들이 쉽게 이해할 수 있도록 게시글이나 댓글을 간결하게 요약해주는 요약 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        "stream": True
    }

    try:
        with requests.post(api_url, json=payload, headers=headers, stream=True) as response:
            if response.status_code != 200:
                try:
                    error_msg = response.json().get("error", "Unknown error occurred.")
                except ValueError:
                    error_msg = "Unknown error occurred."
                logger.error(f"OpenAI API failed with status {response.status_code}: {error_msg}")
                raise Exception(f"OpenAI API failed: {error_msg}")

            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    decoded_chunk = chunk.decode("utf-8")
                    logger.debug(f"Received chunk: {decoded_chunk}")
                    yield decoded_chunk
    except requests.RequestException as e:
        error_message = f"RequestException: {str(e)}"
        logger.error(error_message)
        raise Exception(error_message)
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        logger.error(error_message)
        raise Exception(error_message)

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

    def get(self, request, post_id):
        try:
            # chord로 병렬 실행 + 결과 수집
            result = chord(
                [
                    get_post_summary.s(post_id),
                    get_comment_summary.s(post_id),
                ]
            )(collect_post_and_comment_summaries.s()).get(timeout=120)  # 최대 120초까지 대기

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PostSseSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, post_id):
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return StreamingHttpResponse(
                iter([f"data: 게시글을 찾을 수 없습니다.\n\n"]),
                content_type="text/event-stream"
            )

        comments = Comment.objects.filter(post_id=post_id).order_by("created_at")
        serialized_comments = CommentSummarySerializer(comments, many=True).data

        comment_text = "\n".join(
            f"{idx + 1}. {comment['username']}: {comment['content']}"
            for idx, comment in enumerate(serialized_comments)
        )

        prompt = f"""
아래 게시글과 댓글들을 참고하여 전체적으로 간결하게 요약해 주세요.

1) 게시글:
제목: {post.title}
내용: {post.content}

2) 댓글:
{comment_text}

요약 시 게시글 요약과 댓글 요약을 구분하여 아래와 같은 형식으로 반환해 주세요.

게시글 요약:
[여기에 게시글 요약]

댓글 요약:
[여기에 댓글 요약]
"""

        def sse_stream():
            sum_result = ""

            for chunk in call_openai_api_stream(prompt):
                chunk = chunk.strip()
                logger.debug(f"Received chunk: {chunk}")

                lines = chunk.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith("data: "):
                        data = line[len("data: "):]
                        logger.debug(f"Processed data: {data}")

                        if data == "[DONE]":
                            yield "event: done\ndata: [DONE]\n\n"
                            return

                        try:
                            data_json = json.loads(data)
                            content = data_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                sum_result += content
                                content_sanitized = content.replace(" ", "&nbsp;").replace("\n", "<br>")
                                yield f"data: {content_sanitized}\n\n"
                        except json.JSONDecodeError as e:
                            logger.error(f"JSONDecodeError: {e} for data: {data}")
                            yield "data: JSONDecodeError\n\n"

        response = StreamingHttpResponse(sse_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["Connection"] = "keep-alive"
        response["Access-Control-Allow-Origin"] = "*"

        return response