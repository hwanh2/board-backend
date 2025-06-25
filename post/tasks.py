from celery import shared_task
from comment.serializers import CommentSummarySerializer  # comments 직렬화용
import openai  # OpenAI API 호출용
from django.conf import settings
import requests
import redis
from comment.models import Comment
from .models import Post

# Redis 클라이언트 생성
redis_client = redis.StrictRedis(host="redis", port=6379, decode_responses=True)

def call_openai_api(prompt):
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
        "stream": False
    }

    response = requests.post(api_url, json=payload, headers=headers)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        error_msg = response.json().get("error", "Unknown error occurred.")
        raise Exception(f"DeepSeek API 호출 실패: {error_msg}")

@shared_task
def add_numbers(a, b):
    if a == 999:
        raise Exception("의도된 실패입니다")
    return a + b

@shared_task
def get_post_summary(post_id):
    channel = "task_updates"
    redis_client.publish(channel, "post_summary 작업 시작")

    try:
        post = Post.objects.get(id=post_id)

        prompt = f"""
        제목: {post.title}
        내용: {post.content}

        위의 게시글을 간결하게 요약해 주세요.
        """
        result = call_openai_api(prompt)

        redis_client.publish(channel, "post_summary 작업 완료")
        return result

    except Post.DoesNotExist:
        redis_client.publish(channel, "post_summary 작업 실패: 게시글 없음")
        raise Exception("게시글이 존재하지 않습니다.")
    except Exception as e:
        redis_client.publish(channel, f"post_summary 작업 실패: {e}")
        raise

@shared_task
def get_comment_summary(post_id):
    channel = "task_updates"
    redis_client.publish(channel, "comment_summary 작업 시작")

    try:
        comments = Comment.objects.filter(post_id=post_id).order_by("created_at")
        serialized = CommentSummarySerializer(comments, many=True).data

        comment_text = "\n".join(
            f"{idx + 1}. {comment['username']}: {comment['content']}"
            for idx, comment in enumerate(serialized)
        )

        prompt = f"""
        아래는 게시글에 달린 댓글 목록입니다.
        각 의견들을 참고하여 전체적으로 어떤 논의가 이루어졌는지 요약해 주세요:

        {comment_text}
        """

        comment_summary_content = call_openai_api(prompt)

        redis_client.publish(channel, "comment_summary 작업 완료")
        return comment_summary_content

    except Exception as e:
        redis_client.publish(channel, f"comment_summary 작업 실패: {e}")
        raise Exception(f"Error generating comment_summary: {e}")

@shared_task
def collect_post_and_comment_summaries(results):
    return {
        "post_summary": results[0],
        "comment_summary": results[1]
    }