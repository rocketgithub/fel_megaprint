# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import UserError
import logging

# class IrActionsReport(models.Model):
#     _inherit = 'ir.actions.report'

    # def retrieve_attachment(self, record):
    #     # get the original bills through the message_main_attachment_id field of the record
    #     logging.warn('ATACH RETIREVE2')
    #     logging.warn(self)
    #     logging.warn(record.message_main_attachment_id)
    #     if record and record.pdf_fel:
    #         adjunto = {
    #             'name': 'prueba',
    #             'datas': record.pdf_fel,
    #             'type': 'binary',
    #             'mimetype': 'application/pdf',
    #             'res_model': 'account.move',
    #             'res_id': record.id,
    #
    #         }
    #         attachment_id = self.env['ir.attachment'].create(adjunto)
    #         logging.warn('NUEVO ADJUNTO')
    #         logging.warn(attachment_id)
    #         # logging.warn(self.attachment_ids)
    #         # self.attachment_ids = [(4, [attachment_id.id])]
    #     return super(IrActionsReport, self).retrieve_attachment(record)


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
