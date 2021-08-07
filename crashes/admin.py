from django.contrib import admin
from django.db.models import Count

from .models import (
    AssignedCategory, Category, Event, Stacktrace, EventTag, EventGroup, EventTagKeyed,
    Project, CategoryCount, ComputedTrend, ProjectEndpointCache)

class StacktraceInline(admin.TabularInline):
    model = Stacktrace

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
admin.site.register(Event, EventAdmin)

class EventTagAdmin(admin.ModelAdmin):
    list_display = ('key',)
admin.site.register(EventTag, EventTagAdmin)

class EventTagKeyedAdmin(admin.ModelAdmin):
    list_display = ('tag_key', 'value')
    list_filter = ('event_tag',)

    def tag_key(self, obj):
        return obj.event_tag.key

admin.site.register(EventTagKeyed, EventTagKeyedAdmin)

class CategoryAdmin(admin.ModelAdmin):
    ordering = ('name',)

admin.site.register(Category, CategoryAdmin)

class AssignedCategoryAdmin(admin.ModelAdmin):
    list_display = ('group', 'category')
    list_filter = ('category',)

admin.site.register(AssignedCategory, AssignedCategoryAdmin)

class StacktraceAdmin(admin.ModelAdmin):
    list_display = ('event', 'processed',)
    list_filter = ('processed',)

admin.site.register(Stacktrace, StacktraceAdmin)

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'events_endpoint')

admin.site.register(Project, ProjectAdmin)

admin.site.register(EventGroup)

class CategoryCountAdmin(admin.ModelAdmin):
    list_display = ('date', 'category', 'info_count', 'fatal_count')
    list_filter = ('category__project',)
    date_hierarchy = 'date'

admin.site.register(CategoryCount, CategoryCountAdmin)

class ComputedTrendAdmin(admin.ModelAdmin):
    list_display = ('category', 'for_date', 'days_back', 'info_trend', 'fatal_trend')
    list_filter = ('category__project',)

admin.site.register(ComputedTrend, ComputedTrendAdmin)

@admin.register(ProjectEndpointCache)
class ProjectEndpointCacheAdmin(admin.ModelAdmin):
    list_filter = ('project',)
    list_display = ('project', 'sample_date')
    date_hierarchy = 'sample_date'
