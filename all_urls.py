

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

    path('document/<int:doc_id>/download/', views.download_expression_document, name='download_expression_document'),
    path('render/institution-input/', views.render_institution_input, name='render_institution_input'),
    path('create-institution-page/', views.create_institution_page, name='create_institution_page'),
    path('create-person-page/', views.create_person_page, name='create_person_page'),
]

# ===== From: project_team/urls.py =====



# ===== From: geo/urls.py =====



# ===== From: cbo/urls.py =====



# ===== From: budgets/urls.py =====



# ===== From: evaluations/urls.py =====

from django.urls import path
from . import views

app_name = 'evaluations'

urlpatterns = [
    # Coordinator: Manage Templates & Assignments
    path('coordinator/templates/', 
        views.coordinator_evaluations_dashboard, 
        name='coordinator_templates'),

    path('template/create/', 
        views.create_evaluation_template, 
        name='create_template'),

    path('template/<int:template_id>/edit/', 
        views.edit_evaluation_template, 
        name='edit_template'),

    path('template/<int:template_id>/delete/', 
        views.delete_evaluation_template, 
        name='delete_template'),

    path('template/<int:template_id>/', 
        views.evaluation_template_detail, 
        name='template_detail'),

    path('template/category/create/', 
        views.create_template_category, 
        name='create_template_category'),

    path('template/category/<int:category_id>/edit/',  
        views.edit_template_category, 
        name='edit_template_category'),

    path('template/category/<int:category_id>/delete/', 
        views.delete_template_category, 
        name='delete_template_category'),

    path('template/item/create/',
        views.create_template_item, 
        name='create_template_item'),

    path('template/item/<int:item_id>/edit/', 
        views.edit_template_item, 
        name='edit_template_item'),

    path('template/item/<int:item_id>/delete/', 
        views.delete_template_item, 
        name='delete_template_item'),

    path('template/item/<int:item_id>/get/', 
        views.get_template_item, 
        name='get_template_item'),

    path('template/<int:template_id>/link-call/', 
        views.link_template_to_call, 
        name='link_template_to_call'),

    path('template/<int:template_id>/unlink-call/<int:call_id>/', 
        views.unlink_template_from_call, 
        name='unlink_template_from_call'),

    # Generic Target Assignment
    path('<str:target_type>/<int:target_id>/assign-evaluator/', 
        views.assign_evaluator, 
        name='assign_evaluator'),

    # Evaluator Workflow
    path('evaluator/dashboard/', 
        views.evaluator_dashboard, 
        name='evaluator_dashboard'),

    path('evaluate/<int:evaluation_id>/', 
        views.evaluate_expression, 
        name='evaluate_expression'),

    # Coordinator: View All Evaluations
    path('coordinator/evaluations/all/', 
        views.coordinator_view_evaluations, 
        name='coordinator_view_evaluations'),

    path('evaluation/<int:evaluation_id>/detail-json/',
        views.evaluation_detail_json,
        name='evaluation_detail_json'),
]



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