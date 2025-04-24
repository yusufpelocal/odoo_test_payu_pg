{
    'name': 'Payment PayU',
    'version': '1.0',
    'summary': 'PayU Payment Gateway Integration',
    'description': 'Integrates PayU payment gateway with Odoo.',
    'author': 'Your Name',
    'website': 'Your Website',
    'category': 'Payment Acquirers',
    'depends': ['payment', 'account'],
    'data': [
        'data/payment_method_data.xml',
        'views/payment_provider_views.xml',
        'views/payment_payu_templates.xml',
        'data/payment_provider_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}