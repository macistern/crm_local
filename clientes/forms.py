from django import forms

from .models import Cliente, Etiqueta, MensajeWhatsApp, PlantillaWhatsApp
from .validators import normalize_phone


class ClienteForm(forms.ModelForm):
    telefono_whatsapp = forms.CharField(
        label="teléfono WhatsApp",
        max_length=32,
        help_text="Formato internacional, sólo dígitos. Ejemplo: 5491123456789",
    )

    class Meta:
        model = Cliente
        fields = [
            "nombre_completo",
            "telefono_whatsapp",
            "email",
            "empresa",
            "etiquetas",
            "estado",
            "notas",
        ]
        widgets = {
            "etiquetas": forms.CheckboxSelectMultiple,
            "notas": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if nombre == "etiquetas":
                campo.widget.attrs["class"] = (
                    "h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                )
            else:
                campo.widget.attrs["class"] = (
                    "field-control mt-1 w-full"
                )

    def clean_telefono_whatsapp(self):
        return normalize_phone(self.cleaned_data["telefono_whatsapp"])


class MensajeWhatsAppForm(forms.ModelForm):
    plantilla = forms.ModelChoiceField(
        queryset=PlantillaWhatsApp.objects.none(),
        required=False,
        widget=forms.HiddenInput,
    )

    class Meta:
        model = MensajeWhatsApp
        fields = ["plantilla", "texto"]
        widgets = {
            "texto": forms.Textarea(
                attrs={
                    "rows": 5,
                    "maxlength": 4000,
                    "placeholder": "Escribí el mensaje para el cliente...",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plantilla"].queryset = PlantillaWhatsApp.objects.filter(activa=True)

    def clean_texto(self):
        texto = self.cleaned_data["texto"].strip()
        if not texto:
            raise forms.ValidationError("El mensaje no puede estar vacío.")
        return texto


class PlantillaWhatsAppForm(forms.ModelForm):
    class Meta:
        model = PlantillaWhatsApp
        fields = ["nombre", "texto", "activa"]
        widgets = {
            "texto": forms.Textarea(attrs={"rows": 5, "maxlength": 4000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "field-control mt-1 w-full"
