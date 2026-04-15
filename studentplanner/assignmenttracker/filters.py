import django_filters
from django import forms
from django.db.models import Q

from .models import Assignment, Course


class AssignmentFilter(django_filters.FilterSet):
    PRIORITY_CHOICES = (('', 'All Priorities'),) + tuple(Assignment.PriorityChoices.choices)
    STATUS_CHOICES = (
        ('', 'All Statuses'),
        ('complete', 'Completed'),
        ('incomplete', 'Incomplete'),
    )

    search = django_filters.CharFilter(
        method='filter_search',
        label='Search',
    )
    course = django_filters.ModelChoiceFilter(
        queryset=Course.objects.none(),
        empty_label='All Courses',
        label='Course',
    )
    priority = django_filters.ChoiceFilter(
        choices=PRIORITY_CHOICES,
        label='Priority',
    )
    status = django_filters.ChoiceFilter(
        method='filter_status',
        choices=STATUS_CHOICES,
        label='Status',
    )
    due_before = django_filters.DateFilter(
        field_name='due_date',
        lookup_expr='lte',
        label='Due On or Before',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
    )

    class Meta:
        model = Assignment
        fields = ['search', 'course', 'priority', 'status', 'due_before']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is not None:
            self.filters['course'].queryset = Course.objects.filter(user=user).order_by('name')

        self.form.fields['search'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Search assignments, descriptions, or courses',
        })
        self.form.fields['course'].widget.attrs.update({
            'class': 'form-select',
        })
        self.form.fields['priority'].widget.attrs.update({
            'class': 'form-select',
        })
        self.form.fields['status'].widget.attrs.update({
            'class': 'form-select',
        })

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(course__name__icontains=value) |
            Q(course__course_code__icontains=value)
        )

    def filter_status(self, queryset, name, value):
        if value == 'complete':
            return queryset.filter(is_completed=True)
        if value == 'incomplete':
            return queryset.filter(is_completed=False)
        return queryset