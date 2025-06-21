from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.jobs.models import OrderDelivery, Order


class OrderDeliveryForm(forms.ModelForm):
    """Form for delivering work or submitting revisions."""
    class Meta:
        model = OrderDelivery
        fields = ["file", "message"]
        widgets = {
            "message": forms.Textarea(attrs={
                "rows": 4,
                "class": "form-control",
                "placeholder": "Add a message (optional)",
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        if self.order is None:
            raise ValueError("OrderDeliveryForm requires an 'order' parameter")
            
        super().__init__(*args, **kwargs)
        
        # Set up file field with proper attributes
        self.fields['file'] = forms.FileField(
            label="Upload your work",
            required=not self.order.deliveries.exists(),  # Only required for first delivery
            widget=forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.zip,.rar',
            }),
            help_text="Upload your completed work files (PDF, DOC, DOCX, ZIP, RAR)"
        )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file and not self.order.deliveries.exists():
            raise ValidationError("A file is required for the first delivery")
        return file
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.order = self.order
        if commit:
            instance.save()
        return instance


class OrderReviewForm(forms.ModelForm):
    """Form for submitting order reviews."""
    class Meta:
        from apps.orders.models import OrderReview
        model = OrderReview
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={
                "min": 1, 
                "max": 5, 
                "class": "form-control",
                "required": True
            }),
            "comment": forms.Textarea(attrs={
                "rows": 3, 
                "class": "form-control", 
                "placeholder": "Leave a comment (optional)",
                "required": False
            }),
        }
    
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is not None and (rating < 1 or rating > 5):
            raise ValidationError("Rating must be between 1 and 5")
        return rating


class OrderRevisionForm(forms.Form):
    """Form for requesting revisions on delivered work."""
    message = forms.CharField(
        label=_("Revision Request"),
        widget=forms.Textarea(attrs={
            "rows": 4,
            "class": "form-control",
            "placeholder": _("Please describe what changes or improvements are needed...")
        }),
        required=True,
        help_text=_("Be specific about what needs to be changed or improved.")
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        if self.order and self.order.status != Order.STATUS_DELIVERED:
            raise ValidationError(_("Can only request revision on delivered orders"))
        if self.order and self.order.revision_count >= self.order.max_revisions:
            raise ValidationError(_("Maximum number of revisions reached"))
        return cleaned_data


class OrderPaymentForm(forms.Form):
    """Form for handling order payments."""
    amount = forms.DecimalField(
        label=_("Amount"),
        max_digits=10,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.01",
            "min": "0.01"
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if self.order and self.order.amount:
            self.fields['amount'].initial = self.order.amount
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError(_("Amount must be greater than zero"))
        return amount
