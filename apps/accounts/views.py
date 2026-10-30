import logging
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    CustomTokenObtainPairSerializer,
    CustomTokenRefreshSerializer,
    RegisterSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)


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

    serializer_class = CustomTokenRefreshSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except Exception as exc:
            logger.warning("Token refresh error handled gracefully: %s", exc)
            return Response(
                {
                    "detail": "Token is invalid or expired. Please sign in again.",
                    "code": "token_not_valid",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


class MeView(generics.RetrieveAPIView):
    """GET /api/auth/me/ - the logged-in user profile."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
