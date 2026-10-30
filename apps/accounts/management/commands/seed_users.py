import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Seed initial production users if not present"

    def handle(self, *args, **options):
        # 1. Admin account
        admin_email = os.getenv("ADMIN_EMAIL", "admin@specforge.ai")
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin12345")
        if not User.objects.filter(email=admin_email).exists():
            admin_user = User.objects.create_superuser(
                email=admin_email,
                password=admin_pass,
                first_name="Admin",
                last_name="SpecForge"
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully created admin user: {admin_email}"))
        else:
            self.stdout.write(f"Admin user already exists: {admin_email}")

        # 2. Standard demo account
        demo_email = "me@example.com"
        demo_pass = "pass12345"
        if not User.objects.filter(email=demo_email).exists():
            demo_user = User.objects.create_user(
                email=demo_email,
                password=demo_pass,
                first_name="Demo",
                last_name="User"
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully created demo user: {demo_email}"))
        else:
            self.stdout.write(f"Demo user already exists: {demo_email}")
