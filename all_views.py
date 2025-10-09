

# ===== From: experiences/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: proposals/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: proponent_forms/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: people/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: thematic_axes/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: core/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: expressions/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: intersectionality/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: institutions/views.py =====

from django.shortcuts import render, get_object_or_404
from .models import Institution, InstitutionType

def institution_detail(request, pk):
    institution = get_object_or_404(Institution, pk=pk)
    return render(request, 'institutions/detail.html', {'institution': institution})




# ===== From: antecedents/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: strategic_effects/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: products/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: calls/views.py =====

from django.apps import apps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse, FileResponse, Http404
from django.core.serializers import serialize
from .models import Call
from .forms import CallForm, SharedQuestionForm
from proponent_forms.models import SharedQuestion
from common.models import Status, Scale
from proponent_forms.models import ProponentForm, ProponentFormQuestion, ProponentResponse # For setup_call
# from proponent_forms.models import ProponentForm, ProponentFormQuestion  
from .forms import SharedQuestionForm  # For create_shared_question

from institutions.models import Institution, InstitutionType
from thematic_axes.models import ThematicAxis
from strategic_effects.models import StrategicEffect
from budgets.models import BudgetCategory, BudgetPeriod
from geo.models import Country, DocumentType
from people.models import Person
from expressions.models import Expression, ExpressionDocument
from expressions.forms import ExpressionDocumentForm
from proposals.models import Proposal
from accounts.models import CustomUser

from products.models import Product
from django.forms import modelformset_factory
from django import forms
from django.contrib.contenttypes.models import ContentType

import json
from django.core.serializers.json import DjangoJSONEncoder

from project_team.models import ExpressionTeamMember, InvestigatorCondition, ExpressionInvestigatorThematicAntecedent
from intersectionality.models import IntersectionalityScope
from budgets.models import BudgetCategory, BudgetItem, BudgetPeriod
from evaluations.models import Evaluation, EvaluationResponse, EvaluationTemplate, TemplateCategory, TemplateItem

@login_required
def coordinator_dashboard(request):
    if not hasattr(request.user, 'customuser'):
        messages.error(request, "User profile not found.")
        return redirect('home')

    if request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied. Coordinator role required.")
        return redirect('home')

    # Get coordinator's calls
    calls = Call.objects.filter(coordinator=request.user.customuser).order_by('-opening_datetime')
    # Get all shared questions
    shared_questions = SharedQuestion.objects.all().order_by('target_category', 'question')

    # return render(request, 'calls/coordinator_dashboard.html', {
    #     'calls': calls,
    #     'shared_questions': shared_questions,
    # })
    institution_types = InstitutionType.objects.filter(is_active=True).order_by('name')
    institutions = Institution.objects.all().select_related('institution_type').order_by('name')
    countries = Country.objects.all().order_by('name')
    document_types = DocumentType.objects.select_related('country').order_by('country__name', 'name')
    thematic_axes = ThematicAxis.objects.filter(is_active=True).order_by('name')
    strategic_effects = StrategicEffect.objects.filter(is_active=True).order_by('name')
    budget_categories = BudgetCategory.objects.filter(is_active=True).order_by('name')
    budget_periods = BudgetPeriod.objects.all().order_by('order', 'name')
    people = Person.objects.filter(created_by__isnull=False).order_by('first_name', 'first_last_name')
    # Get all templates
    templates = EvaluationTemplate.objects.all().order_by('-is_active', 'name')
    # print(f"Templates are {templates}")
    
    # Get all submitted expressions (status = 'Enviada')
    submitted_expressions = Expression.objects.filter(
        status__name='Enviada'
    ).select_related('user', 'call', 'scale', 'status').order_by('-submission_datetime')

    
    proposals = Proposal.objects.filter(
        status__name='Aprobada'
    ).select_related(
        'expression_ptr__user',
        'expression_ptr__call',
        'expression_ptr__scale',
        'expression_ptr__status'
    ).order_by('-submission_datetime')

    completed_evaluations = Evaluation.objects.filter(
        status__name='Completada'
    ).select_related(
        'target_content_type',
        'evaluator__person',
        'template',
        'status'
    ).order_by('-submission_datetime')

    # Get all Evaluator users
    evaluators = CustomUser.objects.filter(
        role__name='Evaluator',
        role__is_active=True
    ).select_related('role', 'person', 'user').order_by('person__first_name', 'person__first_last_name')
    context = {
        'calls': calls,
        'shared_questions': shared_questions,
        'submitted_expressions': submitted_expressions,
        'proposals': proposals,
        'evaluations': completed_evaluations,
        'evaluators': evaluators,
        'institutions': institutions,
        'institution_types': institution_types,
        'countries': countries,
        'document_types': document_types,
        'thematic_axes': thematic_axes,
        'strategic_effects': strategic_effects,
        'budget_categories': budget_categories,
        'budget_periods': budget_periods,
        'people': people,
        'templates': templates,
    }
    return render(request, 'calls/coordinator_dashboard.html', context)


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
def evaluator_dashboard(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Evaluator':
        messages.error(request, "Access denied.")
        return redirect('home')

    # Get all evaluations assigned to this evaluator (status: Pendiente, En Progreso, etc.)
    evaluations = Evaluation.objects.filter(
        evaluator=request.user.customuser,
        status__name__in=['Pendiente', 'En Progreso']
    ).select_related(
        'expression', 'expression__call', 'expression__user', 'template'
    ).order_by('-submission_datetime')

    context = {
        'evaluations': evaluations,
    }
    return render(request, 'calls/evaluator_dashboard.html', context)

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

        # Update total score
        evaluation.total_score = total_score
        evaluation.status = Status.objects.get(name='Completada')
        evaluation.submission_datetime = timezone.now()
        evaluation.save()

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
        'expression__user__person',
        'expression__call',
        'evaluator__person',
        'template'
    ).order_by('-submission_datetime')

    context = {
        'evaluations': evaluations,
    }
    return render(request, 'calls/coordinator_view_evaluations.html', context)



@login_required
def create_shared_question(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('home')

    if request.method == 'POST':
        form = SharedQuestionForm(request.POST)
        if form.is_valid():
            question = form.save()
            messages.success(request, f'Question "{question.question}" created successfully!')
            return redirect('calls:coordinator_dashboard')
    else:
        form = SharedQuestionForm()

    return render(request, 'calls/create_shared_question.html', {'form': form})

@login_required
def edit_shared_question(request, question_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('home')

    # Get the question
    question = get_object_or_404(SharedQuestion, id=question_id)

    if request.method == 'POST':
        form = SharedQuestionForm(request.POST, instance=question)
        if form.is_valid():
            updated_question = form.save()
            messages.success(request, f'Question "{updated_question.question}" updated successfully!')
            return redirect('calls:coordinator_dashboard')
    else:
        form = SharedQuestionForm(instance=question)

    return render(request, 'calls/create_shared_question.html', {
        'form': form,
        'editing': True,  # Flag to change button text
        'question': question
    })

@login_required
def delete_shared_question(request, question_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('home')

    question = get_object_or_404(SharedQuestion, id=question_id)
    question.delete()
    messages.success(request, 'Question deleted successfully!')
    return redirect('calls:coordinator_dashboard')

@login_required
def preview_source_model(request, model_path):
    """
    Preview first 5 items from a model.
    Expects model_path like 'geo.Country' or 'common.Status'
    Returns list of 'name' field values.
    """
    # if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
    #     return JsonResponse({'success': False, 'error': 'Access denied.'})
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name not in ['Coordinator', 'Researcher']:
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    try:
        app_label, model_name = model_path.split('.')
        model = apps.get_model(app_label, model_name)
        
        print(f"Current model is {model}")
        # Try to get 'name' field. fallback to 'title' or 'pk'
        name_field = 'name'
        if not hasattr(model, 'name'):
            if hasattr(model, 'title'):
                name_field = 'title'
                print("Here")
            else:
                # Fallback to string representation
                print("Fallback")
                #items = list(model.objects.values_list('pk', flat=True)[:5])
                items = [str(obj) for obj in model.objects.all()[:5]] 
                return JsonResponse({
                    'success': True,
                    'items': items,
                    'field_used': '__str__' # 'pk'
                })

        items = list(model.objects.values_list(name_field, flat=True)[:5])
        return JsonResponse({
            'success': True,
            'items': items,
            'field_used': name_field
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def create_call(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('home')

    if request.method == 'POST':
        form = CallForm(request.POST)
        if form.is_valid():
            call = form.save(commit=False)
            call.coordinator = request.user.customuser
            call.created_by = request.user
            # Set default status
            from common.models import Status
            draft_status, _ = Status.objects.get_or_create(name='Draft')
            call.status = draft_status
            call.save()
            messages.success(request, 'Call created successfully!')
            return redirect('calls:setup_call', call_pk=call.pk)
    else:
        form = CallForm()

    return render(request, 'calls/create_call.html', {'form': form})


@login_required
def create_institution(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            institution_type_id = request.POST.get('institution_type')
            country_id = request.POST.get('country')
            tax_register_number = request.POST.get('tax_register_number')
            acronym = request.POST.get('acronym', '')
            website = request.POST.get('website', '')
            is_active = request.POST.get('is_active') == 'on'

            if not all([name, institution_type_id, country_id, tax_register_number]):
                return JsonResponse({'success': False, 'error': 'Name, type, country, and tax number are required.'})

            institution_type = InstitutionType.objects.get(id=institution_type_id)
            country = Country.objects.get(id=country_id)

            institution = Institution.objects.create(
                name=name,
                institution_type=institution_type,
                country=country,
                tax_register_number=tax_register_number,
                acronym=acronym,
                website=website,
                is_active=is_active,
                created_by=request.user
            )

            return JsonResponse({
                'success': True, 
                'id': institution.id, 
                'name': institution.name,
                'type': institution.institution_type.name
            })
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def create_person_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        first_last_name = request.POST.get('first_last_name')
        if not all([first_name, first_last_name]):
            messages.error(request, 'Nombre y apellido son requeridos.')
        else:
            try:
                person = Person.objects.create(
                    first_name=first_name.strip(),
                    first_last_name=first_last_name.strip(),
                    created_by=request.user
                )
                messages.success(request, f'Persona "{person.first_name} {person.first_last_name}" creada exitosamente.')
                # Redirect back to the calling page (passed via URL)
                return redirect(request.GET.get('return_url', 'calls:researcher_dashboard'))
            except Exception as e:
                messages.error(request, str(e))
    # Always render the form on GET or after error
    return render(request, 'calls/create_person_page.html', {
        'return_url': request.GET.get('return_url', 'calls:researcher_dashboard'),
    })

@login_required
def create_institution_page(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        institution_type_id = request.POST.get('institution_type')
        country_id = request.POST.get('country')
        tax_register_number = request.POST.get('tax_register_number')
        acronym = request.POST.get('acronym', '')
        website = request.POST.get('website', '')
        is_active = request.POST.get('is_active') == 'on'

        if not all([name, institution_type_id, country_id, tax_register_number]):
            messages.error(request, 'Name, type, country, and tax number are required.')
        else:
            try:
                institution_type = InstitutionType.objects.get(id=institution_type_id)
                country = Country.objects.get(id=country_id)
                institution = Institution.objects.create(
                    name=name,
                    institution_type=institution_type,
                    country=country,
                    tax_register_number=tax_register_number,
                    acronym=acronym,
                    website=website,
                    is_active=is_active,
                    created_by=request.user
                )
                messages.success(request, f'Institución "{institution.name}" creada exitosamente.')
                # Redirect back to the calling page (passed via URL)
                return redirect(request.GET.get('return_url', 'calls:researcher_dashboard'))
            except Exception as e:
                messages.error(request, str(e))

    institution_types = InstitutionType.objects.filter(is_active=True).order_by('name')
    countries = Country.objects.all().order_by('name')

    return render(request, 'calls/create_institution_page.html', {
        'institution_types': institution_types,
        'countries': countries,
        'return_url': request.GET.get('return_url', 'calls:researcher_dashboard'),
    })

@login_required
def create_thematic_axis(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            is_active = request.POST.get('is_active') == 'on'

            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required.'})

            axis = ThematicAxis.objects.create(
                name=name,
                description=description,
                is_active=is_active,
                created_by=request.user
            )

            return JsonResponse({
                'success': True,
                'id': axis.id,
                'name': axis.name,
                'description': axis.description
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def create_strategic_effect(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            is_active = request.POST.get('is_active') == 'on'
            thematic_axis_id = request.POST.get('thematic_axis')

            if not name or not thematic_axis_id:
                return JsonResponse({'success': False, 'error': 'Name and Thematic Axis are required.'})


            thematic_axis = ThematicAxis.objects.get(id=thematic_axis_id)

            effect = StrategicEffect.objects.create(
                name=name,
                description=description,
                is_active=is_active,
                thematic_axis=thematic_axis,
                created_by=request.user
            )

            return JsonResponse({
                'success': True,
                'id': effect.id,
                'name': effect.name,
                'axis': effect.thematic_axis.name,
                'description': effect.description
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def view_call(request, call_pk):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('home')

    call = get_object_or_404(Call, pk=call_pk, coordinator=request.user.customuser)

    if request.method == 'POST':
        new_status_id = request.POST.get('status')
        if new_status_id:
            try:
                new_status = Status.objects.get(id=new_status_id)
                call.status = new_status
                call.save()
                messages.success(request, f'Call status updated to "{new_status.name}".')
            except Status.DoesNotExist:
                messages.error(request, 'Invalid status selected.')
        else:
            messages.error(request, 'No status selected.')

        return redirect('calls:view_call', call_pk=call.pk)

    # Get all possible statuses for dropdown
    statuses = Status.objects.all().order_by('name')

    return render(request, 'calls/view_call.html', {
        'call': call,
        'statuses': statuses,
    })

@login_required
def call_detail(request, call_pk):
    call = get_object_or_404(Call, pk=call_pk)
    return render(request, 'calls/call_detail.html', {'call': call})

@login_required
def setup_call(request, call_pk):
    call = get_object_or_404(Call, pk=call_pk)

    # Permission: Must be coordinator of this call
    if not hasattr(request.user, 'customuser') or call.coordinator != request.user.customuser:
        messages.error(request, "You are not authorized to manage this call.")
        return redirect('calls:coordinator_dashboard')

    # Get or create ProponentForm for this call
    proponent_form, created = ProponentForm.objects.get_or_create(
        call=call,
        defaults={'title': f"Form for {call.title}"}
    )

    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        action = request.POST.get('action')

        if question_id and action == 'add':
            shared_question = get_object_or_404(SharedQuestion, pk=question_id)
            obj, created = ProponentFormQuestion.objects.get_or_create(
                form=proponent_form,
                shared_question=shared_question,
                defaults={'order': proponent_form.form_questions.count() + 1}
            )
            if created:
                messages.success(request, 'Question added to form.')
            else:
                messages.info(request, 'Question was already in the form.')

        elif question_id and action == 'remove':
            deleted, _ = ProponentFormQuestion.objects.filter(
                form=proponent_form,
                shared_question_id=question_id
            ).delete()
            if deleted:
                messages.success(request, 'Question removed from form.')
            else:
                messages.info(request, 'Question was not in the form.')

        return redirect('calls:setup_call', call_pk=call.pk)

    # Get all questions and which are in form
    all_questions = SharedQuestion.objects.filter(is_active=True)
    form_question_ids = set(proponent_form.form_questions.values_list('shared_question_id', flat=True))

    return render(request, 'calls/setup_call.html', {
        'call': call,
        'proponent_form': proponent_form,
        'all_questions': all_questions,
        'form_question_ids': form_question_ids,
    })

@login_required
def edit_thematic_axis(request, axis_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    axis = get_object_or_404(ThematicAxis, id=axis_id)

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            is_active = request.POST.get('is_active') == 'on'

            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required.'})

            axis.name = name
            axis.description = description
            axis.is_active = is_active
            axis.save()

            return JsonResponse({
                'success': True,
                'id': axis.id,
                'name': axis.name,
                'description': axis.description
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def edit_strategic_effect(request, effect_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    effect = get_object_or_404(StrategicEffect, id=effect_id)

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            is_active = request.POST.get('is_active') == 'on'
            thematic_axis_id = request.POST.get('thematic_axis') 

            if not name or not thematic_axis_id:
                return JsonResponse({'success': False, 'error': 'Name and Thematic Axis are required.'})

            thematic_axis = ThematicAxis.objects.get(id=thematic_axis_id)

            effect.name = name
            effect.description = description
            effect.is_active = is_active
            effect.thematic_axis = thematic_axis 
            effect.save()

            return JsonResponse({
                'success': True,
                'id': effect.id,
                'name': effect.name,
                'axis': effect.thematic_axis.name,
                'description': effect.description
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def delete_thematic_axis(request, axis_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    axis = get_object_or_404(ThematicAxis, id=axis_id)
    axis.delete()
    messages.success(request, 'Thematic Axis deleted successfully!')
    return redirect('calls:coordinator_dashboard')

@login_required
def delete_strategic_effect(request, effect_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    effect = get_object_or_404(StrategicEffect, id=effect_id)
    effect.delete()
    messages.success(request, 'Strategic Effect deleted successfully!')
    return redirect('calls:coordinator_dashboard')



@login_required
def create_budget_category(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            is_active = request.POST.get('is_active') == 'on'

            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required.'})

            category = BudgetCategory.objects.create(
                name=name,
                description=description,
                is_active=is_active,
                created_by=request.user
            )

            return JsonResponse({
                'success': True,
                'id': category.id,
                'name': category.name,
                'description': category.description
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def edit_budget_category(request, category_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    category = get_object_or_404(BudgetCategory, id=category_id)

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            is_active = request.POST.get('is_active') == 'on'

            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required.'})

            category.name = name
            category.description = description
            category.is_active = is_active
            category.save()

            return JsonResponse({
                'success': True,
                'id': category.id,
                'name': category.name,
                'description': category.description
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def delete_budget_category(request, category_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('home')

    category = get_object_or_404(BudgetCategory, id=category_id)
    category.delete()
    messages.success(request, 'Budget Category deleted successfully!')
    return redirect('calls:coordinator_dashboard')

@login_required
def create_budget_period(request):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            order = request.POST.get('order', 1)

            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required.'})

            period = BudgetPeriod.objects.create(
                name=name,
                order=order,
                created_by=request.user
            )

            return JsonResponse({
                'success': True,
                'id': period.id,
                'name': period.name,
                'order': period.order
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def edit_budget_period(request, period_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        return JsonResponse({'success': False, 'error': 'Access denied.'})

    period = get_object_or_404(BudgetPeriod, id=period_id)

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            order = request.POST.get('order', 1)

            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required.'})

            period.name = name
            period.order = order
            period.save()

            return JsonResponse({
                'success': True,
                'id': period.id,
                'name': period.name,
                'order': period.order
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def delete_budget_period(request, period_id):
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
        messages.error(request, "Access denied.")
        return redirect('home')

    period = get_object_or_404(BudgetPeriod, id=period_id)
    period.delete()
    messages.success(request, 'Budget Period deleted successfully!')
    return redirect('calls:coordinator_dashboard')


# Researcher related
@login_required
def researcher_dashboard(request):
    # Simple placeholder 
    if not hasattr(request.user, 'customuser'):
        messages.error(request, "User profile not found.")
        return redirect('home')

    # Show calls the researcher can apply to
    from .models import Call
    open_calls = Call.objects.filter(
        status__name='Abierta'  # based on Status model
    ).order_by('-opening_datetime')

    # Add context for apply form (optional, but good for consistency)
    thematic_axes = ThematicAxis.objects.filter(is_active=True)
    countries = Country.objects.all()

    return render(request, 'calls/researcher_dashboard.html', {
        'open_calls': open_calls,
        'thematic_axes': thematic_axes,  # Optional
        'countries': countries,          # Optional
    })

    # return render(request, 'calls/researcher_dashboard.html', {
    #     'open_calls': open_calls,
    # })

@login_required
def apply_call(request, call_pk):
    try:
        call = get_object_or_404(Call, pk=call_pk)
        if call.status.name != 'Abierta':
            messages.error(request, "This call is not currently open for applications.")
            return redirect('calls:researcher_dashboard')
    except Http404:
        messages.error(request, "Call not found.")
        return redirect('calls:researcher_dashboard')

        
    
    # Ensure the user is a researcher
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Researcher':
        messages.error(request, "Only researchers can apply to calls.")
        return redirect('home')
    
    # Get or create Expression for this user + call

    default_axis = ThematicAxis.objects.filter(is_active=True).first()
    default_country = Country.objects.first()
    default_status = Status.objects.filter(name='Abierta').first()

    # Validate system configuration before creating
    if not default_axis or not default_country or not default_status:
        messages.error(
            request,
            "System configuration incomplete: missing thematic axis, country, or status."
        )
        return redirect('home')

    expression, created = Expression.objects.get_or_create(
        user=request.user.customuser,
        call=call,
        defaults={
            'thematic_axis': default_axis,
            'status': default_status,
            'project_title': f'Borrador: {call.title}',
            'implementation_country': default_country,
            'problem': 'Descripción breve del problema a abordar.',
            'general_objective': 'Descripción del objetivo general del proyecto.',
            'methodology': 'Descripción breve de la metodología, el marco ético del proyecto y el abordaje comunitario. Los proyectos deberán basarse en el respeto por las voces, conocimientos, experiencias y realidades locales, promoviendo activamente la inclusión, la diversidad, interseccionalidad y la representación de los saberes y perspectivas de grupos en situación de vulnerabilidad.',
        }
    )

    # Get ProponentForm for this call
    try:
        proponent_form = ProponentForm.objects.get(call=call)
        form_questions = proponent_form.form_questions.select_related('shared_question').order_by('order')
    except ProponentForm.DoesNotExist:
        form_questions = []

    # Get data for the form
    strategic_effects = StrategicEffect.objects.filter(is_active=True).order_by('name')
    thematic_axes = ThematicAxis.objects.filter(is_active=True)
    countries = Country.objects.all()
    budget_categories = BudgetCategory.objects.filter(is_active=True).order_by('name')
    budget_periods = BudgetPeriod.objects.all().order_by('order', 'name')
    existing_budget_items = BudgetItem.objects.filter(expression=expression).select_related('category', 'period')
    documents = ExpressionDocument.objects.filter(expression=expression)
    institution_types = InstitutionType.objects.filter(is_active=True).order_by('name')
    people = Person.objects.filter(created_by__isnull=False).order_by('first_name', 'first_last_name')
    scale_choices = Scale.objects.filter(is_active=True).order_by('name')

    # Initialize post_data here - always exists, even on GET
    post_data = {}
    doc_form = ExpressionDocumentForm()
    print("Check documents")
    if documents.exists():
        print("Check documents... They exist.")
        doc_form.fields['file'].required = False
        print(doc_form.fields['file'].required )

    if request.method == 'POST':
        #print(request.POST)
        print('remove_document' in request.POST)
        print(request.POST.get('remove_document'))
        if request.method == "POST" and 'remove_document' in request.POST:
            doc_id = request.POST.get('remove_document')
            ExpressionDocument.objects.filter(id=doc_id, expression=expression).delete()
            messages.info(request, "File removed.")
            # Do NOT proceed to form validation, redirect to avoid re-submission
            #return redirect('calls:apply_call', call_pk=call_pk)
            return JsonResponse({'success': True})
        
        # Capture ALL POST data for re-population
        post_data = {
            'project_title': request.POST.get('project_title', '').strip(),
            'thematic_axis': request.POST.get('thematic_axis'),
            'implementation_country': request.POST.get('implementation_country'),
            'problem': request.POST.get('problem', '').strip(),
            'general_objective': request.POST.get('general_objective', '').strip(),
            'methodology': request.POST.get('methodology', '').strip(),
            'funding_eligibility_acceptance': request.POST.get('funding_eligibility_acceptance') == 'on',
            'primary_institution_id': request.POST.get('primary_institution_id'),
        }

        # Populate Expression from POST
        expression.project_title = post_data['project_title']
        expression.thematic_axis_id = post_data['thematic_axis']
        expression.implementation_country_id = post_data['implementation_country']
        expression.problem = post_data['problem']
        expression.general_objective = post_data['general_objective']
        expression.methodology = post_data['methodology']
        expression.funding_eligibility_acceptance = post_data['funding_eligibility_acceptance']
        
        # Graceful handling for missing primary institution
        inst_id = post_data['primary_institution_id']
        if inst_id and inst_id.isdigit():
            try:
                institution = Institution.objects.get(id=int(inst_id))
                expression.primary_institution = institution
            except Institution.DoesNotExist:
                messages.error(request, "Institución seleccionada no válida.")
                expression.primary_institution = None
        else:
            expression.primary_institution = None
        
        # Validate required fields
        # if not all([
        #     expression.project_title,
        #     expression.thematic_axis_id,
        #     expression.implementation_country_id,
        #     expression.problem,
        #     expression.general_objective,
        #     expression.methodology,
        #     expression.primary_institution_id
        # ]):
        #     messages.error(request, "Please fill in all required fields marked with *.")
        # else:
        #     expression.save()
        required_fields = {
            "Project title": expression.project_title,
            "Thematic axis": expression.thematic_axis_id,
            "Implementation country": expression.implementation_country_id,
            "Problem": expression.problem,
            "General objective": expression.general_objective,
            "Methodology": expression.methodology,
            "Primary institution": expression.primary_institution_id,
        }

        has_errors = False

        missing = [label for label, value in required_fields.items() if value is None or value == ""]
        if missing:
            has_errors = True
            for field in missing:
                messages.error(request, f"The field '{field}' is required.")

        if not has_errors:
            expression.save()
        
        #print('Post required fields', request.POST)
        # Only proceed if core fields are valid
        #if not any(messages.get_messages(request)):
        storage = messages.get_messages(request)
        has_errors = any(storage)
        # re-add them so template still shows them
        for m in storage:
            messages.add_message(request, m.level, m.message)
            print(m.message)

        if not has_errors:
            # Process dynamic questions
            #print('Dynamic questions', request.POST)
            question_errors = []
            for fq in form_questions:
                field_name = f"question_{fq.shared_question.id}"
                #value = request.POST.get(field_name)
                raw_value = request.POST.get(field_name)
                if fq.shared_question.field_type == 'boolean':
                    value = raw_value == "on"
                else:
                    value = raw_value

                if fq.shared_question.is_required and not value:
                    question_errors.append(f'Question "{fq.shared_question.question}" is required.')
                    continue
                    #messages.error(request, f'Question "{fq.shared_question.question}" is required.')
                
                if value is not None:
                    ProponentResponse.objects.update_or_create(
                        expression=expression,
                        shared_question=fq.shared_question,
                        defaults={'value': value}
                    )
            if question_errors:
                for err in question_errors:
                    messages.error(request, err)
                #return redirect(request.path)
            else:  # Only if no break
                # Products
                #print('Products', request.POST)
                Product.objects.filter(expression=expression).delete()
                product_indices = set(k.split('_')[-1] for k in request.POST.keys() if k.startswith('product_title_'))
                for index in product_indices:
                    title = request.POST.get(f'product_title_{index}', '').strip()
                    if title:
                        product = Product.objects.create(
                            expression=expression,
                            title=title,
                            description=request.POST.get(f'product_description_{index}', ''),
                            outcome=request.POST.get(f'product_outcome_{index}', ''),
                            start_date=request.POST.get(f'product_start_date_{index}'),
                            end_date=request.POST.get(f'product_end_date_{index}'),
                            status=Status.objects.get(name='Abierta'),
                            created_by=request.user
                        )
                        effect_ids = request.POST.getlist(f'product_strategic_effects_{index}')
                        if effect_ids:
                            product.strategic_effects.set(StrategicEffect.objects.filter(id__in=effect_ids))

                # Team Members
                #print('Project Members', request.POST)
                ExpressionTeamMember.objects.filter(expression=expression).delete()
                team_indices = set(k.split('_')[-1] for k in request.POST.keys() if k.startswith('team_member_person_'))
                for index in team_indices:
                    person_id = request.POST.get(f'team_member_person_{index}')
                    role = request.POST.get(f'team_member_role_{index}', '').strip()
                    if person_id and person_id.strip() and role:
                        member = ExpressionTeamMember.objects.create(
                            expression=expression,
                            person_id=person_id,
                            role=role,
                            status_id=request.POST.get(f'team_member_status_{index}'),
                            start_date=request.POST.get(f'team_member_start_date_{index}'),
                            end_date=request.POST.get(f'team_member_end_date_{index}'),
                            institution_id=request.POST.get(f'team_member_institution_id_{index}')
                        )
                        # Antecedents
                        axis_ids = request.POST.getlist(f'team_member_antecedent_axis_{index}')
                        descriptions = request.POST.getlist(f'team_member_antecedent_description_{index}')
                        urls = request.POST.getlist(f'team_member_antecedent_url_{index}')
                        for i, axis_id in enumerate(axis_ids):
                            if i < len(descriptions) and descriptions[i].strip():
                                ExpressionInvestigatorThematicAntecedent.objects.create(
                                    team_member=member,
                                    thematic_axis_id=axis_id,
                                    description=descriptions[i].strip(),
                                    evidence_url=urls[i].strip() if i < len(urls) else ''
                                )

                # Budget Items
                #print('Budget', request.POST)
                BudgetItem.objects.filter(expression=expression).delete()
                budget_indices = set(k.split('_')[-1] for k in request.POST.keys() if k.startswith('budget_item_category_'))
                total_budget = 0
                for index in budget_indices:
                    category_id = request.POST.get(f'budget_item_category_{index}')
                    period_id = request.POST.get(f'budget_item_period_{index}')
                    amount_str = request.POST.get(f'budget_item_amount_{index}', '').strip()
                    notes = request.POST.get(f'budget_item_notes_{index}', '').strip()
                    if category_id and period_id:
                        try:
                            amount = float(amount_str) if amount_str else 0.0
                            if amount <= 0:
                                raise ValueError("El valor debe ser mayor que 0.")
                            category = BudgetCategory.objects.get(id=category_id)
                            period = BudgetPeriod.objects.get(id=period_id)
                            BudgetItem.objects.create(
                                expression=expression,
                                category=category,
                                period=period,
                                amount=amount,
                                notes=notes
                            )
                            total_budget += amount
                        except ValueError as e:
                            messages.error(request, f"Invalid amount in budget item {int(index)+1}: {e}")
                        except BudgetCategory.DoesNotExist:
                            messages.error(request, f"Invalid category in budget item {int(index)+1}")
                        except BudgetPeriod.DoesNotExist:
                            messages.error(request, f"Invalid period in budget item {int(index)+1}")
                
                
                MAX_BUDGET = 900000000
                if total_budget > MAX_BUDGET:
                    messages.error(request, "El presupuesto total no puede exceder los $900.000.000 COP.")
                    return render(request, 'calls/apply_call.html', post_data)

                if total_budget <= 250000000:
                    scale = Scale.objects.get(name='S')
                elif total_budget <= 500000000:
                    scale = Scale.objects.get(name='M')
                else:
                    scale = Scale.objects.get(name='B')
                print(f"Total budget is {total_budget}, therefore scale is {scale}")
                expression.scale = scale

                # Handle scale from hidden field (in case JS is bypassed)
                scale_name = request.POST.get('scale')
                if scale_name and scale_name in ['S', 'M', 'B']:
                    expression.scale = Scale.objects.get(name=scale_name)

                # Documents
                #print('Documents', request.POST)
                if 'file' in request.FILES:
                    print("Got to doc branch")
                    print(f"doc existence {documents.exists()}")
                    doc_form = ExpressionDocumentForm(request.POST, request.FILES)
                    if documents.exists():
                        doc_form.fields['file'].required = False
                    if doc_form.is_valid():
                        doc = doc_form.save(commit=False)
                        doc.expression = expression
                        doc.uploaded_by = request.user.customuser
                        if not doc.file.name.lower().endswith(('.pdf', '.docx', '.jpg', '.png')):
                            messages.error(request, "Only PDF, DOCX, JPG, and PNG files are allowed.")
                        else:
                            doc.save()
                            messages.success(request, "File uploaded successfully!")
                            # Security: Empty file input for next render.
                            doc_form = ExpressionDocumentForm()
                    else:
                        for error in doc_form.non_field_errors():
                            messages.error(request, f"Upload error: {error}")
                else:
                    # No file uploaded in this POST, but we might still need to validate
                    # the form if it's part of the submit. We'll let the form be invalid if required.
                    # But we don't want to show a "required" error if there's already a document.
                    # So, if there are existing documents, we make the form NOT required for this submission.
                    if documents.exists():
                        print("Documents exist...")
                        # Temporarily make the file field not required for this validation
                        doc_form.fields['file'].required = False
                        # We don't validate it here because we're not uploading, but we need to pass it to the template
                        # If the user *did* try to upload, it would have been caught above.
                    # If there are NO documents, we leave document_form as is (required=True) so it validates
                    #   if the user tries to submit without uploading.

                # Submit or save
                if 'submit_application' in request.POST:
                    if not expression.primary_institution_id:
                        messages.error(request, "La institución principal es obligatoria para enviar la expresión.")
                        has_errors = True
                    submitted_status, _ = Status.objects.get_or_create(name='Enviada')
                    expression.status = submitted_status
                    expression.submission_datetime = timezone.now()
                    expression.save()
                    print('Your application has been submitted successfully!')
                    messages.success(request, 'Your application has been submitted successfully!')
                elif 'save_draft' in request.POST:
                    submitted_status, _ = Status.objects.get_or_create(name='Borrador')
                    expression.status = submitted_status
                    expression.submission_datetime = timezone.now()
                    expression.save()
                    print('Your application has been saved as a draft.')
                    messages.success(request, 'Your application has been saved as a draft.')
                else:
                    print("Something wrong")

    # Re-fetch expression to ensure fresh state
    expression = Expression.objects.select_related(
        'thematic_axis',
        'implementation_country',
        'user',
        'call'
    ).prefetch_related(
        'documents',
        'intersectionality_scopes'
    ).get(pk=expression.pk)

    # Prepare context
    institutions_list = list(Institution.objects.filter(is_active=True).order_by('name').values('id', 'name'))

    context = {
        'call': call,
        'expression': expression,
        'form_questions': form_questions,
        'existing_responses': {
            pr.shared_question.id: pr.value 
            for pr in ProponentResponse.objects.filter(expression=expression)
        },
        'thematic_axes': thematic_axes,
        'countries': countries,
        'strategic_effects': strategic_effects,
        'strategic_effects_json': json.dumps([
            {
                'id': effect.id, 
                'name': effect.name,
                'thematic_axis_id': str(effect.thematic_axis_id)
            }
            for effect in strategic_effects
        ], cls=DjangoJSONEncoder),
        'existing_products': Product.objects.filter(expression=expression).prefetch_related('strategic_effects'),
        'existing_team_members': ExpressionTeamMember.objects.filter(expression=expression).prefetch_related('thematic_antecedents'),
        'statuses': Status.objects.all().order_by('name'),
        'institutions': institutions_list,
        'institution_types': institution_types,
        'people': people,
        'people_json': [
            {
                'id': person.id,
                'first_name': person.first_name,
                'first_last_name': person.first_last_name
            }
            for person in people
        ],
        'budget_categories': budget_categories,
        'budget_periods': budget_periods,
        'existing_budget_items': existing_budget_items,
        'scale_choices': scale_choices,
        'scale_choices_json': json.dumps([
            {
                'name': s.name,
                'description': s.description,
                'min_amount': float(s.min_amount),
                'max_amount': float(s.max_amount) if s.max_amount else None
            } 
             for s in scale_choices
        ], cls=DjangoJSONEncoder),
        'documents': documents,
        'document_form': doc_form,
        'intersectionality_scopes': IntersectionalityScope.objects.filter(is_active=True).order_by('name'),
        # ALWAYS pass post_data - even on GET
        'post_data': post_data,
    }

    #print(f"People list is: {context['people_json']}")
    return render(request, 'calls/apply_call.html', context)

@login_required
def get_strategic_effects_by_axis(request):
    """
    AJAX view to get Strategic Effects filtered by Thematic Axis ID.
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

    axis_id = request.GET.get('axis_id')
    if not axis_id:
        return JsonResponse({'success': False, 'error': 'Thematic Axis ID is required.'})

    try:
        effects = StrategicEffect.objects.filter(
            thematic_axis_id=axis_id,
            is_active=True
        ).order_by('name')

        effect_list = [
            {'id': effect.id, 'name': effect.name}
            for effect in effects
        ]

        return JsonResponse({'success': True, 'effects': effect_list})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    

@login_required
def download_expression_document(request, doc_id):
    doc = get_object_or_404(ExpressionDocument, id=doc_id, expression__user=request.user.customuser)
    response = FileResponse(doc.file.open(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{doc.name}"'
    return response    

def render_institution_input(request):
    """
    Renders the institution input partial with given index.
    Used for dynamically adding team members.
    """
    index = request.GET.get('index')
    if not index:
        return JsonResponse({'error': 'index required'}, status=400)

    context = {
        'index': index,
        'institution_name': '',   # empty for new entries
        'institution_id': '',     # empty for new entries
    }
    return render(request, 'calls/institution_input.html', context)

# ===== From: project_team/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: geo/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: cbo/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: budgets/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: evaluations/views.py =====

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
from evaluations.utils import approve_if_auto_approved
from django.db import transaction
from decimal import Decimal
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
        category__template=template
    ).select_related('category').order_by('category__order', 'order')

    if request.method == 'POST':
        total_score = 0
        try:
            with transaction.atomic():
                for item in items:
                    field_name = f"item_{item.id}"
                    score_str = request.POST.get(field_name)
                    comment = request.POST.get(f"comment_{item.id}", "")

                    if not score_str:
                        raise ValueError(f"Debe asignar una puntuación para: {item.question}")

                    try:
                        score = float(score_str)
                        if score < 0 or score > item.max_score:
                            raise ValueError(f"Puntuación inválida para '{item.question}'. Debe estar entre 0 y {item.max_score}.")
                    except ValueError as e:
                        raise ValueError(str(e))

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

                # Calculate ratio safely
                # if evaluation.max_possible_score == 0:
                #     ratio = Decimal('0')
                # else:
                #     ratio = total_score_decimal / evaluation.max_possible_score
                # Recalculate max_possible_score first!
                evaluation.total_score = total_score_decimal
                evaluation.max_possible_score = evaluation.template.get_total_max_score()

                # Then calculate is_positive
                if evaluation.max_possible_score > 0:
                    ratio = total_score / float(evaluation.max_possible_score)
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
            })
        except Exception as e:
            messages.error(request, "Ocurrió un error al guardar la evaluación.")
            print("Error saving evaluation:", e)
            return render(request, 'evaluations/evaluate_expression.html', {
                'evaluation': evaluation,
                'template': template,
                'items': items,
            })

        return redirect('evaluations:evaluator_dashboard')

    context = {
        'evaluation': evaluation,
        'template': template,
        'items': items,
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


# ===== From: common/views.py =====

from django.shortcuts import render

# Create your views here.


# ===== From: accounts/views.py =====

# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import CustomUser, Role
from .forms.forms import ResearcherRegistrationForm, ProfileForm, LoginForm
from django.http import HttpResponse


# def register_view(request):
#     print("\n\nDEBUG: MINIMAL VIEW IS WORKING - URL AND SERVER ARE FINE")
#     return HttpResponse("HELLO FROM REGISTER VIEW - URL ROUTING IS WORKING!")


def register_view(request):
    print("\n\n=== DEBUG: register_view FUNCTION WAS CALLED ===")
    """Registration for researchers only. Coordinators/Evaluators need approval."""
    if request.method == 'POST':
        form = ResearcherRegistrationForm(request.POST)
        print("So far so good...")
        if form.is_valid():
            print("Form is valid...")
            try:
                user = form.save()
                messages.success(request, 'Registro exitoso. Ahora puedes ingresar.')
                return redirect('accounts:login')
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
                print(f"Error de registro: {e}")
        else:
            print("Form is not valid.")
            print("FORM ERRORS:", form.errors)  
            print("NON-FIELD ERRORS:", form.non_field_errors()) 
            # # Create Django User
            # user = User.objects.create_user(
            #     username=form.cleaned_data['username'],
            #     email=form.cleaned_data['email'],
            #     password=form.cleaned_data['password1'],
            #     first_name=form.cleaned_data['first_name'],
            #     last_name=form.cleaned_data['last_name']
            # )
            
            # # Get or create Researcher role
            # researcher_role, created = Role.objects.get_or_create(
            #     name='Researcher',
            #     defaults={'description': 'Research proposal submitter'}
            # )
            
            # # Create CustomUser
            # custom_user = CustomUser.objects.create(
            #     user=user,
            #     email=form.cleaned_data['email'],
            #     role=researcher_role,
            #     phone_number=form.cleaned_data.get('phone_number', '')
            # )
            
            # messages.success(request, 'Registration successful! You can now log in.')
            # return redirect('accounts:login')
    else:
        print("DEBUG: GET request - showing empty form")
        form = ResearcherRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect based on user role
                try:
                    custom_user = user.customuser
                    if custom_user.role and custom_user.role.name == 'Coordinator':
                        return redirect('calls:coordinator_dashboard')
                    elif custom_user.role and custom_user.role.name == 'Evaluator':
                        return redirect('evaluations:evaluator_dashboard')
                    else:  # Researcher or no role
                        return redirect('calls:researcher_dashboard')
                except CustomUser.DoesNotExist:
                    return redirect('home')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})





@login_required
def profile_view(request):
    """User profile management"""
    try:
        custom_user = request.user.customuser
    except CustomUser.DoesNotExist:
        messages.error(request, 'Profile not found. Please contact support.')
        return redirect('home')
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=custom_user)
        if form.is_valid():
            form.save()
            # Also update Django User fields if needed
            request.user.first_name = form.cleaned_data.get('first_name', request.user.first_name)
            request.user.last_name = form.cleaned_data.get('last_name', request.user.last_name)
            request.user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=custom_user)
    
    return render(request, 'accounts/profile.html', {
        'form': form, 
        'custom_user': custom_user
    })

def request_coordinator_access(request):
    """Request coordinator role (needs approval)"""
    if request.method == 'POST':
        # Send email to admin for approval
        subject = f'Coordinator Access Request - {request.user.username}'
        message = f"""
        User {request.user.username} ({request.user.email}) has requested coordinator access.
        
        User details:
        - Name: {request.user.get_full_name()}
        - Email: {request.user.email}
        - Current Role: {getattr(request.user.customuser, 'role', 'None')}
        
        Please review and approve if appropriate.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],  # You need to define this in settings
            fail_silently=False,
        )
        
        messages.success(request, 'Your coordinator access request has been submitted for review.')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/request_coordinator.html')

def request_evaluator_access(request):
    """Request evaluator role (needs approval)"""
    if request.method == 'POST':
        # Similar to coordinator request
        subject = f'Evaluator Access Request - {request.user.username}'
        message = f"""
        User {request.user.username} ({request.user.email}) has requested evaluator access.
        
        User details:
        - Name: {request.user.get_full_name()}
        - Email: {request.user.email}
        - Current Role: {getattr(request.user.customuser, 'role', 'None')}
        
        Please review and approve if appropriate.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        
        messages.success(request, 'Your evaluator access request has been submitted for review.')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/request_evaluator.html')