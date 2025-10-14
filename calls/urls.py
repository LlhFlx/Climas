from django.urls import path, include
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
    path('expression/<int:expression_id>/apply-proposal/', views.apply_proposal, name='apply_proposal'),
    path('upload-commitment/', views.upload_commitment_document, name='upload_commitment_document'),

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
    
    path('proposals/', include('proposals.urls', namespace='proposals')),
]