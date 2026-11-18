from django.db import models
from django.contrib.auth.models import User

class Cliente(models.Model):
    """RF04: registrar clientes con datos heterogéneos"""
    nombre = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20, unique=True)
    direccion = models.TextField()
    comodato_actual = models.IntegerField(default=0, help_text="Envases en poder del cliente")
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.telefono}"


class Pedido(models.Model):
    """RF01: Registrar pedido. RF03: bloquear despacho sin pago"""
    ESTADOS = [
        ('PENDIENTE_PAGO', 'Pendiente de pago'),
        ('PAGADO', 'Pagado'),
        ('EN_RUTA', 'En ruta'),
        ('ENTREGADO', 'Entregado'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    total = models.IntegerField(help_text="Monto en CLP")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE_PAGO')
    token_webpay = models.CharField(max_length=100, blank=True, null=True)
    
    # ⭐ NUEVO CAMPO: Chofer asignado al pedido
    chofer_asignado = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pedidos_asignados',
        limit_choices_to={'groups__name': 'Chofer'},  # Solo permite usuarios del grupo Chofer
        verbose_name="Chofer asignado"
    )
    
    creado_en = models.DateTimeField(auto_now_add=True)
    entregado_en = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        chofer = self.chofer_asignado.username if self.chofer_asignado else "Sin asignar"
        return f"Pedido #{self.id} - {self.cliente.nombre} (Chofer: {chofer})"


class Inventario(models.Model):
    """RF07: Monitorear stock y generar alertas"""
    TIPOS = [
        ('LLENO', 'Botellón lleno'),
        ('VACIO', 'Botellón vacío'),
        ('ROTO', 'Botellón roto'),
    ]
    tipo = models.CharField(max_length=10, choices=TIPOS)
    cantidad = models.IntegerField(default=0)
    umbral_critico = models.IntegerField(default=20)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.cantidad}"