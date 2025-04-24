#from odoo import fields, models
#
#class PaymentProvider(models.Model):
#    _inherit = 'payment.provider'
#
#    code = fields.Selection(
#        selection_add=[('payu', 'PayU')],
#        ondelete={'payu': 'set default'}
#    )
from odoo import models, fields, api

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('payu', 'PayU')], ondelete={'payu': 'set default'})
    payu_merchant_key = fields.Char(string='Merchant Key', required_if_provider='payu')
    payu_merchant_salt = fields.Char(string='Merchant Salt', required_if_provider='payu')
