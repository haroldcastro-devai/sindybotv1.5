from django import forms
from .models import GuionPractiseguro

class GuionPractiseguroForm(forms.ModelForm):
    costo = forms.DecimalField(max_digits=5, decimal_places=0)  # Limitar a 5 dígitos sin decimales

    def clean_costo(self):
        costo = self.cleaned_data['costo']
        if len(str(costo)) > 5:
            raise forms.ValidationError("El costo no puede tener más de 5 dígitos.")
        return costo

    class Meta:
        model = GuionPractiseguro
        fields = '__all__'