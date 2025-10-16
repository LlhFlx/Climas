from django import forms
from .models import Call
from common.models import Status
from proponent_forms.models import SharedQuestion, SharedQuestionCategory

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
        fields = [
            'category',
            'question',
            'field_type',
            'source_model',
            'target_category',
            'is_active',
            'is_required',
        ]
        widgets = {
            'question': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active categories
        self.fields['category'].queryset = SharedQuestionCategory.objects.filter(is_active=True).order_by('order', 'name')
        # Make category optional in UI (though it is nullable in DB)
        self.fields['category'].required = False

    def clean(self):
        cleaned_data = super().clean()
        field_type = cleaned_data.get('field_type')
        source_model = cleaned_data.get('source_model')

        if field_type == 'dynamic_dropdown':
            if not source_model:
                raise forms.ValidationError('For dynamic dropdown, you must select a source model.')
            # Clear legacy JSON field (not used)
            cleaned_data['options'] = None
        else:
            # For all other types (including radio/dropdown), we use SharedQuestionOption
            # So we don't validate the legacy 'options' field at all
            cleaned_data['source_model'] = None
            cleaned_data['options'] = None

        return cleaned_data