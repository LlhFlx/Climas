from django.shortcuts import render, get_object_or_404
from .models import Institution, InstitutionType

def institution_detail(request, pk):
    institution = get_object_or_404(Institution, pk=pk)
    return render(request, 'institutions/detail.html', {'institution': institution})


