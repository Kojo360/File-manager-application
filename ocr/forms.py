from django import forms

class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'multiple': True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result

class FileUploadForm(forms.Form):
    files = MultipleFileField(
        label='Select files (up to 100)',
        required=True,
        widget=MultipleFileInput(attrs={
            'accept': '.pdf,.png,.jpg,.jpeg',
            'multiple': True,
            'class': 'form-control'
        })
    )
