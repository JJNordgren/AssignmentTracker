from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone

import pdfkit

from .filters import AssignmentFilter
from .forms import AssignmentForm, CourseForm, SignUpForm
from .models import Assignment, Course


def apply_assignment_sorting(queryset, sort_option):
    if sort_option == 'due_desc':
        return queryset.order_by('is_completed', '-due_date', 'priority', 'title')

    if sort_option == 'priority_high':
        return queryset.order_by('is_completed', 'priority', 'due_date', 'title')

    if sort_option == 'priority_low':
        return queryset.order_by('is_completed', '-priority', 'due_date', 'title')

    if sort_option == 'status_complete':
        return queryset.order_by('-is_completed', 'due_date', 'priority', 'title')

    if sort_option == 'status_incomplete':
        return queryset.order_by('is_completed', 'due_date', 'priority', 'title')

    if sort_option == 'title_az':
        return queryset.order_by('is_completed', 'title')

    return queryset.order_by('is_completed', 'due_date', 'priority', 'title')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your account was created successfully.')
            return redirect('dashboard')
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


@login_required
def dashboard(request):
    assignments = Assignment.objects.filter(user=request.user).select_related('course')

    assignment_filter = AssignmentFilter(
        request.GET,
        queryset=assignments,
        user=request.user,
    )

    filtered_assignments = assignment_filter.qs

    today = timezone.localdate()
    due_soon_date = today + timedelta(days=7)

    hide_old_completed = request.GET.get('hide_old_completed', 'on') == 'on'

    if hide_old_completed:
        cutoff_date = today - timedelta(days=7)
        filtered_assignments = filtered_assignments.exclude(
            is_completed=True,
            due_date__lt=cutoff_date
        )

    sort_option = request.GET.get('sort', 'due_asc')
    filtered_assignments = apply_assignment_sorting(filtered_assignments, sort_option)

    paginator = Paginator(filtered_assignments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    summary_queryset = filtered_assignments
    incomplete_queryset = summary_queryset.filter(is_completed=False)

    overdue_count = incomplete_queryset.filter(due_date__lt=today).count()
    due_today_count = incomplete_queryset.filter(due_date=today).count()
    due_soon_count = incomplete_queryset.filter(
        due_date__gt=today,
        due_date__lte=due_soon_date
    ).count()

    query_params = request.GET.copy()
    query_params.pop('page', None)

    context = {
        'filter': assignment_filter,
        'page_obj': page_obj,
        'query_string': query_params.urlencode(),
        'today': today,
        'due_soon_date': due_soon_date,
        'sort_option': sort_option,
        'hide_old_completed': hide_old_completed,
        'filtered_count': summary_queryset.count(),
        'incomplete_count': incomplete_queryset.count(),
        'overdue_count': overdue_count,
        'due_today_count': due_today_count,
        'due_soon_count': due_soon_count,
        'course_count': Course.objects.filter(user=request.user).count(),
    }

    return render(request, 'assignmenttracker/dashboard.html', context)


@login_required
def update_assignment_statuses(request):
    if request.method != 'POST':
        return redirect('dashboard')

    current_page_ids = request.POST.getlist('visible_assignment_ids')
    completed_ids = set(request.POST.getlist('completed_assignments'))
    next_url = request.POST.get('next', '')

    if current_page_ids:
        assignments_on_page = Assignment.objects.filter(
            user=request.user,
            pk__in=current_page_ids
        )

        for assignment in assignments_on_page:
            assignment.is_completed = str(assignment.pk) in completed_ids
            assignment.save(update_fields=['is_completed', 'updated_at'])

        messages.success(request, 'Assignment statuses updated successfully.')

    if next_url:
        return redirect(next_url)

    return redirect('dashboard')


@login_required
def course_list(request):
    courses = Course.objects.filter(user=request.user).order_by('name')

    return render(request, 'assignmenttracker/course_list.html', {
        'courses': courses,
    })


@login_required
def course_add(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.user = request.user
            course.save()

            messages.success(request, 'Course added successfully.')
            return redirect('course_list')
    else:
        form = CourseForm()

    return render(request, 'assignmenttracker/course_form.html', {
        'form': form,
        'page_title': 'Add Course',
        'button_text': 'Save Course',
    })


@login_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()

            messages.success(request, 'Course updated successfully.')
            return redirect('course_list')
    else:
        form = CourseForm(instance=course)

    return render(request, 'assignmenttracker/course_form.html', {
        'form': form,
        'page_title': 'Edit Course',
        'button_text': 'Update Course',
    })


@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)

    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully.')
        return redirect('course_list')

    return render(request, 'assignmenttracker/course_confirm_delete.html', {
        'course': course,
    })


@login_required
def assignment_add(request):
    if request.method == 'POST':
        form = AssignmentForm(request.POST, user=request.user)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.user = request.user
            assignment.save()

            messages.success(request, 'Assignment added successfully.')
            return redirect('dashboard')
    else:
        form = AssignmentForm(user=request.user)

    return render(request, 'assignmenttracker/assignment_form.html', {
        'form': form,
        'page_title': 'Add Assignment',
        'button_text': 'Save Assignment',
    })


@login_required
def assignment_edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)

    if request.method == 'POST':
        form = AssignmentForm(request.POST, instance=assignment, user=request.user)
        if form.is_valid():
            form.save()

            messages.success(request, 'Assignment updated successfully.')
            return redirect('dashboard')
    else:
        form = AssignmentForm(instance=assignment, user=request.user)

    return render(request, 'assignmenttracker/assignment_form.html', {
        'form': form,
        'page_title': 'Edit Assignment',
        'button_text': 'Update Assignment',
    })


@login_required
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)

    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Assignment deleted successfully.')
        return redirect('dashboard')

    return render(request, 'assignmenttracker/assignment_confirm_delete.html', {
        'assignment': assignment,
    })


@login_required
def export_assignments_pdf(request):
    assignments = Assignment.objects.filter(user=request.user).select_related('course')

    assignment_filter = AssignmentFilter(
        request.GET,
        queryset=assignments,
        user=request.user,
    )

    filtered_assignments = assignment_filter.qs.filter(is_completed=False)

    sort_option = request.GET.get('sort', 'due_asc')
    filtered_assignments = apply_assignment_sorting(filtered_assignments, sort_option)

    html = render_to_string('assignmenttracker/assignment_pdf.html', {
        'assignments': filtered_assignments,
        'user': request.user,
        'generated_on': timezone.now(),
    })

    options = {
        'page-size': 'Letter',
        'encoding': 'UTF-8',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.5in',
        'margin-left': '0.5in',
    }

    try:
        pdf = pdfkit.from_string(html, False, options=options)
    except OSError:
        return HttpResponse(
            'PDF export is not ready yet because wkhtmltopdf is not installed or is not on your system PATH.',
            status=500
        )

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="assignment_list.pdf"'
    return response