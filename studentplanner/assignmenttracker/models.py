from django.conf import settings
from django.db import models


class Course(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses'
    )

    name = models.CharField(max_length=100)
    course_code = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        if self.course_code:
            return f"{self.course_code} - {self.name}"
        return self.name


class Assignment(models.Model):
    class PriorityChoices(models.IntegerChoices):
        HIGH = 1, 'High'
        MEDIUM = 2, 'Medium'
        LOW = 3, 'Low'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments'
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    priority = models.PositiveSmallIntegerField(
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM
    )
    is_completed = models.BooleanField(default=False)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['is_completed', 'due_date', 'priority', 'title']

    def __str__(self):
        return self.title