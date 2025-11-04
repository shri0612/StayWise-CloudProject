from django import forms
from .models import Booking
from .models import Profile 
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm

class BookingForm(forms.ModelForm):
    people = forms.IntegerField(min_value=1, label="Number of People")
    checkin_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Check-in Date"
    )
    checkout_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Check-out Date"
    )

    class Meta:
        model = Booking
        fields = ['name', 'email', 'days', 'people', 'checkin_date', 'checkout_date']
        
        
# ✅ Registration Form
class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data

    def save(self, commit=True):
        """Save user with hashed password."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
# class RegisterForm(forms.ModelForm):
#     password = forms.CharField(widget=forms.PasswordInput)
#     confirm_password = forms.CharField(widget=forms.PasswordInput)

#     class Meta:
#         model = User
#         fields = ['username', 'email', 'password']

#     def clean(self):
#         cleaned_data = super().clean()
#         password = cleaned_data.get('password')
#         confirm_password = cleaned_data.get('confirm_password')

#         if password != confirm_password:
#             raise forms.ValidationError("Passwords do not match!")
#         return cleaned_data


# ✅ Login Form
class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))