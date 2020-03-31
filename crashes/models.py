from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class EventGroup(models.Model):
    group_id = models.IntegerField()

    def __str__(self):
        return f"{self.group_id}"

class EventTag(models.Model):
    key = models.CharField(max_length=255)

    def __str__(self):
        return self.key

class EventTagKeyed(models.Model):
    event_tag = models.ForeignKey(EventTag, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    class Meta:
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
    categories = models.ManyToManyField(Category, through='AssignedCategory')

    def __str__(self):
        return f"{self.sentry_id} : {self.message}"

class AssignedCategory(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    confidence = models.FloatField()

class Stacktrace(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    stacktrace = models.TextField()

    def __str__(self):
        return f"Stacktrace for {self.event.message}"
