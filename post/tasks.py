from celery import shared_task
from comment.serializers import CommentSummarySerializer  # comments 직렬화용
import openai  # OpenAI API 호출용
from django.conf import settings
import requests

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
            {"role": "system", "content": "당신은 전문적인 기술 문서를 작성하는 전문가입니다."},
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


def get_post_summary(post):
    prompt = f"""
    제목: {post.title}
    내용: {post.content}

    위의 게시글을 간결하게 요약해 주세요.
    """
    return call_openai_api(prompt)

def get_comment_summary(comments_queryset):
    serialized = CommentSummarySerializer(comments_queryset, many=True).data

    comment_text = "\n".join(
        f"{idx + 1}. {comment['username']}: {comment['content']}"
        for idx, comment in enumerate(serialized)
    )

    prompt = f"""
    아래는 게시글에 달린 댓글 목록입니다.
    각 의견들을 참고하여 전체적으로 어떤 논의가 이루어졌는지 요약해 주세요:

    {comment_text}
    """
    return call_openai_api(prompt)