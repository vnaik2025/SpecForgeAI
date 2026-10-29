from rest_framework import serializers

from .models import AiAnalysis, ProjectScaffold, Report, TechStackBlueprint


class AiAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiAnalysis
        fields = ("id", "summary_markdown", "created_at")


class ReportListSerializer(serializers.ModelSerializer):
    """Light version for lists and for creating."""

    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Report
        fields = ("id", "title", "content", "status", "status_label", "created_at")
        read_only_fields = ("id", "status", "status_label", "created_at")


class ReportDetailSerializer(ReportListSerializer):
    """Detail version: adds error and the nested AI analyses."""

    analyses = AiAnalysisSerializer(many=True, read_only=True)

    class Meta(ReportListSerializer.Meta):
        fields = ReportListSerializer.Meta.fields + ("error", "analyses")


class TechStackBlueprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechStackBlueprint
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "keywords",
            "file_structure",
            "coding_standards",
            "agent_instructions",
            "setup_commands",
            "created_at",
            "updated_at",
        )


class ProjectScaffoldListSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    blueprint_name = serializers.CharField(source="blueprint.name", read_only=True)

    class Meta:
        model = ProjectScaffold
        fields = (
            "id",
            "title",
            "description",
            "detected_tech_stack",
            "blueprint",
            "blueprint_name",
            "status",
            "status_label",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "detected_tech_stack", "status", "status_label", "created_at", "updated_at")


class ProjectScaffoldCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectScaffold
        fields = ("id", "title", "description", "scope_document", "blueprint", "custom_tech_stack", "custom_notes")
        read_only_fields = ("id",)

    def validate(self, attrs):
        scope_document = attrs.get("scope_document", "")
        title = attrs.get("title", "")
        from .services import extract_clean_text_from_scope_stream
        doc_title, clean_scope = extract_clean_text_from_scope_stream(scope_document)
        if clean_scope and clean_scope != scope_document:
            attrs["scope_document"] = clean_scope
        if doc_title and (not title or title in ["School Accessories Mart", "PulseDesk Issue Tracker", "Project Workspace"]):
            attrs["title"] = doc_title
        return attrs


class ProjectScaffoldDetailSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    blueprint_name = serializers.CharField(source="blueprint.name", read_only=True)

    class Meta:
        model = ProjectScaffold
        fields = (
            "id",
            "title",
            "description",
            "scope_document",
            "custom_tech_stack",
            "custom_notes",
            "detected_tech_stack",
            "blueprint",
            "blueprint_name",
            "status",
            "status_label",
            "error",
            "agents_md",
            "architecture_md",
            "setup_md",
            "skill_md",
            "api_setup_md",
            "initial_prompt",
            # Frontend Specifications (frontend/ folder)
            "frontend_agents_md",
            "frontend_architecture_md",
            "frontend_setup_md",
            "frontend_skill_md",
            "frontend_api_setup_md",
            "frontend_initial_prompt",
            # Backend Specifications (backend/ folder)
            "backend_agents_md",
            "backend_architecture_md",
            "backend_setup_md",
            "backend_skill_md",
            "backend_api_setup_md",
            "backend_initial_prompt",
            "ui_prototype_html",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "status_label", "created_at", "updated_at")