"""Carga de datos de demostración para InvenShop.

Uso:
    python manage.py seed_demo

El comando es idempotente: se puede ejecutar varias veces sin duplicar
categorías, productos, usuarios ni pedidos. Genera las imágenes de los
productos con Pillow dentro de MEDIA_ROOT.
"""

from __future__ import annotations

import shutil
import textwrap
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from catalogo.models import Categoria, Producto
from pedidos.models import DetallePedido, Pedido
from usuarios.models import Usuario

# ---------------------------------------------------------------------------
# Datos base
# ---------------------------------------------------------------------------
CATEGORIAS = {
    "Tecnología": "Dispositivos, accesorios y periféricos para tu día a día.",
    "Hogar": "Todo para hacer de tu casa un lugar más cómodo y funcional.",
    "Indumentaria": "Prendas y accesorios para todos los estilos.",
    "Deportes": "Equipamiento para entrenar en casa o al aire libre.",
    "Librería": "Cuadernos, agendas y papelería para estudiar y trabajar.",
    "Belleza": "Cuidado personal y rutinas de belleza.",
}

# (nombre, categoría, precio, stock, activo, descripción)
PRODUCTOS = [
    (
        "Auriculares Bluetooth Pro",
        "Tecnología",
        "89999.00",
        18,
        True,
        "Auriculares inalámbricos con cancelación activa de ruido, 30 horas de autonomía y estuche de carga rápida. Conexión multipunto para alternar entre notebook y celular.",
    ),
    (
        "Teclado mecánico RGB",
        "Tecnología",
        "74999.00",
        12,
        True,
        "Teclado mecánico 75% con switches táctiles, iluminación RGB configurable y estructura de aluminio. Ideal para programar y jugar.",
    ),
    (
        "Mouse inalámbrico Ergo",
        "Tecnología",
        "35999.00",
        25,
        True,
        "Mouse ergonómico con sensor de alta precisión, seis botones programables y batería recargable de larga duración.",
    ),
    (
        'Monitor 27" QHD',
        "Tecnología",
        "389999.00",
        7,
        True,
        "Monitor de 27 pulgadas con resolución QHD, 165 Hz, panel IPS y soporte ajustable en altura. Perfecto para diseño y productividad.",
    ),
    (
        "Webcam Full HD",
        "Tecnología",
        "54999.00",
        0,
        True,
        "Cámara web 1080p con micrófono dual, corrección automática de luz y obturador de privacidad integrado.",
    ),
    (
        "Hub USB-C 7 en 1",
        "Tecnología",
        "42999.00",
        15,
        True,
        "Expansor USB-C con HDMI 4K, lector SD, tres puertos USB 3.0 y carga PD de 100 W. Compacto y liviano.",
    ),
    (
        "Lámpara de escritorio LED",
        "Hogar",
        "28999.00",
        20,
        True,
        "Lámpara LED con brazo articulado, tres temperaturas de color y regulación de intensidad. Base estable y bajo consumo.",
    ),
    (
        "Set de sábanas queen",
        "Hogar",
        "64999.00",
        9,
        True,
        "Juego de sábanas de algodón 300 hilos para cama queen. Incluye sábana bajera, encimera y dos fundas de almohada.",
    ),
    (
        "Cafetera de filtro",
        "Hogar",
        "89999.00",
        6,
        True,
        "Cafetera de goteo con jarra de vidrio de 1,5 litros, filtro reutilizable y función de mantenimiento caliente.",
    ),
    (
        "Organizador modular",
        "Hogar",
        "19999.00",
        30,
        True,
        "Set de tres cajas apilables con tapas transparentes para ordenar escritorio, placard o despensa.",
    ),
    (
        "Difusor de aromas",
        "Hogar",
        "24999.00",
        4,
        True,
        "Difusor ultrasónico con luz cálida, temporizador y apagado automático. Apto para aceites esenciales.",
    ),
    (
        "Remera algodón premium",
        "Indumentaria",
        "18999.00",
        40,
        True,
        "Remera de algodón peinado 100% con calce relajado, cuello reforzado y colores de temporada.",
    ),
    (
        "Buzo con capucha",
        "Indumentaria",
        "45999.00",
        14,
        True,
        "Buzo unisex de frisa con capucha forrada, bolsillo canguro y puños elastizados. Abrigo y comodidad todo el año.",
    ),
    (
        "Zapatillas urbanas",
        "Indumentaria",
        "79999.00",
        11,
        True,
        "Zapatillas de lona con suela de goma antideslizante y plantilla acolchada. Diseño versátil para el día a día.",
    ),
    (
        "Mochila urbana",
        "Indumentaria",
        "52999.00",
        0,
        True,
        "Mochila de 22 litros con compartimento para notebook de 15,6 pulgadas, bolsillos laterales y espalda ventilada.",
    ),
    (
        "Gorra trucker",
        "Indumentaria",
        "15999.00",
        22,
        True,
        "Gorra trucker con frente de algodón, malla trasera y cierre ajustable. Un clásico para todos los días.",
    ),
    (
        "Mat de yoga",
        "Deportes",
        "29999.00",
        16,
        True,
        "Esterilla antideslizante de 6 mm con línea de alineación central y correa para transportar.",
    ),
    (
        "Mancuernas 5 kg (par)",
        "Deportes",
        "39999.00",
        8,
        True,
        "Par de mancuernas recubiertas en neopreno de 5 kg cada una. Ideales para rutinas de fuerza en casa.",
    ),
    (
        "Botella térmica 1L",
        "Deportes",
        "21999.00",
        35,
        True,
        "Botella de acero inoxidable con doble pared al vacío. Mantiene frío 24 h y caliente 12 h.",
    ),
    (
        "Banda elástica set",
        "Deportes",
        "17999.00",
        3,
        True,
        "Set de cinco bandas elásticas de resistencia progresiva con bolsa de transporte y guía de ejercicios.",
    ),
    (
        "Cuaderno A5 dotted",
        "Librería",
        "9999.00",
        50,
        True,
        "Cuaderno de tapa dura con 160 páginas punteadas de papel 100 g. Ideal para bullet journal y notas.",
    ),
    (
        "Agenda 2026",
        "Librería",
        "14999.00",
        19,
        True,
        "Agenda semanal 2026 con vistas mensuales, hojas de notas y cinta separadora. Formato A5.",
    ),
    (
        "Set de bolígrafos",
        "Librería",
        "7999.00",
        27,
        True,
        "Set de cuatro bolígrafos de tinta gel en colores clásicos, con cuerpo metálico y trazo suave.",
    ),
    (
        "Lámpara de lectura",
        "Librería",
        "23999.00",
        5,
        True,
        "Lámpara portátil recargable con pinza, tres niveles de luz y brazo flexible. Perfecta para leer de noche.",
    ),
    (
        "Set de skincare",
        "Belleza",
        "59999.00",
        10,
        True,
        "Rutina completa con limpiador facial, sérum de ácido hialurónico e hidratante con SPF 30. Apto para todo tipo de piel.",
    ),
    (
        "Cepillo de cerdas",
        "Belleza",
        "12999.00",
        24,
        True,
        "Cepillo desenredante con cerdas suaves y mango ergonómico. Apto para cabello húmedo o seco.",
    ),
]

COLORES = {
    "Tecnología": ("#0f172a", "#2563eb"),
    "Hogar": ("#7c2d12", "#f59e0b"),
    "Indumentaria": ("#3f0f3f", "#db2777"),
    "Deportes": ("#064e3b", "#10b981"),
    "Librería": ("#3b0764", "#8b5cf6"),
    "Belleza": ("#500724", "#f43f5e"),
}

USUARIOS_DEMO = [
    {
        "email": "admin@invenshop.com",
        "password": "Admin1234!",
        "nombre": "Ana",
        "apellido": "Gómez",
        "telefono": "341 555-0101",
        "rol": Usuario.Rol.ADMIN,
        "superuser": True,
    },
    {
        "email": "empleado@invenshop.com",
        "password": "Empleado1234!",
        "nombre": "Bruno",
        "apellido": "Fernández",
        "telefono": "341 555-0102",
        "rol": Usuario.Rol.EMPLEADO,
        "superuser": False,
    },
    {
        "email": "cliente@invenshop.com",
        "password": "Cliente1234!",
        "nombre": "Carla",
        "apellido": "Ríos",
        "telefono": "341 555-0103",
        "rol": Usuario.Rol.CLIENTE,
        "superuser": False,
    },
    {
        "email": "lucia@invenshop.com",
        "password": "Cliente1234!",
        "nombre": "Lucía",
        "apellido": "Pereyra",
        "telefono": "341 555-0104",
        "rol": Usuario.Rol.CLIENTE,
        "superuser": False,
    },
]


class Command(BaseCommand):
    help = "Carga categorías, productos con imágenes, usuarios y pedidos de demostración."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sin-imagenes",
            action="store_true",
            help="No genera las imágenes PNG de los productos (usa el placeholder).",
        )

    def handle(self, *args, **options):
        self.sin_imagenes = options["sin_imagenes"]
        self.stdout.write(self.style.MIGRATE_HEADING("Cargando datos de demostración…"))

        with transaction.atomic():
            categorias = self._crear_categorias()
            productos = self._crear_productos(categorias)
            usuarios = self._crear_usuarios()
            self._crear_pedidos(usuarios, productos)

        self._mostrar_resumen()

    # ------------------------------------------------------------------
    # Categorías y productos
    # ------------------------------------------------------------------
    def _crear_categorias(self):
        categorias = {}
        for nombre, descripcion in CATEGORIAS.items():
            categoria, creada = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": descripcion},
            )
            if not creada and not categoria.descripcion:
                categoria.descripcion = descripcion
                categoria.save(update_fields=["descripcion"])
            categorias[nombre] = categoria
        self.stdout.write(f"  · Categorías: {len(categorias)}")
        return categorias

    def _crear_productos(self, categorias):
        productos = {}
        for nombre, categoria_nombre, precio, stock, activo, descripcion in PRODUCTOS:
            producto = Producto.objects.filter(nombre=nombre).first()
            if producto is None:
                producto = Producto(
                    nombre=nombre,
                    stock=stock,
                )
            if not self.sin_imagenes:
                producto.imagen = self._preparar_imagen(nombre, categoria_nombre)
            producto.categoria = categorias[categoria_nombre]
            producto.descripcion = descripcion
            producto.precio = Decimal(precio)
            producto.activo = activo
            producto.save()
            productos[nombre] = producto
        self.stdout.write(f"  · Productos: {len(productos)}")
        return productos

    # ------------------------------------------------------------------
    # Usuarios
    # ------------------------------------------------------------------
    def _crear_usuarios(self):
        usuarios = {}
        for datos in USUARIOS_DEMO:
            usuario = Usuario.objects.filter(email=datos["email"]).first()
            if usuario is None:
                if datos["superuser"]:
                    usuario = Usuario.objects.create_superuser(
                        email=datos["email"],
                        password=datos["password"],
                        nombre=datos["nombre"],
                        apellido=datos["apellido"],
                        telefono=datos["telefono"],
                        rol=datos["rol"],
                    )
                else:
                    usuario = Usuario.objects.create_user(
                        email=datos["email"],
                        password=datos["password"],
                        nombre=datos["nombre"],
                        apellido=datos["apellido"],
                        telefono=datos["telefono"],
                        rol=datos["rol"],
                    )
            else:
                usuario.nombre = datos["nombre"]
                usuario.apellido = datos["apellido"]
                usuario.telefono = datos["telefono"]
                usuario.rol = datos["rol"]
                if datos["superuser"]:
                    usuario.is_superuser = True
                usuario.save()
            usuarios[datos["email"]] = usuario
        self.stdout.write(f"  · Usuarios demo: {len(usuarios)}")
        return usuarios

    # ------------------------------------------------------------------
    # Pedidos de ejemplo
    # ------------------------------------------------------------------
    def _crear_pedidos(self, usuarios, productos):
        if Pedido.objects.exists():
            self.stdout.write("  · Pedidos: ya existen pedidos, se omite la carga de ejemplos.")
            return

        pedidos_demo = [
            {
                "usuario": usuarios["cliente@invenshop.com"],
                "estado": Pedido.Estado.PENDIENTE,
                "dias_atras": 2,
                "items": [("Auriculares Bluetooth Pro", 1), ("Hub USB-C 7 en 1", 1)],
                "envio": {
                    "direccion": "Av. Pellegrini 1450, 4º B",
                    "ciudad": "Rosario",
                    "codigo_postal": "2000",
                    "telefono_contacto": "341 555-0103",
                    "notas": "Timbre 4B. Entregar por la tarde.",
                },
            },
            {
                "usuario": usuarios["cliente@invenshop.com"],
                "estado": Pedido.Estado.PAGADO,
                "dias_atras": 5,
                "items": [("Remera algodón premium", 2), ("Gorra trucker", 1)],
                "envio": {
                    "direccion": "Av. Pellegrini 1450, 4º B",
                    "ciudad": "Rosario",
                    "codigo_postal": "2000",
                    "telefono_contacto": "341 555-0103",
                    "notas": "",
                },
            },
            {
                "usuario": usuarios["cliente@invenshop.com"],
                "estado": Pedido.Estado.ENVIADO,
                "dias_atras": 8,
                "items": [("Cafetera de filtro", 1), ("Set de sábanas queen", 1)],
                "envio": {
                    "direccion": "Av. Pellegrini 1450, 4º B",
                    "ciudad": "Rosario",
                    "codigo_postal": "2000",
                    "telefono_contacto": "341 555-0103",
                    "notas": "Dejar en portería si no hay respuesta.",
                },
            },
            {
                "usuario": usuarios["cliente@invenshop.com"],
                "estado": Pedido.Estado.CANCELADO,
                "dias_atras": 12,
                "items": [('Monitor 27" QHD', 1)],
                "envio": {
                    "direccion": "Av. Pellegrini 1450, 4º B",
                    "ciudad": "Rosario",
                    "codigo_postal": "2000",
                    "telefono_contacto": "341 555-0103",
                    "notas": "Cancelado por el cliente antes del despacho.",
                },
            },
            {
                "usuario": usuarios["lucia@invenshop.com"],
                "estado": Pedido.Estado.PAGADO,
                "dias_atras": 1,
                "items": [("Zapatillas urbanas", 1), ("Botella térmica 1L", 1)],
                "envio": {
                    "direccion": "Bv. Oroño 820, piso 2",
                    "ciudad": "Rosario",
                    "codigo_postal": "2000",
                    "telefono_contacto": "341 555-0104",
                    "notas": "Llamar antes de entregar.",
                },
            },
        ]

        for demo in pedidos_demo:
            self._registrar_pedido(
                usuario=demo["usuario"],
                items=demo["items"],
                estado=demo["estado"],
                dias_atras=demo["dias_atras"],
                envio=demo["envio"],
                productos=productos,
            )
        self.stdout.write(f"  · Pedidos de ejemplo: {len(pedidos_demo)}")

    def _registrar_pedido(self, usuario, items, estado, dias_atras, envio, productos):
        pedido = Pedido.objects.create(
            usuario=usuario,
            estado=estado,
            total=Decimal("0.00"),
            **envio,
        )
        total = Decimal("0.00")
        for nombre, cantidad in items:
            producto = productos[nombre]
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
            )
            total += producto.precio * cantidad
            # Los pedidos cancelados reponen el stock, por eso no se descuenta.
            if estado != Pedido.Estado.CANCELADO:
                Producto.objects.filter(pk=producto.pk).update(stock=F("stock") - cantidad)

        pedido.total = total
        pedido.save(update_fields=["total"])

        fecha = timezone.now() - timedelta(days=dias_atras, hours=3)
        Pedido.objects.filter(pk=pedido.pk).update(fecha_creacion=fecha)

    # ------------------------------------------------------------------
    # Imágenes generadas con Pillow
    # ------------------------------------------------------------------
    def _preparar_imagen(self, nombre, categoria_nombre):
        if self.sin_imagenes:
            return ""
        carpeta = Path(settings.MEDIA_ROOT) / "productos" / "seed"
        carpeta.mkdir(parents=True, exist_ok=True)
        archivo = carpeta / f"{slugify(nombre)}.png"
        relativa = f"productos/seed/{archivo.name}"
        fuente = Path(settings.BASE_DIR) / "static" / "img" / "productos" / archivo.name

        if fuente.exists():
            shutil.copyfile(fuente, archivo)
        elif not archivo.exists():
            self._generar_imagen(nombre, categoria_nombre, archivo)
        return relativa

    def _generar_imagen(self, nombre, categoria_nombre, destino):
        ancho = alto = 900
        color_inicio, color_fin = COLORES.get(categoria_nombre, ("#1e293b", "#6366f1"))

        base = Image.new("RGB", (ancho, alto), color_inicio)
        degradado = Image.new("RGB", (ancho, alto), color_fin)
        mascara = Image.linear_gradient("L").resize((ancho, alto))
        base.paste(degradado, (0, 0), mascara)

        capa = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
        dibujo = ImageDraw.Draw(capa)
        dibujo.ellipse((-180, -160, 420, 440), fill=(255, 255, 255, 32))
        dibujo.ellipse((580, 560, 1120, 1100), fill=(255, 255, 255, 24))
        dibujo.rounded_rectangle((70, 70, 830, 830), radius=56, outline=(255, 255, 255, 70), width=3)
        imagen = Image.alpha_composite(base.convert("RGBA"), capa)

        dibujo = ImageDraw.Draw(imagen)
        fuente_inicial = self._fuente(250)
        fuente_nombre = self._fuente(42)
        fuente_categoria = self._fuente(26)

        inicial = nombre.strip()[:1].upper()
        dibujo.text((ancho / 2, 300), inicial, font=fuente_inicial, fill=(255, 255, 255), anchor="mm")

        lineas = textwrap.wrap(nombre, width=22)[:3]
        dibujo.multiline_text(
            (ancho / 2, 620),
            "\n".join(lineas),
            font=fuente_nombre,
            fill=(255, 255, 255),
            anchor="mm",
            align="center",
            spacing=12,
        )
        dibujo.text(
            (ancho / 2, 750),
            categoria_nombre.upper(),
            font=fuente_categoria,
            fill=(255, 255, 255),
            anchor="mm",
        )

        imagen.convert("RGB").save(destino, format="PNG", optimize=True)

    @staticmethod
    def _fuente(tamano):
        candidatas = [
            "seguisb.ttf",
            "arialbd.ttf",
            "calibrib.ttf",
            "DejaVuSans-Bold.ttf",
        ]
        for candidata in candidatas:
            try:
                return ImageFont.truetype(candidata, tamano)
            except OSError:
                continue
        return ImageFont.load_default(size=tamano)

    # ------------------------------------------------------------------
    # Resumen final
    # ------------------------------------------------------------------
    def _mostrar_resumen(self):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados correctamente."))
        self.stdout.write("")
        self.stdout.write("Cuentas de acceso:")
        self.stdout.write("  Administrador  admin@invenshop.com     / Admin1234!")
        self.stdout.write("  Empleado       empleado@invenshop.com  / Empleado1234!")
        self.stdout.write("  Cliente        cliente@invenshop.com   / Cliente1234!")
        self.stdout.write("  Cliente        lucia@invenshop.com     / Cliente1234!")
        self.stdout.write("")
        self.stdout.write("Iniciá el servidor con: python manage.py runserver")
