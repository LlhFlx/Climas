from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .models import SharedQuestionCategory

@require_POST
@csrf_protect
def create_shared_question_category(request):
    try:
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required.'}, status=400)

        # Enforce uniqueness
        if SharedQuestionCategory.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'A category with this name already exists.'}, status=400)

        category = SharedQuestionCategory.objects.create(
            name=name.strip(),
            description=request.POST.get('description', '').strip(),
            order=int(request.POST.get('order', 0)),
            is_active=request.POST.get('is_active') == 'on'
        )
        return JsonResponse({
            'success': True,
            'id': category.id,
            'name': category.name
        })
    except Exception as e:
        # Log error for debugging
        print("Error creating category:", str(e))
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred.'}, status=500)