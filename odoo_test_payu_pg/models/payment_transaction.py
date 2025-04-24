from odoo import models, fields

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'payu' or len(tx) == 1:
            return tx
        reference = notification_data.get('reference')
        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'payu')])
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'payu':
            return
        self.provider_reference = notification_data.get('reference', 'payu_test_ref')
        simulated_state = notification_data.get('simulated_state', 'done')
        if simulated_state == 'done':
            self._set_done()
        elif simulated_state == 'pending':
            self._set_pending()
        else:
            self._set_error("Payment simulation failed")
