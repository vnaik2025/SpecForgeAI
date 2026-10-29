from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    # Legacy Reports API
    path("reports/", views.ReportListCreateView.as_view(), name="report_list"),
    path("reports/<uuid:pk>/", views.ReportDetailView.as_view(), name="report_detail"),
    path("reports/<uuid:pk>/analyse/", views.AnalyseReportView.as_view(), name="report_analyse"),

    # Tech Stack Blueprints
    path("blueprints/", views.TechStackBlueprintListView.as_view(), name="blueprint_list"),
    path("blueprints/<int:pk>/", views.TechStackBlueprintDetailView.as_view(), name="blueprint_detail"),

    # Project Scaffolding API
    path("scaffolds/", views.ScaffoldListCreateView.as_view(), name="scaffold_list"),
    path("scaffolds/analyze-scope/", views.AnalyzeScopeDocumentView.as_view(), name="scaffold_analyze_scope"),
    path("scaffolds/<uuid:pk>/", views.ScaffoldDetailView.as_view(), name="scaffold_detail"),
    path("scaffolds/<uuid:pk>/generate/", views.GenerateScaffoldView.as_view(), name="scaffold_generate"),
    path("scaffolds/<uuid:pk>/generate-ui/", views.GenerateUiPrototypeView.as_view(), name="scaffold_generate_ui"),
    path("scaffolds/<uuid:pk>/download/", views.DownloadScaffoldZipView.as_view(), name="scaffold_download"),
]