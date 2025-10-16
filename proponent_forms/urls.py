from django.urls import path
from . import views

app_name = 'proponent_forms'

urlpatterns = [
    path('shared-question-category/create/', 
         views.create_shared_question_category, 
         name='create_shared_question_category'),
]