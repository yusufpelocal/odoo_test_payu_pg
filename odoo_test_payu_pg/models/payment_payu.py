from odoo import models, fields, api
from odoo.addons.payment import utils as payment_utils
from odoo.exceptions import ValidationError
import hashlib
import logging

_logger = logging.getLogger(__name__)

class PaymentPayU(models.Model):
    _inherit = 'payment.provider'
    _description = 'PayU Payment Provider'

    payu_merchant_id = fields.Char(string='PayU Merchant ID', groups='base.group_user')
    payu_api_key = fields.Char(string='PayU API Key', groups='base.group_user')
    payu_salt = fields.Char(string='PayU Salt', groups='base.group_user', help='Optional Salt Key for added security')
    payu_test_mode = fields.Boolean(string='Test Mode')

    code = fields.Selection(
        selection_add=[('payu', 'PayU')],
        ondelete={'payu': 'set default'} # Or 'cascade', or a callable
    )


    @api.model
    def _get_supported_currencies(self):
        return ['INR']  # Add other supported currencies

    def _payu_generate_sign(self, values):
        hash_sequence = "key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10"
        hash_vars_seq = hash_sequence.split('|')
        hash_value = ''
        for var in hash_vars_seq:
            hash_value += f"{values.get(var, '')}|"
        hash_value += self.payu_salt
        return hashlib.sha512(hash_value.encode()).hexdigest().lower()

    def _payu_verify_sign(self, data):
        status = data.get('status')
        hash_sequence = "key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10"
        hash_vars_seq = hash_sequence.split('|')
        hash_value = self.payu_salt + '|' + status
        for var in reversed(hash_vars_seq):
            hash_value += f"|{data.get(var, '')}"
        calculated_hash = hashlib.sha512(hash_value.encode()).hexdigest().lower()
        received_hash = data.get('hash')
        return calculated_hash == received_hash

    def _payu_prepare_payment_request(self, tx):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        values = {
            'key': self.payu_merchant_id,
            'txnid': tx.reference,
            'amount': tx.amount,
            'productinfo': tx.sale_order_ids[0].name if tx.sale_order_ids else 'N/A',
            'firstname': tx.partner_id.name,
            'email': tx.partner_id.email,
            'phone': tx.partner_id.phone or '',
            'surl': f'{base_url}/payment/payu/return',
            'furl': f'{base_url}/payment/payu/cancel',
            'curl': f'{base_url}/payment/payu/pending', # Optional
            'udf1': tx.id, # Store transaction ID for easy retrieval
        }
        values['hash'] = self._payu_generate_sign(values)
        return values

    def _payu_get_portal_url(self, tx):
        if self.payu_test_mode:
            return 'https://test.payu.in/_payment'
        else:
            return 'https://secure.payu.in/_payment'

    def render(self, tx, values):
        payu_values = self._payu_prepare_payment_request(tx)
        portal_url = self._payu_get_portal_url(tx)
        return {
            'acquirer_id': self.id,
            'portal_url': portal_url,
            'params': payu_values,
        }

    def _process_feedback_data(self, data):
        _logger.info("PayU Feedback Data: %s", data)
        if not self._payu_verify_sign(data):
            raise ValidationError("PayU: Invalid signature in feedback data.")

        tx_id = data.get('udf1')
        tx = self.env['payment.transaction'].browse(int(tx_id)) if tx_id else None

        if not tx:
            raise ValidationError(f"PayU: No transaction found with ID: {tx_id}")

        if data.get('status') == 'success':
            tx._set_transaction_done()
            tx.write({'acquirer_reference': data.get('txnid')})
        elif data.get('status') in ['pending', 'initiated']:
            tx._set_transaction_pending()
            tx.write({'acquirer_reference': data.get('txnid')})
        else:
            tx._set_transaction_cancel()
            tx.write({'acquirer_reference': data.get('txnid'), 'error_message': data.get('error') or data.get('mihpayid')})

    def _process_notification_data(self, notification_data):
        # For PayU, the feedback and notification are often handled by the same return URL
        self._process_feedback_data(notification_data)

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        if provider_code != 'payu':
            return super()._get_tx_from_notification_data(provider_code, notification_data)
        tx_id = notification_data.get('udf1')
        tx = self.env['payment.transaction'].search([('id', '=', int(tx_id)), ('provider_code', '=', 'payu')])
        return tx

    def _create_missing_journal_for_acquirer(self, company_id):
        return self.env['account.journal'].create({
            'name': f'PayU {self.name or ""}',
            'type': 'bank',
            'company_id': company_id,
            'currency_id': self.env.ref('base.INR').id, # Set your default currency
        })
