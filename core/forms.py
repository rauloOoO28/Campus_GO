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
