from django import forms
from .models import ExpressionDocument

class ExpressionDocumentForm(forms.ModelForm):
    class Meta:
        model = ExpressionDocument
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf, .doc, .docx',
                'multiple': False, # Single file per upload
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1028 * 1024: # 10 MB
                raise forms.ValidationError("El archivo no puede superar los 10 MB.")
            # Validate file type
            allowed_types = [
                'application/pdf',
                'applicaiton/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]

            if file.content_type not in allowed_types:
                raise forms.ValidationError("Tipo de archivo no permitido. Solo PDF, DOC, DOCX.")
        return file
            