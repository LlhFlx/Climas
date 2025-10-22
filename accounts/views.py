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
from django.http import JsonResponse
from geo.models import DocumentType, Country
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode


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

def get_document_types_by_country(request, country_id):
    doc_types = DocumentType.objects.filter(country_id=country_id).values('id', 'name')
    return JsonResponse(list(doc_types), safe=False)

def confirm_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, "¡Tu correo ha sido confirmado! Bienvenido.")
        return redirect('home')
    else:
        messages.error(request, "El enlace de confirmación es inválido o ha expirado.")
        return redirect('accounts:login')