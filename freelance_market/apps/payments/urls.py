from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from . import views

app_name = 'payments'

urlpatterns = [
    # Dashboard
    path('', login_required(views.PaymentDashboardView.as_view()), name='dashboard'),
    
    # Transactions
    path('transactions/', login_required(views.TransactionHistoryView.as_view()), name='transactions'),
    path('transactions/<str:reference>/', login_required(views.transaction_detail), name='transaction_detail'),
    
    # Payment Methods
    path('payment-methods/', login_required(views.PaymentMethodListView.as_view()), name='payment_methods'),
    path('payment-methods/add/', login_required(views.PaymentMethodCreateView.as_view()), name='add_payment_method'),
    path('payment-methods/<int:pk>/edit/', login_required(views.PaymentMethodUpdateView.as_view()), name='edit_payment_method'),
    path('payment-methods/<int:pk>/delete/', login_required(views.PaymentMethodDeleteView.as_view()), name='delete_payment_method'),
    path('payment-methods/<int:pk>/set-primary/', login_required(views.set_primary_payment_method), name='set_primary_payment_method'),
    
    # Withdrawals
    path('debug-withdraw/', login_required(views.DebugWithdrawView.as_view()), name='debug_withdraw'),
    path('withdraw/', login_required(views.WithdrawFundsView.as_view()), name='withdraw'),
    
    # Payments
    path('pay/', login_required(views.PaymentView.as_view()), name='make_payment'),
    path('payment/success/', login_required(views.PaymentSuccessView.as_view()), name='payment_success'),
    
    # Invoices
    path('invoices/<str:invoice_number>/', login_required(views.invoice_detail), name='invoice_detail'),
    path('invoices/<str:invoice_number>/download/', login_required(views.download_invoice), name='download_invoice'),
    
    # Webhooks
    path('webhook/', views.PaymentWebhookView.as_view(), name='payment_webhook'),
    
    # Export functionality
    path('transactions/export/', login_required(views.export_transactions), name='export_transactions'),
    
    # Debug URLs
    path('debug-template/', login_required(views.DebugTemplateView.as_view()), name='debug_template'),
    path('test-template/', login_required(views.TestTemplateView.as_view()), name='test_template'),
    path('test-inheritance/', login_required(views.TestInheritanceTemplateView.as_view()), name='test_inheritance'),
    
    # Redirect old URLs for backward compatibility
    path('dashboard/', RedirectView.as_view(pattern_name='payments:dashboard', permanent=False)),
    path('transactions', RedirectView.as_view(pattern_name='payments:transactions', permanent=False)),
]