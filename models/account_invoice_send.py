# -*- coding: utf-8 -*-

from odoo import models, api, _
import logging

class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    @api.onchange('template_id')
    def onchange_template_id(self):
        res = super(AccountInvoiceSend, self).onchange_template_id()
        for wizard in self:
            self.adjuntar_fel_pdf(wizard)
        return res


    def adjuntar_fel_pdf(self,wizard):
        if wizard and wizard.invoice_ids.pdf_fel:
            adjunto = {
                'name': 'fel',
                'datas': wizard.invoice_ids.pdf_fel,
                'type': 'binary',
                'mimetype': 'application/pdf',
                'res_model': 'mail.compose.message',
                'res_id': 0,
            }
            attachment_id = self.env['ir.attachment'].create(adjunto)
            if attachment_id:
                wizard.attachment_ids = [(6, 0,[attachment_id.id])]

        return True
