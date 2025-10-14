from django.apps import apps
import json
from django.urls import reverse 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse, FileResponse, Http404
from django.core.serializers import serialize
from .models import (
    EvaluationTemplate, TemplateCategory, TemplateSubcategory,
    TemplateItem, TemplateItemOption, Evaluation, EvaluationResponse
)
from expressions.models import Expression
from proposals.models import Proposal
from people.models import Person
from accounts.models import CustomUser
from common.models import Status
from django.contrib.contenttypes.models import ContentType
from calls.models import Call
from evaluations.utils import approve_if_auto_approved
from budgets.models import BudgetItem
from django.db import transaction
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.views.decorators.clickjacking import xframe_options_exempt 
#from proposals.models import Proposal

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
        print("Trying...")
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        applies_to_expression = request.POST.get('applies_to_expression') == 'on'
        applies_to_proposal = request.POST.get('applies_to_proposal') == 'on'

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
                applies_to_expression=applies_to_expression,
                applies_to_proposal=applies_to_proposal,
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
        applies_to_expression = request.POST.get('applies_to_expression') == 'on'
        applies_to_proposal = request.POST.get('applies_to_proposal') == 'on'
        print("Expression", applies_to_expression, request.POST.get('applies_to_expression'))
        print("Proposal", applies_to_proposal, request.POST.get('applies_to_proposal') )

        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required.'})

        template.name = name
        template.description = description
        template.is_active = is_active
        template.applies_to_expression=applies_to_expression
        template.applies_to_proposal=applies_to_proposal
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
    categories = TemplateCategory.objects.filter(template=template).prefetch_related(
        'subcategories',
        'subcategories__items'
    ).order_by('order')

    # Get all calls for linking
    all_calls = Call.objects.all().order_by('title')

    context = {
        'template': template,
        'categories': categories,
        'all_calls': all_calls,  # Pass to template
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
            # Delete all items under subcategories of this category
            TemplateItem.objects.filter(subcategory__category=category).delete()
            # Delete all subcategories
            TemplateSubcategory.objects.filter(category=category).delete()
            # Then delete the category
            category.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

@login_required
def create_template_subcategory(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})
    if request.method == 'POST':
        try:
            category_id = request.POST.get('category_id')
            name = request.POST.get('name')
            order = int(request.POST.get('order', 0))
            category = get_object_or_404(TemplateCategory, id=category_id)
            subcategory = TemplateSubcategory.objects.create(
                category=category,
                name=name,
                order=order
            )
            return JsonResponse({
                'success': True,
                'id': subcategory.id,
                'name': subcategory.name,
                'order': subcategory.order,
                'category_id': category.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def edit_template_subcategory(request, subcategory_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})
    subcategory = get_object_or_404(TemplateSubcategory, id=subcategory_id)
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            order = int(request.POST.get('order', 0))
            is_active = request.POST.get('is_active') == 'on'
            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required.'})
            subcategory.name = name
            subcategory.order = order
            subcategory.is_active = is_active
            subcategory.save()
            return JsonResponse({
                'success': True,
                'id': subcategory.id,
                'name': subcategory.name,
                'order': subcategory.order,
                'is_active': subcategory.is_active
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def delete_template_subcategory(request, subcategory_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})
    subcategory = get_object_or_404(TemplateSubcategory, id=subcategory_id)
    if request.method == 'DELETE':
        try:
            # Delete items and their options
            TemplateItem.objects.filter(subcategory=subcategory).delete()
            subcategory.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def create_template_item(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})
    if request.method == 'POST':
        try:
            subcategory_id = request.POST.get('subcategory_id')
            question = request.POST.get('question')
            field_type = request.POST.get('field_type', 'text')
            max_score = float(request.POST.get('max_score', 5.0))
            source_model = request.POST.get('source_model') or None
            options_json = request.POST.get('options')  # JSON string of [{display_text, score}]
            print("Options", options_json)
            subcategory = get_object_or_404(TemplateSubcategory, id=subcategory_id)
            with transaction.atomic():
                item = TemplateItem.objects.create(
                    subcategory=subcategory,
                    question=question.strip(),
                    field_type=field_type,
                    max_score=max_score,
                    source_model=source_model,
                    order=subcategory.items.count() + 1
                )
                
                # Save options
                if options_json:
                    options = json.loads(options_json)
                    for opt in options:
                        TemplateItemOption.objects.create(
                            item=item,
                            display_text=opt.get('display_text', '').strip(),
                            score=opt.get('score', 0)
                        )

            return JsonResponse({
                'success': True,
                'id': item.id,
                'question': item.question,
                'field_type': item.field_type,
                'max_score': float(item.max_score),
                'subcategory_id': subcategory.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def get_template_item(request, item_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})
    try:
        item = TemplateItem.objects.prefetch_related('options').get(id=item_id)
        options = [
            {'display_text': opt.display_text, 'score': float(opt.score)}
            for opt in item.options.all()
        ]
        return JsonResponse({
            'success': True,
            'id': item.id,
            'question': item.question,
            'field_type': item.field_type,
            'max_score': float(item.max_score),
            'source_model': item.source_model,
            'subcategory_id': item.subcategory.id,
            'options': options
        })
    except TemplateItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found.'})
    
@login_required
def get_template_item(request, item_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})
    try:
        item = TemplateItem.objects.prefetch_related('options').get(id=item_id)
        options = [
            {'display_text': opt.display_text, 'score': float(opt.score)}
            for opt in item.options.all()
        ]
        return JsonResponse({
            'success': True,
            'id': item.id,
            'question': item.question,
            'field_type': item.field_type,
            'max_score': float(item.max_score),
            'source_model': item.source_model,
            'subcategory_id': item.subcategory.id,
            'options': options
        })
    except TemplateItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found.'})
    

login_required
def edit_template_item(request, item_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})
    item = get_object_or_404(TemplateItem, id=item_id)
    if request.method == 'POST':
        try:
            question = request.POST.get('question')
            field_type = request.POST.get('field_type', 'text')
            max_score = float(request.POST.get('max_score', 5.0))
            source_model = request.POST.get('source_model') or None
            options_json = request.POST.get('options')

            if not question:
                return JsonResponse({'success': False, 'error': 'Question is required.'})

            with transaction.atomic():
                item.question = question
                item.field_type = field_type
                item.max_score = max_score
                item.source_model = source_model
                item.save()

                # Replace all options
                item.options.all().delete()
                if options_json:
                    options = json.loads(options_json)
                    for opt in options:
                        TemplateItemOption.objects.create(
                            item=item,
                            display_text=opt.get('display_text', ''),
                            score=opt.get('score', 0)
                        )

            return JsonResponse({
                'success': True,
                'id': item.id,
                'question': item.question,
                'field_type': item.get_field_type_display(),
                'max_score': float(item.max_score),
                'subcategory_id': item.subcategory.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def load_dynamic_options(request):
    """AJAX endpoint to preload display_text from source_model (score = 0 by default)."""
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})
    source_model = request.GET.get('source_model')
    if not source_model:
        return JsonResponse({'success': False, 'error': 'source_model required.'})
    try:
        app_label, model_name = source_model.split('.')
        model = apps.get_model(app_label, model_name)
        options = []
        for field in ['name', 'title', 'code', 'label', 'description']:
            if hasattr(model, field):
                for obj in model.objects.values('id', field):
                    options.append({
                        'display_text': str(obj[field]),
                        'score': 0.0,
                        'source_object_id': obj['id']
                    })
                break
        else:
            # Fallback to __str__
            for obj in model.objects.all()[:50]:
                options.append({
                    'display_text': str(obj),
                    'score': 0.0,
                    'source_object_id': obj.pk
                })
        return JsonResponse({'success': True, 'options': options})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
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

@login_required
def assign_evaluator(request, target_type, target_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('calls:coordinator_dashboard')
    
    # Map target_type to model
    model_map = {
        "expression": Expression,
        "proposal": Proposal,  # Make sure this import exists!
    }

    Model = model_map.get(target_type.lower())
    if not Model:
        messages.error(request, "Tipo de objetivo inválido.")
        return redirect('calls:coordinator_dashboard')

    # Get the actual object
    target = get_object_or_404(Model, id=target_id)
    
    # Validate status based on type
    if target_type == "expression" and target.status.name != 'Enviada':
        messages.error(request, "Solo se pueden asignar evaluadores a expresiones enviadas.")
        return redirect('calls:coordinator_dashboard')
    elif target_type == "proposal" and target.proposal_status.name != 'Enviada':
        messages.error(request, "Solo se pueden asignar evaluadores a propuestas en estado 'Enviada'.")
        return redirect('calls:coordinator_dashboard')

    if request.method == 'POST':
        evaluator_id = request.POST.get('evaluator_id')
        template_id = request.POST.get('template_id')

        if not evaluator_id:
            messages.error(request, "Debe seleccionar un evaluador.")
            return redirect('calls:coordinator_dashboard')

        evaluator = get_object_or_404(
            CustomUser,
            id=evaluator_id,
            role__name='Evaluator',
            role__is_active=True
        )
        
        # Validate template if selected
        template = None
        if template_id:
            try:
                if target_type == "expression":
                    template = EvaluationTemplate.objects.get(
                        id=template_id,
                        calls=target.call,
                        applies_to_expression=True
                    )
                elif target_type == "proposal":
                    template = EvaluationTemplate.objects.get(
                        id=template_id,
                        calls=target.call,
                        applies_to_proposal=True
                    )
            except EvaluationTemplate.DoesNotExist:
                messages.error(request, "La plantilla seleccionada no es válida para esta convocatoria o tipo de objetivo.")
                return redirect('calls:coordinator_dashboard')

        # Get or create status
        pending_status, _ = Status.objects.get_or_create(
            name='Pendiente',
            defaults={'description': 'Evaluación pendiente de revisión'}
        )

        # Save evaluation dynamically
        content_type = ContentType.objects.get_for_model(target)

        # print("Pre save")
        # print(content_type)
        # print(target.id)

        evaluation, created = Evaluation.objects.get_or_create(
            target_content_type=content_type,
            target_object_id=target.id,
            evaluator=evaluator,
            defaults={
                'status': pending_status,
                'template': template,
                'created_by': request.user,
            }
        )

        # If template changed, update it
        if template and evaluation.template != template:
            evaluation.template = template
            evaluation.save()

        # Force recalculation via signal
        if evaluation.template:
            evaluation.template.update_evaluations()

        if created:
            msg = f"Evaluador '{evaluator.person or evaluator.user.username}' asignado"
            if template:
                msg += f" con plantilla '{template.name}'"
            msg += f" a '{target.project_title}'."
            messages.success(request, msg)
        else:
            messages.info(
                request,
                f"Evaluador '{evaluator.person or evaluator.user.username}' ya estaba asignado a esta {target_type}."
            )

    return redirect('calls:coordinator_dashboard')

@login_required
def approve_expression(request, expression_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Acceso denegado.")
        return redirect('calls:coordinator_dashboard')

    expression = get_object_or_404(Expression, id=expression_id)

    if expression.status.name != 'Enviada':
        messages.error(request, "Solo se puede aprobar expresiones con estado 'Enviada'.")
        return redirect('calls:coordinator_dashboard')

    
    # Create Proposal (inherits Expression fields)
    proposal = Proposal.objects.create(
        expression_ptr=expression,
        budget_breakdown="",
        implementation_plan="",
        risk_analysis="",
        sustainability_plan="",
        status=Status.objects.get(name='Aprobada'),
    )

    expression.status = Status.objects.get(name='Aprobada')
    expression.save()

    # Let coordinator choose template for Proposal
    template_id = request.POST.get('proposal_template_id')
    if template_id:
        try:
            template = EvaluationTemplate.objects.get(
                id=template_id,
                calls=expression.call,
                applies_to_proposal=True
            )
            Evaluation.objects.filter(
                target_content_type=ContentType.objects.get_for_model(Expression),
                target_object_id=expression.id
            ).update(
                target=proposal,  # Point to Proposal now
                template=template
            )
            messages.success(
                request,
                f"Propuesta aprobada y evaluación actualizada con plantilla '{template.name}'."
            )
        except EvaluationTemplate.DoesNotExist:
            messages.error(request, "La plantilla seleccionada no aplica a propuestas.")
    else:
        # If no template selected, leave Evaluation.template as-is (or None)
        messages.info(
            request,
            "Propuesta aprobada. Evaluación existente se mantiene. Asigne plantilla si es necesario."
        )

    return redirect('calls:coordinator_dashboard')


@login_required
def evaluator_dashboard(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Evaluator':
        messages.error(request, "Access denied.")
        return redirect('home')

    # Get all evaluations assigned to this evaluator
    evaluations = Evaluation.objects.filter(
        evaluator=request.user.customuser,
        status__name__in=['Pendiente', 'En Progreso', 'Completada']
    ).select_related(
        'target_content_type',
        'template',
        'status'
    ).order_by('-updated_at')

    context = {
        'evaluations': evaluations
    }
    return render(request, 'evaluations/evaluator_dashboard.html', context)

@login_required
def evaluate_expression(request, evaluation_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Evaluator':
        messages.error(request, "Access denied.")
        return redirect('home')

    evaluation = get_object_or_404(
        Evaluation, 
        id=evaluation_id, 
        evaluator=request.user.customuser
    )

    # Validate state
    if evaluation.status.name not in ['Pendiente', 'En Progreso']:
        messages.error(request, "Esta evaluación ya fue completada o no está disponible.")
        return redirect('calls:evaluator_dashboard')

    # Load template and items
    template = evaluation.template
    if not template:
        messages.error(request, "No se encontró una plantilla de evaluación activa.")
        return redirect('calls:evaluator_dashboard')

    items = TemplateItem.objects.filter(
        subcategory__category__template=template
    ).select_related('subcategory__category').prefetch_related(
        'options'
    ).order_by(
        'subcategory__category__order', 'subcategory__order', 'order'
    )

    # Determine target type and get proposal-specific data if needed
    target = evaluation.target
    print("target", target)
    print(isinstance(target, Expression))
    print(isinstance(target, Proposal))
    # target_type = 'expression' if isinstance(target, Expression) else 'proposal'
    target_type = 'proposal' if isinstance(target, Proposal) else 'expression'

    # Prepare proposal-specific fields to pass to template (only if Proposal)
    proposal_fields = {}
    if target_type == 'proposal':
        proposal_fields = {
            'principal_research_experience': target.principal_research_experience,
            'community_country': target.community_country,
            'community_description': target.community_description,
            'project_location': target.project_location,
            'duration_months': target.duration_months,
            'summary': target.summary,
            'context_problem_justification': target.context_problem_justification,
            'specific_objectives': target.specific_objectives.all(),
            'methodology_analytical_plan_ethics': target.methodology_analytical_plan_ethics,
            'equity_inclusion': target.equity_inclusion,
            'communication_strategy': target.communication_strategy,
            'risk_analysis_mitigation': target.risk_analysis_mitigation,
            'research_team': target.research_team,
            'timeline_document': target.timeline_document,
            'budget_document': target.budget_document,
            'partner_institutions': target.partner_institutions.all(),
            'partner_institution_commitments': target.partner_institution_commitments.all(),
        }
    
    # EXTRA DATA: Products, Team Members, Budget Items, Responses
    # Extract related objects using correct _set syntax
    try:
        # Products
        # print("DEBUG")
        # for attr in dir(target):
        #     print(attr)
        # print("END DEBUG")
        if isinstance(target, Proposal):
            print("A: This is a Proposal instance")
            if hasattr(target, 'proposalproduct_set') and target.proposalproduct_set.exists():
                products = list(
                    target.proposalproduct_set.prefetch_related('strategic_effects').all()
                )
            print(products)
        elif isinstance(target, Expression):
            if hasattr(target, 'expressionproduct_set') and target.expressionproduct_set.exists():
                products = list(
                    target.expressionproduct_set.prefetch_related('strategic_effects').all()
                )
            print("B: This is NOT a Proposal (it's a", type(target).__name__, ")")
        
        # if hasattr(target, 'proposalproduct_set') and target.proposalproduct_set.exists():
        #     products = list(
        #         target.product_set.prefetch_related('strategic_effects').all()
        #     )
        # elif hasattr(target, 'expressionproduct_set') and target.expressionproduct_set.exists():
        #     products = list(
        #         target.expressionproduct_set.prefetch_related('strategic_effects').all()
        #     )
        #     # for product in products:
        #     #     print(f"Product: {product.title}")
        #     #     effects = product.strategic_effects.all()
        #     #     for effect in effects:
        #     #         print(f"  → Effect: {effect.name}")
        #     #     print(f"\nProduct ID is: {product.id} - Title: {product.title}")
        #     #     if effects:
        #     #         for effect in effects:
        #     #             print(f"    {effect.id} - {effect.name}")
        #     #     else:
        #     #         print("   No strategic effects linked.")
        # else:
        #     print("Error loading products:")
        #     products = []

        # # Team Members
        # if hasattr(target, 'projectteammember_set') and target.teammember_set.exists():
        #     team_members = list(target.teammember_set.all())
        # else:
        #     team_members = []

        # print("Team Members", team_members)

        try:
            # Safe: use the actual related_name or default _set
            if hasattr(target, 'team_members'):  
                team_members = list(target.team_members.all())
            else:
                # Fallback: try default _set name
                rel_name = 'projectteammember_set'
                if hasattr(target, rel_name):
                    team_members = list(getattr(target, rel_name).all())
                else:
                    team_members = []
        except Exception as e:
            print("Error loading team members:", str(e))
            team_members = []

        # Budget Items
        existing_budget_items = BudgetItem.objects.filter(expression=target.id).select_related('category', 'period')
        for item in existing_budget_items:
            print(item.id, item.category.name, item.period.name)
        
        # Dynamic Question Responses
        print(target, "EVALUATION QUESTIONS")
        responses = {}
        try:
            # Use correct related name
            response_qs = target.form_responses.select_related('shared_question')
            if response_qs.exists():
                for r in response_qs:
                    question_text = r.shared_question.question
                    responses[question_text] = r.value.strip() if r.value else "No respondido"
        except Exception as e:
            print("Error accessing form_responses:", str(e))
            # Fallback: try default reverse accessor
            try:
                from proponent_forms.models import ProponentResponse
                response_qs = ProponentResponse.objects.filter(expression=target).select_related('shared_question')
                for r in response_qs:
                    question_text = r.shared_question.question
                    responses[question_text] = r.value.strip() if r.value else "No respondido"
            except:
                pass
        print(len(responses))
    except Exception as e:
        print("Error loading extended fields:", e)
        products = []
        team_members = []
        budget_items = []
        responses = {}

    if request.method == 'POST':
        total_score = 0
        try:
            with transaction.atomic():
                for item in items:
                    field_name = f"item_{item.id}"
                    option_id = request.POST.get(field_name)
                    try:
                        option_id = int(option_id)
                    except (TypeError, ValueError):
                        raise ValueError(f"Opción inválida para '{item.question}'.")
                    comment = request.POST.get(f"comment_{item.id}", "")
                    #print("EVALUATION QUESTION:", dir(item))

                    if not option_id:
                        raise ValueError(f"Debe asignar una puntuación para: {item.question}")

                    # print("Opt id:", option_id)

                    try:
                        # # The item already has its options prefetched
                        # selected_option = next(
                        #     (opt for opt in item.options.all() if str(opt.id) == option_id),
                        #     None
                        # )
                        # # print(selected_option)
                        # # for val in item.options.all():
                        # #     print("Values:", val, type(val))
                        # if not selected_option:
                        #     raise TemplateItemOption.DoesNotExist
                        # score = selected_option.score
                        selected_option = TemplateItemOption.objects.get(id=option_id, item=item)
                        score = selected_option.score
                        print(f"Starting questions {item.question.strip()}: Score is {score}")
                    except TemplateItemOption.DoesNotExist:
                        raise ValueError(f"Opción inválida seleccionada para '{item.question}'.")

                    # Validation
                    if score < 0 or score > item.max_score:
                        raise ValueError(
                            f"Puntuación inválida para '{item.question}'. "
                            f"Debe estar entre 0 y {item.max_score}."
                        )

                    # Update or create response
                    EvaluationResponse.objects.update_or_create(
                        evaluation=evaluation,
                        item=item,
                        defaults={
                            'score': score,
                            'comment': comment,
                        }
                    )
                    total_score += score

                # Set completion status
                status_completada, _ = Status.objects.get_or_create(
                    name='Completada',
                    defaults={'description': 'Evaluación completada por el evaluador'}
                )
                # THRESHOLD LOGIC - SAFE DECIMAL ARITHMETIC
                # Convert to Decimal
                total_score_decimal = Decimal(str(total_score))
                evaluation.total_score = total_score_decimal
                evaluation.max_possible_score = evaluation.template.get_total_max_score()
                print("Total score and max_possible score are good")
                # Then calculate is_positive
                if evaluation.max_possible_score > 0:
                    ratio = total_score / Decimal(evaluation.max_possible_score)
                    evaluation.is_positive = ratio >= 0.7
                else:
                    evaluation.is_positive = False

                # Save final evaluation
                evaluation.status = status_completada
                evaluation.submission_datetime = timezone.now()
                evaluation.save()

                # Auto-approve check (if applicable)
                target = evaluation.target
                target_type = 'expression' if isinstance(target, Expression) else 'proposal'
                print(approve_if_auto_approved(target.id, target_type))
                if approve_if_auto_approved(target.id, target_type):
                    messages.info(
                        request,
                        "¡Autoaprobado! Dos evaluaciones positivas recibidas. La propuesta ha sido aprobada automáticamente."
                    )

                messages.success(request, "Evaluación enviada con éxito.")

        except ValueError as ve:
            messages.error(request, str(ve))
            return render(request, 'evaluations/evaluate_expression.html', {
                'evaluation': evaluation,
                'template': template,
                'items': items,
                'target_type': target_type,
                'proposal_fields': proposal_fields,
                'products': products,
                'team_members': team_members,
                #'existing_budget_items': existing_budget_items,
                'responses': responses,
            })
        except Exception as e:
            messages.error(request, "Ocurrió un error al guardar la evaluación.")
            print("Error saving evaluation:", e)
            return render(request, 'evaluations/evaluate_expression.html', {
                'evaluation': evaluation,
                'template': template,
                'items': items,
                'target_type': target_type,
                'proposal_fields': proposal_fields,
                'products': products,
                'team_members': team_members,
                #'existing_budget_items': existing_budget_items,
                'responses': responses,
            })

        return redirect('evaluations:evaluator_dashboard')

    context = {
        'evaluation': evaluation,
        'template': template,
        'items': items,
        'target_type': target_type,
        'proposal_fields': proposal_fields,
        'products': products,
        'team_members': team_members,
        #'existing_budget_items': existing_budget_items,
        'responses': responses,
    }
    return render(request, 'evaluations/evaluate_expression.html', context)

@login_required
def coordinator_view_evaluations(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('home')

    evaluations = Evaluation.objects.filter(
        status__name='Completada'
    ).select_related(
        'target_content_type',
        'evaluator__person',
        'template',
        'status'
    ).order_by('-submission_datetime')

    context = {
        'evaluations': evaluations,
    }
    return render(request, 'evaluations/coordinator_view_evaluations.html', context)

@login_required
def link_template_to_call(request, template_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('calls:coordinator_dashboard')

    template = get_object_or_404(EvaluationTemplate, id=template_id)

    if request.method == 'POST':
        call_id = request.POST.get('call_id')
        if not call_id:
            messages.error(request, "Debe seleccionar una convocatoria.")
            return redirect('evaluations:template_detail', template_id=template.id)

        call = get_object_or_404(Call, id=call_id)
        template.calls.add(call)
        messages.success(request, f"Plantilla '{template.name}' asociada a la convocatoria '{call.title}'.")

    return redirect('evaluations:template_detail', template_id=template.id)


@login_required
def unlink_template_from_call(request, template_id, call_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('calls:coordinator_dashboard')

    template = get_object_or_404(EvaluationTemplate, id=template_id)
    call = get_object_or_404(Call, id=call_id)
    template.calls.remove(call)
    messages.success(request, f"Plantilla '{template.name}' desasociada de la convocatoria '{call.title}'.")

    return redirect('evaluations:template_detail', template_id=template.id)

@login_required
def evaluation_detail_json(request, evaluation_id):
    # Get evaluation with all related data
    try:
        evaluation = Evaluation.objects.select_related(
            'target_content_type',
            'evaluator__person',
            'template',
            'status'
        ).get(id=evaluation_id)
    except Evaluation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Evaluación no encontrada.'}, status=404)

    # Permission Check: Only evaluator or coordinator
    user = request.user
    if not hasattr(user, 'customuser'):
        return JsonResponse({'success': False, 'error': 'Acceso denegado.'}, status=403)

    customuser = user.customuser
    is_evaluator = (customuser == evaluation.evaluator)
    is_coordinator = (customuser.role.name == 'Coordinator')

    if not (is_evaluator or is_coordinator):
        return JsonResponse({'success': False, 'error': 'Acceso denegado.'}, status=403)

    # Resolve target (Expression or Proposal)
    target = evaluation.target  # Uses GenericForeignKey - safe

    # Safety fallbacks for missing related objects
    def safe_str(obj, field):
        return str(getattr(obj, field, '')) or ''

    return JsonResponse({
        'success': True,
        'id': evaluation.id,
        'project_title': target.project_title,

        'investigator_name': (
            target.user.person.get_full_name()
            if target.user.person else target.user.user.username
        ),

        'evaluator_name': (
            evaluation.evaluator.person.get_full_name()
            if evaluation.evaluator.person else evaluation.evaluator.user.username
        ),

        'call_title': target.call.title,
        'template_name': evaluation.template.name,

        'total_score': float(evaluation.total_score) if evaluation.total_score else None,
        'max_possible_score': float(evaluation.max_possible_score),
        'is_positive': evaluation.is_positive,

        'submission_datetime': (
            evaluation.submission_datetime.strftime('%d/%m/%Y %H:%M')
            if evaluation.submission_datetime else '-'
        ),

        'target_type': evaluation.target_content_type.model,
        'status': evaluation.status.name,

        'is_own_evaluation': is_evaluator,
    })

@login_required
@xframe_options_exempt
def serve_pdf(request, evaluation_id, doc_type):
    """
    Securely serve a PDF file (timeline or budget) associated with an evaluation.
    Only the assigned evaluator can access it.
    """

    # Get the evaluation
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)

    # Ensure user is the evaluator
    if request.user.customuser != evaluation.evaluator:
        raise PermissionDenied("No permission to view this document.")

    # Ensure evaluation is completed
    # if evaluation.status.name != "Completada":
    #     raise PermissionDenied("Document not available until evaluation is completed.")

    # Map doc_type to the correct field on the target
    target = evaluation.target
    if not hasattr(target, 'timeline_document') and not hasattr(target, 'budget_document'):
        raise Http404("Document type not supported.")

    doc_field = None
    if doc_type == 'timeline':
        doc_field = getattr(target, 'timeline_document', None)
    elif doc_type == 'budget':
        doc_field = getattr(target, 'budget_document', None)
    else:
        raise Http404("Invalid document type.")

    if not doc_field:
        raise Http404("Document not found.")

    # Ensure file exists
    if not doc_field.file:
        raise Http404("File not found.")

    # Serve the file securely
    response = FileResponse(
        doc_field.file.open('rb'),
        content_type='application/pdf',
        as_attachment=False  # This makes it display in-browser
    )
    response['Content-Disposition'] = f'inline; filename="{doc_field.name}"'
    return response

@login_required
def get_document_url(request, evaluation_id, doc_type):
    """
    Returns the secure URL to view a document (PDF, DOCX, XLSX, etc.) via Google Docs Viewer.
    Only the evaluator can access it.
    """
    evaluation = get_object_or_404(Evaluation, id=evaluation_id)

    if request.user.customuser != evaluation.evaluator:
        raise PermissionDenied("No permission to view this document.")

    target = evaluation.target
    doc_field = None

    if doc_type == 'timeline':
        doc_field = getattr(target, 'timeline_document', None)
    elif doc_type == 'budget':
        doc_field = getattr(target, 'budget_document', None)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid document type.'})

    if not doc_field or not doc_field.file:
        return JsonResponse({'success': False, 'error': 'Document not found.'})

    # Return the *secure* Django URL - Google will fetch it
    secure_url = request.build_absolute_uri(
        f"{reverse('evaluations:serve_pdf', args=[evaluation_id, doc_type])}"
    )

    return JsonResponse({
        'success': True,
        'secure_url': secure_url,
        'filename': doc_field.name
    })