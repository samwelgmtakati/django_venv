# apps/payments/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import PaymentMethod

class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = [
            'name', 'account_number', 'account_name', 'phone_number',
            'bank_name', 'branch_code', 'swift_code', 'iban',
            'is_primary', 'is_active'
        ]
        widgets = {
            'name': forms.RadioSelect(choices=PaymentMethod.PAYMENT_METHOD_CHOICES),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set field attributes for better UI
        self.fields['account_number'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Account number'
        })
        self.fields['account_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Account holder name'
        })
        self.fields['phone_number'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'e.g. 0712345678'
        })
        self.fields['bank_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Bank name (for bank transfers)'
        })
        self.fields['branch_code'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Branch code (if applicable)'
        })
        self.fields['swift_code'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'SWIFT/BIC code (if applicable)'
        })
        self.fields['iban'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'IBAN (if applicable)'
        })

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        account_number = cleaned_data.get('account_number')
        phone_number = cleaned_data.get('phone_number')

        # Validate phone number for mobile money
        if name in ['azampesa', 'mpesa', 'tigopesa', 'halopesa'] and not phone_number:
            self.add_error('phone_number', 'Phone number is required for mobile money payments')

        # Validate account number format for mobile money
        if name in ['azampesa', 'mpesa', 'tigopesa', 'halopesa'] and account_number:
            if not account_number.startswith('0') or not account_number[1:].isdigit() or len(account_number) != 10:
                self.add_error('account_number', 'Please enter a valid 10-digit phone number starting with 0')

        # Check for duplicate payment methods
        if self.instance.pk is None:  # Only for new instances
            if PaymentMethod.objects.filter(
                user=self.user,
                name=name,
                account_number=account_number
            ).exists():
                self.add_error('account_number', 'This payment method already exists')

        return cleaned_data

class WithdrawalRequestForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=10000,  # Minimum withdrawal amount: 10,000 TZS
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount in TZS'
        })
    )
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.none(),  # Will be set in the view
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any notes about this withdrawal (optional)'
        })
    )
    terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['payment_method'].queryset = user.payment_methods.filter(is_active=True)

class PaymentForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1000,  # Minimum payment amount: 1,000 TZS
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount in TZS'
        })
    )
    description = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'What is this payment for?'
        })
    )
    reference = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional reference or invoice number'
        })
    )
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.none(),  # Will be set in the view
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['payment_method'].queryset = user.payment_methods.filter(is_active=True)

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        # Add any additional validation for the amount if needed
        return amount