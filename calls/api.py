# calls/api.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
import json

from .models import Call
from proponent_forms.models import ProponentForm, SharedQuestion
from evaluations.models import EvaluationTemplate, TemplateCategory, TemplateItem

User = get_user_model()

@csrf_exempt
@login_required
def api_save_call_templates(request, call_pk):
    """
    Save ProponentForm and EvaluationTemplate via AJAX.
    Called from setup_call.html with Alpine.js.
    """
    if not request.user.role.name == 'Coordinator':
        return JsonResponse({'error': 'Permiso denegado'}, status=403)

    try:
        data = json.loads(request.body)
        call = get_object_or_404(Call, pk=call_pk, coordinator=request.user)

        proponent_form, created = ProponentForm.objects.get_or_create(
            call=call,
            defaults={'title': f"Formulario: {call.title}", 'is_active': True}
        )

        proponent_form.questions.clear()

        for q in data.get('proponent_questions', []):
            SharedQuestion.objects.create(
                form=proponent_form,
                question=q['question'],
                field_type=q['field_type'],
                target_category='expression',
                is_required=True
            )



        evaluation_template, created = EvaluationTemplate.objects.get_or_create(
            name=f"Evaluación: {call.title}",
            defaults={'description': f"Para la convocatoria: {call.title}", 'is_active': True}
        )
        
        evaluation_template.categories.all().delete()

        category = TemplateCategory.objects.create(
            template=evaluation_template,
            name="General",
            order=1
        )

        for q in data.get('evaluation_questions', []):
            TemplateItem.objects.create(
                category=category,
                question=q['question'],
                field_type=q['field_type'],
                max_score=q.get('max_score', 5.0),
                order=q.get('order', 0)
            )

        return JsonResponse({'status': 'ok'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)