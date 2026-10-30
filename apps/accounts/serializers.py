from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Read-only view of a user (used by /me/ and auth responses)."""

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "date_joined")
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Validates sign-up data and creates the user."""

    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = User
        fields = ("email", "password", "first_name", "last_name")

    def validate_email(self, value):
        norm_email = value.lower().strip()
        if User.objects.filter(email__iexact=norm_email).exists():
            raise serializers.ValidationError("An account with this email address already exists.")
        return norm_email

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Enriches JWT login response with user identity."""

    def validate(self, attrs):
        if "email" in attrs:
            attrs["email"] = attrs["email"].lower().strip()
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
