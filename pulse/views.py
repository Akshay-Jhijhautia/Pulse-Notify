from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, RegisterSerializer

User = get_user_model()


class RegisterView(APIView):
    """Public endpoint — create a user and return a JWT access token."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        if User.objects.filter(username=username).exists():
            return Response(
                {'username': ['A user with that username already exists.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            email=serializer.validated_data.get('email', ''),
            password=serializer.validated_data['password'],
        )
        # UserProfile is created by the post_save signal (Feature 2)
        access = str(RefreshToken.for_user(user).access_token)
        return Response(
            {
                'username': user.username,
                'access': access,
                'role': user.profile.role,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Public endpoint — validate credentials and return a JWT access token."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access = str(RefreshToken.for_user(user).access_token)
        return Response(
            {
                'username': user.username,
                'access': access,
                'role': user.profile.role,
            },
            status=status.HTTP_200_OK,
        )
