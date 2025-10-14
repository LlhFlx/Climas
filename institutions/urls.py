from django.urls import path
from . import views

app_name = 'institutions' #Enable institutions:detail

urlpatterns = [
    #path('', views.institution_list, name='list'),
    path('<int:pk>', views.institution_detail, name='detail'),
    #path('create/', views.institution.create, name='create')
]