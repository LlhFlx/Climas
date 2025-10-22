# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
     # Registration and Login
     path('register/', views.register_view, name='register'),
     path('login/', views.login_view, name='login'),
     path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
     path('document-types/<int:country_id>/', views.get_document_types_by_country, name='document_types_by_country'),
     path('confirm-email/<uidb64>/<token>/', views.confirm_email, name='confirm_email'),
     # Password Reset
     path('password-reset/',
          auth_views.PasswordResetView.as_view(
               template_name='accounts/password_reset.html',
               email_template_name='accounts/password_reset_email.html',
               subject_template_name='accounts/password_reset_subject.txt',
               success_url='/accounts/password-reset/done/'
          ),
          name='password_reset'),

     path('password-reset/done/',
          auth_views.PasswordResetDoneView.as_view(
               template_name='accounts/password_reset_done.html'
          ),
          name='password_reset_done'),

     path('reset/<uidb64>/<token>/',
          auth_views.PasswordResetConfirmView.as_view(
               template_name='accounts/password_reset_confirm.html',
               success_url='/accounts/reset/done/'
          ),
          name='password_reset_confirm'),

     path('reset/done/',
          auth_views.PasswordResetCompleteView.as_view(
               template_name='accounts/password_reset_complete.html'
          ),
          name='password_reset_complete'),

    # Profile Management
    path('profile/', views.profile_view, name='profile'),
    
    # Role Requests
    path('request-coordinator/', views.request_coordinator_access, name='request_coordinator'),
    path('request-evaluator/', views.request_evaluator_access, name='request_evaluator'),
]