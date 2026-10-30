from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ - registers user and automatically returns signed JWT tokens."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT token pair directly on registration
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data

        response_data = {
            **user_data,
            "user": user_data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "message": "Account created successfully.",
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ - returns {access, refresh, user}."""

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class RefreshView(TokenRefreshView):
    """POST /api/auth/token/refresh/ - exchanges refresh token for fresh access token."""

    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    """GET /api/auth/me/ - the logged-in user profile."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
