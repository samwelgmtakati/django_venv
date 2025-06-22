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
    """Form for submitting order reviews.
    
    This form is used by both clients and freelancers to review each other.
    The fields shown will vary based on who is being reviewed.
    """
    RATING_CHOICES = [
        (5, 'Excellent'),
        (4, 'Very Good'),
        (3, 'Good'),
        (2, 'Fair'),
        (1, 'Poor'),
    ]
    
    # Common fields
    comment = forms.CharField(
        label=_("Your Review"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Share your experience working with this user...')
        }),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if not self.user or not self.order:
            raise ValueError("Both 'user' and 'order' must be provided")
            
        # Determine if we're reviewing a freelancer or client
        self.reviewing_freelancer = (self.user == self.order.client)
        
        # Add the main rating field (required)
        self.fields['rating'] = forms.ChoiceField(
            label=_('Overall Rating'),
            choices=[('', _('Select rating...'))] + [(str(i), str(i)) for i in range(1, 6)],
            widget=forms.HiddenInput(attrs={'required': 'required'}),
            required=True,
            error_messages={
                'required': _('Please select a rating'),
            }
        )
        
        # Add appropriate rating fields based on who is being reviewed
        if self.reviewing_freelancer:
            self._add_freelancer_rating_fields()
        else:
            self._add_client_rating_fields()
    
    def _add_freelancer_rating_fields(self):
        """Add rating fields specific to freelancer reviews."""
        # Overall rating (required)
        self.fields['rating'] = forms.ChoiceField(
            label=_('Overall Rating'),
            choices=self.RATING_CHOICES,
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=True
        )
        
        # Detailed ratings (optional)
        self.fields['quality_rating'] = forms.ChoiceField(
            label=_('Quality of Work'),
            choices=self.RATING_CHOICES,
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=False
        )
        self.fields['communication_rating'] = forms.ChoiceField(
            label=_('Communication'),
            choices=self.RATING_CHOICES,
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=False
        )
        self.fields['deadline_rating'] = forms.ChoiceField(
            label=_('Meeting Deadlines'),
            choices=self.RATING_CHOICES,
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=False
        )
        self.fields['professionalism_rating'] = forms.ChoiceField(
            label=_('Professionalism'),
            choices=self.RATING_CHOICES,
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=False
        )
    
    def _add_client_rating_fields(self):
        """Add rating fields specific to client reviews."""
        # Overall rating (required)
        self.fields['rating'] = forms.ChoiceField(
            label=_('Overall Rating'),
            choices=self.RATING_CHOICES,
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=True
        )
        
        # Detailed ratings (optional)
        self.fields['clarity_rating'] = forms.ChoiceField(
            label=_('Clarity of Requirements'),
            choices=self.RATING_CHOICES,
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=False
        )
        self.fields['responsiveness_rating'] = forms.ChoiceField(
            label=_('Responsiveness'),
            choices=self.RATING_CHOICES,
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=False
        )
        self.fields['payment_rating'] = forms.ChoiceField(
            label=_('Timely Payment'),
            choices=self.RATING_CHOICES,
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=False
        )
    
    class Meta:
        from apps.reviews.models import Review
        model = Review
        fields = []  # All fields are added dynamically in __init__
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure rating is provided and valid
        rating = cleaned_data.get('rating')
        if not rating:
            self.add_error('rating', _('Please select a rating'))
        else:
            try:
                # Convert to int and validate range
                rating_int = int(rating)
                if not 1 <= rating_int <= 5:
                    self.add_error('rating', _('Rating must be between 1 and 5'))
                cleaned_data['rating'] = rating_int
            except (ValueError, TypeError):
                self.add_error('rating', _('Invalid rating value'))
        
        # Convert other rating fields to integers if provided
        for field in self.fields:
            if field != 'rating' and field.endswith('_rating') and field in cleaned_data and cleaned_data[field]:
                try:
                    cleaned_data[field] = int(cleaned_data[field])
                except (ValueError, TypeError):
                    # If conversion fails, just keep the original value
                    pass
        
        return cleaned_data
    
    def save(self, commit=True):
        review = super().save(commit=False)
        # Set the reviewer and reviewed user
        review.reviewer = self.user
        review.order = self.order  # Make sure to set the order
        review.user_being_reviewed = self.order.freelancer if self.reviewing_freelancer else self.order.client
        review.is_client_review = self.reviewing_freelancer
        
        # Set the overall rating (should be validated by clean())
        review.rating = self.cleaned_data['rating']
        
        # Set detailed ratings if provided
        rating_fields = [
            'quality_rating', 'communication_rating', 'deadline_rating', 
            'professionalism_rating', 'clarity_rating', 'responsiveness_rating', 'payment_rating'
        ]
        
        for field in rating_fields:
            if field in self.cleaned_data and self.cleaned_data[field]:
                try:
                    setattr(review, field, int(self.cleaned_data[field]))
                except (ValueError, TypeError):
                    # Skip invalid values
                    pass
        
        if commit:
            review.save()
            # Update the user's average rating
            from apps.reviews.models import update_user_rating
            update_user_rating(review.user_being_reviewed)
        
        return review


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
