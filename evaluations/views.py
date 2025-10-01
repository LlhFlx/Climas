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
from proposals.models import Proposal
from people.models import Person
from accounts.models import CustomUser
from common.models import Status
from django.contrib.contenttypes.models import ContentType
from calls.models import Call
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
    elif target_type == "proposal" and target.status.name != 'Aprobada':
        messages.error(request, "Solo se pueden asignar evaluadores a propuestas aprobadas.")
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

        print("Pre save")
        print(content_type)
        print(target.id)
        
        evaluation, created = Evaluation.objects.get_or_create(
            target_content_type=content_type,
            target_object_id=target.id,
            evaluator=evaluator,
            defaults={
                'status': pending_status,
                'template': template,
                'max_possible_score': 100.00,
                'created_by': request.user,
            }
        )

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
def evaluator_dashboard():
    return None

@login_required
def evaluate_expression(request, evaluation_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Evaluator':
        messages.error(request, "Access denied.")
        return redirect('home')

    evaluation = get_object_or_404(Evaluation, id=evaluation_id, evaluator=request.user.customuser)
    if evaluation.status.name not in ['Pendiente', 'En Progreso']:
        messages.error(request, "Esta evaluación ya fue completada o no está disponible.")
        return redirect('calls:evaluator_dashboard')

    # Load template and items
    template = evaluation.template
    if not template:
        messages.error(request, "No se encontró una plantilla de evaluación activa.")
        return redirect('calls:evaluator_dashboard')

    items = TemplateItem.objects.filter(category__template=template).select_related('category').order_by('category__order', 'order')

    if request.method == 'POST':
        total_score = 0
        for item in items:
            field_name = f"item_{item.id}"
            score_str = request.POST.get(field_name)
            comment = request.POST.get(f"comment_{item.id}", "")

            if not score_str:
                messages.error(request, f"Debe asignar una puntuación para: {item.question}")
                return render(request, 'calls/evaluate_expression.html', {
                    'evaluation': evaluation,
                    'template': template,
                    'items': items,
                })

            try:
                score = float(score_str)
                if score < 0 or score > item.max_score:
                    messages.error(request, f"Puntuación inválida para: {item.question}. Debe estar entre 0 y {item.max_score}.")
                    return render(request, 'calls/evaluate_expression.html', {
                        'evaluation': evaluation,
                        'template': template,
                        'items': items,
                    })
            except ValueError:
                messages.error(request, f"Puntuación inválida para: {item.question}.")
                return render(request, 'calls/evaluate_expression.html', {
                    'evaluation': evaluation,
                    'template': template,
                    'items': items,
                })

            # Save or update response
            response, created = EvaluationResponse.objects.update_or_create(
                evaluation=evaluation,
                item=item,
                defaults={
                    'score': score,
                    'comment': comment,
                }
            )
            total_score += score

        # THRESHOLD LOGIC HERE
        evaluation.total_score = total_score
        evaluation.is_positive = (total_score / evaluation.max_possible_score) >= 0.7  # 70% threshold
        evaluation.status = Status.objects.get_or_create(name='Completada')
        evaluation.submission_datetime = timezone.now()
        evaluation.save()

        from evaluations.utils import approve_if_auto_approved
        target = evaluation.target
        target_type = 'expression' if isinstance(target, Expression) else 'proposal'
        if approve_if_auto_approved(target.id, target_type):
            messages.info(
                request,
                "¡Autoaprobado! Dos evaluaciones positivas recibidas. La propuesta ha sido aprobada automáticamente."
            )

        messages.success(request, "Evaluación enviada con éxito.")
        return redirect('calls:evaluator_dashboard')

    context = {
        'evaluation': evaluation,
        'template': template,
        'items': items,
    }
    return render(request, 'calls/evaluate_expression.html', context)

@login_required
def coordinator_view_evaluations(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('home')

    evaluations = Evaluation.objects.select_related(
        'target__user__person',     # Use target
        'target__call',
        'evaluator__person',
        'template'
    ).order_by('-submission_datetime')

    context = {
        'evaluations': evaluations,
    }
    return render(request, 'calls/coordinator_view_evaluations.html', context)

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