from django.apps import apps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse, FileResponse
from django.core.serializers import serialize
from .models import Call
from .forms import CallForm, SharedQuestionForm
from proponent_forms.models import SharedQuestion
from common.models import Status
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

from products.models import Product
from django.forms import modelformset_factory
from django import forms

import json
from django.core.serializers.json import DjangoJSONEncoder

from project_team.models import ProjectTeamMember, InvestigatorCondition, InvestigatorThematicAxisAntecedent
from intersectionality.models import IntersectionalityScope
from budgets.models import BudgetCategory, BudgetItem, BudgetPeriod

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

    return render(request, 'calls/coordinator_dashboard.html', {
        'calls': calls,
        'shared_questions': shared_questions,
        'institutions': institutions,
        'institution_types': institution_types,
        'countries': countries,
        'document_types': document_types,
        'thematic_axes': thematic_axes,
        'strategic_effects': strategic_effects,
        'budget_categories': budget_categories,
        'budget_periods': budget_periods,
        'people': people,
    })

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
                # Redirect back to the calling page (you'll pass this via URL)
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
        call = get_object_or_404(Call, pk=call_pk, status__name='Abierta')
    except:
        messages.error(request, "This call is not currently open for applications.")
        return redirect('calls:researcher_dashboard')
    
    # Ensure the user is a researcher
    if not hasattr(request.user, 'customuser') or request.user.customuser.role.name != 'Researcher':
        messages.error(request, "Only researchers can apply to calls.")
        return redirect('home')
    
    # Get or create Expression for this user + call
    expression, created = Expression.objects.get_or_create(
        user=request.user.customuser,
        call=call,
        defaults={
            'thematic_axis': ThematicAxis.objects.first(),  # Default user will change
            'status': Status.objects.get(name='Abierta'),
            'project_title': f'Borrador: {call.title}',
            'implementation_country': Country.objects.first(),  # Default
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

    # Get Strategic Effects and other data for the form
    strategic_effects = StrategicEffect.objects.filter(is_active=True).order_by('name')
    thematic_axes = ThematicAxis.objects.filter(is_active=True)
    countries = Country.objects.all()

    # Get Budget Categories and Periods
    budget_categories = BudgetCategory.objects.filter(is_active=True).order_by('name')
    budget_periods = BudgetPeriod.objects.all().order_by('order', 'name')
    # Fetch existing budget items for editing
    existing_budget_items = BudgetItem.objects.filter(expression=expression).select_related('category', 'period')

    # --- Document handling ---
    documents = ExpressionDocument.objects.filter(expression=expression)
    document_form = ExpressionDocumentForm()

    if request.method == 'POST':
        #print("=== DEBUG: POST request received ===")
        #print("Form data keys:", list(request.POST.keys()))
        # Capture POST data for form re-population AND processing
        post_data = {
            'project_title': request.POST.get('project_title', '').strip(),
            'thematic_axis': request.POST.get('thematic_axis'),
            'implementation_country': request.POST.get('implementation_country'),
            'problem': request.POST.get('problem', '').strip(),
            'general_objective': request.POST.get('general_objective', '').strip(),
            'methodology': request.POST.get('methodology', '').strip(),
            'funding_eligibility_acceptance': request.POST.get('funding_eligibility_acceptance') == 'on',  # ← Now explicit
        }

        # Save core Expression fields from the POST data
        expression.project_title = request.POST.get('project_title', '').strip()
        expression.thematic_axis_id = request.POST.get('thematic_axis')
        expression.implementation_country_id = request.POST.get('implementation_country')
        expression.problem = request.POST.get('problem', '').strip()
        expression.general_objective = request.POST.get('general_objective', '').strip()
        expression.methodology = request.POST.get('methodology', '').strip()
        expression.funding_eligibility_acceptance = request.POST.get('funding_eligibility_acceptance') == 'on'
        primary_institution_id = request.POST.get('primary_institution_id')
        if primary_institution_id and primary_institution_id.isdigit():
            expression.primary_institution_id = int(primary_institution_id)
        else:
            expression.primary_institution = None  # clear if empty or invalid

        # Validate core fields
        if not all([
            expression.project_title,
            expression.thematic_axis_id,
            expression.implementation_country_id,
            expression.problem,
            expression.general_objective,
            expression.methodology,
            expression.primary_institution_id
        ]):
            messages.error(request, "Please fill in all required fields marked with *.")
        else:
            # Save the Expression
            expression.save()

        # Only proceed if core fields are valid
        if not messages.get_messages(request):
            # Process dynamic question responses
            for fq in form_questions:
                field_name = f"question_{fq.shared_question.id}"
                value = request.POST.get(field_name)
                
                if fq.shared_question.is_required and not value:
                    messages.error(request, f'Question "{fq.shared_question.question}" is required.')
                    break # Break to re-render form with error

                # Handle boolean fields
                if fq.shared_question.field_type == 'boolean':
                    value = True if value == 'true' else False if value == 'false' else None

                # Save or update the response
                ProponentResponse.objects.update_or_create(
                    expression=expression,
                    shared_question=fq.shared_question,
                    defaults={'value': value}
                )

            # Only proceed if no errors from dynamic questions
            if not messages.get_messages(request):
                # Handle Products
                Product.objects.filter(expression=expression).delete()
                product_indices = set()
                for key in request.POST.keys():
                    if key.startswith('product_title_'):
                        index = key.split('_')[-1]
                        product_indices.add(index)

                for index in product_indices:
                    title = request.POST.get(f'product_title_{index}', '').strip()
                    description = request.POST.get(f'product_description_{index}', '').strip()
                    outcome = request.POST.get(f'product_outcome_{index}', '').strip()
                    start_date = request.POST.get(f'product_start_date_{index}')
                    end_date = request.POST.get(f'product_end_date_{index}')
                    effect_ids = request.POST.getlist(f'product_strategic_effects_{index}')

                    if title:
                        try:
                            product = Product.objects.create(
                                expression=expression,
                                title=title,
                                description=description,
                                outcome=outcome,
                                start_date=start_date,
                                end_date=end_date,
                                status=Status.objects.get(name='Abierta'),
                                created_by=request.user
                            )
                            if effect_ids:
                                effects = StrategicEffect.objects.filter(id__in=effect_ids)
                                product.strategic_effects.set(effects)
                        except Exception as e:
                            messages.error(request, f"Error saving product '{title}': {str(e)}")

                # Handle Project Team Members
                # Delete existing team members to avoid duplicates
                ProjectTeamMember.objects.filter(expression=expression).delete()

                # --- Handle Budget Items ---
                BudgetItem.objects.filter(expression=expression).delete()
                budget_item_indices = set()
                for key in request.POST.keys():
                    if key.startswith('budget_item_category_'):
                        index = key.split('_')[-1]
                        budget_item_indices.add(index)

                for index in budget_item_indices:
                    category_id = request.POST.get(f'budget_item_category_{index}')
                    period_id = request.POST.get(f'budget_item_period_{index}')
                    amount_str = request.POST.get(f'budget_item_amount_{index}', '').strip()
                    notes = request.POST.get(f'budget_item_notes_{index}', '').strip()

                    # Skip if no category or period selected
                    if not category_id or not period_id:
                        continue

                    # Validate amount is a valid decimal
                    try:
                        amount = float(amount_str) if amount_str else 0.0
                        if amount < 0:
                            raise ValueError("Amount cannot be negative")
                    except (ValueError, TypeError):
                        messages.error(request, f"Invalid amount for Budget Item {int(index)+1}. Please enter a valid number.")
                        continue

                    try:
                        category = BudgetCategory.objects.get(id=category_id)
                        period = BudgetPeriod.objects.get(id=period_id)
                        BudgetItem.objects.create(
                            expression=expression,
                            category=category,
                            period=period,
                            amount=amount,
                            notes=notes
                        )
                    except (BudgetCategory.DoesNotExist, BudgetPeriod.DoesNotExist):
                        messages.error(request, f"Invalid category or period selected for Budget Item {int(index)+1}.")


                # Get all team member indices
                team_member_indices = set()
                for key in request.POST.keys():
                    if key.startswith('team_member_person_'):
                        index = key.split('_')[-1]
                        team_member_indices.add(index)

                # Create new team members
                for index in team_member_indices:
                    person_id = request.POST.get(f'team_member_person_{index}')
                    role = request.POST.get(f'team_member_role_{index}', '').strip()

                    print(f"=== DEBUG: Processing team member {index} ===")
                    print(f"Person ID: {person_id}, Role: {role}")

                    status_id = request.POST.get(f'team_member_status_{index}')
                    start_date = request.POST.get(f'team_member_start_date_{index}')
                    end_date = request.POST.get(f'team_member_end_date_{index}')

                    institution_id = request.POST.get(f'team_member_institution_id_{index}')

                    # Only create if person and role are provided
                    #if person_id and role:
                    if person_id and person_id.strip() != "" and role:
                        try:
                            # Create the team member
                            team_member = ProjectTeamMember.objects.create(
                                expression=expression,
                                person_id=person_id,
                                role=role,
                                status_id=status_id,
                                start_date=start_date,
                                end_date=end_date,
                                institution_id=institution_id
                            )

                            # Handle Conditions for this team member
                            # condition_texts = request.POST.getlist(f'team_member_condition_text_{index}')
                            # for condition_text in condition_texts:
                            #     if condition_text.strip():
                            #         InvestigatorCondition.objects.create(
                            #             team_member=team_member,
                            #             condition_text=condition_text.strip(),
                            #             is_fulfilled=False # Default to not fulfilled
                            #         )

                            # Handle Thematic Antecedents for this team member
                            antecedent_axis_ids = request.POST.getlist(f'team_member_antecedent_axis_{index}')
                            antecedent_descriptions = request.POST.getlist(f'team_member_antecedent_description_{index}')
                            antecedent_urls = request.POST.getlist(f'team_member_antecedent_url_{index}')

                            # Pair up axis, description, and URL
                            for i, axis_id in enumerate(antecedent_axis_ids):
                                description = antecedent_descriptions[i] if i < len(antecedent_descriptions) else ''
                                url = antecedent_urls[i] if i < len(antecedent_urls) else ''
                                if axis_id and description.strip():
                                    InvestigatorThematicAxisAntecedent.objects.create(
                                        team_member=team_member,
                                        thematic_axis_id=axis_id,
                                        description=description.strip(),
                                        evidence_url=url.strip() if url else ''
                                    )

                        except Exception as e:
                            messages.error(request, f"Error saving team member: {str(e)}")
                            print(f"Error saving team member: {str(e)}")
                # print(request.FILES)
                # print(type(request.FILES))
                # print("???", 'document_upload' in request.FILES)
                # print(request.FILES.keys())
                if 'file' in request.FILES:
                    print('Trying upload')
                    document_form = ExpressionDocumentForm(request.POST, request.FILES)
                    if document_form.is_valid():
                        doc = document_form.save(commit=False)
                        doc.expression = expression
                        doc.uploaded_by = request.user.customuser
                        doc.save()
                        messages.success(request, "File uploaded successfully!")
                    else:
                        for field, errors in document_form.errors.items():
                            for error in errors:
                                messages.error(request, f"Upload error: {error}")
                elif 'remove_document' in request.POST:
                    doc_id = request.POST.get('remove_document')
                    ExpressionDocument.objects.filter(id=doc_id, expression=expression).delete()
                    messages.info(request, "File removed.")

                # If we got here without any `messages.error`, everything was saved successfully.
                if 'submit_application' in request.POST:
                    submitted_status, _ = Status.objects.get_or_create(name='Enviada')
                    expression.status = submitted_status
                    expression.submission_datetime = timezone.now()
                    expression.save()
                    #messages.success(request, 'Your application has been submitted successfully!')
                    #return redirect('calls:researcher_dashboard')
                    messages.success(request, 'Your application has been submitted successfully!')
                else:
                    messages.success(request, 'Your application has been saved as a draft.')

    # --- CONTEXT SETUP: Re-fetch expression from DB to ensure fresh state ---
    expression = Expression.objects.select_related(
        'thematic_axis',
        'implementation_country',
        'user',
        'call'
    ).prefetch_related(
        'documents',
        'intersectionality_scopes'
    ).get(pk=expression.pk)


    # --- Get all active institutions for dropdown ---
    institutions = Institution.objects.filter(is_active=True).order_by('name')
    institutions = list(Institution.objects.filter(is_active=True).order_by('name').values('id', 'name')),
    # --- For institution modal ---
    institution_types = InstitutionType.objects.filter(is_active=True).order_by('name')


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
        # Add data for Project Team Members
        'existing_team_members': ProjectTeamMember.objects.filter(expression=expression).prefetch_related(
            #'conditions', 
            'thematic_antecedents'
        ),
        'statuses': Status.objects.all().order_by('name'), # For team member status dropdown
        'institutions': institutions, # For team member institution dropdown
        
        # --- For institution input ---
        # Seralizable object for the template filter
        'institutions': list(Institution.objects.filter(is_active=True).order_by('name').values('id', 'name')),
        # 'institutions': list(
        #     Institution.objects.filter(is_active=True)
        #         .select_related('institution_type')
        #         .order_by('name')
        #         .values('id', 'name', 'institution_type__name')
        # )
        'institution_types': institution_types,
        'countries': countries,  # Redundant? No — needed in partial
        'people': Person.objects.filter(created_by__isnull=False).order_by('first_name', 'first_last_name'),
        # --- BUDGET ---
        'budget_categories': budget_categories,
        'budget_periods': budget_periods,
        'existing_budget_items': existing_budget_items,

        # --- Document Context ---
        'documents': expression.documents.all(),  # All uploaded docs
        'document_form': ExpressionDocumentForm(),

        # --- Intersectionality Context ---
        'intersectionality_scopes': IntersectionalityScope.objects.filter(is_active=True).order_by('name'),

        # Pass post_data to template for re-populating fields on validation error ---
        #'post_data': post_data if messages.get_messages(request) else None,
        
    }

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
    return render(request, 'calls/partials/institution_input.html', context)