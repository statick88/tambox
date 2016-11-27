# -*- coding: utf-8 -*- 
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT, TA_JUSTIFY
from requerimientos.models import DetalleRequerimiento, AprobacionRequerimiento
from contabilidad.models import Empresa, Configuracion
from django.conf import settings
import os
from reportlab.platypus import Table
from reportlab.lib import colors
from reportlab.lib.pagesizes import cm
from administracion.models import Puesto
from reportlab.platypus.flowables import Spacer
from io import BytesIO

try:
    empresa = Empresa.load()
except:
    empresa = None
 
class ReporteRequerimiento():
    
    def __init__(self, pagesize, requerimiento):
        self.requerimiento = requerimiento
        self.buffer = BytesIO()
        if pagesize == 'A4':
            self.pagesize = A4
        elif pagesize == 'Letter':
            self.pagesize = letter
        self.width, self.height = self.pagesize
        
    def tabla_encabezado(self, styles):
        sp = ParagraphStyle('parrafos',
                            alignment = TA_CENTER,
                            fontSize = 14,
                            fontName="Times-Roman")
        requerimiento = self.requerimiento
        try:
            archivo_imagen = os.path.join(settings.MEDIA_ROOT,str(empresa.logo))
            imagen = Image(archivo_imagen, width=90, height=50,hAlign='LEFT')
        except:
            imagen = Paragraph(u"LOGO", sp)        
        nro = Paragraph(u"REQUERIMIENTO DE BIENES Y SERVICIOS<br/>N°"+requerimiento.codigo, sp)
        encabezado = [[imagen,nro,'']]
        tabla_encabezado = Table(encabezado,colWidths=[4 * cm, 11 * cm, 4 * cm])
        tabla_encabezado.setStyle(TableStyle(
            [
                ('ALIGN',(0,0),(1,0),'CENTER'),
                ('VALIGN',(0,0),(1,0),'CENTER'),                                
            ]
        ))
        return tabla_encabezado
    
    def tabla_datos(self, styles):
        requerimiento = self.requerimiento
        izquierda = ParagraphStyle('parrafos',
                            alignment = TA_LEFT,
                            fontSize = 10,
                            fontName="Times-Roman")
        solicitado = Paragraph(u"SOLICITADO POR: "+requerimiento.solicitante.nombre_completo(), izquierda)
        oficina = Paragraph(u"OFICINA: "+requerimiento.oficina.nombre, izquierda)
        motivo = Paragraph(u"MOTIVO: "+requerimiento.motivo, izquierda)
        fecha = Paragraph(u"FECHA DE REQUERIMIENTO: "+requerimiento.fecha.strftime('%d/%m/%Y'), izquierda)
        mes = Paragraph(u"MES EN QUE SE NECESITA: "+requerimiento.get_mes_display(), izquierda)
        para_stock = Paragraph(u"AÑO EN QUE SE NECESITA: "+str(requerimiento.annio), izquierda)
        if requerimiento.entrega_directa_solicitante:
            entrega = Paragraph(u"ENTREGA DIRECTAMENTE AL SOLICITANTE: SI", izquierda)
        else:
            entrega = Paragraph(u"ENTREGA DIRECTAMENTE AL SOLICITANTE: NO", izquierda)
        datos = [[solicitado,oficina],[motivo],[fecha,mes],[para_stock,entrega]]
        tabla_datos = Table(datos,colWidths=[11* cm, 9 * cm])   
        style = TableStyle(
            [
                ('SPAN',(0,1),(1,1)),          
            ]
        )
        tabla_datos.setStyle(style)     
        return tabla_datos
    
    def tabla_detalle(self):
        requerimiento = self.requerimiento
        encabezados = ['Nro', 'Cantidad', 'Unidad', u'Descripción','Uso']
        detalles = DetalleRequerimiento.objects.filter(requerimiento=requerimiento)
        sp = ParagraphStyle('parrafos')
        sp.alignment = TA_JUSTIFY 
        sp.fontSize = 8
        sp.fontName="Times-Roman"        
        lista_detalles = []
        for detalle in detalles:
            tupla_producto = [Paragraph(str(detalle.nro_detalle),sp), 
                              Paragraph(str(detalle.cantidad), sp),
                              Paragraph(detalle.producto.unidad_medida.descripcion,sp),
                              Paragraph(detalle.producto.descripcion, sp),
                              Paragraph(detalle.uso,sp)]
            lista_detalles.append(tupla_producto)
        adicionales = [('','','','','')] * (15-len(detalles))
        tabla_detalle = Table([encabezados] + lista_detalles,colWidths=[0.8 * cm, 2 * cm, 2.5 * cm,7* cm, 7.7 * cm])
        style = TableStyle(
            [
                ('ALIGN',(0,0),(4,0),'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 7),  
                ('ALIGN',(4,1),(-1,-1),'LEFT'), 
                ('VALIGN',(0,0),(-1,-1),'TOP'),          
            ]
        )
        tabla_detalle.setStyle(style)
        return tabla_detalle
    
    def tabla_observaciones(self):
        requerimiento = self.requerimiento
        p = ParagraphStyle('parrafos')
        p.alignment = TA_JUSTIFY 
        p.fontSize = 8
        p.fontName="Times-Roman"
        obs=Paragraph("OBSERVACIONES: "+requerimiento.observaciones,p)
        observaciones = [[obs]]
        tabla_observaciones = Table(observaciones,colWidths=[20 * cm], rowHeights=1.8 * cm)
        tabla_observaciones.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (0, 2), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN',(0,0),(-1,-1),'LEFT'),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
            ]
        ))
        return tabla_observaciones
    
    def obtener_firma(self, firma_trabajador):
        p = ParagraphStyle('parrafos', 
                           alignment = TA_CENTER,
                           fontSize = 8,
                           fontName="Times-Roman")
        if firma_trabajador!='':
            archivo_firma = os.path.join(settings.MEDIA_ROOT,str(firma_trabajador))
            firma = Image(archivo_firma, width=90, height=50,hAlign='CENTER')
        else:
            firma = Paragraph(u"Firma No Encontrada", p)
        return firma
            
    def tabla_firmas(self):
        requerimiento = self.requerimiento
        p = ParagraphStyle('parrafos', 
                           alignment = TA_CENTER,
                           fontSize = 8,
                           fontName="Times-Roman")
        encabezados = [(u'Recepción', '', '', '','','')]
        oficina = requerimiento.oficina
        jefatura = Puesto.objects.get(oficina=oficina,es_jefatura=True,estado=True)
        gerencia = Puesto.objects.get(oficina=oficina.gerencia,es_jefatura=True,estado=True)
        configuracion = Configuracion.objects.first()
        oficina_administracion = configuracion.administracion
        presupuesto = configuracion.presupuesto
        logistica = configuracion.logistica
        jefatura_administracion = Puesto.objects.get(oficina = oficina_administracion,es_jefatura=True,estado=True)
        jefatura_presupuesto = Puesto.objects.get(oficina=presupuesto,es_jefatura=True,estado=True)
        jefatura_logistica = Puesto.objects.get(oficina=logistica,es_jefatura=True,estado=True)
        jefe = jefatura.trabajador
        gerente = gerencia.trabajador
        gerente_administracion = jefatura_administracion.trabajador
        jefe_logistica = jefatura_logistica.trabajador
        jefe_presupuesto = jefatura_presupuesto.trabajador 
        firma_solicitante = self.obtener_firma(requerimiento.solicitante.firma)
        firma_jefe_departamento = self.obtener_firma(jefe.firma)
        firma_gerente = self.obtener_firma(gerente.firma)
        firma_gerente_administracion = self.obtener_firma(gerente_administracion.firma)
        firma_jefe_oficina_logistica = self.obtener_firma(jefe_logistica.firma)
        firma_jefe_oficina_presupuesto = self.obtener_firma(jefe_presupuesto.firma)
        solicitante = requerimiento.solicitante.nombre_completo()
        if requerimiento.aprobacionrequerimiento.estado==AprobacionRequerimiento.STATUS.PEND:
            cuerpo = [('',firma_solicitante,'','','','')]            
        elif requerimiento.aprobacionrequerimiento.estado==AprobacionRequerimiento.STATUS.APROB_JEF:
            cuerpo = [('',firma_solicitante,firma_jefe_departamento,'','','')]
        elif requerimiento.aprobacionrequerimiento.estado==AprobacionRequerimiento.STATUS.APROB_GER_INM:
            cuerpo = [('',firma_solicitante,firma_jefe_departamento,firma_gerente,'','')]
        elif requerimiento.aprobacionrequerimiento.estado==AprobacionRequerimiento.STATUS.APROB_GER_ADM:
            cuerpo = [('',firma_solicitante,firma_jefe_departamento,firma_gerente,firma_gerente_administracion,'')]           
        elif requerimiento.aprobacionrequerimiento.estado==AprobacionRequerimiento.STATUS.APROB_PRES:
            cuerpo = [('',firma_solicitante,firma_jefe_departamento,firma_gerente,firma_gerente_administracion,firma_jefe_oficina_presupuesto)]           
        elif requerimiento.aprobacionrequerimiento.estado==AprobacionRequerimiento.STATUS.APROB_LOG:
            cuerpo = [(firma_jefe_oficina_logistica,firma_solicitante,firma_jefe_departamento,firma_gerente,firma_gerente_administracion,firma_jefe_oficina_presupuesto)]  
            
        try:
            fecha_recepcion = requerimiento.aprobacionrequerimiento.fecha_recepcion.strftime('%d/%m/%Y')
        except:
            fecha_recepcion = ''
        pie = [(Paragraph('Fecha: '+fecha_recepcion+"<br/>"+jefe_logistica.nombre_completo(),p), 
                Paragraph("Solicitado por: <br/>"+solicitante,p), 
                Paragraph('Jefe de Departamento: <br/>'+jefe.nombre_completo(),p), 
                Paragraph(u'V° B° Gerente Inm.: <br/>'+gerente.nombre_completo(),p),
                Paragraph(u'Vº Bº Gerente Adm.: <br/>'+gerente_administracion.nombre_completo(),p),
                Paragraph(u'Vº Bº Presupuesto: <br/>'+jefe_presupuesto.nombre_completo(),p))]
        tabla_firmas = Table(encabezados+cuerpo+pie,colWidths=[3.3 * cm, 3.3 * cm, 3.3 * cm,3.3* cm, 3.4 * cm, 3.4 * cm], rowHeights=[0.5 * cm,2 * cm,1.8 * cm])
        tabla_firmas.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (5, 2), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN',(0,0),(-1,-1),'LEFT'),
                ('ALIGN',(0,1),(5,1),'CENTER'),
                ('ALIGN',(0,2),(5,2),'CENTER'),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
            ]
        ))
        return tabla_firmas
        
    def imprimir(self):
        buffer = self.buffer
        doc = SimpleDocTemplate(buffer,
                                rightMargin=50,
                                leftMargin=50,
                                topMargin=20,
                                bottomMargin=50,
                                pagesize=self.pagesize)
 
        elements = [] 
        styles = getSampleStyleSheet()        
        elements.append(self.tabla_encabezado(styles))
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_datos(styles))
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_detalle())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_observaciones())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_firmas())
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf