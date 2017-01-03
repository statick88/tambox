# -*- coding: utf-8 -*-
from django.db import models
from django.utils.encoding import smart_str
from model_utils import Choices
from django.utils.translation import gettext as _
from requerimientos.models import Requerimiento, DetalleRequerimiento
from model_utils.models import TimeStampedModel, StatusModel
from django.db.models import Max
from contabilidad.models import FormaPago
from productos.models import Producto
from compras.querysets import NavegableQuerySet
from compras.settings import CHOICES_ESTADO_COTIZ, CONFIGURACION
from compras.managers import DetalleCotizacionManager, \
    DetalleConformidadServicioManager
from decimal import Decimal


class DetalleOrdenManager(models.Manager):
    def bulk_create(self, objs, cotizacion):
        if cotizacion is not None:
            self.guardar_detalles_con_referencia(objs, cotizacion)
        else:
            self.guardar_detalles_sin_referencia(objs)

    def actualizar_cotizaciones(self):
        cotizaciones = Cotizacion.objects.filter(estado=Cotizacion.STATUS.PEND)
        for cot in cotizaciones:
            cot.establecer_estado_comprado()
            cot.save()

    def actualizar_detalle_cotizaciones(self, detalle_requerimiento):
        if detalle_requerimiento.estado == DetalleRequerimiento.STATUS.COMP:
            DetalleCotizacion.objects.filter(detalle_requerimiento=detalle_requerimiento,
                                             estado=DetalleCotizacion.STATUS.PEND).update(
                estado=DetalleCotizacion.STATUS.DESC)

    def guardar_detalles_con_referencia(self, objs, cotizacion):
        requerimiento = cotizacion.requerimiento
        for detalle in objs:
            detalle_cotizacion = detalle.detalle_cotizacion
            detalle_cotizacion.cantidad_comprada = detalle_cotizacion.cantidad_comprada + detalle.cantidad
            detalle_cotizacion.establecer_estado_comprado()
            detalle_cotizacion.save()
            detalle_requerimiento = detalle_cotizacion.detalle_requerimiento
            detalle_requerimiento.cantidad_comprada = detalle_requerimiento.cantidad_comprada + detalle_cotizacion.cantidad_comprada
            detalle_requerimiento.establecer_estado_comprado()
            detalle_requerimiento.save()
            self.actualizar_detalle_cotizaciones(detalle_requerimiento)
            detalle.save()
        requerimiento.establecer_estado_comprado()
        requerimiento.save()
        cotizacion.establecer_estado_comprado()
        cotizacion.save()
        self.actualizar_cotizaciones()

    def guardar_detalles_sin_referencia(self, objs):
        for detalle in objs:
            detalle.save()


class RepresentanteLegal(TimeStampedModel):
    documento = models.CharField(primary_key=True, max_length=11)
    nombre = models.CharField(max_length=150)
    cargo = models.CharField(max_length=50)

    class Meta:
        permissions = (('can_view', 'Can view Representante Legal'),
                       ('can_view_listado', 'Can view Listado Representante Legal'),
                       ('can_view_excel', 'Can view Representante Legal excel'),)

    def __str__(self):
        return self.nombre


class Proveedor(TimeStampedModel):
    ruc = models.CharField(unique=True, max_length=11)
    razon_social = models.CharField(max_length=150)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=15, null=True)
    correo = models.EmailField(null=True)
    estado_sunat = models.CharField(max_length=50)
    condicion = models.CharField(max_length=50)
    representantes = models.ManyToManyField(RepresentanteLegal)
    ciiu = models.CharField(max_length=250)
    fecha_alta = models.DateField()
    estado = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()

    class Meta:
        permissions = (('ver_detalle_proveedor', 'Puede ver detalle Proveedor'),
                       ('ver_tabla_proveedores', 'Puede ver tabla de Proveedores'),
                       ('ver_reporte_proveedores_excel', 'Puede ver Reporte Proveedores en excel'),)
        ordering = ['ruc']

    def anterior(self):
        ant = Proveedor.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = Proveedor.objects.siguiente(self)
        return sig.pk

    def __str__(self):
        return smart_str(self.razon_social)


class Cotizacion(TimeStampedModel):
    codigo = models.CharField(primary_key=True, max_length=12)
    proveedor = models.ForeignKey(Proveedor)
    requerimiento = models.ForeignKey(Requerimiento, null=True)
    fecha = models.DateField()
    observaciones = models.TextField(blank=True)
    STATUS = CHOICES_ESTADO_COTIZ
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    objects = NavegableQuerySet.as_manager()

    def anterior(self):
        ant = Cotizacion.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = Cotizacion.objects.siguiente(self)
        return sig.pk

    def eliminar_cotizacion(self):
        self.estado = Cotizacion.STATUS.CANC
        self.save()

    def eliminar_referencia(self):
        cotizacion = self
        requerimiento = cotizacion.requerimiento
        detalles = DetalleCotizacion.objects.filter(cotizacion=cotizacion)
        for detalle in detalles:
            detalle_requerimiento = detalle.detalle_requerimiento
            if detalle_requerimiento.cantidad_cotizada > 0:
                detalle_requerimiento.cantidad_cotizada = detalle_requerimiento.cantidad_cotizada - detalle.cantidad
            detalle_requerimiento.establecer_estado_cotizado()
            detalle_requerimiento.save()
        requerimiento.establecer_estado_cotizado()
        requerimiento.save()
        DetalleCotizacion.objects.filter(cotizacion=cotizacion).delete()

    def establecer_estado_comprado(self):
        total = 0
        total_comprado = 0
        detalles = DetalleCotizacion.objects.filter(cotizacion=self)
        for detalle in detalles:
            total = total + detalle.cantidad
            total_comprado = total_comprado + detalle.cantidad_comprada
        if total_comprado == 0:
            estado = Cotizacion.STATUS.DESC
        elif total_comprado < total:
            estado = Cotizacion.STATUS.ELEG_PARC
        elif total_comprado >= total:
            estado = Cotizacion.STATUS.ELEG
        self.estado = estado
        return self.estado

    class Meta:
        unique_together = (('proveedor', 'requerimiento'),)
        permissions = (('ver_detalle_cotizacion', 'Puede ver detalle de Cotización'),
                       ('ver_tabla_cotizaciones', 'Puede ver tabla Cotizaciones'),
                       ('ver_reporte_cotizaciones_excel', 'Puede ver Reporte de Cotizaciones en excel'),
                       ('puede_hacer_transferencia_cotizacion', 'Puede hacer transferencia de Cotización'),)

    def save(self, *args, **kwargs):
        if self.codigo == '':
            anio = self.fecha.year
            mov_ant = Cotizacion.objects.filter(fecha__year=anio).aggregate(Max('codigo'))
            id_ant = mov_ant['codigo__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-6:]) + 1
            correlativo = str(aux).zfill(6)
            self.codigo = 'CO' + str(anio) + correlativo
        super(Cotizacion, self).save()

    def __str__(self):
        return self.codigo


class DetalleCotizacion(TimeStampedModel, StatusModel):
    objects = DetalleCotizacionManager()
    nro_detalle = models.IntegerField()
    cotizacion = models.ForeignKey(Cotizacion)
    detalle_requerimiento = models.ForeignKey(DetalleRequerimiento, null=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=5)
    cantidad_comprada = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ELEG', _('ELEGIDA')),
                     ('ELEG_PARC', _('ELEGIDA PARCIALMENTE')),
                     ('DESC', _('DESCARTADA')),
                     ('CANC', _('CANCELADO')), )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)

    def establecer_estado_comprado(self):
        if self.cantidad_comprada == 0:
            estado = DetalleCotizacion.STATUS.PEND
        elif self.cantidad_comprada < self.cantidad:
            estado = DetalleCotizacion.STATUS.ELEG_PARC
        elif self.cantidad_comprada >= self.cantidad:
            estado = DetalleCotizacion.STATUS.ELEG
        self.estado = estado
        return self.estado

    class Meta:
        permissions = (('can_view', 'Can view Detalle Orden de Compra'),)


class OrdenCompra(TimeStampedModel):
    codigo = models.CharField(primary_key=True, max_length=12)
    cotizacion = models.ForeignKey(Cotizacion, null=True)
    proveedor = models.ForeignKey(Proveedor, null=True)
    proceso = models.CharField(max_length=50, default='')
    fecha = models.DateField()
    forma_pago = models.ForeignKey(FormaPago)
    subtotal = models.DecimalField(max_digits=15, decimal_places=5)
    igv = models.DecimalField(max_digits=15, decimal_places=5)
    total = models.DecimalField(max_digits=15, decimal_places=5)
    total_letras = models.CharField(max_length=150)
    observaciones = models.TextField(default='')
    nombre_informe = models.CharField(max_length=150, default='')
    informe = models.FileField(upload_to='informes', null=True)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ING', _('INGRESADA')),
                     ('ING_PARC', _('INGRESADA PARCIALMENTE')),
                     ('CANC', _('CANCELADA')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    objects = NavegableQuerySet.as_manager()

    def anterior(self):
        ant = OrdenCompra.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = OrdenCompra.objects.siguiente(self)
        return sig.pk

    def eliminar_referencia(self):
        cotizacion = self.cotizacion
        requerimiento = self.cotizacion
        detalles = DetalleOrdenCompra.objects.filter(orden=self)
        for detalle in detalles:
            detalle_cotizacion = detalle.detalle_cotizacion
            detalle_cotizacion.cantidad_comprada = detalle_cotizacion.cantidad_comprada - detalle.cantidad
            detalle_cotizacion.establecer_estado_comprado()
            detalle_cotizacion.save()
            detalle_requerimiento = detalle_cotizacion.detalle_requerimiento
            detalle_requerimiento.cantidad_comprada = detalle_requerimiento.cantidad_comprada - detalle.cantidad
            detalle_requerimiento.establecer_estado_comprado()
            detalle_requerimiento.save()
        cotizacion.establecer_estado_comprado()
        requerimiento.establecer_estado_comprado()
        cotizacion.save()

    def establecer_estado(self):
        estado_orden = OrdenCompra.STATUS.ING
        detalles_orden = DetalleOrdenCompra.objects.filter(orden=self)
        for detalle in detalles_orden:
            if detalle.estado == DetalleOrdenCompra.STATUS.ING_PARC or detalle.estado == DetalleOrdenCompra.STATUS.PEND:
                estado_orden = OrdenCompra.STATUS.ING_PARC
                break
        self.estado = estado_orden
        return self.estado

    class Meta:
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('ver_detalle_orden_compra', 'Puede ver detalle de Orden de Compra'),
                       ('ver_tabla_ordenes_compra', 'Puede ver tabla Ordenes de Compra'),
                       ('ver_reporte_ordenes_compra_excel', 'Puede ver Reporte de Ordenes de Compra en excel'),
                       ('puede_hacer_transferencia_orden_compra', 'Puede hacer transferencia de Orden de Compra'),)
        ordering = ('codigo',)

    def save(self, *args, **kwargs):
        if self.codigo == '':
            anio = self.fecha.year
            mov_ant = OrdenCompra.objects.filter(fecha__year=anio).aggregate(Max('codigo'))
            id_ant = mov_ant['codigo__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-6:]) + 1
            correlativo = str(aux).zfill(6)
            self.codigo = 'OC' + str(anio) + correlativo
        super(OrdenCompra, self).save()

    def __str__(self):
        return self.codigo


class DetalleOrdenCompra(TimeStampedModel):
    objects = DetalleOrdenManager()
    nro_detalle = models.IntegerField()
    orden = models.ForeignKey(OrdenCompra)
    detalle_cotizacion = models.ForeignKey(DetalleCotizacion, null=True)
    producto = models.ForeignKey(Producto, null=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=5)
    cantidad_ingresada = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    precio = models.DecimalField(max_digits=15, decimal_places=5)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ING', _('INGRESADO')),
                     ('ING_PARC', _('INGRESADO PARCIALMENTE')),
                     ('CANC', _('CANCELADO')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)

    @property
    def valor(self):
        return round(self.precio * self.cantidad, 5)

    @property
    def impuesto(self):
        val = Decimal(self.valor)
        monto_impuesto = CONFIGURACION.impuesto_compra.monto
        base = val / (monto_impuesto + 1)
        imp = val - base
        return round(imp, 5)

    def establecer_estado(self):
        if self.cantidad_ingresada < self.cantidad:
            estado = DetalleOrdenCompra.STATUS.ING_PARC
        elif self.cantidad_ingresada >= self.cantidad:
            estado = DetalleOrdenCompra.STATUS.ING
        self.estado = estado
        return self.estado

    class Meta:
        permissions = (('can_view', 'Can view Detalle Orden de Compra'),)


class OrdenServicios(TimeStampedModel):
    codigo = models.CharField(primary_key=True, max_length=12)
    cotizacion = models.ForeignKey(Cotizacion, null=True)
    proveedor = models.ForeignKey(Proveedor, null=True)
    forma_pago = models.ForeignKey(FormaPago)
    proceso = models.CharField(max_length=50, default='')
    subtotal = models.DecimalField(max_digits=15, decimal_places=5)
    igv = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=5)
    total_letras = models.CharField(max_length=150)
    nombre_informe = models.CharField(max_length=150, default='')
    informe = models.FileField(upload_to='informes', null=True)
    fecha = models.DateField()
    observaciones = models.TextField(default='')
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('CONF', _('CONFORME')),
                     ('CONF_PARC', _('CONFORME PARCIALMENTE')),
                     ('CANC', _('CANCELADA')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    objects = NavegableQuerySet.as_manager()

    def anterior(self):
        ant = OrdenServicios.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = OrdenServicios.objects.siguiente(self)
        return sig.pk

    def eliminar_referencia(self):
        cotizacion = self.cotizacion
        requerimiento = self.cotizacion
        detalles = DetalleOrdenServicios.objects.filter(orden=self)
        for detalle in detalles:
            detalle_cotizacion = detalle.detalle_cotizacion
            detalle_cotizacion.cantidad_comprada = detalle_cotizacion.cantidad_comprada - detalle.cantidad
            detalle_cotizacion.establecer_estado_comprado()
            detalle_cotizacion.save()
            detalle_requerimiento = detalle_cotizacion.detalle_requerimiento
            detalle_requerimiento.cantidad_comprada = detalle_requerimiento.cantidad_comprada - detalle.cantidad
            detalle_requerimiento.establecer_estado_comprado()
            detalle_requerimiento.save()
        cotizacion.establecer_estado_comprado()
        requerimiento.establecer_estado_comprado()
        cotizacion.save()

    def establecer_estado(self):
        estado_orden = OrdenServicios.STATUS.CONF
        detalles_orden = DetalleOrdenServicios.objects.filter(orden=self)
        for detalle in detalles_orden:
            if detalle.estado == DetalleOrdenServicios.STATUS.CONF_PARC or detalle.estado == DetalleOrdenServicios.STATUS.PEND:
                estado_orden = OrdenServicios.STATUS.CONF_PARC
                break
        self.estado = estado_orden
        return self.estado

    class Meta:
        permissions = (('ver_detalle_orden_servicios', 'Puede ver detalle de Orden de Servicios'),
                       ('ver_tabla_ordenes_servicios', 'Puede ver tabla de Ordenes de Servicios'),
                       ('ver_reporte_ordenes_servicios_excel', 'Puede ver Reporte de Ordenes de Servicios en excel'),)
        ordering = ('codigo',)

    def generar_codigo(self):
        anio = self.fecha.year
        mov_ant = OrdenServicios.objects.filter(fecha__year=anio).aggregate(Max('codigo'))
        id_ant = mov_ant['codigo__max']
        if id_ant is None:
            aux = 1
        else:
            aux = int(id_ant[-6:]) + 1
        correlativo = str(aux).zfill(6)
        codigo = 'OS' + str(anio) + correlativo
        print codigo
        return codigo

    def save(self, *args, **kwargs):
        if self.codigo == '':
            self.codigo = self.generar_codigo()
        super(OrdenServicios, self).save()

    def __str__(self):
        return self.codigo


class DetalleOrdenServicios(TimeStampedModel):
    objects = DetalleOrdenManager()
    nro_detalle = models.IntegerField()
    orden = models.ForeignKey(OrdenServicios)
    detalle_cotizacion = models.ForeignKey(DetalleCotizacion, null=True)
    producto = models.ForeignKey(Producto, null=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=5)
    cantidad_conforme = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    precio = models.DecimalField(max_digits=15, decimal_places=5)
    valor = models.DecimalField(max_digits=15, decimal_places=5, blank=True, null=True)
    impuesto = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('CONF', _('CONFORME')),
                     ('CONF_PARC', _('CONFORME PARCIALMENTE')),
                     ('CANC', _('CANCELADA')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)

    class Meta:
        permissions = (('ver_detalle_orden_servicios', 'Puede ver Detalle Orden de Servicios'),)
        ordering = ['nro_detalle']

    def establecer_estado_atendido(self):
        if self.cantidad_conforme < self.cantidad:
            self.estado = DetalleOrdenServicios.STATUS.CONF_PARC
        elif self.cantidad_conforme >= self.cantidad:
            self.estado = DetalleOrdenServicios.STATUS.CONF
        self.save()
        return self.estado


class ConformidadServicio(TimeStampedModel):
    codigo = models.CharField(primary_key=True, max_length=12)
    orden_servicios = models.ForeignKey(OrdenServicios)
    doc_sustento = models.CharField(max_length=50)
    archivo = models.FileField(upload_to='informes', null=True)
    fecha = models.DateField()
    total = models.DecimalField(max_digits=15, decimal_places=5)
    total_letras = models.CharField(max_length=150)
    estado = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()

    class Meta:
        permissions = (('ver_detalle_conformidad_servicio', 'Puede ver detalle de Conformidad de Servicio'),
                       ('ver_tabla_conformidades_servicio', 'Puede ver tabla de Conformidades de Servicio'),
                       ('ver_reporte_conformidades_servicio_excel',
                        'Puede ver Reporte de Conformidades de Servicio en excel'),)

    def anterior(self):
        ant = ConformidadServicio.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = ConformidadServicio.objects.siguiente(self)
        return sig.pk

    def eliminar_referencia(self, orden_compra):
        referencia = orden_compra.cotizacion
        referencia.abierta = True
        referencia.save()
        detalles = DetalleOrdenCompra.objects.filter(orden=orden_compra)
        for detalle in detalles:
            try:
                detalle_requerimiento = detalle.detalle_requerimiento
                detalle_requerimiento.cantidad_atendida = detalle_requerimiento.cantidad_atendida - detalle.cantidad
                detalle_requerimiento.abierta = True
                detalle_requerimiento.save()
            except DetalleRequerimiento.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        if self.codigo == '':
            anio = self.fecha.year
            conf_ant = ConformidadServicio.objects.filter(fecha__year=anio).aggregate(Max('codigo'))
            id_ant = conf_ant['codigo__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-6:]) + 1
            correlativo = str(aux).zfill(6)
            self.codigo = 'CS' + str(anio) + correlativo
        super(ConformidadServicio, self).save()

    def __str__(self):
        return self.codigo


class DetalleConformidadServicio(TimeStampedModel):
    objects = DetalleConformidadServicioManager()
    nro_detalle = models.IntegerField()
    conformidad = models.ForeignKey(ConformidadServicio)
    detalle_orden_servicios = models.ForeignKey(DetalleOrdenServicios, null=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=5, default=0)