from django.contrib import admin

from django.contrib import admin
from .models import Country, DocumentType

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number_indicative')
    search_fields = ('name', 'phone_number_indicative')
    ordering = ['name']

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    list_filter = ('country'),
    search_fields = ('name', 'country__name')