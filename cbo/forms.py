from django import forms
from .models import CBODocument

class CBODocumentForm(forms.ModelForm):
    class Meta:
        model = CBODocument
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'accept': '.pdf,.docx,.jpg,.png'})
        }