from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import BootstrapAuthenticationForm
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            authentication_form=BootstrapAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup_view, name='signup'),

    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_add, name='course_add'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),

    path('assignments/add/', views.assignment_add, name='assignment_add'),
    path('assignments/<int:pk>/edit/', views.assignment_edit, name='assignment_edit'),
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),
    path('assignments/update-statuses/', views.update_assignment_statuses, name='update_assignment_statuses'),

    path('assignments/export/pdf/', views.export_assignments_pdf, name='export_assignments_pdf'),
]