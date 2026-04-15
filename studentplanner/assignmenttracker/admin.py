from django.contrib import admin
from .models import Course, Assignment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'course_code', 'user', 'created_at')
    search_fields = ('name', 'course_code', 'user__username')


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'due_date', 'priority', 'is_completed', 'user')
    list_filter = ('priority', 'is_completed', 'due_date')
    search_fields = ('title', 'description', 'course__name', 'user__username')