from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import Message, Thread

User = get_user_model()


class MessageForm(forms.ModelForm):
    """Form for creating and replying to messages"""
    message = forms.CharField(
        label=_('Message'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Type your message here...')
        })
    )
    
    class Meta:
        model = Message
        fields = []  # use custom field 'message' and map it to body
    
    def __init__(self, *args, **kwargs):
        self.thread = kwargs.pop('thread', None)
        self.sender = kwargs.pop('sender', None)
        self.recipient = kwargs.pop('recipient', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        msg_obj = super().save(commit=False)
        # transfer text from the custom form field to the model field
        msg_obj.body = self.cleaned_data.get('message', '')
        if self.thread:
            msg_obj.thread = self.thread
        if self.sender:
            msg_obj.sender = self.sender
        if self.recipient:
            msg_obj.recipient = self.recipient
        if commit:
            msg_obj.save()
        return msg_obj


class NewThreadForm(forms.Form):
    """Form for starting a new message thread"""
    subject = forms.CharField(
        label=_('Subject'),
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Subject')
        })
    )
    
    message = forms.CharField(
        label=_('Message'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': _('Type your message here...')
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.sender = kwargs.pop('sender', None)
        self.recipient = kwargs.pop('recipient', None)
        self.job = kwargs.pop('job', None)
        self.proposal = kwargs.pop('proposal', None)
        super().__init__(*args, **kwargs)
        
        # Initialize the recipient field
        self.fields['recipient'] = forms.ModelChoiceField(
            queryset=User.objects.none(),
            label=_('Recipient'),
            required=True,
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        
        # Set the queryset based on the context
        if self.job:
            # If there's a job, only show the client as recipient
            self.fields['recipient'].queryset = User.objects.filter(pk=self.job.client_id)
            self.fields['recipient'].initial = self.job.client
            self.fields['recipient'].widget.attrs['disabled'] = True
        elif self.proposal:
            # If there's a proposal, only show the freelancer as recipient
            self.fields['recipient'].queryset = User.objects.filter(pk=self.proposal.freelancer_id)
            self.fields['recipient'].initial = self.proposal.freelancer
            self.fields['recipient'].widget.attrs['disabled'] = True
        elif self.recipient:
            # If recipient is explicitly provided
            self.fields['recipient'].queryset = User.objects.filter(pk=self.recipient.pk)
            self.fields['recipient'].initial = self.recipient
            self.fields['recipient'].widget.attrs['disabled'] = True
        else:
            # Default: show all users except the sender
            self.fields['recipient'].queryset = User.objects.exclude(pk=self.sender.pk if self.sender else None)
    
    def save(self, commit=True):
        # Get or create the thread
        thread = Thread()
        
        # Set the recipient from the form data if not already set
        if not self.recipient and 'recipient' in self.cleaned_data:
            self.recipient = self.cleaned_data['recipient']
        
        # Set job or proposal if provided
        if self.job:
            thread.job = self.job
            if not self.recipient:
                self.recipient = self.job.client
        if self.proposal:
            thread.proposal = self.proposal
            if not self.recipient:
                self.recipient = self.proposal.freelancer
        
        # Set the subject
        thread.subject = self.cleaned_data['subject']
        
        if commit:
            thread.save()
            
            # Add participants
            participants = [self.sender]
            if self.recipient and self.recipient != self.sender:
                participants.append(self.recipient)
            
            thread.participants.add(*participants)
            
            # Create the first message
            message = Message.objects.create(
                thread=thread,
                sender=self.sender,
                recipient=self.recipient,
                body=self.cleaned_data['message'],
            )
        
        return thread
