from django import forms
from .models import Call
from common.models import Status
from proponent_forms.models import SharedQuestion

class CallForm(forms.ModelForm):
    class Meta:
        model = Call
        fields = [
            'title', 'description', 'opening_datetime', 'closing_datetime'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'opening_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'closing_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        opening = cleaned_data.get('opening_datetime')
        closing = cleaned_data.get('closing_datetime')
        if opening and closing and opening >= closing:
            raise forms.ValidationError('La fecha de apertura debe ser anterior a la fecha de cierre.')
        return cleaned_data
    
class SharedQuestionForm(forms.ModelForm):
    class Meta:
        model = SharedQuestion
        fields = ['question', 'field_type', 'options', 'source_model', 'target_category', 'is_active', 'is_required']
        widgets = {
            'options': forms.Textarea(attrs={
                'placeholder': 'JSON format, e.g., ["Option 1", "Option 2"]',
                'rows': 3
            }),
            'question': forms.Textarea(attrs={'rows': 2}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        field_type = cleaned_data.get('field_type')
        options = cleaned_data.get('options')
        source_model = cleaned_data.get('source_model')

        if field_type == 'dropdown':
            if not options:
                raise forms.ValidationError('For static dropdown, you must provide options in JSON format.')
            # Clear source_model for static dropdown
            cleaned_data['source_model'] = ''

        elif field_type == 'dynamic_dropdown':
            if not source_model:
                raise forms.ValidationError('For dynamic dropdown, you must select a source model.')
            # Clear options for dynamic dropdown
            cleaned_data['options'] = None

        elif field_type == 'radio':
            if not options:
                raise forms.ValidationError('For radio buttons, you must provide options in JSON format.')
            # Clear source_model for radio
            cleaned_data['source_model'] = ''

        else:
            # Clear both for other types
            cleaned_data['options'] = None
            cleaned_data['source_model'] = ''

        return cleaned_data