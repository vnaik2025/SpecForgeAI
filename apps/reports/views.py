import logging
import re
from django.http import FileResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .enums import ReportStatus, ScaffoldStatus
from .models import ProjectScaffold, Report, TechStackBlueprint

logger = logging.getLogger(__name__)


class DashboardView(TemplateView):
    """Interactive Web Dashboard for Project Scaffolding."""
    template_name = "index.html"
from .serializers import (
    AiAnalysisSerializer,
    ProjectScaffoldCreateSerializer,
    ProjectScaffoldDetailSerializer,
    ProjectScaffoldListSerializer,
    ReportDetailSerializer,
    ReportListSerializer,
    TechStackBlueprintSerializer,
)


class OwnedReportsMixin:
    """Every query is limited to the logged-in user's reports."""

    def get_queryset(self):
        return Report.objects.filter(owner=self.request.user)


class ReportListCreateView(OwnedReportsMixin, generics.ListCreateAPIView):
    """GET /api/reports/  -> my reports
    POST /api/reports/ -> create one"""

    serializer_class = ReportListSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ReportDetailView(OwnedReportsMixin, generics.RetrieveAPIView):
    """GET /api/reports/<uuid>/ -> one report with its analyses"""

    serializer_class = ReportDetailSerializer


class AnalyseReportView(APIView):
    """POST /api/reports/<uuid>/analyse/ -> run AI analysis (synchronous)."""

    def post(self, request, pk):
        try:
            report = Report.objects.get(pk=pk, owner=request.user)
        except Report.DoesNotExist:
            raise NotFound("Report not found.")

        if report.status == ReportStatus.PROCESSING.value:
            return Response({"detail": "Report is already being analysed."},
                            status=status.HTTP_409_CONFLICT)

        try:
            analysis = services.analyse_report(report)
        except Exception as exc:
            return Response({"detail": f"AI analysis failed: {exc}"},
                            status=status.HTTP_502_BAD_GATEWAY)

        return Response(
            {"status": "COMPLETED", "analysis": AiAnalysisSerializer(analysis).data},
            status=status.HTTP_200_OK,
        )


# --- Project Scaffolding & Blueprint Views ---


class TechStackBlueprintListView(generics.ListCreateAPIView):
    """GET /api/scaffolds/blueprints/ -> List all available tech stack blueprints
    POST /api/scaffolds/blueprints/ -> Add custom company blueprint"""

    queryset = TechStackBlueprint.objects.all()
    serializer_class = TechStackBlueprintSerializer
    permission_classes = [AllowAny]


class TechStackBlueprintDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/scaffolds/blueprints/<id>/"""

    queryset = TechStackBlueprint.objects.all()
    serializer_class = TechStackBlueprintSerializer
    permission_classes = [AllowAny]


class OwnedScaffoldsMixin:
    """Every query is scoped strictly to the authenticated user."""

    def get_queryset(self):
        return ProjectScaffold.objects.filter(owner=self.request.user)


class AnalyzeScopeDocumentView(APIView):
    """
    POST /api/scaffolds/analyze-scope/
    Instant 1st-place AI analysis of an uploaded scope document or PDF.
    Extracts project title, summary, categorized tech stack (frontend, backend, database, libraries/services),
    matching blueprint, architectural notes, and ideated core modules.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        scope_text = request.data.get("scope_text", "")
        filename = request.data.get("filename", "")

        # Also support direct multipart file upload
        uploaded_file = request.FILES.get("file")
        if uploaded_file and not scope_text:
            filename = uploaded_file.name
            try:
                content_bytes = uploaded_file.read()
                try:
                    scope_text = content_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    scope_text = content_bytes.decode("latin-1", errors="ignore")
            except Exception as e:
                return Response(
                    {"detail": f"Could not read uploaded file: {e}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if not scope_text or not scope_text.strip():
            return Response(
                {"detail": "No scope document content or file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = services.extract_scope_fields_with_ai(scope_text, filename=filename)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.exception("AI scope analysis endpoint error: %s", exc)
            return Response(
                {"detail": f"Scope analysis failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ScaffoldListCreateView(OwnedScaffoldsMixin, generics.ListCreateAPIView):
    """GET /api/scaffolds/ -> List my generated scaffolds
    POST /api/scaffolds/ -> Create new scaffold from scope"""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectScaffoldCreateSerializer
        return ProjectScaffoldListSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ScaffoldDetailView(OwnedScaffoldsMixin, generics.RetrieveAPIView):
    """GET /api/scaffolds/<uuid>/ -> Get complete generated specs & status"""

    permission_classes = [IsAuthenticated]
    serializer_class = ProjectScaffoldDetailSerializer


class GenerateScaffoldView(APIView):
    """POST /api/scaffolds/<uuid>/generate/ -> Triggers AI analysis & spec generation"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            scaffold = ProjectScaffold.objects.get(pk=pk, owner=request.user)
        except ProjectScaffold.DoesNotExist:
            raise NotFound("Scaffold not found.")

        if scaffold.status == ScaffoldStatus.PROCESSING.value:
            return Response(
                {"detail": "Scaffold generation is currently in progress."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            updated = services.generate_project_scaffold(scaffold)
        except Exception as exc:
            return Response(
                {"detail": f"Scaffold generation failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            ProjectScaffoldDetailSerializer(updated).data,
            status=status.HTTP_200_OK,
        )


class DownloadScaffoldZipView(APIView):
    """GET /api/scaffolds/<uuid>/download/?target=all|frontend|backend -> Streams the requested zip directly"""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            scaffold = ProjectScaffold.objects.get(pk=pk)
        except ProjectScaffold.DoesNotExist:
            raise NotFound("Scaffold not found.")

        target = request.GET.get("target", "all").lower()
        if target not in ("all", "frontend", "backend"):
            target = "all"

        buffer = services.create_scaffold_zip(scaffold, target=target)
        clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '', scaffold.title.lower().replace(" ", "-"))[:30] or "project"
        if target == "frontend":
            filename = f"{clean_name}-frontend-specs.zip"
        elif target == "backend":
            filename = f"{clean_name}-backend-specs.zip"
        else:
            filename = f"{clean_name}-scaffold.zip"

        response = FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/zip",
        )
        response["Access-Control-Expose-Headers"] = "Content-Disposition"
        return response


class GenerateUiPrototypeView(APIView):
    """POST /api/scaffolds/<uuid>/generate-ui/ -> Synthesizes single-file HTML/Tailwind UI prototype"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            scaffold = ProjectScaffold.objects.get(pk=pk, owner=request.user)
        except ProjectScaffold.DoesNotExist:
            raise NotFound("Scaffold not found.")

        try:
            html = services.generate_ui_prototype(scaffold)
            return Response(
                {
                    "id": str(scaffold.id),
                    "title": scaffold.title,
                    "ui_prototype_html": html,
                    "status": "success",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {"detail": f"UI Prototype synthesis failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

