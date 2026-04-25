from django import forms
from .models import Application, Document

# Ограничения из технического задания
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 МБ
ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png']

class ApplicationForm(forms.ModelForm):
    """Форма подачи заявления на заселение."""
    class Meta:
        model = Application
        fields = ['ege_score', 'diploma_type', 'distance_km', 'has_priority_benefit', 'is_orphan', 'is_disabled']
        widgets = {
            'diploma_type': forms.Select(attrs={'class': 'form-select'}),
            'ege_score': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Сумма баллов'}),
            'distance_km': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Расстояние в км'}),
        }

class DocumentUploadForm(forms.ModelForm):
    """Форма загрузки скан-копий документов."""
    class Meta:
        model = Document
        fields = ['doc_type', 'file']
        widgets = {
            'doc_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_file(self):
        """Серверная валидация файла: размер и расширение."""
        file = self.cleaned_data.get('file')
        if file:
            if file.size > MAX_FILE_SIZE:
                raise forms.ValidationError('Размер файла не должен превышать 10 МБ.')
            
            ext = file.name.split('.')[-1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise forms.ValidationError(f'Допустимые форматы: {", ".join(ALLOWED_EXTENSIONS)}. Архивы (.zip, .7z) не принимаются.')
        return file