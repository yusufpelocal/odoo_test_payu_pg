from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.debug("Loading controllers/main.py")


class PayUController(http.Controller):
    @http.route('/payment/payu/return', type='http', methods=['POST', 'GET'], auth='public', csrf=False)
    def payu_return(self, **post):
        _logger.debug("PayU Return: Data: %s", post)
        try:
            request.env['payment.transaction'].sudo()._handle_feedback('payu', post)
        except ValidationError as e:
            _logger.error("PayU Return: Error: %s", e)
        return request.redirect('/payment/process')

    @http.route('/payment/payu/cancel', type='http', auth='public', csrf=False)
    def payu_cancel(self, **post):
        _logger.debug("PayU Cancel: Data: %s", post)
        return request.redirect('/payment/process')

    @http.route('/payment/payu/pending', type='http', auth='public', csrf=False)
    def payu_pending(self, **post):
        _logger.debug("PayU Pending: Data: %s", post)
        return request.redirect('/payment/process')

