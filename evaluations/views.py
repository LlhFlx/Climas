from django.shortcuts import render
from django.apps import apps
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse, FileResponse, Http404
from django.core.serializers import serialize
from evaluations.models import Evaluation, EvaluationResponse, EvaluationTemplate, TemplateCategory, TemplateItem
from expressions.models import Expression
from people.models import Person
from accounts.models import CustomUser
from common.models import Status

@login_required
def coordinator_evaluations_dashboard(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('home')

    # Get all submitted expressions (status = 'Enviada')
    submitted_expressions = Expression.objects.filter(
        status__name='Enviada'
    ).select_related(
        'user', 'call', 'scale', 'status'
    ).order_by('-submission_datetime')

    # Get all Evaluator users
    evaluators = CustomUser.objects.filter(
        role__name='Evaluator',
        role__is_active=True
    ).select_related('role', 'person').order_by('person__first_name', 'person__first_last_name')

    context = {
        'submitted_expressions': submitted_expressions,
        'evaluators': evaluators,
    }
    return render(request, 'evaluations/coordinator_evaluations_dashboard.html', context)


@login_required
def create_evaluation_template(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'

        if not name:
            return JsonResponse({'success': False, 'error': 'El nombre es obligatorio.'})

        # Prevent duplicates
        if EvaluationTemplate.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'error': 'Ya existe una plantilla con este nombre.'})

        try:
            template = EvaluationTemplate.objects.create(
                name=name,
                description=description,
                is_active=is_active,
                created_by=request.user
            )
            return JsonResponse({
                'success': True,
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'is_active': template.is_active
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def edit_evaluation_template(request, template_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})
    template = get_object_or_404(EvaluationTemplate, id=template_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required.'})

        template.name = name
        template.description = description
        template.is_active = is_active
        template.save()

        return JsonResponse({
            'success': True,
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'is_active': template.is_active
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def delete_evaluation_template(request, template_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('home')

    template = get_object_or_404(EvaluationTemplate, id=template_id)
    template.delete()
    messages.success(request, 'Plantilla eliminada correctamente.')
    return redirect('calls:coordinator_dashboard')

@login_required
def evaluation_template_detail(request, template_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('home')
    
    template = get_object_or_404(EvaluationTemplate, id=template_id)
    categories = TemplateCategory.objects.filter(template=template).prefetch_related('items').order_by('order')

    context = {
        'template': template,
        'categories': categories,
    }
    return render(request, 'evaluations/template_detail.html', context)

@login_required
def create_template_category(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    if request.method == 'POST':
        try:
            template_id = request.POST.get('template_id')
            name = request.POST.get('name')
            order = int(request.POST.get('order', 0))

            template = get_object_or_404(EvaluationTemplate, id=template_id)
            category = TemplateCategory.objects.create(
                template=template,
                name=name,
                order=order
            )
            return JsonResponse({
                'success': True,
                'id': category.id,
                'name': category.name,
                'order': category.order
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})
@login_required
def edit_template_category(request, category_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'}, status=403)

    category = get_object_or_404(TemplateCategory, id=category_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            order = int(request.POST.get('order', 0))
            is_active = request.POST.get('is_active') == 'on'

            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required.'})

            # Update category
            category.name = name
            category.order = order
            category.is_active = is_active 
            category.save()

            return JsonResponse({
                'success': True,
                'id': category.id,
                'name': category.name,
                'order': category.order,
                'is_active': category.is_active
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def delete_template_category(request, category_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'}, status=403)

    category = get_object_or_404(TemplateCategory, id=category_id)

    if request.method == 'DELETE':
        try:
            # Delete all items under this category first
            TemplateItem.objects.filter(category=category).delete()
            # Then delete the category
            category.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def create_template_item(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category_id')
            question = request.POST.get('question')
            field_type = request.POST.get('field_type', 'text')
            max_score = float(request.POST.get('max_score', 5.0))
            options_str = request.POST.get('options')
            source_model = request.POST.get('source_model')

            category = get_object_or_404(TemplateCategory, id=category_id)

            # Handle JSON options
            options = None
            if options_str:
                try:
                    options = json.loads(options_str)
                except json.JSONDecodeError:
                    return JsonResponse({'success': False, 'error': 'Opciones no son un JSON válido.'})

            item = TemplateItem.objects.create(
                category=category,
                question=question,
                field_type=field_type,
                max_score=max_score,
                options=options,
                source_model=source_model,
                order=category.items.count() + 1
            )

            return JsonResponse({
                'success': True,
                'id': item.id,
                'question': item.question,
                'field_type': item.field_type,
                'max_score': float(item.max_score),
                'category_id': category.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def get_template_item(request, item_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    try:
        item = TemplateItem.objects.get(id=item_id)
        return JsonResponse({
            'success': True,
            'id': item.id,
            'question': item.question,
            'field_type': item.field_type,
            'max_score': float(item.max_score),
            'options': item.options,
            'source_model': item.source_model,
            'category_id': item.category.id,
        })
    except TemplateItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found.'})
    
@login_required
def edit_template_item(request, item_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category_id')
            question = request.POST.get('question')
            field_type = request.POST.get('field_type', 'text')
            max_score = float(request.POST.get('max_score', 5.0))
            options_str = request.POST.get('options')
            source_model = request.POST.get('source_model')

            category = get_object_or_404(TemplateCategory, id=category_id)

            # Handle JSON options
            options = None
            if options_str:
                try:
                    options = json.loads(options_str)
                except json.JSONDecodeError:
                    return JsonResponse({'success': False, 'error': 'Opciones no son un JSON válido.'})

            item = TemplateItem.objects.update(
                category=category,
                question=question,
                field_type=field_type,
                max_score=max_score,
                options=options,
                source_model=source_model,
                order=category.items.count() + 1
            )

            return JsonResponse({
                'success': True,
                'id': item.id,
                'question': item.question,
                'field_type': item.field_type,
                'max_score': float(item.max_score),
                'category_id': category.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def edit_template_item(request, item_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'}, status=403)

    item = get_object_or_404(TemplateItem, id=item_id)

    if request.method == 'POST':
        try:
            question = request.POST.get('question')
            field_type = request.POST.get('field_type', 'text')
            max_score_str = request.POST.get('max_score', '5.0')
            options_str = request.POST.get('options', '')
            source_model = request.POST.get('source_model', '')

            if not question:
                return JsonResponse({'success': False, 'error': 'Question is required.'})

            try:
                max_score = float(max_score_str)
                if max_score <= 0:
                    return JsonResponse({'success': False, 'error': 'Max score must be greater than 0.'})
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid max score value.'})

            # Parse JSON options if present
            options = None
            if options_str:
                try:
                    options = json.loads(options_str)
                except json.JSONDecodeError:
                    return JsonResponse({'success': False, 'error': 'Options must be valid JSON.'})

            # Update the item
            item.question = question
            item.field_type = field_type
            item.max_score = max_score
            item.options = options
            item.source_model = source_model if source_model else None
            item.save()

            return JsonResponse({
                'success': True,
                'id': item.id,
                'question': item.question,
                'field_type': item.get_field_type_display(),
                'max_score': float(item.max_score),
                'category_id': item.category.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def delete_template_item(request, item_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'}, status=403)

    item = get_object_or_404(TemplateItem, id=item_id)

    if request.method == 'DELETE':
        try:
            # Delete associated EvaluationResponses first
            # These are responses TO this template item
            from evaluations.models import EvaluationResponse
            EvaluationResponse.objects.filter(item=item).delete()

            # Now delete the template item itself
            item.delete()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Failed to delete: {str(e)}'}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405) 

login_required
def assign_evaluator(request, expression_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('calls:coordinator_dashboard')

    expression = get_object_or_404(Expression, id=expression_id)
    evaluator_id = request.POST.get('evaluator_id')

    if not evaluator_id:
        messages.error(request, "Debe seleccionar un evaluador.")
        return redirect('calls:coordinator_dashboard')

    evaluator = get_object_or_404(CustomUser, id=evaluator_id)

    # Check if evaluation already exists
    if Evaluation.objects.filter(expression=expression, evaluator=evaluator).exists():
        messages.warning(request, f"Ya existe una evaluación asignada a {evaluator.person or evaluator.user.username}.")
        return redirect('calls:coordinator_dashboard')

    # Create the evaluation - but we DON’T assign a template yet!
    # We’ll assign it later, when the evaluator opens the evaluation.    
    evaluation = Evaluation.objects.create(
        expression=expression,
        evaluator=evaluator,        
        status=Status.objects.get(name='Pendiente'),  # or whatever initial status
        template=None,  # We'll set this later
        created_by=request.user
    )

    messages.success(request, f"Evaluador '{evaluator.person or evaluator.user.username}' asignado exitosamente.")
    return redirect('calls:coordinator_dashboard')

@login_required
def evaluator_dashboard():
    return None

@login_required
def evaluate_expression():
    return None

@login_required
def coordinator_view_evaluations():
    return None
