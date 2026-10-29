from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ - open to anyone."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # 400 if invalid
        user = serializer.save()
        # Respond with the safe serializer (never echo the password)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ - returns {access, refresh}.

    TokenObtainPairView already does the work: it checks email + password
    (because USERNAME_FIELD='email') and signs the JWTs.
    """

    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    """GET /api/auth/me/ - the logged-in user."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user  # set by JWTAuthentication from the token