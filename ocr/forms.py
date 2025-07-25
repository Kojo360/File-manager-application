from django import forms

class FileUploadForm(forms.Form):
    file = forms.FileField(
        label='Select a file',
        widget=forms.ClearableFileInput(attrs={'accept':'.pdf,image/*'})
    )
