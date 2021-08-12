from django.contrib import admin
from django.db.models import Count

from .models import (
    AssignedCategory, Category, Event, Stacktrace, EventTag, EventGroup, EventTagKeyed,
    Project, CategoryCount, ComputedTrend, ProjectEndpointCache, Organization, ProcessEventTag)

class StacktraceInline(admin.TabularInline):
    model = Stacktrace

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'sentry_id', 'message', 'is_info', 'event_created')
    list_filter = ('project',)
    search_fields = ['tags__value', 'sentry_id', 'event_id', 'group__group_id', 'message']
    date_hierarchy = 'event_created'

    def group_id(self, obj):
        return obj.group.group_id

    inlines = [
        StacktraceInline,
    ]

@admin.register(EventTag)
class EventTagAdmin(admin.ModelAdmin):
    list_display = ('key',)

@admin.register(EventTagKeyed)
class EventTagKeyedAdmin(admin.ModelAdmin):
    list_display = ('tag_key', 'value')
    list_filter = ('event_tag',)

    def tag_key(self, obj):
        return obj.event_tag.key

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    ordering = ('name',)

@admin.register(AssignedCategory)
class AssignedCategoryAdmin(admin.ModelAdmin):
    list_display = ('group', 'category')
    list_filter = ('category',)

@admin.register(Stacktrace)
class StacktraceAdmin(admin.ModelAdmin):
    list_display = ('event', 'processed',)
    list_filter = ('processed',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'org', 'events_endpoint')
    list_filter = ('org',)

@admin.register(CategoryCount)
class CategoryCountAdmin(admin.ModelAdmin):
    list_display = ('date', 'category', 'keyed_tag', 'info_count', 'fatal_count')
    list_filter = ('category__project',)
    date_hierarchy = 'date'

@admin.register(ComputedTrend)
class ComputedTrendAdmin(admin.ModelAdmin):
    list_display = ('category', 'for_date', 'days_back', 'info_trend', 'fatal_trend')
    list_filter = ('category__project',)

@admin.register(ProjectEndpointCache)
class ProjectEndpointCacheAdmin(admin.ModelAdmin):
    list_filter = ('project',)
    list_display = ('project', 'sample_date')
    date_hierarchy = 'sample_date'

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')

@admin.register(ProcessEventTag)
class ProcessEventTagAdmin(admin.ModelAdmin):
    list_display = ('project', 'event_tag',)
    list_filter = ('project',)

admin.site.register(EventGroup)