from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("accounts:register")
        self.login_url = reverse("accounts:login")
        self.me_url = reverse("accounts:me")
        self.refresh_url = reverse("accounts:token_refresh")
        self.user_data = {
            "email": "testuser@example.com",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User",
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], self.user_data["email"])
        self.assertTrue(User.objects.filter(email=self.user_data["email"]).exists())

    def test_user_login(self):
        User.objects.create_user(**self.user_data)
        response = self.client.post(
            self.login_url,
            {"email": self.user_data["email"], "password": self.user_data["password"]},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        access_token = response.data["access"]

        # Authenticate me endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        me_response = self.client.get(self.me_url)
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["email"], self.user_data["email"])
    def test_token_refresh_lifecycle(self):
        # 1. Login to get token pair
        user = User.objects.create_user(**self.user_data)
        login_res = self.client.post(self.login_url, {
            "email": self.user_data["email"],
            "password": self.user_data["password"],
        })
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        refresh_token = login_res.data["refresh"]

        # 2. Exchange refresh token for fresh access token
        refresh_res = self.client.post(self.refresh_url, {"refresh": refresh_token})
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_res.data)

        # 3. Test resilience: deleted/non-existent user must return 401, not 500
        user.delete()
        res_deleted = self.client.post(self.refresh_url, {"refresh": refresh_token})
        self.assertEqual(res_deleted.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(res_deleted.data.get("code"), "token_not_valid")

        # 4. Test invalid token
        res_invalid = self.client.post(self.refresh_url, {"refresh": "malformed.refresh.token"})
        self.assertEqual(res_invalid.status_code, status.HTTP_401_UNAUTHORIZED)
    def test_firebase_sync_endpoint(self):
        url = reverse("accounts:firebase_sync")
        payload = {
            "email": "firebaseuser@example.com",
            "uid": "fb_uid_123456789",
            "first_name": "Firebase",
            "last_name": "Dev",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertEqual(res.data["user"]["email"], "firebaseuser@example.com")
        self.assertTrue(User.objects.filter(email="firebaseuser@example.com").exists())

