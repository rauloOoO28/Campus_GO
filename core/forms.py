from django import forms
from django.contrib.auth.models import User

from .models import Perfil


class RegistroForm(forms.ModelForm):
    nombre_completo = forms.CharField(label="Nombre completo", max_length=200)
    rol = forms.ChoiceField(label="Rol", choices=Perfil.ROL_CHOICES)
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar contraseña")

    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe un usuario con ese correo.")
        return email

    def clean(self):
        cleaned = super().clean()
        p = cleaned.get("password")
        p2 = cleaned.get("password2")
        if p and p2 and p != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            Perfil.objects.create(
                user=user,
                nombre_completo=self.cleaned_data["nombre_completo"],
                rol=self.cleaned_data["rol"],
            )
        return user


class PerfilUpdateForm(forms.Form):
    nombre_completo = forms.CharField(label="Nombre completo", max_length=200)
    email = forms.EmailField(label="Correo institucional")
    rol = forms.ChoiceField(label="Rol", choices=Perfil.ROL_CHOICES)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_authenticated:
            self.fields['email'].initial = self.user.email or self.user.username
            try:
                perfil = self.user.perfil
            except Perfil.DoesNotExist:
                perfil = None
            if perfil:
                self.fields['nombre_completo'].initial = perfil.nombre_completo
                self.fields['rol'].initial = perfil.rol

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not self.user:
            return email
        duplicate = User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists()
        duplicate_username = User.objects.filter(username__iexact=email).exclude(pk=self.user.pk).exists()
        if duplicate or duplicate_username:
            raise forms.ValidationError("Ya existe otro usuario con ese correo.")
        return email

    def save(self):
        if not self.user:
            raise ValueError('Se requiere un usuario autenticado para guardar el perfil.')

        email = self.cleaned_data['email'].strip().lower()
        nombre_completo = self.cleaned_data['nombre_completo'].strip()
        rol = self.cleaned_data['rol']

        self.user.email = email
        self.user.username = email
        self.user.save(update_fields=['email', 'username'])

        perfil, _ = Perfil.objects.get_or_create(
            user=self.user,
            defaults={
                'nombre_completo': nombre_completo,
                'rol': rol,
            }
        )
        perfil.nombre_completo = nombre_completo
        perfil.rol = rol
        perfil.save(update_fields=['nombre_completo', 'rol'])

        return self.user
