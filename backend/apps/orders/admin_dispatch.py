"""Forms for controlled, auditable merchant fulfillment actions."""

from django import forms


class DispatchOrderForm(forms.Form):
    carrier = forms.CharField(
        label="شرکت حمل / ارسال",
        max_length=80,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    tracking_code = forms.CharField(
        label="کد رهگیری مرسوله",
        max_length=120,
        widget=forms.TextInput(attrs={"autocomplete": "off", "dir": "ltr"}),
    )

    def clean_tracking_code(self):
        value = self.cleaned_data["tracking_code"].strip()
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise forms.ValidationError("کد رهگیری نباید شامل کاراکتر کنترلی باشد.")
        return value
