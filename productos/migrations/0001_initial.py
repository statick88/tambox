# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-07 16:00
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contabilidad', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GrupoProductos',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('codigo', models.CharField(max_length=6, primary_key=True, serialize=False)),
                ('descripcion', models.CharField(max_length=100)),
                ('son_productos', models.BooleanField(default=True)),
                ('estado', models.BooleanField(default=True)),
                ('ctacontable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contabilidad.CuentaContable')),
            ],
            options={
                'permissions': (('cargar_grupo_productos', 'Puede cargar Grupos de Productos desde un archivo externo'), ('ver_detalle_grupo_productos', 'Puede ver detalle Grupo de Productos'), ('ver_tabla_grupos_productos', 'Puede ver tabla Grupos de Productos'), ('ver_reporte_grupo_productos_excel', 'Puede ver Reporte de grupo de productos en excel')),
            },
        ),
        migrations.CreateModel(
            name='HistoricalGrupoProductos',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('codigo', models.CharField(db_index=True, max_length=6)),
                ('descripcion', models.CharField(max_length=100)),
                ('son_productos', models.BooleanField(default=True)),
                ('estado', models.BooleanField(default=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('ctacontable', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='contabilidad.CuentaContable')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical grupo productos',
            },
        ),
        migrations.CreateModel(
            name='HistoricalProducto',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('codigo', models.CharField(db_index=True, max_length=10)),
                ('descripcion', models.CharField(db_index=True, max_length=100)),
                ('desc_abreviada', models.CharField(blank=True, max_length=40)),
                ('es_servicio', models.BooleanField(default=False)),
                ('marca', models.CharField(blank=True, max_length=40)),
                ('modelo', models.CharField(blank=True, max_length=40)),
                ('precio', models.DecimalField(decimal_places=5, default=0, max_digits=15)),
                ('stock_minimo', models.DecimalField(decimal_places=5, default=0, max_digits=15)),
                ('imagen', models.TextField(default=b'productos/sinimagen.png', max_length=100)),
                ('estado', models.BooleanField(default=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('grupo_productos', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='productos.GrupoProductos')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('tipo_existencia', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='contabilidad.TipoExistencia')),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical producto',
            },
        ),
        migrations.CreateModel(
            name='HistoricalUnidadMedida',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('codigo', models.CharField(db_index=True, max_length=5)),
                ('descripcion', models.CharField(max_length=50)),
                ('estado', models.BooleanField(default=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical unidad medida',
            },
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('codigo', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('descripcion', models.CharField(max_length=100, unique=True)),
                ('desc_abreviada', models.CharField(blank=True, max_length=40)),
                ('es_servicio', models.BooleanField(default=False)),
                ('marca', models.CharField(blank=True, max_length=40)),
                ('modelo', models.CharField(blank=True, max_length=40)),
                ('precio', models.DecimalField(decimal_places=5, default=0, max_digits=15)),
                ('stock_minimo', models.DecimalField(decimal_places=5, default=0, max_digits=15)),
                ('imagen', models.ImageField(default=b'productos/sinimagen.png', upload_to=b'productos')),
                ('estado', models.BooleanField(default=True)),
                ('grupo_productos', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='productos.GrupoProductos')),
                ('tipo_existencia', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='contabilidad.TipoExistencia')),
            ],
            options={
                'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicaci\xf3n'), ('cargar_productos', 'Puede cargar Productos desde un archivo externo'), ('ver_detalle_producto', 'Puede ver detalle de Productos'), ('ver_tabla_productos', 'Puede ver tabla Productos'), ('ver_reporte_productos_excel', 'Puede ver Reporte de Productos en excel'), ('puede_hacer_busqueda_producto', 'Puede hacer busqueda Producto')),
            },
        ),
        migrations.CreateModel(
            name='UnidadMedida',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('codigo', models.CharField(max_length=5, unique=True)),
                ('descripcion', models.CharField(max_length=50)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['codigo'],
                'permissions': (('ver_detalle_unidad_medida', 'Puede ver detalle Unidad de Medida'), ('ver_tabla_unidades_medida', 'Puede ver tabla de unidades de medida'), ('ver_reporte_unidades_medida_excel', 'Puede ver Reporte Unidades de Medida en excel')),
            },
        ),
        migrations.AddField(
            model_name='producto',
            name='unidad_medida',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='productos.UnidadMedida'),
        ),
        migrations.AddField(
            model_name='historicalproducto',
            name='unidad_medida',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='productos.UnidadMedida'),
        ),
    ]
