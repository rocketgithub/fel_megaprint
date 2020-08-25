# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round

from datetime import datetime
import base64
from lxml import etree
import requests

import html
import uuid

import logging

class AccountMove(models.Model):
    _inherit = "account.move"

    pdf_fel = fields.Binary('PDF FEL', copy=False)
    name_pdf_fel = fields.Char('Nombre archivo PDF FEL', default='fel.pdf', size=32)

    def post(self):
        for factura in self:
            if factura.journal_id.generar_fel and factura.type in ['out_invoice', 'out_refund', 'in_invoice']:
                if factura.firma_fel:
                    raise UserError("La factura ya fue validada, por lo que no puede ser validada nuevamnte")
                
                dte = factura.dte_documento()
                logging.warn(dte)
                if dte:
                    xml_sin_firma = etree.tostring(dte, encoding="UTF-8").decode("utf-8")
                    logging.warn(xml_sin_firma)

                    request_url = "apiv2"
                    request_path = ""
                    request_url_firma = ""
                    if factura.company_id.pruebas_fel:
                        request_url = "dev2.api"
                        request_path = ""
                        request_url_firma = "dev."

                    headers = { "Content-Type": "application/xml" }
                    data = '<?xml version="1.0" encoding="UTF-8"?><SolicitaTokenRequest><usuario>{}</usuario><apikey>{}</apikey></SolicitaTokenRequest>'.format(factura.company_id.usuario_fel, factura.company_id.clave_fel)
                    r = requests.post('https://'+request_url+'.ifacere-fel.com/'+request_path+'api/solicitarToken', data=data.encode('utf-8'), headers=headers)
                    resultadoXML = etree.XML(bytes(r.text, encoding='utf-8'))

                    if len(resultadoXML.xpath("//token")) > 0:
                        token = resultadoXML.xpath("//token")[0].text
                        uuid_factura = str(uuid.uuid5(uuid.NAMESPACE_OID, str(factura.id))).upper()

                        headers = { "Content-Type": "application/xml", "authorization": "Bearer "+token }
                        data = '<?xml version="1.0" encoding="UTF-8"?><FirmaDocumentoRequest id="{}"><xml_dte><![CDATA[{}]]></xml_dte></FirmaDocumentoRequest>'.format(uuid_factura, xml_sin_firma)
                        r = requests.post('https://'+request_url_firma+'api.soluciones-mega.com/api/solicitaFirma', data=data.encode('utf-8'), headers=headers)
                        resultadoXML = etree.XML(bytes(r.text, encoding='utf-8'))

                        if len(resultadoXML.xpath("//xml_dte")) > 0:
                            xml_con_firma = resultadoXML.xpath("//xml_dte")[0].text

                            headers = { "Content-Type": "application/xml", "authorization": "Bearer "+token }
                            data = '<?xml version="1.0" encoding="UTF-8"?><RegistraDocumentoXMLRequest id="{}"><xml_dte><![CDATA[{}]]></xml_dte></RegistraDocumentoXMLRequest>'.format(uuid_factura, xml_con_firma)
                            logging.warn(data)
                            r = requests.post('https://'+request_url+'.ifacere-fel.com/'+request_path+'api/registrarDocumentoXML', data=data.encode('utf-8'), headers=headers)
                            resultadoXML = etree.XML(bytes(r.text, encoding='utf-8'))

                            if len(resultadoXML.xpath("//listado_errores")) == 0:
                                xml_certificado = resultadoXML.xpath("//xml_dte")[0].text
                                xml_certificado_root = etree.XML(bytes(xml_certificado, encoding='utf-8'))
                                numero_autorizacion = xml_certificado_root.find(".//{http://www.sat.gob.gt/dte/fel/0.2.0}NumeroAutorizacion")

                                factura.firma_fel = numero_autorizacion.text
                                factura.name = numero_autorizacion.get("Serie")+"-"+numero_autorizacion.get("Numero")
                                factura.serie_fel = numero_autorizacion.get("Serie")
                                factura.numero_fel = numero_autorizacion.get("Numero")

                                headers = { "Content-Type": "application/xml", "authorization": "Bearer "+token }
                                data = '<?xml version="1.0" encoding="UTF-8"?><RetornaPDFRequest><uuid>{}</uuid></RetornaPDFRequest>'.format(factura.firma_fel)
                                r = requests.post('https://'+request_url+'.ifacere-fel.com/'+request_path+'api/retornarPDF', data=data, headers=headers)
                                resultadoXML = etree.XML(bytes(r.text, encoding='utf-8'))
                                if len(resultadoXML.xpath("//listado_errores")) == 0:
                                    pdf = resultadoXML.xpath("//pdf")[0].text
                                    factura.pdf_fel = pdf
                            else:
                                raise UserError(r.text)
                        else:
                            raise UserError(r.text)
                    else:
                        raise UserError(r.text)

        return super(AccountMove,self).post()
        
    def button_cancel(self):
        result = super(AccountMove, self).button_cancel()
        for factura in self:
            logging.warn(result)
            if factura.journal_id.generar_fel:
                dte = factura.dte_anulacion()
                logging.warn(dte)
                if dte:
                    xml_sin_firma = etree.tostring(dte, encoding="UTF-8").decode("utf-8")

                    request_url = "apiv2"
                    request_path = ""
                    request_url_firma = ""
                    if factura.company_id.pruebas_fel:
                        request_url = "dev2.api"
                        request_path = ""
                        request_url_firma = "dev."

                    headers = { "Content-Type": "application/xml" }
                    data = '<?xml version="1.0" encoding="UTF-8"?><SolicitaTokenRequest><usuario>{}</usuario><apikey>{}</apikey></SolicitaTokenRequest>'.format(factura.company_id.usuario_fel, factura.company_id.clave_fel)
                    r = requests.post('https://'+request_url+'.ifacere-fel.com/'+request_path+'api/solicitarToken', data=data, headers=headers)
                    resultadoXML = etree.XML(bytes(r.text, encoding='utf-8'))

                    if len(resultadoXML.xpath("//token")) > 0:
                        token = resultadoXML.xpath("//token")[0].text
                        uuid_factura = str(uuid.uuid5(uuid.NAMESPACE_OID, str(factura.id))).upper()

                        headers = { "Content-Type": "application/xml", "authorization": "Bearer "+token }
                        data = '<?xml version="1.0" encoding="UTF-8"?><FirmaDocumentoRequest id="{}"><xml_dte><![CDATA[{}]]></xml_dte></FirmaDocumentoRequest>'.format(uuid_factura, xml_sin_firma)
                        r = requests.post('https://'+request_url_firma+'api.soluciones-mega.com/api/solicitaFirma', data=data.encode('utf-8'), headers=headers)
                        logging.warn(r.text)
                        resultadoXML = etree.XML(bytes(r.text, encoding='utf-8'))
                        if len(resultadoXML.xpath("//xml_dte")) > 0:
                            xml_con_firma = html.unescape(resultadoXML.xpath("//xml_dte")[0].text)

                            headers = { "Content-Type": "application/xml", "authorization": "Bearer "+token }
                            data = '<?xml version="1.0" encoding="UTF-8"?><AnulaDocumentoXMLRequest id="{}"><xml_dte><![CDATA[{}]]></xml_dte></AnulaDocumentoXMLRequest>'.format(uuid_factura, xml_con_firma)
                            logging.warn(data)
                            r = requests.post('https://'+request_url+'.ifacere-fel.com/'+request_path+'api/anularDocumentoXML', data=data.encode('utf-8'), headers=headers)
                            resultadoXML = etree.XML(bytes(r.text, encoding='utf-8'))

                            if len(resultadoXML.xpath("//listado_errores")) > 0:
                                raise UserError(r.text)
                        else:
                            raise UserError(r.text)
                    else:
                        raise UserError(r.text)
                    
        return result
                
class AccountJournal(models.Model):
    _inherit = "account.journal"

    generar_fel = fields.Boolean('Generar FEL',)

class ResCompany(models.Model):
    _inherit = "res.company"

    usuario_fel = fields.Char('Usuario FEL')
    clave_fel = fields.Char('Clave FEL')
    pruebas_fel = fields.Boolean('Modo de Pruebas FEL')
