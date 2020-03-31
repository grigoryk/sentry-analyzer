from django.contrib import admin

from .models import Category, Event, Stacktrace, EventTag, EventGroup, EventTagKeyed

class StacktraceInline(admin.TabularInline):
    model = Stacktrace

class EventAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'sentry_id', 'message')
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

admin.site.register(Category)
admin.site.register(Stacktrace)