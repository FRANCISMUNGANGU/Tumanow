# forms.py
from django import forms
from .models import Customer
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
    name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(max_length=15, required=False)
    profile_pic = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['name']
        if commit:
            user.save()
            # Now create the Customer instance
            Customer.objects.create(
                customer=user,
                name=self.cleaned_data['name'],
                username=user.username,
                email=self.cleaned_data['email'],
                phone_number=self.cleaned_data['phone_number'],
                profile_pic=self.cleaned_data.get('profile_pic')
            )
        return user
