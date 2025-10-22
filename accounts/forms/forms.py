# accounts/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from ..models import CustomUser
from geo.models import DocumentType, Country
from people.models import Person

from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from captcha.fields import CaptchaField

from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

class ResearcherRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    #last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(
        max_length=17,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]{9,17}$',
                message="Enter a valid phone number (e.g., +57(601)1234444, +1 555-123-4567)"
            )
        ],
        label="Phone Number (Optional)",
        help_text="Optional. Format: +57(601)1234444 or +1 555-123-4567"
    )

    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        empty_label="Select country",
        label="País",
        widget=forms.Select(attrs={'id': 'id_country'})
    )

    document_type = forms.ChoiceField(
        choices=[], # poblado en __init__
        label = "Tipo de Documento",
        widget=forms.Select(attrs={'id': 'id_document_type'})
    )

    document_number = forms.CharField(max_length=50, label="Numero de Documento")
    second_name = forms.CharField(max_length=32, required=False, label="Segundo nomobre (Opcional)")
    first_last_name = forms.CharField(max_length=32, required=False, label="Second Name (Optional)")
    second_last_name = forms.CharField(max_length=32, required=False, label="Second Last Name (Optional)")
    gender = forms.ChoiceField(
        choices=[
            ('F', 'Femenino'),
            ('M', 'Masculino'),
            ('O', 'Otro'),
            ('N', 'Prefiero no decir'),
        ],
        label="Gender"
    )

    captcha = CaptchaField()

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get Colombia (handle case where it might not exist)
        try:
            colombia = Country.objects.get(name="Colombia")  # or use ISO code if more reliable
            self.fields['country'].initial = colombia.id
            default_country_id = colombia.id
        except Country.DoesNotExist:
            default_country_id = None
            self.fields['country'].initial = None

        # Populate document_type based on country (POST or default)
        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                doc_types = DocumentType.objects.filter(country_id=country_id)
            except (ValueError, TypeError):
                doc_types = DocumentType.objects.none()
        else:
            # Use default country (Colombia) if available
            if default_country_id:
                doc_types = DocumentType.objects.filter(country_id=default_country_id)
            else:
                doc_types = DocumentType.objects.none()

        # Set choices for document_type
        if doc_types.exists():
            self.fields['document_type'].choices = [(dt.id, dt.name) for dt in doc_types]
        else:
            self.fields['document_type'].choices = [('', 'Select country first')]

        # Apply CSS classes
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control u-full-width'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
    
    def save(self, commit=True):
        print("\n=== DEBUG: Entering save() ===")
        # Crear el usuario
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['first_last_name']
        user.is_active = False  # Require email confirmation
        if commit:
            user.save()
            print(f"DEBUG: User saved: {user.username}")

        # Crear el usuario final
        from ..models import CustomUser, Role
        researcher_role, _ = Role.objects.get_or_create(
            name='Researcher',
            defaults={'description': 'Research proposal submitter'}
        )

        custom_user = CustomUser(
            user=user,
            #person=person,
            person=None,
            email=self.cleaned_data['email'],
            phone_number=self.cleaned_data.get('phone_number', ''),
            role=researcher_role
        )
        if commit:
            custom_user.save()

        # Crear la persona
        from people.models import Person
        person = Person(
            document_type_id=self.cleaned_data['document_type'],
            document_number=self.cleaned_data['document_number'],
            first_name=self.cleaned_data['first_name'],
            second_name=self.cleaned_data.get('second_name', ''),
            first_last_name=self.cleaned_data['first_last_name'],
            second_last_name=self.cleaned_data.get('second_last_name', ''),
            gender=self.cleaned_data['gender'],
            created_by=user  # CreatedByMixin expects User
        )
        if commit:
            person.save()
            print(f"DEBUG: Person saved: {person.id}")

        custom_user.person = person
        if commit:
            custom_user.save()  # Save again to update the person FK
            print("DEBUG: CustomUser updated with person link")
        
        if commit:
            self._send_confirmation_email(user)
    
        return user
    
    def _send_confirmation_email(self, user):
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        confirm_url = reverse('accounts:confirm_email', kwargs={'uidb64': uid, 'token': token})
        full_url = f"{settings.FRONTEND_URL or 'http://localhost:8220'}{confirm_url}"

        subject = "Confirma tu registro en [Nombre de la Plataforma]"
        message = f"""
        ¡Hola {user.first_name}!

        Gracias por registrarte. Por favor confirma tu correo haciendo clic en el siguiente enlace:

        {full_url}

        Si no solicitaste esta cuenta, ignora este mensaje.

        Saludos,
        El equipo de [Plataforma]
        """
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )




class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = CustomUser
        fields = ['email', 'phone_number', 'birthdate']
        widgets = {
            'birthdate': forms.DateInput(attrs={'type': 'date'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email is already taken by another user
        if User.objects.filter(email=email).exclude(id=self.instance.user.id).exists():
            raise forms.ValidationError("This email is already in use.")
        return email
    
class LoginForm(AuthenticationForm):
    captcha = CaptchaField(
        error_messages={'invalid': 'Código de verificación incorrecto. Inténtalo de nuevo.'}
    )