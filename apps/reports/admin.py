from django.contrib import admin

from .models import AiAnalysis, ProjectScaffold, Report, TechStackBlueprint

admin.site.register(Report)
admin.site.register(AiAnalysis)


@admin.register(TechStackBlueprint)
class TechStackBlueprintAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description", "keywords")


@admin.register(ProjectScaffold)
class ProjectScaffoldAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "blueprint", "status", "created_at")
    list_filter = ("status", "blueprint", "created_at")
    search_fields = ("title", "description", "scope_document")