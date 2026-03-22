from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Teacher, ScientificWork, WorkType, Deadline


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, label='Ism')
    last_name = forms.CharField(max_length=100, label='Familiya')
    email = forms.EmailField(label='Email', required=False)
    phone = forms.CharField(max_length=20, label='Telefon', required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        self.fields['username'].label = 'Login'
        self.fields['username'].help_text = ''
        self.fields['password1'].label = 'Parol'
        self.fields['password1'].help_text = 'Kamida 4 ta belgi'
        self.fields['password2'].label = 'Parolni tasdiqlang'
        self.fields['password2'].help_text = ''

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Parollar mos kelmadi!")
        return password2


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['kafedra', 'position', 'experience_years', 'degree', 'bio']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ScientificWorkForm(forms.ModelForm):
    class Meta:
        model = ScientificWork
        fields = ['work_type', 'title', 'description', 'date', 'file']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext != '.pdf':
                raise forms.ValidationError("Faqat PDF formatdagi fayllar qabul qilinadi!")
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Fayl hajmi 10 MB dan oshmasligi kerak!")
        return file


class PasswordChangeCustomForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Eski parol')
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Yangi parol')
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Yangi parolni tasdiqlang')


class WorkTypeForm(forms.ModelForm):
    class Meta:
        model = WorkType
        fields = ['name', 'score']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class DeadlineForm(forms.ModelForm):
    class Meta:
        model = Deadline
        fields = ['title', 'description', 'due_date', 'is_active']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            field.widget.attrs['class'] = 'form-control'


class RejectForm(forms.Form):
    reject_reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Rad etish sababini kiriting...'}),
        label='Rad etish sababi'
    )
