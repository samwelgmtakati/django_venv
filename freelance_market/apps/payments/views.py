import logging
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, DetailView, TemplateView, FormView, View, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Sum, Q
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.conf import settings
import csv
import xlsxwriter
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from .models import PaymentMethod, Transaction, WithdrawalRequest, Invoice
from .forms import PaymentMethodForm, WithdrawalRequestForm, PaymentForm

logger = logging.getLogger(__name__)

class PaymentDashboardView(TemplateView):
    """Main dashboard for payment-related activities"""
    template_name = 'payments/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's balance (sum of all completed transactions)
        balance = Transaction.objects.filter(
            user=user, 
            status=Transaction.STATUS_COMPLETED
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Recent transactions
        recent_transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Pending withdrawal requests
        pending_withdrawals = WithdrawalRequest.objects.filter(
            user=user,
            status=WithdrawalRequest.STATUS_PENDING
        ).order_by('-created_at')
        
        context.update({
            'active_page': 'payments_dashboard',
            'balance': balance,
            'recent_transactions': recent_transactions,
            'pending_withdrawals': pending_withdrawals,
            'currency': 'TZS',  # Using the default currency from settings
        })
        return context


class TransactionHistoryView(ListView):
    """View for displaying transaction history"""
    model = Transaction
    template_name = 'payments/transactions.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Transaction.objects.filter(user=self.request.user).select_related('payment_method')
        
        # Filter by transaction type if provided
        transaction_type = self.request.GET.get('type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
            
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Filter by date range if provided
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'transactions'
        context['transaction_type_choices'] = Transaction.TYPE_CHOICES
        context['status_choices'] = Transaction.STATUS_CHOICES
        return context


class PaymentMethodListView(ListView):
    """View for listing payment methods"""
    model = PaymentMethod
    template_name = 'payments/payment_methods.html'
    context_object_name = 'payment_methods'
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'payment_methods'
        return context


class PaymentMethodCreateView(CreateView):
    """View for adding a new payment method"""
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = 'payments/payment_method_form.html'
    success_url = reverse_lazy('payments:payment_methods')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Payment method added successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'payment_methods'
        context['form_title'] = 'Add Payment Method'
        return context


class PaymentMethodUpdateView(UpdateView):
    """View for updating an existing payment method"""
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = 'payments/payment_method_form.html'
    success_url = reverse_lazy('payments:payment_methods')
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment method updated successfully.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'payment_methods'
        context['form_title'] = 'Edit Payment Method'
        return context


class PaymentMethodDeleteView(DeleteView):
    """View for deleting a payment method"""
    model = PaymentMethod
    success_url = reverse_lazy('payments:payment_methods')
    template_name = 'payments/paymentmethod_confirm_delete.html'
    
    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Payment method deleted successfully.')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'payment_methods'
        return context


@login_required
def set_primary_payment_method(request, pk):
    """Set a payment method as primary for the user"""
    if request.method == 'POST':
        payment_method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)
        
        # Set all user's payment methods to not primary
        PaymentMethod.objects.filter(user=request.user).update(is_primary=False)
        
        # Set the selected method as primary
        payment_method.is_primary = True
        payment_method.save()
        
        messages.success(request, 'Primary payment method updated successfully.')
    
    return redirect('payments:payment_methods')


class DebugTemplateView(TemplateView):
    """Debug view to test template loading"""
    template_name = 'payments/debug_template.html'
    
    def get(self, request, *args, **kwargs):
        # Debug template loading
        from django.template.loader import get_template
        from django.conf import settings
        import os
        
        # Check if template exists in all template dirs
        template_path = 'payments/withdraw.html'
        template_dirs = settings.TEMPLATES[0]['DIRS']
        
        debug_info = {
            'template_path': template_path,
            'template_dirs': template_dirs,
            'template_exists': False,
            'found_in': None,
            'template_content': None
        }
        
        # Check each template directory
        for template_dir in template_dirs:
            full_path = os.path.join(template_dir, template_path)
            if os.path.exists(full_path):
                debug_info['template_exists'] = True
                debug_info['found_in'] = full_path
                with open(full_path, 'r') as f:
                    debug_info['template_content'] = f.read()
                break
        
        # Check if template can be loaded by Django
        try:
            template = get_template(template_path)
            debug_info['django_can_load'] = True
        except Exception as e:
            debug_info['django_can_load'] = False
            debug_info['django_error'] = str(e)
        
        return self.render_to_response({'debug_info': debug_info})


class DebugWithdrawView(TemplateView):
    """Debug view to test template inheritance"""
    template_name = 'payments/debug_withdraw.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'withdraw'
        return context


class WithdrawFundsView(FormView):
    """View for requesting a withdrawal"""
    template_name = 'payments/withdraw.html'
    form_class = WithdrawalRequestForm
    success_url = reverse_lazy('payments:withdraw')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            withdrawal = form.save(commit=False)
            withdrawal.user = self.request.user
            withdrawal.currency = 'TZS'  # Using default currency
            withdrawal.status = WithdrawalRequest.STATUS_PENDING
            withdrawal.save()
            
            # Create a pending transaction for the withdrawal
            transaction = Transaction.objects.create(
                user=self.request.user,
                amount=withdrawal.amount * -1,  # Negative amount for withdrawal
                currency='TZS',
                transaction_type=Transaction.TYPE_WITHDRAWAL,
                status=Transaction.STATUS_PENDING,
                payment_method=withdrawal.payment_method,
                description=f"Withdrawal request #{withdrawal.reference}",
            )
            
            withdrawal.transaction = transaction
            withdrawal.save()
            
            messages.success(
                self.request,
                f"Withdrawal request for {withdrawal.amount} TZS has been submitted. "
                "It will be processed within 1-3 business days."
            )
            
            # TODO: Send notification to admin about new withdrawal request
            
            return super().form_valid(form)
            
        except Exception as e:
            logger.error(f"Withdrawal error: {str(e)}", exc_info=True)
            messages.error(
                self.request,
                "An error occurred while processing your withdrawal request. Please try again later."
            )
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'withdraw'
        context['min_withdrawal'] = 10000  # Minimum withdrawal amount in TZS
        
        # Get user's available balance
        balance = Transaction.objects.filter(
            user=self.request.user,
            status=Transaction.STATUS_COMPLETED
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        context['available_balance'] = max(balance, Decimal('0.00'))  # Ensure balance is not negative
        return context


class PaymentView(FormView):
    """View for making a payment"""
    template_name = 'payments/make_payment.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments:payment_success')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        try:
            payment = form.save(commit=False)
            payment.user = self.request.user
            payment.currency = 'TZS'  # Using default currency
            payment.status = Transaction.STATUS_PENDING
            payment.save()
            
            # Process payment based on the selected payment method
            if payment.payment_method.name == 'azampesa':
                return self._process_azampesa_payment(payment)
            # Add other payment methods here
            else:
                return self._process_default_payment(payment)
                
        except Exception as e:
            logger.error(f"Payment error: {str(e)}", exc_info=True)
            messages.error(
                self.request,
                "An error occurred while processing your payment. Please try again later."
            )
            return self.form_invalid(form)
    
    def _process_azampesa_payment(self, payment):
        """Process payment via AzamPesa"""
        # TODO: Implement AzamPesa API integration
        # This is a placeholder for the actual implementation
        
        # For now, we'll simulate a successful payment
        payment.status = Transaction.STATUS_COMPLETED
        payment.processed_at = timezone.now()
        payment.save()
        
        # Create a transaction record
        transaction = Transaction.objects.create(
            user=payment.user,
            amount=payment.amount,
            currency=payment.currency,
            transaction_type=Transaction.TYPE_PAYMENT,
            status=Transaction.STATUS_COMPLETED,
            payment_method=payment.payment_method,
            description=f"Payment for {payment.purpose}",
            processed_at=timezone.now(),
            reference=f"PAY-{timezone.now().strftime('%Y%m%d')}-{str(transaction.id)[:8]}"
        )
        
        # Update payment with transaction reference
        payment.transaction = transaction
        payment.save()
        
        # TODO: Send payment confirmation email
        
        return super().form_valid(form)
    
    def _process_default_payment(self, payment):
        """Process payment via other methods"""
        # Similar to AzamPesa but with different provider
        payment.status = Transaction.STATUS_PENDING  # Will be updated via webhook
        payment.save()
        
        # Redirect to payment gateway or show payment instructions
        # For now, just redirect to success page
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'make_payment'
        return context


class PaymentSuccessView(TemplateView):
    """Payment success page"""
    template_name = 'payments/payment_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'payments'
        return context


@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookView(View):
    """Webhook for processing payment callbacks from payment providers"""
    
    def post(self, request, *args, **kwargs):
        # TODO: Implement webhook handling for payment providers
        # This is a placeholder for the actual implementation
        
        # Verify the webhook signature/authentication
        # Process the webhook data
        # Update the relevant transaction/payment status
        
        return JsonResponse({'status': 'received'})


@login_required
def transaction_detail(request, reference):
    """View for displaying transaction details"""
    transaction = get_object_or_404(
        Transaction.objects.select_related('payment_method'),
        reference=reference,
        user=request.user
    )
    
    return render(request, 'payments/transaction_detail.html', {
        'transaction': transaction,
        'active_page': 'transactions',
    })


@login_required
def invoice_detail(request, invoice_number):
    """View for displaying invoice details"""
    invoice = get_object_or_404(
        Invoice.objects.select_related('transaction', 'user'),
        invoice_number=invoice_number,
        user=request.user
    )
    
    return render(request, 'payments/invoice_detail.html', {
        'invoice': invoice,
        'active_page': 'invoices',
    })


@login_required
def download_invoice(request, invoice_number):
    """View for downloading invoice as PDF"""
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
    if invoice.user != request.user and not request.user.is_staff:
        raise PermissionDenied("You don't have permission to view this invoice.")
    
    # This is a simplified version - you might want to use a proper PDF library
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_number}.pdf"'
    # Add PDF generation logic here
    return response


class TestTemplateView(TemplateView):
    """Test view to verify template loading"""
    template_name = 'payments/withdraw_test.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'test'
        return context


class TestInheritanceTemplateView(TemplateView):
    """Test view to verify template inheritance"""
    template_name = 'payments/test_inheritance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test_message'] = "Template inheritance test successful!"
        return context


def export_transactions(request):
    """
    Export transactions in the requested format (CSV, PDF, or Excel).
    URL parameters:
    - format: csv, pdf, or xlsx
    - start_date: (optional) filter transactions after this date (YYYY-MM-DD)
    - end_date: (optional) filter transactions before this date (YYYY-MM-DD)
    - type: (optional) filter by transaction type
    - status: (optional) filter by transaction status
    """
    # Get filter parameters
    format_type = request.GET.get('format', 'csv').lower()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    transaction_type = request.GET.get('type')
    status = request.GET.get('status')
    
    # Build base queryset
    transactions = Transaction.objects.filter(user=request.user)
    
    # Apply filters
    if start_date:
        transactions = transactions.filter(created_at__gte=start_date)
    if end_date:
        transactions = transactions.filter(created_at__lte=end_date)
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    if status:
        transactions = transactions.filter(status=status)
    
    # Order by most recent first
    transactions = transactions.order_by('-created_at')
    
    # Prepare data for export
    data = [
        ['Date', 'Reference', 'Type', 'Amount (TZS)', 'Status', 'Description']
    ]
    
    for txn in transactions:
        data.append([
            txn.created_at.strftime('%Y-%m-%d %H:%M'),
            txn.reference,
            txn.get_transaction_type_display(),
            f"{txn.amount:,.2f}",
            txn.get_status_display(),
            txn.description or ''
        ])
    
    # Generate the appropriate response based on format
    if format_type == 'pdf':
        return _export_to_pdf(data, 'transactions')
    elif format_type == 'xlsx':
        return _export_to_excel(data, 'transactions')
    else:  # Default to CSV
        return _export_to_csv(data, 'transactions')


def _export_to_csv(data, filename):
    """Export data to CSV format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    writer = csv.writer(response)
    for row in data:
        writer.writerow(row)
    
    return response


def _export_to_excel(data, filename):
    """Export data to Excel format"""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    
    # Add a bold format for headers
    bold = workbook.add_format({'bold': True})
    
    # Write headers
    for col_num, header in enumerate(data[0]):
        worksheet.write(0, col_num, header, bold)
    
    # Write data
    for row_num, row in enumerate(data[1:], 1):
        for col_num, cell in enumerate(row):
            worksheet.write(row_num, col_num, cell)
    
    # Auto-adjust column widths
    for i, col in enumerate(zip(*data)):
        max_length = max([len(str(cell)) for cell in col] + [len(str(data[0][i]))])
        worksheet.set_column(i, i, min(max_length + 2, 30))  # Cap width at 30
    
    workbook.close()
    output.seek(0)
    response.write(output.getvalue())
    
    return response


def _export_to_pdf(data, filename):
    """Export data to PDF format"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    
    # Create the PDF object, using the response object as its "file."
    doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    # Prepare data for the table
    table_data = []
    
    # Add headers with styling
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle('Header', parent=styles['Heading4'], textColor=colors.HexColor('#FFFFFF'))
    
    # Add header row
    header_row = []
    for header in data[0]:
        header_row.append(Paragraph(header, header_style))
    table_data.append(header_row)
    
    # Add data rows
    for row in data[1:]:
        table_data.append(row)
    
    # Create the table
    table = Table(table_data, colWidths=[doc.width/len(data[0])]*len(data[0]))
    
    # Add style to the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6c757d')),  # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Left align all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header font
        ('FONTSIZE', (0, 0), (-1, 0), 10),  # Header font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Header bottom padding
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Data row background
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),  # Data row text color
        ('FONTSIZE', (0, 1), (-1, -1), 9),  # Data row font size
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),  # Grid lines
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align content to top
    ])
    
    # Apply the style to the table
    table.setStyle(style)
    
    # Add the table to the elements to be added to the document
    elements = [table]
    
    # Build the PDF document
    doc.build(elements)
    
    return response
