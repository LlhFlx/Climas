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

    path('template/subcategory/create/',
        views.create_template_subcategory,
        name='create_template_subcategory'),

    path('template/subcategory/<int:subcategory_id>/edit/',
        views.edit_template_subcategory,
        name='edit_template_subcategory'),

    path('template/subcategory/<int:subcategory_id>/delete/',
        views.delete_template_subcategory,
        name='delete_template_subcategory'),

    path('template/item/load-dynamic-options/',
        views.load_dynamic_options,
        name='load_dynamic_options'),

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

    path('serve-pdf/<int:evaluation_id>/<str:doc_type>/', 
        views.serve_pdf, 
        name='serve_pdf'),

    path('get-document-url/<int:evaluation_id>/<str:doc_type>/', 
        views.get_document_url, 
        name='get_document_url'),

    # Coordinator: View All Evaluations
    path('coordinator/evaluations/all/', 
        views.coordinator_view_evaluations, 
        name='coordinator_view_evaluations'),

    path('evaluation/<int:evaluation_id>/detail-json/',
        views.evaluation_detail_json,
        name='evaluation_detail_json'),
]

