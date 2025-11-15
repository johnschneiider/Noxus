from django.contrib import admin
from .models import Llamada, MensajeConversacion


@admin.register(Llamada)
class LlamadaAdmin(admin.ModelAdmin):
    list_display = ['sid', 'numero_destino', 'estado', 'duracion', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['sid', 'numero_destino', 'transcripcion']
    readonly_fields = ['sid', 'fecha_creacion', 'fecha_inicio', 'fecha_fin']
    
    fieldsets = (
        ('Información de Twilio', {
            'fields': ('sid', 'numero_destino', 'numero_origen')
        }),
        ('Estado', {
            'fields': ('estado', 'duracion')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_inicio', 'fecha_fin')
        }),
        ('Contenido', {
            'fields': ('transcripcion', 'notas')
        }),
    )


@admin.register(MensajeConversacion)
class MensajeConversacionAdmin(admin.ModelAdmin):
    list_display = ['llamada', 'tipo', 'timestamp']
    list_filter = ['tipo', 'timestamp']
    search_fields = ['contenido', 'llamada__sid']
    readonly_fields = ['timestamp']

