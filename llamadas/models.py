from django.db import models
from django.utils import timezone


class Llamada(models.Model):
    """Modelo para almacenar información de las llamadas"""
    
    ESTADO_CHOICES = [
        ('iniciada', 'Iniciada'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('fallida', 'Fallida'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Información de Twilio
    sid = models.CharField(max_length=100, unique=True, help_text="SID de Twilio")
    numero_destino = models.CharField(max_length=20, help_text="Número de teléfono destino")
    numero_origen = models.CharField(max_length=20, help_text="Número de Twilio usado")
    
    # Estado y metadatos
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='iniciada')
    duracion = models.IntegerField(default=0, help_text="Duración en segundos")
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    
    # Información adicional
    transcripcion = models.TextField(blank=True, help_text="Transcripción completa de la conversación")
    notas = models.TextField(blank=True, help_text="Notas adicionales sobre la llamada")
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Llamada'
        verbose_name_plural = 'Llamadas'
    
    def __str__(self):
        return f"Llamada {self.sid} - {self.numero_destino} ({self.estado})"


class MensajeConversacion(models.Model):
    """Modelo para almacenar los mensajes de la conversación"""
    
    TIPO_CHOICES = [
        ('usuario', 'Usuario'),
        ('ia', 'IA'),
    ]
    
    llamada = models.ForeignKey(Llamada, on_delete=models.CASCADE, related_name='mensajes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    contenido = models.TextField(help_text="Contenido del mensaje")
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Mensaje de Conversación'
        verbose_name_plural = 'Mensajes de Conversación'
    
    def __str__(self):
        return f"{self.tipo} - {self.llamada.sid}"

