import uuid

from django.conf import settings
from django.db import models

from .enums import ReportStatus, ScaffoldStatus


class Report(models.Model):
    STATUS_CHOICES = [(s.value, s.name.title()) for s in ReportStatus]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,   # delete user -> delete their reports
        related_name="reports",     # user.reports.all()
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    status = models.IntegerField(choices=STATUS_CHOICES, default=ReportStatus.PENDING.value)
    error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reports"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class AiAnalysis(models.Model):
    """One AI summary of a report. A report can be analysed many times."""

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="analyses")
    summary_markdown = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_analyses"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Analysis of {self.report_id}"


class TechStackBlueprint(models.Model):
    """Stored repository of tech stacks, preferred folder structures, and coding rules."""

    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(blank=True, default="")
    keywords = models.JSONField(
        default=list,
        help_text="Keywords to match against uploaded scopes (e.g. ['django', 'drf', 'react'])",
    )
    file_structure = models.TextField(
        help_text="Standard project directory structure tree for this tech stack"
    )
    coding_standards = models.TextField(
        help_text="Rules, design patterns, and conventions (e.g. thin views, repository pattern, DTOs)"
    )
    agent_instructions = models.TextField(
        help_text="Directives and constraints for AI coding agents (Antigravity, Cursor, etc.)"
    )
    setup_commands = models.TextField(
        help_text="Step-by-step setup commands and environment requirements"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tech_stack_blueprints"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProjectScaffold(models.Model):
    """A generated project scaffolding job based on an uploaded/pasted scope document."""

    SCAFFOLD_STATUS_CHOICES = [(s.value, s.name.title()) for s in ScaffoldStatus]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scaffolds",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    scope_document = models.TextField(help_text="The raw scope document or PRD text")
    custom_tech_stack = models.TextField(
        blank=True,
        default="",
        help_text="User-specified tech stack (languages, frameworks, tools) to override AI detection",
    )
    custom_notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional constraints, preferences or directives for the AI agent",
    )
    detected_tech_stack = models.CharField(max_length=150, blank=True, default="")
    blueprint = models.ForeignKey(
        TechStackBlueprint,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="scaffolds",
        help_text="The tech stack blueprint matched and applied to this project",
    )
    status = models.IntegerField(
        choices=SCAFFOLD_STATUS_CHOICES,
        default=ScaffoldStatus.DRAFT.value,
    )
    error = models.TextField(blank=True, default="")

    # General / Root Markdown Specifications
    agents_md = models.TextField(blank=True, default="")
    architecture_md = models.TextField(blank=True, default="")
    setup_md = models.TextField(blank=True, default="")
    skill_md = models.TextField(blank=True, default="")
    api_setup_md = models.TextField(blank=True, default="")
    initial_prompt = models.TextField(blank=True, default="")

    # Frontend-Specific Markdown Specifications (frontend/ folder)
    frontend_agents_md = models.TextField(blank=True, default="")
    frontend_architecture_md = models.TextField(blank=True, default="")
    frontend_setup_md = models.TextField(blank=True, default="")
    frontend_skill_md = models.TextField(blank=True, default="")
    frontend_api_setup_md = models.TextField(blank=True, default="")
    frontend_initial_prompt = models.TextField(blank=True, default="")

    # Backend-Specific Markdown Specifications (backend/ folder)
    backend_agents_md = models.TextField(blank=True, default="")
    backend_architecture_md = models.TextField(blank=True, default="")
    backend_setup_md = models.TextField(blank=True, default="")
    backend_skill_md = models.TextField(blank=True, default="")
    backend_api_setup_md = models.TextField(blank=True, default="")
    backend_initial_prompt = models.TextField(blank=True, default="")

    ui_prototype_html = models.TextField(
        blank=True,
        default="",
        help_text="AI-generated interactive single-file UI prototype HTML",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_scaffolds"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"