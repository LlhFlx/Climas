from django.apps import apps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse, FileResponse, Http404
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from .models import Call
from .forms import CallForm, SharedQuestionForm # For create_shared_question
from proponent_forms.models import SharedQuestion
from common.models import Status, Scale
from proponent_forms.models import (
    ProponentForm, 
    ProponentFormQuestion, 
    ProponentResponse, 
    SharedQuestionCategory, 
    SharedQuestionOption
) # For setup_call
# from proponent_forms.models import ProponentForm, ProponentFormQuestion  
from institutions.models import Institution, InstitutionType
from thematic_axes.models import ThematicAxis
from strategic_effects.models import StrategicEffect
from budgets.models import BudgetCategory, BudgetPeriod, ProposalBudgetItem
from geo.models import Country, DocumentType
from people.models import Person
from expressions.models import Expression, ExpressionDocument
from expressions.forms import ExpressionDocumentForm
from proposals.models import Proposal, ProposalDocument, ProposalSpecificObjective
from accounts.models import CustomUser
from products.models import ExpressionProduct, ProposalProduct
from django.forms import modelformset_factory
from django import forms
from django.contrib.contenttypes.models import ContentType
import json
from project_team.models import (
    ExpressionTeamMember, 
    InvestigatorCondition, 
    ExpressionInvestigatorThematicAntecedent, 
    ProposalTeamMember, 
    ProposalInvestigatorThematicAntecedent
)
from intersectionality.models import IntersectionalityScope
from budgets.models import BudgetCategory, BudgetItem, BudgetPeriod
from evaluations.models import Evaluation, EvaluationResponse, EvaluationTemplate, TemplateCategory, TemplateItem
from cbo.models import CBORelevantRole, CBO, CBOAntecedent, CBODocument
from cbo.forms import CBODocumentForm
from django.db import transaction
from collections import defaultdict
from decimal import Decimal

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
    # Filter people NOT linked to any CustomUser (for safe assignment)
    users_with_person = CustomUser.objects.exclude(person__isnull=True).values_list('person_id', flat=True)
    people_without_user = Person.objects.exclude(id__in=users_with_person).order_by('first_name', 'first_last_name')
    people = Person.objects.filter(created_by__isnull=False).order_by('first_name', 'first_last_name')


    # Get all templates
    templates = EvaluationTemplate.objects.all().order_by('-is_active', 'name')
    # print(f"Templates are {templates}")
    
    # Get all submitted expressions (status = 'Enviada')
    submitted_expressions = Expression.objects.filter(
        status__name='Enviada'
    ).select_related('user', 'call', 'scale', 'status').order_by('-submission_datetime')

    submitted_proposals = Proposal.objects.filter(
        proposal_status__name='Enviada'
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
        'submitted_proposals': submitted_proposals,
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
        'people_without_user': people_without_user, 
        'templates': templates,
    }
    return render(request, 'calls/coordinator_dashboard.html', context)


# @login_required
# def assign_evaluator(request, target_type, target_id):
#     if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Coordinator':
#         messages.error(request, "Access denied.")
#         return redirect('calls:coordinator_dashboard')

#     # Map target_type to model
#     model_map = {
#         "expression": Expression,
#         "proposal": Proposal,  # Make sure this import exists!
#     }

#     Model = model_map.get(target_type.lower())
#     if not Model:
#         messages.error(request, "Tipo de objetivo inválido.")
#         return redirect('calls:coordinator_dashboard')

#     # Get the actual object
#     target = get_object_or_404(Model, id=target_id)

#     # Validate status based on type
#     print("x"*50)
#     print(target.proposal_status.name)
#     if target_type == "expression" and target.status.name != 'Enviada':
#         messages.error(request, "Solo se pueden asignar evaluadores a expresiones enviadas.")
#         return redirect('calls:coordinator_dashboard')
#     #elif target_type == "proposal" and target.proposal_status.name != 'Aprobada':
#     elif target_type == "proposal" and target.proposal_status.name != 'Enviada':
#         messages.error(request, "Solo se pueden asignar evaluadores a propuestas aprobadas.")
#         return redirect('calls:coordinator_dashboard')

#     if request.method == 'POST':
#         evaluator_id = request.POST.get('evaluator_id')
#         template_id = request.POST.get('template_id')

#         if not evaluator_id:
#             messages.error(request, "Debe seleccionar un evaluador.")
#             return redirect('calls:coordinator_dashboard')

#         evaluator = get_object_or_404(
#             CustomUser,
#             id=evaluator_id,
#             role__name='Evaluator',
#             role__is_active=True
#         )

#         # Validate template if selected
#         template = None
#         if template_id:
#             try:
#                 if target_type == "expression":
#                     template = EvaluationTemplate.objects.get(
#                         id=template_id,
#                         calls=target.call,
#                         applies_to_expression=True
#                     )
#                 elif target_type == "proposal":
#                     template = EvaluationTemplate.objects.get(
#                         id=template_id,
#                         calls=target.call,
#                         applies_to_proposal=True
#                     )
#             except EvaluationTemplate.DoesNotExist:
#                 messages.error(request, "La plantilla seleccionada no es válida para esta convocatoria o tipo de objetivo.")
#                 return redirect('calls:coordinator_dashboard')

#         # Get or create status
#         pending_status, _ = Status.objects.get_or_create(
#             name='Pendiente',
#             defaults={'description': 'Evaluación pendiente de revisión'}
#         )

#         # Save evaluation dynamically
#         content_type = ContentType.objects.get_for_model(target)

#         evaluation, created = Evaluation.objects.get_or_create(
#             target_content_type=content_type,
#             target_object_id=target.id,
#             evaluator=evaluator,
#             defaults={
#                 'status': pending_status,
#                 'template': template,
#                 'max_possible_score': 100.00,
#                 'created_by': request.user,
#             }
#         )

#         if created:
#             msg = f"Evaluador '{evaluator.person or evaluator.user.username}' asignado"
#             if template:
#                 msg += f" con plantilla '{template.name}'"
#             msg += f" a '{target.project_title}'."
#             messages.success(request, msg)
#         else:
#             messages.info(
#                 request,
#                 f"Evaluador '{evaluator.person or evaluator.user.username}' ya estaba asignado a esta {target_type}."
#             )

#     return redirect('calls:coordinator_dashboard')

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
            # Now handle the "options" JSON from request.POST
            options_json = request.POST.get('options')
            if options_json:
                options_data = json.loads(options_json)
                question.options_set.all().delete()
                for opt in options_data:
                    SharedQuestionOption.objects.create(
                        shared_question=question,
                        display_text=opt['display_text'],
                        score=Decimal(str(opt['score']))
                    )
            messages.success(request, f'Question "{question.question}" created successfully!')
            return redirect('calls:coordinator_dashboard')
    form = SharedQuestionForm()
    categories = SharedQuestionCategory.objects.filter(is_active=True).order_by('order', 'name')
    print(categories)

    return render(request, 'calls/create_shared_question.html', {
        'form': form, 
        'editing': False,
        'categories': categories,
    })

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
            # Handle scored options from hidden JSON input
            options_json = request.POST.get('options')
            if options_json:
                try:
                    options_data = json.loads(options_json)
                    # Clear existing options
                    updated_question.options_set.all().delete()
                    # Create new ones
                    for opt in options_data:
                        SharedQuestionOption.objects.create(
                            shared_question=updated_question,
                            display_text=opt['display_text'],
                            score=Decimal(str(opt['score']))
                        )
                except (ValueError, KeyError, TypeError) as e:
                    # Optional: log error or notify user
                    print(f"Error parsing options on edit: {e}")
            messages.success(request, f'Question "{updated_question.question}" updated successfully!')
            return redirect('calls:coordinator_dashboard')
    
    form = SharedQuestionForm(instance=question)
    categories = SharedQuestionCategory.objects.filter(is_active=True).order_by('order', 'name')

    return render(request, 'calls/create_shared_question.html', {
        'form': form,
        'editing': True,  # Flag to change button text
        'question': question,
        'categories': categories,
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
            name = request.POST.get('name', '').strip()
            institution_type_id = request.POST.get('institution_type')
            country_id = request.POST.get('country')
            tax_register_number = request.POST.get('tax_register_number', '').strip()
            acronym = request.POST.get('acronym', '').strip()
            website = request.POST.get('website', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            legal_rep_id = request.POST.get('legal_representative') or None
            admin_rep_id = request.POST.get('administrative_representative') or None

            # AddressMixin fields
            address_line1 = request.POST.get('address_line1', '').strip()
            address_line2 = request.POST.get('address_line2', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()

            # Phone
            phone_number = request.POST.get('phone_number', '').strip()
            print(name, institution_type_id, country_id, tax_register_number)
            if not all([name, institution_type_id, country_id, tax_register_number]):
                return JsonResponse({'success': False, 'error': 'Name, type, country, and tax number are required.'})

            try:
                institution_type = InstitutionType.objects.get(id=institution_type_id)
                country = Country.objects.get(id=country_id)
            except Country.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'País inválido.'})
            except InstitutionType.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Tipo de institución inválido.'})

            # Optional relations
            legal_rep = None
            if legal_rep_id:
                try:
                    legal_rep = Person.objects.get(id=legal_rep_id)
                except Person.DoesNotExist:
                    pass

            admin_rep = None
            if admin_rep_id:
                try:
                    admin_rep = Person.objects.get(id=admin_rep_id)
                except Person.DoesNotExist:
                    pass

            institution = Institution.objects.create(
                name=name,
                institution_type=institution_type,
                country=country,
                tax_register_number=tax_register_number,
                acronym=acronym,
                website=website,
                is_active=is_active,
                created_by=request.user,
                legal_representative=legal_rep,
                administrative_representative=admin_rep,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                phone_number=phone_number,
            )

            messages.success(request, f"Institución '{name}' creada con éxito.")

            return JsonResponse({
                'success': True, 
                'id': institution.id, 
                'name': institution.name,
                'type': institution.institution_type.name,
                'country': institution.country.name,
            })
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
@transaction.atomic
def create_person_page(request):
    """
    Create a new Person from any context (researcher or coordinator).
    Redirects back to calling page with auto-fill support.
    """
    # Get return URL from query string
    return_url = request.GET.get('return_url') or request.POST.get('return_url')

    # If no return_url is provided, fall back based on user role
    if not return_url:
        user_role = getattr(request.user.customuser.role, 'name', '')
        if user_role == 'Researcher':
            return_url = 'calls:researcher_dashboard'
        elif user_role == 'Coordinator':
            return_url = 'calls:coordinator_dashboard'
        else:
            return_url = 'home'  # Safe fallback

    field_name = request.GET.get('field_name', '') or request.POST.get('field_name', '')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        first_last_name = request.POST.get('first_last_name')
        if not all([first_name, first_last_name]):
            messages.error(request, 'Nombre y apellido son requeridos.')
            # Stay in same context
            context = {
                'return_url': return_url,
                'field_name': field_name,
            }
            return render(request, 'calls/create_person_page.html', context)
        else:
            try:
                person = Person.objects.create(
                    first_name=first_name.strip(),
                    first_last_name=first_last_name.strip(),
                    document_type=DocumentType.objects.first(),
                    document_number=f"TEMP-{Person.objects.count()}",
                    gender='N',
                    created_by=request.user
                )

                # Build success redirect URL
                if return_url.startswith('/'):
                    pass  # Already absolute
                elif ':' in return_url:
                    return_url = f"/{return_url.replace(':', '/')}"

                # Add success parameters
                url_parts = return_url.split('?')[0]
                final_url = f"{url_parts}?created_id={person.id}&field_name={field_name}"

                messages.success(request, f'Persona "{person.first_name} {person.first_last_name}" creada exitosamente.')
                # Redirect back to the calling page (passed via URL)
                # return redirect(request.GET.get('return_url', 'calls:researcher_dashboard'))
                return redirect(final_url)
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

    # Get the latest approved Expression (if any)
    latest_approved_expression = None
    proposal_status = None

    expressions = Expression.objects.filter(
        user=request.user.customuser,
        status__name='Aprobada'
    ).order_by('-created_at')

    if expressions.exists():
        latest_approved_expression = expressions.first()
        # Check if a Proposal exists for this Expression
        if hasattr(latest_approved_expression, 'proposal_set'):
            proposal = latest_approved_expression.proposal_set.first()
            if proposal:
                proposal_status = proposal.status.name

    return render(request, 'calls/researcher_dashboard.html', {
        'open_calls': open_calls,
        'thematic_axes': thematic_axes,  # Optional
        'countries': countries,          # Optional
        'latest_approved_expression': latest_approved_expression,
        'proposal_status': proposal_status,
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
            "Configuración del sistema incompleta: faltan eje temático, país o estado."
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
    all_cbos = CBO.objects.filter(is_active=True).order_by('name')
    cbo_role_choices = CBORelevantRole.PREDEFINED_ROLE_CHOICES
    
    
    # Initialize post_data here - always exists, even on GET
    doc_form = ExpressionDocumentForm()
    # cbo_doc_form = CBODocumentForm()

    # print("Check documents")
    if documents.exists():
        # print("Check documents... They exist.")
        doc_form.fields['file'].required = False
        # print(doc_form.fields['file'].required )

    # if expression.community_organization and expression.community_organization.documents.exists():
    #     cbo_doc_form.fields['file'].required = False

    post_data = {}
    if request.method == 'POST':
        #print(request.POST)
        # print('remove_document' in request.POST)
        # print(request.POST.get('remove_document'))
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
            'cbo_name': request.POST.get('cbo_name', '').strip(),
            'cbo_description': request.POST.get('cbo_description', '').strip(),
            'cbo_number_of_members': request.POST.get('cbo_number_of_members', '').strip(),
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
        # Validate required core fields
        required_fields = {
            "Título del Proyecto": expression.project_title,
            "Eje Temático": expression.thematic_axis_id,
            "País de Implementación": expression.implementation_country_id,
            "Descripción del Problema": expression.problem,
            "Objetivo General": expression.general_objective,
            "Metodología": expression.methodology,
            "Institución Principal": expression.primary_institution_id,
        }

        has_errors = False

        missing = [label for label, value in required_fields.items() if value is None or value == ""]
        if missing:
            has_errors = True
            for field in missing:
                messages.error(request, f"El campo '{field}' es obligatorio.")

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
                ExpressionProduct.objects.filter(expression=expression).delete()
                product_indices = set(k.split('_')[-1] for k in request.POST.keys() if k.startswith('product_title_'))
                for index in product_indices:
                    title = request.POST.get(f'product_title_{index}', '').strip()
                    if title:
                        product = ExpressionProduct.objects.create(
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

                # print("START DEBUG")
                # print("POST keys:")
                # for k in request.POST.keys():
                #     print(f"'{k}'")

                # print("Team indices:", team_indices)
                # for i in team_indices:
                #     key = f"team_member_person_id_{i}"
                #     print(f"Checking key: '{key}' -> {key in request.POST}")
                #     print(f"Raw index repr: {repr(i)}")
                # print(request.POST.get('team_member_person_id_0'))
                # print("END DEBUG")
                # print("Team indices", team_indices)
                # print("POST dict is:",request.POST)
                for index in team_indices:
                    person_id = request.POST.get(f'team_member_person_id_{index}')
                    role = request.POST.get(f'team_member_role_{index}', '').strip()
                    # print(f'team_member_person_id_{index}')
                    # print("Person ID:", request.POST.get(f'team_member_person_id_{index}'))
                    # print("Person ID:", person_id)
                    # print(request.POST.get(f'team_member_role_{index}', '').strip())
                    if person_id and person_id.strip() and role:
                        member = ExpressionTeamMember.objects.create(
                            expression=expression,
                            person_id=person_id,
                            role=role,
                            status_id=request.POST.get(f'team_member_status_{index}'),
                            start_date=request.POST.get(f'team_member_start_date_{index}'),
                            end_date=request.POST.get(f'team_member_end_date_{index}'),
                            institution_id=request.POST.get(f'team_member_institution_{index}')
                        )
                        # print("Member inst ID:", member.institution_id)
                        # Antecedents
                        axis_ids = request.POST.getlist(f'team_member_antecedent_axis_{index}')
                        descriptions = request.POST.getlist(f'team_member_antecedent_description_{index}')
                        urls = request.POST.getlist(f'team_member_antecedent_url_{index}')
                        print(axis_ids)
                        print(descriptions)
                        print(urls)
                        for i, description in enumerate(descriptions):
                            description = description.strip()
                            if not description:
                                continue
                            ExpressionInvestigatorThematicAntecedent.objects.create(
                                team_member=member,
                                thematic_axis_id=axis_ids[i] if i < len(axis_ids) and axis_ids[i] else None,
                                description=description,
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

                cbo_name = post_data['cbo_name']
                if cbo_name:
                    description = post_data['cbo_description']
                    members_str = post_data['cbo_number_of_members']
                    if not members_str.isdigit():
                        messages.warning(request, "Número de miembros inválido.")
                    else:
                        try:
                            cbo, _ = CBO.objects.get_or_create(
                                name=cbo_name,
                                defaults={
                                    'description': description,
                                    'number_of_members': int(members_str),
                                    'is_active': True
                                }
                            )
                            if cbo.description != description or cbo.number_of_members != int(members_str):
                                cbo.description = description
                                cbo.number_of_members = int(members_str)
                                cbo.save()
                            expression.community_organization = cbo

                            # Save CBO roles
                            if expression.community_organization:
                                CBORelevantRole.objects.filter(cbo=expression.community_organization).delete()
                                role_indices = [k.split('_')[-1] for k in request.POST.keys() if k.startswith('cbo_role_person_name_')]
                                for r_idx in role_indices:
                                    person_name = request.POST.get(f'cbo_role_person_name_{r_idx}', '').strip()
                                    if not person_name:
                                        continue
                                    predefined = request.POST.get(f'cbo_role_predefined_{r_idx}')
                                    custom = request.POST.get(f'cbo_role_custom_{r_idx}', '').strip()
                                    phone = request.POST.get(f'cbo_role_phone_{r_idx}', '').strip()
                                    email = request.POST.get(f'cbo_role_email_{r_idx}', '').strip()

                                    CBORelevantRole.objects.create(
                                        cbo=expression.community_organization,
                                        predefined_role=predefined if predefined else None,
                                        custom_role=custom,
                                        person_name=person_name,
                                        contact_phone=phone,
                                        contact_email=email
                                    )
                                
                                # Save CBO document
                                # if 'cbo_document_file' in request.FILES:
                                #     cbo_doc_form = CBODocumentForm(request.POST, request.FILES)
                                #     if expression.community_organization.documents.exists():
                                #         cbo_doc_form.fields['file'].required = False
                                #     if cbo_doc_form.is_valid():
                                #         doc = cbo_doc_form.save(commit=False)
                                #         doc.cbo = expression.community_organization
                                #         doc.uploaded_by = request.user.customuser
                                #         if not doc.file.name.lower().endswith(('.pdf', '.docx', '.jpg', '.png')):
                                #             messages.error(request, "Solo se permiten PDF, DOCX, JPG o PNG para documentos de CBO.")
                                #         else:
                                #             doc.save()
                                #             messages.success(request, "Documento de CBO cargado.")
                                #     else:
                                #         for error in cbo_doc_form.non_field_errors():
                                #             messages.error(request, f"Error en documento de CBO: {error}")
                        except Exception as e:
                            messages.warning(request, f"Error al guardar CBO: {str(e)}")
                else:
                    expression.community_organization = None
                expression.save()

                # Save main expression document
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
                        # print("Documents exist...")
                        # Temporarily make the file field not required for this validation
                        doc_form.fields['file'].required = False
                        # We don't validate it here because we're not uploading, but we need to pass it to the template
                        # If the user *did* try to upload, it would have been caught above.
                    # If there are NO documents, we leave document_form as is (required=True) so it validates
                    #   if the user tries to submit without uploading.

                # -------------------------------
                # FINAL WORD COUNT VALIDATION BLOCK
                # -------------------------------

                has_errors = False  # Reset for word count checks

                # === 1. SINGLE FIELD: Project Title (max 15 words) ===
                title = request.POST.get('project_title', '').strip()
                if title:
                    words = [w for w in title.split() if w]
                    if len(words) > 50:
                        messages.error(request, "El título del proyecto no puede tener más de 15 palabras.")
                        has_errors = True

                # === 2. CATEGORY: All ExpressionProduct Descriptions Combined (max 600 words) ===
                product_desc_words = 0
                product_indices_set = set(k.split('_')[-1] for k in request.POST.keys() if k.startswith('product_description_'))
                for index in product_indices_set:
                    desc = request.POST.get(f'product_description_{index}', '').strip()
                    if desc:
                        word_count = len([w for w in desc.split() if w])
                        product_desc_words += word_count

                if product_desc_words > 600:
                    messages.error(request, f"Las descripciones de productos combinadas exceden el límite de 600 palabras ({product_desc_words}).")
                    has_errors = True

                # === 3. CATEGORY: All Team Member Roles + Antecedents (max 500 words) ===
                team_member_words = 0
                team_indices_set = set(k.split('_')[-1] for k in request.POST.keys() if k.startswith('team_member_role_'))
                print("==== DEBUG TEAM MEMBER WORD COUNT ====")
                print("POST KEYS:", [k for k in request.POST.keys() if k.startswith('team_member')])
                print("team_indices_set:", team_indices_set)
                for index in team_indices_set:
                    role = request.POST.get(f'team_member_role_{index}', '').strip()
                    antecedent_descriptions = request.POST.getlist(f'team_member_antecedent_description_{index}')
                    print(f"Index {index}:")
                    print(f"  role = {repr(role)}")
                    print(f"  antecedent_descriptions = {antecedent_descriptions}")
                    if role:
                        team_member_words += len([w for w in role.split() if w])
                    for desc in antecedent_descriptions:
                        if desc.strip():
                            team_member_words += len([w for w in desc.split() if w])

                if team_member_words > 900:
                    messages.error(request, f"Los roles y antecedentes de colaboradores no deben exceder 500 palabras ({team_member_words}).")
                    has_errors = True

                # === 4. CATEGORY: All Budget Item Notes (max 100 words) ===
                budget_notes_words = 0
                budget_indices_set = set(k.split('_')[-1] for k in request.POST.keys() if k.startswith('budget_item_notes_'))
                for index in budget_indices_set:
                    note = request.POST.get(f'budget_item_notes_{index}', '').strip()
                    if note:
                        budget_notes_words += len([w for w in note.split() if w])

                if budget_notes_words > 100:
                    messages.error(request, f"Las notas del presupuesto no deben superar 100 palabras en total ({budget_notes_words}).")
                    has_errors = True

                # === 5. SINGLE FIELDS: Other Text Fields ===
                field_limits = {
                    'problem': 50,
                    'general_objective': 50,
                    'methodology': 1500,
                }

                for field_name, max_words in field_limits.items():
                    value = request.POST.get(field_name, '').strip()
                    if not value:
                        continue
                    word_count = len([w for w in value.split() if w])
                    if word_count > max_words:
                        human_names = {
                            'problem': 'Descripción del Problema',
                            'general_objective': 'Objetivo General',
                            'methodology': 'Metodología'
                        }
                        messages.error(
                            request,
                            f"{human_names[field_name]} no debe exceder {max_words} palabras ({word_count} detectadas)."
                        )
                        has_errors = True

                # If any word count fails, stop here
                if has_errors:
                    # Re-fetch fresh state
                    expression.refresh_from_db()
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
                        'existing_products': ExpressionProduct.objects.filter(expression=expression).prefetch_related('strategic_effects'),
                        'existing_team_members': ExpressionTeamMember.objects.filter(
                            expression=expression
                        ).select_related('person', 'institution').prefetch_related('expression_thematic_antecedents'),
                        'statuses': Status.objects.all().order_by('name'),
                        'institutions': list(Institution.objects.filter(is_active=True).order_by('name').values('id', 'name')),
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
                        'existing_budget_items': BudgetItem.objects.filter(expression=expression).select_related('category', 'period'),
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
                        'post_data': post_data,
                    }
                    return render(request, 'calls/apply_call.html', context)

                # Submit or save
                if 'submit_application' in request.POST:
                    if not expression.primary_institution_id:
                        messages.error(request, "La institución principal es obligatoria para enviar la expresión.")
                        has_errors = True
                    if expression.status.name == 'Aprobada':
                        messages.warning(request, "Esta expresión ya fue aprobada. No se puede volver a enviar.")
                    else:
                        submitted_status, _ = Status.objects.get_or_create(name='Enviada')
                        expression.status = submitted_status
                        expression.submission_datetime = timezone.now()
                        expression.save()
                        messages.success(request, '¡Expresión de interés enviada con éxito!')
                    #messages.success(request, '¡Expresión de interés enviada con éxito!')
                    return redirect('calls:researcher_dashboard')
                elif 'save_draft' in request.POST:
                    submitted_status, _ = Status.objects.get_or_create(name='Borrador')
                    expression.status = submitted_status
                    expression.submission_datetime = timezone.now()
                    expression.save()
                    print('Expresión guardada como borrador.')
                    messages.success(request, 'Expresión guardada como borrador.')
                    return redirect('calls:researcher_dashboard')
                else:
                    print("Something wrong")

    # Re-fetch expression to ensure fresh state
    expression = Expression.objects.select_related(
        'thematic_axis',
        'implementation_country',
        'user',
        'call',
        'community_organization'
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
        'existing_products': ExpressionProduct.objects.filter(expression=expression).prefetch_related('strategic_effects'),
        'existing_team_members': ExpressionTeamMember.objects.filter(expression=expression).select_related('person', 'institution').prefetch_related('expression_thematic_antecedents'),
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
        'all_cbos': CBO.objects.filter(is_active=True).order_by('name'),
        'cbo_role_choices': CBORelevantRole.PREDEFINED_ROLE_CHOICES,
        # 'cbo_doc_form': cbo_doc_form,
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


@login_required
def apply_proposal(request, expression_id):
    """
    Allows researcher to submit a full Proposal after Expression is approved.
    """
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Researcher':
        messages.error(request, "Solo los investigadores pueden enviar propuestas.")
        return redirect('home')

    expression = get_object_or_404(Expression, id=expression_id, user=request.user.customuser)

    # Only allow if Expression is approved
    if expression.status.name != 'Aprobada':
        messages.error(request, "Esta expresión aún no ha sido aprobada. No puede enviar una propuesta.")
        return redirect('calls:researcher_dashboard')
    
    # Get or create Proposal linked to this Expression
    # proposal, created = Proposal.objects.get_or_create(
    #     pk=expression.pk, 
    #     defaults={
    #         'principal_research_experience': '',
    #         'community_description': '',
    #         'duration_months': 12,
    #         'summary': '',
    #         'context_problem_justification': '',
    #         'specific_objectives': '',
    #         'methodology_analytical_plan_ethics': '',
    #         'equity_inclusion': '',
    #         'communication_strategy': '',
    #         'risk_analysis_mitigation': '',
    #         'research_team': '',
    #         'created_by': request.user,
    #         'status': Status.objects.get_or_create(
    #             name='Borrador',
    #             defaults={
    #                 'description': 'Propuesta creada automáticamente tras aprobación de expresión',
    #                 'is_active': True
    #             }
    #         )[0]
    #     }
    # )

    draft_status, _ = Status.objects.get_or_create(
        name='Borrador',
        defaults={
            'description': 'Propuesta creada automáticamente tras aprobación de expresión',
            'is_active': True
        }
    )
    # Check if proposal already exists
    try:
        proposal = Proposal.objects.get(pk=expression.pk)
        created = False
    except Proposal.DoesNotExist:
        # Promote expression into proposal
        print("Proposal does not exist")
        data = expression.__dict__.copy()
        data.pop("id", None)
        data.pop("_state", None)    
        proposal = Proposal(
            expression_ptr=expression,
            **data,
            #created_by=expression.created_by,
            general_objective_override='',
            principal_research_experience='',
            community_description='',
            duration_months=12,
            summary='',
            context_problem_justification='',
            methodology_analytical_plan_ethics='',
            equity_inclusion='',
            communication_strategy='',
            risk_analysis_mitigation='',
            #research_team='',
            proposal_status=draft_status,
            #user_id=expression.user_id,
            #call_id=expression.call_id,
        )
        created = True
        proposal.save()        

    # Load ProponentForm questions for 'proposal' target
    proposal_questions = []
    try:
        proponent_form = ProponentForm.objects.get(call=expression.call)
        form_questions = ProponentFormQuestion.objects.filter(
            form=proponent_form
        ).select_related('shared_question').order_by('order')
        proposal_questions = [
            fq.shared_question for fq in form_questions
            if fq.shared_question.target_category == 'proposal'
        ]
    except ProponentForm.DoesNotExist:
        pass  # No form: no extra questions

    # Load existing responses for these questions
    existing_responses = ProponentResponse.objects.filter(
        expression=expression,
        shared_question__in=proposal_questions
    )
    response_dict = {resp.shared_question_id: resp for resp in existing_responses}

    # Load context data
    countries = Country.objects.all().order_by('name')
    institutions = list(
        Institution.objects.filter(is_active=True)
        .order_by('name')
        .values('id', 'name')
    )   
    people = Person.objects.filter(created_by__isnull=False).order_by('first_name', 'first_last_name')

    thematic_axes = ThematicAxis.objects.filter(is_active=True)
    strategic_effects = StrategicEffect.objects.filter(is_active=True).order_by('name')
    budget_categories = BudgetCategory.objects.filter(is_active=True).order_by('name')
    budget_periods = BudgetPeriod.objects.all().order_by('order', 'name')
    # all_cbos = CBO.objects.filter(is_active=True).order_by('name')
    # cbo_role_choices =  CBORelevantRole.PREDEFINED_ROLE_CHOICES

    # Load existing Proposal-specific related data: mirrored from apply_call structure
    existing_products = ProposalProduct.objects.filter(proposal=proposal).prefetch_related('strategic_effects')
    existing_team_members = ProposalTeamMember.objects.filter(proposal=proposal).select_related(
        'person', 'institution'
    ).prefetch_related('proposal_thematic_antecedents')
    existing_budget_items = ProposalBudgetItem.objects.filter(proposal=proposal).select_related('category', 'period')

    commitment_docs = proposal.proposal_documents.filter(document_type='commitment')
    partner_institutions = proposal.partner_institutions.all()
    docs_by_institution = defaultdict(list)
    for doc in commitment_docs:
        if doc.linked_institution:
            docs_by_institution[doc.linked_institution].append(doc)
    docs_by_institution = dict(docs_by_institution)

    timeline_doc = proposal.timeline_document
    budget_doc = proposal.budget_document



    # Initialize post_data
    post_data = {}
    
    if request.method == 'POST':
        if request.POST.get('ajax_upload') == '1':
            try:
                file = request.FILES.get('commitment_document')
                institution_id = request.POST.get('institution_id')
                proposal_id = request.POST.get('proposal_id')

                if not file or not institution_id or not proposal_id:
                    return JsonResponse({'success': False, 'error': 'Archivo, institución o propuesta no especificados.'})

                # Validate file type
                allowed_mime_types = [
                    'application/pdf',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ]
                if file.content_type not in allowed_mime_types:
                    return JsonResponse({'success': False, 'error': 'Solo se permiten archivos PDF o DOCX.'})

                # Validate file size (10 MB)
                if file.size > 10 * 1024 * 1024:
                    return JsonResponse({'success': False, 'error': 'El archivo no puede exceder 10 MB.'})

                institution = Institution.objects.get(id=institution_id)
                proposal = Proposal.objects.get(pk=proposal_id)

                # Validate institution is linked to proposal
                if not proposal.partner_institutions.filter(id=institution_id).exists():
                    return JsonResponse({'success': False, 'error': 'Institución no asignada a esta propuesta.'})

                doc = ProposalDocument.objects.create(
                    proposal=proposal,
                    file=file,
                    document_type='commitment',
                    uploaded_by=request.user.customuser
                )

                # Link to proposal's M2M commitments
                proposal.partner_institution_commitments.add(doc)

                return JsonResponse({
                    'success': True,
                    'id': doc.id,
                    'name': doc.name,
                    'url': doc.file.url,
                })

            except Institution.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Institución no encontrada.'})
            except Proposal.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Propuesta no encontrada.'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': 'Error interno del servidor. Por favor, inténtelo de nuevo.'})
        # Capture all POST data
        post_data = {
            'project_title_override': request.POST.get('project_title_override', '').strip(),
            'general_objective_override': request.POST.get('general_objective_override', '').strip(),
            'thematic_axis_override': request.POST.get('thematic_axis_override'),
            'principal_research_experience': request.POST.get('principal_research_experience', '').strip(),
            'community_description': request.POST.get('community_description', '').strip(),
            'duration_months': request.POST.get('duration_months', 12),
            'summary': request.POST.get('summary', '').strip(),
            'context_problem_justification': request.POST.get('context_problem_justification', '').strip(),
            'specific_objectives': request.POST.get('specific_objectives', '').strip(),
            'methodology_analytical_plan_ethics': request.POST.get('methodology_analytical_plan_ethics', '').strip(),
            'equity_inclusion': request.POST.get('equity_inclusion', '').strip(),
            'communication_strategy': request.POST.get('communication_strategy', '').strip(),
            'risk_analysis_mitigation': request.POST.get('risk_analysis_mitigation', '').strip(),
            #'research_team': request.POST.get('research_team', '').strip(),
            'community_country': request.POST.get('community_country'),
            'project_location': request.POST.get('project_location'),
            'principal_investigator_title': request.POST.get('principal_investigator_title', '').strip(),
            'principal_investigator_position': request.POST.get('principal_investigator_position', '').strip(),
            'primary_institution_id': request.POST.get('primary_institution_id'),
            'total_requested_budget': request.POST.get('total_requested_budget', '').strip(),
        }
        
        # Update Proposal fields
        proposal.project_title_override = post_data['project_title_override']
        proposal.general_objective_override = post_data['general_objective_override']
        print(proposal.project_title_override)
        proposal.principal_research_experience = post_data['principal_research_experience']
        proposal.community_description = post_data['community_description']
        proposal.duration_months = int(post_data['duration_months']) if post_data['duration_months'] else 12
        proposal.summary = post_data['summary']
        proposal.context_problem_justification = post_data['context_problem_justification']
        #proposal.specific_objectives = post_data['specific_objectives']
        proposal.methodology_analytical_plan_ethics = post_data['methodology_analytical_plan_ethics']
        proposal.equity_inclusion = post_data['equity_inclusion']
        proposal.communication_strategy = post_data['communication_strategy']
        proposal.risk_analysis_mitigation = post_data['risk_analysis_mitigation']
        #proposal.research_team = post_data['research_team']
        proposal.principal_investigator_title = post_data['principal_investigator_title']
        proposal.principal_investigator_position = post_data['principal_investigator_position']

        # # Update proposal fields
        # for field in [
        #     'principal_research_experience', 'community_description', 'summary',
        #     'context_problem_justification', 'methodology_analytical_plan_ethics',
        #     'equity_inclusion', 'communication_strategy', 'risk_analysis_mitigation', 'research_team',
        #     'principal_investigator_title', 'principal_investigator_position'
        # ]:
        #     setattr(proposal, field, post_data[field])     


        # Country fields
        if post_data['community_country']:
            proposal.community_country = Country.objects.get(id=post_data['community_country'])
        if post_data['project_location']:
            proposal.project_location = Country.objects.get(id=post_data['project_location'])

        if post_data['primary_institution_id'] and post_data['primary_institution_id'].isdigit():
            try:
                proposal.primary_institution = Institution.objects.get(id=int(post_data['primary_institution_id']))
            except Institution.DoesNotExist:
                pass

        if post_data['project_title_override']:
            proposal.project_title_override = post_data['project_title_override']
        if post_data['thematic_axis_override']:
            try:
                proposal.thematic_axis_override = ThematicAxis.objects.get(id=post_data['thematic_axis_override'])
            except ThematicAxis.DoesNotExist:
                pass

        # # Partner institutions
        # institution_ids = request.POST.getlist('partner_institution_ids')
        # proposal.partner_institutions.clear()
        # for inst_id in institution_ids:
        #     if inst_id.isdigit():
        #         try:
        #             inst = Institution.objects.get(id=int(inst_id))
        #             proposal.partner_institutions.add(inst)
        #         except Institution.DoesNotExist:
        #             continue

        # Timeline document
        if 'timeline_document' in request.FILES:
            doc = ProposalDocument.objects.create(
                proposal=proposal,
                file=request.FILES['timeline_document'],
                document_type='timeline',
                uploaded_by=request.user.customuser
            )
            proposal.timeline_document = doc
        elif request.POST.get('remove_timeline_doc'):
            if proposal.timeline_document:
                proposal.timeline_document.delete()
                proposal.timeline_document = None

        # Budget document
        if 'budget_document' in request.FILES:
            doc = ProposalDocument.objects.create(
                proposal=proposal,
                file=request.FILES['budget_document'],
                document_type='budget',
                uploaded_by=request.user.customuser
            )
            proposal.budget_document = doc
        elif request.POST.get('remove_budget_doc'):
            if proposal.budget_document:
                proposal.budget_document.delete()
                proposal.budget_document = None

        # Commitment letters (multiple files)
        # This is for non-AJAX case: e.g., user uploaded multiple files in one go
        if 'commitment_documents' in request.FILES:
            proposal.refresh_from_db()
            for file in request.FILES.getlist('commitment_documents'):
                doc = ProposalDocument.objects.create(
                    proposal=proposal,
                    file=file,
                    document_type='commitment',
                    uploaded_by=request.user.customuser
                )
                # proposal.partner_institution_commitments.add(doc)
                fresh_proposal = Proposal.objects.get(pk=proposal.pk)
                fresh_proposal.partner_institution_commitments.add(doc)

        # Handle removal of individual commitment docs (via AJAX or form)
        if request.POST.get('remove_document'):
            doc_id = request.POST.get('remove_document')
            try:
                doc = ProposalDocument.objects.get(id=doc_id, proposal=proposal)
                # Remove from M2M
                proposal.partner_institution_commitments.remove(doc)
                doc.delete()
            except ProposalDocument.DoesNotExist:
                pass
        
        # Save SharedQuestion responses
        for question in proposal_questions:
            field_name = f'shared_question_{question.id}'
            comment_name = f'shared_question_comment_{question.id}'

            value = request.POST.get(field_name)
            comment = request.POST.get(comment_name, '').strip()

            # Handle value type
            if question.field_type == 'number':
                try:
                    value = float(value) if value else None
                except (TypeError, ValueError):
                    value = None
            # For text/radio/dropdown/dynamic_dropdown, value is string or None

            # Get or create response
            response, created = ProponentResponse.objects.update_or_create(
                expression=expression,
                shared_question=question,
                defaults={'value': value, 'comment': comment}
            )

            # Auto-assign score for choice fields
            if question.field_type in ['radio', 'dropdown']:
                scored_opts = dict(question.get_scored_options())
                response.score = scored_opts.get(str(value), None)
                response.save(update_fields=['score'])

        # ============================
        # SAVE PROPOSAL-SPECIFIC ITEMS
        # ============================

        # Specific Objectives (new table)
        ProposalSpecificObjective.objects.filter(proposal=proposal).delete()
        obj_indices = set(k.split('_')[-1] for k in request.POST.keys() if k.startswith('objective_title_'))
        for idx in obj_indices:
            title = request.POST.get(f'objective_title_{idx}', '').strip()
            desc = request.POST.get(f'objective_description_{idx}', '').strip()
            if title:
                objective = ProposalSpecificObjective.objects.create(
                    proposal=proposal,
                    title=title,
                    description=desc
                )
                print("Got objective:", objective)

        # Products
        ProposalProduct.objects.filter(proposal=proposal).delete()
        product_indices = {k.split('_')[-1] for k in request.POST.keys() if k.startswith('proposal_product_title_')}
        for idx in product_indices:
            title = request.POST.get(f'proposal_product_title_{idx}', '').strip()
            if title:
                product = ProposalProduct.objects.create(
                    proposal=proposal,
                    title=title,
                    description=request.POST.get(f'proposal_product_description_{idx}', '').strip(),
                    outcome=request.POST.get(f'proposal_product_outcome_{idx}', '').strip(),
                    start_date=request.POST.get(f'proposal_product_start_date_{idx}'),
                    end_date=request.POST.get(f'proposal_product_end_date_{idx}'),
                    status=draft_status,
                )
                print("Got Product:", product)
                effect_ids = request.POST.getlist(f'proposal_product_strategic_effects_{idx}')
                if effect_ids:
                    product.strategic_effects.set(StrategicEffect.objects.filter(id__in=effect_ids))

        # Plain budget
        total_budget_str = post_data['total_requested_budget']
        total_requested_budget = None

        if total_budget_str:
            try:
                total_requested_budget = float(total_budget_str)
                if total_requested_budget > 900_000_000:
                    messages.error(request, "El presupuesto total no puede exceder 900,000,000 COP.")
                    has_word_errors = True  # reuse your flag or create a new one
                elif total_requested_budget <= 0:
                    messages.error(request, "El presupuesto total debe ser mayor a 0 COP.")
                    has_word_errors = True
            except (ValueError, TypeError):
                messages.error(request, "Ingrese un valor numérico válido para el presupuesto.")
                has_word_errors = True
        else:
            messages.error(request, "El campo 'Presupuesto Total Solicitado' es obligatorio.")
            has_word_errors = True

        # Budget Items (separate relation)
        # ProposalBudgetItem.objects.filter(proposal=proposal).delete()
        # budget_indices = set(k.split('_')[-1] for k in request.POST.keys() if k.startswith('proposal_budget_category_'))
        # total_budget = 0
        # for idx in budget_indices:
        #     cat_id = request.POST.get(f'proposal_budget_category_{idx}')
        #     period_id = request.POST.get(f'proposal_budget_period_{idx}')
        #     amount_str = request.POST.get(f'proposal_budget_amount_{idx}', '').strip()
        #     notes = request.POST.get(f'proposal_budget_notes_{idx}', '').strip()

        #     if not cat_id or not period_id or not amount_str:
        #         continue

        #     try:
        #         amount = float(amount_str)
        #         if amount <= 0:
        #             raise ValueError()

        #         category = BudgetCategory.objects.get(id=cat_id)
        #         period = BudgetPeriod.objects.get(id=period_id)

        #         item = ProposalBudgetItem.objects.create(
        #             proposal=proposal,
        #             category=category,
        #             period=period,
        #             amount=amount,
        #             notes=notes
        #         )
        #         total_budget += amount
        #     except Exception:
        #         messages.warning(request, f"Ítem de presupuesto inválido: {idx}")

        # proposal.total_requested_budget = total_budget

        # Team Members (separate from Expression)
        ProposalTeamMember.objects.filter(proposal=proposal).delete()
        team_indices = set(k.split('_')[-1] for k in request.POST.keys() if k.startswith('proposal_team_member_person_id_'))
        for idx in team_indices:
            person_id = request.POST.get(f'proposal_team_member_person_id_{idx}')
            role = request.POST.get(f'proposal_team_member_role_{idx}', '').strip()
            inst_id = request.POST.get(f'proposal_team_member_institution_{idx}')

            if person_id and person_id.strip() and role:
                try:
                    member = ProposalTeamMember.objects.create(
                        proposal=proposal,
                        person_id=int(person_id),
                        role=role,
                        institution_id=inst_id,
                        status_id=request.POST.get(f'proposal_team_member_status_{idx}'),
                        # start_date=request.POST.get(f'proposal_team_member_start_date_{idx}'),
                        # end_date=request.POST.get(f'proposal_team_member_end_date_{idx}'),
                    )

                    # Save antecedents
                    axis_ids = request.POST.getlist(f'proposal_team_member_antecedent_axis_{idx}')
                    descriptions = request.POST.getlist(f'proposal_team_member_antecedent_description_{idx}')
                    urls = request.POST.getlist(f'proposal_team_member_antecedent_url_{idx}')

                    for i, description in enumerate(descriptions):
                        description = description.strip()
                        if not description:
                            continue
                            
                        antecedent = ProposalInvestigatorThematicAntecedent.objects.create(
                            team_member=member,
                            thematic_axis_id=axis_ids[i] if i < len(axis_ids) and axis_ids[i] else None,
                            description=description,
                            evidence_url=urls[i].strip() if i < len(urls) else ''
                        )
                        print(antecedent.team_member)
                except Exception as e:
                    messages.warning(request, f"Error al guardar colaborador: {str(e)}")
            else:
                continue

        # CBOs: Handle as dynamic form
        # Clear existing
        # proposal.community_organizations.clear()
        # cbo_indices = {k.split('_')[-1] for k in request.POST.keys() if k.startswith('cbo_name_')}
        # for idx in cbo_indices:
        #     name = request.POST.get(f'cbo_name_{idx}', '').strip()
        #     if not name:
        #         continue
        #     description = request.POST.get(f'cbo_description_{idx}', '').strip()
        #     members = request.POST.get(f'cbo_number_of_members_{idx}', '').strip()
        #     if not members.isdigit():
        #         messages.warning(request, f"CBO '{name}': número de miembros inválido.")
        #         continue
        #     try:
        #         cbo, _ = CBO.objects.get_or_create(
        #             name=name,
        #             defaults={
        #                 'description': description,
        #                 'number_of_members': int(members),
        #                 'is_active': True
        #             }
        #         )
        #         # Update if exists but changed
        #         if cbo.description != description or cbo.number_of_members != int(members):
        #             cbo.description = description
        #             cbo.number_of_members = int(members)
        #             cbo.save()
        #         proposal.community_organizations.add(cbo)

        #         # Save roles for this CBO
        #         role_indices = {k.split('_')[-1] for k in request.POST.keys() if k.startswith(f'cbo_role_person_name_{idx}_')}
        #         CBORelevantRole.objects.filter(cbo=cbo).delete()
        #         for r_idx in role_indices:
        #             person_name = request.POST.get(f'cbo_role_person_name_{idx}_{r_idx}', '').strip()
        #             if not person_name:
        #                 continue
        #             predefined = request.POST.get(f'cbo_role_predefined_{idx}_{r_idx}')
        #             custom = request.POST.get(f'cbo_role_custom_{idx}_{r_idx}', '').strip()
        #             phone = request.POST.get(f'cbo_role_phone_{idx}_{r_idx}', '').strip()
        #             email = request.POST.get(f'cbo_role_email_{idx}_{r_idx}', '').strip()
        #             CBORelevantRole.objects.create(
        #                 cbo=cbo,
        #                 predefined_role=predefined if predefined else None,
        #                 custom_role=custom,
        #                 person_name=person_name,
        #                 contact_phone=phone,
        #                 contact_email=email
        #             )

        #     except Exception as e:
        #         messages.warning(request, f"Error al guardar CBO: {str(e)}")

        # Handle CBO Document Upload or Deletion
        if expression.community_organization:
            existing_cbo_doc = expression.community_organization.documents.first()

            # Upload new CBO document
            if 'cbo_document_file' in request.FILES:
                file = request.FILES['cbo_document_file']
                # Validate file type
                ext = file.name.split('.')[-1].lower()
                if ext not in ['pdf', 'docx']:
                    messages.error(request, "Solo se permiten PDF o DOCX para documentos de CBO.")
                else:
                    # Delete existing if any
                    if existing_cbo_doc:
                        existing_cbo_doc.delete()
                    # Create new
                    
                    CBODocument.objects.create(
                        cbo=expression.community_organization,
                        file=file,
                        uploaded_by=request.user.customuser
                    )
                    messages.success(request, "Documento de CBO cargado.")

            # Delete existing CBO document
            elif request.POST.get('remove_cbo_document') and existing_cbo_doc:
                existing_cbo_doc.delete()
                messages.success(request, "Documento de CBO eliminado.")

        # -------------------------------
        # FINAL WORD COUNT VALIDATION BLOCK
        # -------------------------------

        has_word_errors = False

        def count_words(text):
            return len([w for w in text.strip().split() if w])

        field_limits = [
            ('principal_research_experience', 250, "Experiencia en investigación del Investigador/a Principal"),
            ('summary', 250, "Resumen"),
            ('context_problem_justification', 400, "Contexto, problema y justificación"),
            ('specific_objectives', 200, "Objetivos específicos"),
            ('methodology_analytical_plan_ethics', 1500, "Metodología, planeamiento analítico y aspectos éticos"),
            ('equity_inclusion', 250, "Equidad, género, interseccionalidad e inclusión"),
            ('communication_strategy', 100, "Estrategia de comunicación"),
            ('risk_analysis_mitigation', 200, "Riesgos y plan de mitigación"),
            #('research_team', 900, "Equipo de investigación"),
            ('community_description', 150, "Descripción de la Comunidad"),
        ]

        for field_name, max_words, label in field_limits:
            value = post_data.get(field_name, '')
            if not value:
                print(f"{field_name} -- {label}: No value")
                continue
            word_count = count_words(value)
            if word_count > max_words:
                messages.error(
                    request,
                    f"{label}: Máximo {max_words} palabras. Tienes {word_count}."
                )
                has_word_errors = True
                print(f"{label}: Máximo {max_words} palabras. Tienes {word_count}.")
            f"{label}: Máximo {max_words} palabras. Tienes {word_count}."
        # If any word count fails, re-render with error messages
        if has_word_errors:
            # Re-fetch fresh proposal
            try:
                proposal = Proposal.objects.select_related(
                    'expression_ptr__call',
                    'expression_ptr__user',
                    'expression_ptr__thematic_axis',
                    'expression_ptr__implementation_country',
                    'expression_ptr__primary_institution',
                    'community_country',
                    'project_location',
                    'timeline_document',
                    'budget_document',
                ).prefetch_related(
                    'partner_institutions',
                    'proposal_documents'
                ).get(pk=proposal.pk)
            except Proposal.DoesNotExist:
                pass

            context = {
                'call': expression.call,
                'expression': expression,
                'proposal': proposal,
                'countries': countries,
                'institutions': institutions,
                'thematic_axes': thematic_axes,
                'strategic_effects': strategic_effects,
                'strategic_effects_json': json.dumps([
                    {
                        'id': effect.id,
                        'name': effect.name,
                        'thematic_axis_id': effect.thematic_axis_id
                    }
                    for effect in strategic_effects
                ], cls=DjangoJSONEncoder),
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
                # 'all_cbos': all_cbos,
                # 'cbo_role_choices': cbo_role_choices,
                'cbo': expression.community_organization,
                'existing_cbo_doc': expression.community_organization.documents.first() if expression.community_organization else None,
                'commitment_docs': commitment_docs,
                'timeline_doc': timeline_doc,
                'budget_doc': budget_doc,
                'existing_proposal_products': existing_products,
                'existing_proposal_team_members': existing_team_members,
                'existing_proposal_budget_items': existing_budget_items,
                'partner_institutions': partner_institutions,
                'docs_by_institution': docs_by_institution,
                'post_data': post_data,
                'proposal_id': proposal.id,
                'proposal_questions': proposal_questions,
                'response_dict': response_dict,
            }
            return render(request, 'calls/apply_proposal.html', context)

        #  ALL VALIDATIONS PASSED, THEN SAVE PROPOSAL
        proposal.total_requested_budget = total_requested_budget
        # Save
        proposal.save()

        if 'submit_proposal' in request.POST:
            status, _ = Status.objects.get_or_create(
                name='Enviada',
                defaults={'description': 'Propuesta enviada por investigador', 'is_active': True}
            )
            proposal.proposal_status = status
            proposal.submission_datetime = timezone.now()
            proposal.save()
            print(proposal.proposal_status)
            messages.success(request, "¡Propuesta formal enviada con éxito! Su propuesta será revisada por el coordinador.")
            return redirect('calls:researcher_dashboard')
        elif 'save_draft' in request.POST:
            status, _ = Status.objects.get_or_create(
                name='Borrador',
                defaults={'description': 'Propuesta guardada como borrador', 'is_active': True}
            )
            proposal.proposal_status = status
            proposal.save()
            messages.success(request, "Propuesta guardada como borrador.")
            return redirect('calls:researcher_dashboard')

    # Re-fetch fresh state
    try:
        proposal.refresh_from_db()
    except:
        pass

    context = {
        'call': expression.call,
        'expression': expression,
        'proposal': proposal,
        'countries': countries,
        'institutions': institutions,
        'thematic_axes': thematic_axes,
        'strategic_effects': strategic_effects,
        'strategic_effects_json': json.dumps([
                    {
                        'id': effect.id,
                        'name': effect.name,
                        'thematic_axis_id': effect.thematic_axis_id
                    }
                    for effect in strategic_effects
                ], cls=DjangoJSONEncoder),
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
        # 'all_cbos': all_cbos,
        # 'cbo_role_choices': cbo_role_choices,
        'cbo': expression.community_organization,
        'existing_cbo_doc': expression.community_organization.documents.first() if expression.community_organization else None,
        'commitment_docs': commitment_docs,
        'timeline_doc': timeline_doc,
        'budget_doc': budget_doc,
        'existing_proposal_products': existing_products,
        'existing_proposal_team_members': existing_team_members,
        'existing_proposal_budget_items': existing_budget_items,
        'partner_institutions': partner_institutions,
        'docs_by_institution': docs_by_institution,
        'post_data': post_data,
        'proposal_id': proposal.id,
        'proposal_questions': proposal_questions,
        'response_dict': response_dict,
    }

    return render(request, 'calls/apply_proposal.html', context)


@login_required
def upload_commitment_document(request):
    """
    Uploads a commitment letter. It is linked to the Proposal.
    The institution is identified by ID from the frontend.
    The association between document and institution is maintained
    by the frontend and the M2M field `proposal.partner_institution_commitments`.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido.'})

    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Researcher':
        return JsonResponse({'success': False, 'error': 'Acceso denegado.'})

    file = request.FILES.get('commitment_document')
    institution_id = request.POST.get('institution_id')
    proposal_id = request.POST.get('proposal_id')

    if not all([file, institution_id, proposal_id]):
        return JsonResponse({
            'success': False,
            'error': 'Archivo, institución o propuesta no especificados.'
        })

    allowed_mime_types = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    if file.content_type not in allowed_mime_types:
        return JsonResponse({
            'success': False,
            'error': 'Solo se permiten archivos PDF o DOCX.'
        })

    if file.size > 10 * 1024 * 1024:
        return JsonResponse({
            'success': False,
            'error': 'El archivo no puede exceder 10 MB.'
        })

    try:
        institution = Institution.objects.get(id=institution_id)
        proposal = Proposal.objects.get(pk=proposal_id)

        # Validate institution is a partner of this proposal
        if not proposal.partner_institutions.filter(id=institution_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Institución no asignada a esta propuesta.'
            })
        # Create the document - linked ONLY to the proposal
        doc = ProposalDocument.objects.create(
            proposal=proposal,
            file=file,
            document_type='commitment',
            linked_institution=institution,
            uploaded_by=request.user.customuser
        )

        # Link this document to the proposal's commitment list
        # This is the ONLY way we associate it with the proposal's institutions
        proposal.partner_institution_commitments.add(doc)

        return JsonResponse({
            'success': True,
            'id': doc.id,
            'name': doc.name,
            'url': doc.file.url,
            'uploaded_at': doc.created_at.isoformat(),
        })

    except Institution.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Institución no encontrada.'
        })
    except Proposal.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Propuesta no encontrada.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor. Por favor, inténtelo de nuevo.'
        })


# @login_required
# def upload_commitment_document(request):
#     if request.method != 'POST':
#         return JsonResponse({'success': False, 'error': 'Método no permitido.'})

#     # Permission check
#     if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Researcher':
#         return JsonResponse({'success': False, 'error': 'Acceso denegado.'})

#     # Extract data
#     file = request.FILES.get('commitment_document')
#     institution_id = request.POST.get('institution_id')
#     proposal_id = request.POST.get('proposal_id')

#     if not file or not institution_id or not proposal_id:
#         return JsonResponse({
#             'success': False,
#             'error': 'Archivo, institución o propuesta no especificados.'
#         })

#     # Validate file type
#     allowed_mime_types = [
#         'application/pdf',
#         'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
#     ]
#     if file.content_type not in allowed_mime_types:
#         return JsonResponse({
#             'success': False,
#             'error': 'Solo se permiten archivos PDF o DOCX.'
#         })

#     # Validate file size (10 MB)
#     if file.size > 10 * 1024 * 1024:
#         return JsonResponse({
#             'success': False,
#             'error': 'El archivo no puede exceder 10 MB.'
#         })

#     try:
#         institution = Institution.objects.get(id=institution_id)
#         proposal = Proposal.objects.get(pk=proposal_id)

#         # Validate institution is linked to proposal
#         if not proposal.partner_institutions.filter(id=institution_id).exists():
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Institución no asignada a esta propuesta.'
#             })

#         # Create document
#         doc = ProposalDocument.objects.create(
#             proposal=proposal,
#             file=file,
#             document_type='commitment',
#             uploaded_by=request.user.customuser
#         )

#         proposal.partner_institution_commitments.add(doc)

#         # Return success with clean data
#         return JsonResponse({
#             'success': True,
#             'id': doc.id,
#             'name': doc.name,
#             'url': doc.file.url,
#             'uploaded_at': doc.created_at.isoformat(),  # Optional: for UI feedback
#         })

#     except Institution.DoesNotExist:
#         return JsonResponse({
#             'success': False,
#             'error': 'Institución no encontrada.'
#         })
#     except Proposal.DoesNotExist:
#         return JsonResponse({
#             'success': False,
#             'error': 'Propuesta no encontrada.'
#         })
#     except Exception as e:
#         # Log the error in production (use logging)
#         return JsonResponse({
#             'success': False,
#             'error': 'Error interno del servidor. Por favor, inténtelo de nuevo.'
#         })
    
    # try:
    #     file = request.FILES.get('commitment_document')
    #     institution_id = request.POST.get('institution_id')
    #     if not file or not institution_id:
    #         return JsonResponse({'success': False, 'error': 'Archivo o institución no especificados.'})

    #     institution = Institution.objects.get(id=institution_id)
    #     proposal = Proposal.objects.get(pk=request.POST.get('proposal_id'))  # ← Pass this from form!

    #     # Validate institution is in proposal
    #     if not proposal.partner_institutions.filter(id=institution_id).exists():
    #         return JsonResponse({'success': False, 'error': 'Institución no asignada a esta propuesta.'})

    #     doc = ProposalDocument.objects.create(
    #         proposal=proposal,
    #         file=file,
    #         document_type='commitment',
    #         uploaded_by=request.user.customuser
    #     )

    #     return JsonResponse({
    #         'success': True,
    #         'id': doc.id,
    #         'name': doc.name,
    #         'url': doc.file.url,
    #     })
    # except Institution.DoesNotExist:
    #     return JsonResponse({'success': False, 'error': 'Institución no encontrada.'})
    # except Proposal.DoesNotExist:
    #     return JsonResponse({'success': False, 'error': 'Propuesta no encontrada.'})
    # except Exception as e:
    #     return JsonResponse({'success': False, 'error': str(e)})
    
@login_required
def download_proposal_document(request, doc_id):
    """
    Securely serve proposal documents only to authorized users.
    """
    try:
        doc = ProposalDocument.objects.select_related('proposal', 'uploaded_by').get(
            id=doc_id,
            proposal__user=request.user.customuser  # Only allow own user
        )
    except ProposalDocument.DoesNotExist:
        raise Http404("Documento no encontrado o acceso denegado.")

    # Guess file type (e.g., application/pdf, image/png)
    import mimetypes
    mime_type, _ = mimetypes.guess_type(doc.file.name)
    if not mime_type:
        mime_type = 'application/octet-stream'

    # Open the file
    file_handle = doc.file.open()

    # Decide between inline or attachment
    response = FileResponse(file_handle, content_type=mime_type)
    print(mime_type)
    if mime_type in ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']:
        # Browser can render these → show inline
        response['Content-Disposition'] = f'inline; filename="{doc.name}"'
    else:
        # Force download for other file types
        response['Content-Disposition'] = f'attachment; filename="{doc.name}"'

    return response

# @login_required
# def download_proposal_document(request, doc_id):
#     doc = get_object_or_404(ProposalDocument, id=doc_id)
#     # Optional: Check if user owns proposal or has permission
#     if not request.user.customuser == doc.uploaded_by and not request.user.is_staff:
#         raise PermissionDenied

#     response = FileResponse(doc.file.open('rb'), content_type='application/octet-stream')
#     response['Content-Disposition'] = f'attachment; filename="{doc.name}"'
#     return response