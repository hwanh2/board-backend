from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import PostCreateSerializer, PostSerializer
from .models import Post
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class PostCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

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
            response_data = PostSerializer(post).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
