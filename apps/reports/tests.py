import zipfile
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ProjectScaffold, TechStackBlueprint
from .services import create_scaffold_zip, generate_dynamic_specifications
from .views import DashboardView

User = get_user_model()


class ReportsAndScaffoldTests(APITestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="developer@example.com",
            password="StrongPassword123!",
            first_name="Dev",
            last_name="Tester",
        )
        self.client.force_authenticate(user=self.user)

    def test_dashboard_view(self):
        request = self.factory.get("/")
        response = DashboardView.as_view()(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_blueprints_endpoint(self):
        TechStackBlueprint.objects.create(
            name="Django + React",
            slug="django-react",
            description="Full stack blueprint",
            keywords=["django", "react"],
            file_structure="src/\nmanage.py",
            coding_standards="Clean Architecture",
        )
        url = reverse("reports:blueprint_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_scaffold_lifecycle_and_spec_synthesis(self):
        # 1. Create a scaffold record
        scaffold = ProjectScaffold.objects.create(
            owner=self.user,
            title="Pilates Studio Management",
            description="Centralized multi-studio fitness management",
            scope_document="Pilates studio management platform with mobile app for bookings and admin dashboard for trainers.",
            custom_tech_stack="React Native, React, Node.js, Express, PostgreSQL",
        )

        # 2. Test dynamic specification generator (independent of external LLM API)
        specs = generate_dynamic_specifications(scaffold)
        self.assertIn("frontend", specs)
        self.assertIn("backend", specs)
        self.assertIn("agents_md", specs["frontend"])
        self.assertIn("architecture_md", specs["backend"])

        # Populate scaffold with generated specs
        scaffold.frontend_agents_md = specs["frontend"]["agents_md"]
        scaffold.frontend_architecture_md = specs["frontend"]["architecture_md"]
        scaffold.frontend_setup_md = specs["frontend"]["setup_md"]
        scaffold.backend_agents_md = specs["backend"]["agents_md"]
        scaffold.backend_architecture_md = specs["backend"]["architecture_md"]
        scaffold.backend_setup_md = specs["backend"]["setup_md"]
        scaffold.save()

        # 3. Test Scaffold Detail API View
        detail_url = reverse("reports:scaffold_detail", kwargs={"pk": scaffold.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Pilates Studio Management")

        # 4. Test ZIP Generation
        zip_buffer = create_scaffold_zip(scaffold, target="all")
        self.assertIsInstance(zip_buffer, BytesIO)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            namelist = zf.namelist()
            self.assertIn("frontend/AGENT.md", namelist)
            self.assertIn("backend/ARCHITECTURE.md", namelist)
            self.assertIn("SCOPE.md", namelist)
    def test_docx_text_extraction_and_analysis_endpoint(self):
        # Create an in-memory .docx archive
        docx_buf = BytesIO()
        with zipfile.ZipFile(docx_buf, "w") as zf:
            xml = '''<?xml version="1.0" encoding="UTF-8"?>
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
              <w:body>
                <w:p><w:r><w:t>Fleet Logistics Control Platform</w:t></w:r></w:p>
                <w:p><w:r><w:t>Real-time vehicle telemetry and dispatch system built with React, Node.js, and PostgreSQL.</w:t></w:r></w:p>
              </w:body>
            </w:document>'''
            zf.writestr("word/document.xml", xml.encode("utf-8"))

        docx_data = docx_buf.getvalue()

        # Test services.extract_text_from_docx_bytes directly
        from . import services
        title, text = services.extract_text_from_docx_bytes(docx_data)
        self.assertEqual(title, "Fleet Logistics Control Platform")
        self.assertIn("Real-time vehicle telemetry", text)

        # Test POST /api/scaffolds/analyze-scope/ with multipart docx file
        uploaded = SimpleUploadedFile("fleet-scope.docx", docx_data, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        url = reverse("reports:scaffold_analyze_scope")
        res = self.client.post(url, {"file": uploaded}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("extracted_text", res.data)
        self.assertIn("Fleet Logistics Control Platform", res.data["extracted_text"])

    def test_analyze_scope_binary_rejection_guard(self):
        # Raw binary zip header string submitted as JSON text should be rejected gracefully
        url = reverse("reports:scaffold_analyze_scope")
        corrupted_binary = "PK\x03\x04\x14\x00[Content_Types].xml\x00\x00some_binary_garbage_stream"
        res = self.client.post(url, {"scope_text": corrupted_binary}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Binary file content detected", res.data.get("detail", ""))

