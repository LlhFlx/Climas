

# ===== From: experiences/urls.py =====



# ===== From: proposals/urls.py =====



# ===== From: proponent_forms/urls.py =====



# ===== From: people/urls.py =====



# ===== From: thematic_axes/urls.py =====



# ===== From: core/urls.py =====



# ===== From: expressions/urls.py =====



# ===== From: intersectionality/urls.py =====



# ===== From: institutions/urls.py =====

from django.urls import path
from . import views

app_name = 'institutions' #Enable institutions:detail

urlpatterns = [
    #path('', views.institution_list, name='list'),
    path('<int:pk>', views.institution_detail, name='detail'),
    #path('create/', views.institution.create, name='create')
]

# ===== From: antecedents/urls.py =====



# ===== From: strategic_effects/urls.py =====



# ===== From: products/urls.py =====



# ===== From: calls/urls.py =====

from django.urls import path
from . import views

app_name = 'calls'

urlpatterns = [
    # Calls
    path('researcher/', views.researcher_dashboard, name='researcher_dashboard'),
    path('coordinator/', views.coordinator_dashboard, name='coordinator_dashboard'),
    path('institution/create/', views.create_institution, name='create_institution'),
    path('create/', views.create_call, name='create_call'),
    path('<int:call_pk>/setup/', views.setup_call, name='setup_call'),
    path('<int:call_pk>/', views.call_detail, name='call_detail'),
    path('<int:call_pk>/apply/', views.apply_call, name='apply_call'),
    path('<int:call_pk>/view/', views.view_call, name='view_call'), 

    # Shared Questions
    path('shared-question/create/', views.create_shared_question, name='create_shared_question'),
    path('shared-question/<int:question_id>/edit/', views.edit_shared_question, name='edit_shared_question'),
    path('shared-question/<int:question_id>/delete/', views.delete_shared_question, name='delete_shared_question'),
    path('shared-question/preview/<str:model_path>/', views.preview_source_model, name='preview_source_model'),
    
    # Thematic Axes
    path('thematic-axis/create/', views.create_thematic_axis, name='create_thematic_axis'),
    path('thematic-axis/<int:axis_id>/edit/', views.edit_thematic_axis, name='edit_thematic_axis'),
    path('thematic-axis/<int:axis_id>/delete/', views.delete_thematic_axis, name='delete_thematic_axis'),


    # Strategic Effects
    path('strategic-effect/create/', views.create_strategic_effect, name='create_strategic_effect'),
    path('strategic-effect/<int:effect_id>/edit/', views.edit_strategic_effect, name='edit_strategic_effect'),
    path('strategic-effect/<int:effect_id>/delete/', views.delete_strategic_effect, name='delete_strategic_effect'),

    # URL for filtered strategic effects
    path('strategic-effects/', views.get_strategic_effects_by_axis, name='get_strategic_effects_by_axis'),

    # Budgets
    path('budget-category/create/', views.create_budget_category, name='create_budget_category'),
    path('budget-category/<int:category_id>/edit/', views.edit_budget_category, name='edit_budget_category'),
    path('budget-category/<int:category_id>/delete/', views.delete_budget_category, name='delete_budget_category'),

    path('budget-period/create/', views.create_budget_period, name='create_budget_period'),
    path('budget-period/<int:period_id>/edit/', views.edit_budget_period, name='edit_budget_period'),
    path('budget-period/<int:period_id>/delete/', views.delete_budget_period, name='delete_budget_period'),
]

# ===== From: project_team/urls.py =====



# ===== From: geo/urls.py =====



# ===== From: cbo/urls.py =====



# ===== From: budgets/urls.py =====



# ===== From: evaluations/urls.py =====



# ===== From: common/urls.py =====



# ===== From: accounts/urls.py =====

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
    

    # Profile Management
    path('profile/', views.profile_view, name='profile'),
    
    # Role Requests
    path('request-coordinator/', views.request_coordinator_access, name='request_coordinator'),
    path('request-evaluator/', views.request_evaluator_access, name='request_evaluator'),
    
    # Password Reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
]