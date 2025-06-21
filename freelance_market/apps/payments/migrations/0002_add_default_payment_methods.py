from django.db import migrations


def add_default_payment_methods(apps, schema_editor):
    PaymentMethod = apps.get_model('payments', 'PaymentMethod')
    
    # Default payment methods for Tanzania
    default_methods = [
        {'name': 'azampesa', 'is_active': True},
        {'name': 'mtn', 'is_active': True},
        {'name': 'tigopesa', 'is_active': True},
        {'name': 'halopesa', 'is_active': True},
        {'name': 'bank', 'is_active': True},
    ]
    
    for method_data in default_methods:
        PaymentMethod.objects.get_or_create(
            name=method_data['name'],
            defaults={'is_active': method_data['is_active']}
        )


def remove_default_payment_methods(apps, schema_editor):
    # No need to delete the payment methods as they will be deleted when the table is dropped
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            add_default_payment_methods,
            reverse_code=remove_default_payment_methods,
        ),
    ]
