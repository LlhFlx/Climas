from django.urls import path
from . import views

app_name = 'proposals'

urlpatterns = [
    path('document/<int:doc_id>/download/', 
         views.download_proposal_document, 
         name='download_proposal_document'),
]