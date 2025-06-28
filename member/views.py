from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import *
from rest_framework.permissions import AllowAny

User = get_user_model()

class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['members'],
        operation_summary="로그인 또는 회원가입",
        request_body=LoginRequestSerializer,
        responses={
            200: openapi.Response(description="로그인 성공", schema=LoginResponseSerializer),
            400: "아이디와 비밀번호를 입력해주세요.",
            401: "비밀번호가 틀렸습니다.",
        }
    )
    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(username=username)
            if not check_password(password, user.password):
                return Response({"error": "비밀번호가 틀렸습니다."}, status=status.HTTP_401_UNAUTHORIZED)
            message = "로그인 성공 (기존 사용자)"
        except User.DoesNotExist:
            user = User.objects.create(
                username=username,
                password=make_password(password)
            )
            message = "로그인 성공 (신규 사용자)"

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        data = {
            "message": message,
            "access": access_token,
            "refresh": refresh_token,
        }
        
        response_serializer = LoginResponseSerializer(data=data)
        
        if response_serializer.is_valid():
            response = Response(response_serializer.data, status=status.HTTP_200_OK)
            response.set_cookie("access", access_token, httponly=True, samesite="None", secure=False)
            response.set_cookie("refresh", refresh_token, httponly=True, samesite="None", secure=False)
            return response
        else:
            return Response(response_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        