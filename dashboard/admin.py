from django.contrib import admin

from .models import State, Scheme, Initiative, Report

# Admin branding
admin.site.site_header = "MHRD Dashboard Admin"
admin.site.site_title = "MHRD Admin"
admin.site.index_title = "Administration"


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "lat", "lng")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 50


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 50


@admin.register(Initiative)
class InitiativeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "state",
        "scheme",
        "category",
        "year",
        "status",
        "progress",
        "schools_impacted",
        "students_impacted",
        "scholarships_awarded",
        "budget_utilized",
    )
    list_filter = ("year", "category", "status", "scheme", "state")
    search_fields = ("name", "state__name", "scheme__name", "category", "status")
    ordering = ("-year", "name")
    list_select_related = ("state", "scheme")
    autocomplete_fields = ("state", "scheme")
    list_per_page = 50


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("report_id", "status", "created_at")
    search_fields = ("report_id", "status")
    list_filter = ("status",)
    readonly_fields = ("report_id", "created_at")
    ordering = ("-created_at",)
    list_per_page = 50
