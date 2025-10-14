from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    path('document/<int:doc_id>/download/', 
        views.download_proposal_document, 
        name='download_proposal_document'),
    path('add-institution/', 
        views.add_institution_to_proposal, 
        name='add_institution_to_proposal'),
    path('remove-institution/',
        views.remove_institution_from_proposal, 
        name='remove_institution_from_proposal'),
]