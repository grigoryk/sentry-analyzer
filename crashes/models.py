from django.db import models
import functools

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def group_count(self):
        return self.eventgroup_set.all().count()

    # todo ugh, these should be sql instead

    def event_count(self):
        return functools.reduce(lambda sum, eg: sum + eg.event_count(), self.eventgroup_set.all(), 0)

    def event_info_count(self):
        return functools.reduce(lambda sum, eg: sum + eg.event_info_count(), self.eventgroup_set.all(), 0)

    def event_fatal_count(self):
        return functools.reduce(lambda sum, eg: sum + eg.event_fatal_count(), self.eventgroup_set.all(), 0)

class EventGroup(models.Model):
    group_id = models.IntegerField()
    categories = models.ManyToManyField(Category, through='AssignedCategory')

    def __str__(self):
        return f"{self.group_id} (events: {self.event_count()})"

    def event_info_count(self):
        return self.event_set.filter(tags__value='info', tags__event_tag__key='level').count()

    def event_fatal_count(self):
        return self.event_set.exclude(tags__value='info', tags__event_tag__key='level').count()

    def event_count(self):
        return self.event_set.all().count()

class EventTag(models.Model):
    key = models.CharField(max_length=255)

    def __str__(self):
        return self.key

class EventTagKeyed(models.Model):
    event_tag = models.ForeignKey(EventTag, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    class Meta:
        # running a data import from sentry somehow produced a constraint violation that wasn't caught during an insert.
        # had to find it manually and resolve it (by deleting bad records).
        # >>> r = EventTagKeyed.objects.raw('select * from crashes_eventtagkeyed group by event_tag_id, value having count(*) > 1')
        # >>> r[0]
        # <EventTagKeyed: device = Joy 1+>
        # >>> r[1]
        # <EventTagKeyed: device = LG-V400>
        # >>> r[2]
        # Traceback (most recent call last):
        #   File "<console>", line 1, in <module>
        #   File "/Users/grishakruglov/Code/sentry-analyzer/venv/lib/python3.9/site-packages/django/db/models/query.py", line 1526, in __getitem__
        #     return list(self)[k]
        # IndexError: list index out of range
        # >>> r[0].delete()
        # >>> r[1].delete()
        unique_together = ['event_tag', 'value']

    def __str__(self):
        return f"{self.event_tag.key} = {self.value}"

class Event(models.Model):
    group = models.ForeignKey(EventGroup, on_delete=models.CASCADE)
    event_id = models.CharField(max_length=255)
    sentry_id = models.IntegerField()
    event_received = models.DateTimeField()
    event_created = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=500, null=True, blank=True)
    tags = models.ManyToManyField(EventTagKeyed)
    info = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ['-event_created',]

    def is_info(self):
        if self.info is None:
            self.info = self.tags.filter(value='info', event_tag__key='level').count() > 0
            return self.info
        else:
            return self.info

    def __str__(self):
        return f"{self.sentry_id} : {self.message}"

class AssignedCategory(models.Model):
    group = models.ForeignKey(EventGroup, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    confidence = models.FloatField(default=1.0)

class Stacktrace(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    stacktrace = models.TextField()

    def __str__(self):
        return f"Stacktrace for {self.event.message}"
