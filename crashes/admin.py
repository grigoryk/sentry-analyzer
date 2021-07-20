from django.contrib import admin
from django.db.models import Count

from .models import AssignedCategory, Category, Event, Stacktrace, EventTag, EventGroup, EventTagKeyed

class StacktraceInline(admin.TabularInline):
    model = Stacktrace

class EventAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'sentry_id', 'message', 'is_info')
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

admin.site.register(Stacktrace)
