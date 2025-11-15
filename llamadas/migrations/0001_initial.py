# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Llamada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sid', models.CharField(help_text='SID de Twilio', max_length=100, unique=True)),
                ('numero_destino', models.CharField(help_text='Número de teléfono destino', max_length=20)),
                ('numero_origen', models.CharField(help_text='Número de Twilio usado', max_length=20)),
                ('estado', models.CharField(choices=[('iniciada', 'Iniciada'), ('en_progreso', 'En Progreso'), ('completada', 'Completada'), ('fallida', 'Fallida'), ('cancelada', 'Cancelada')], default='iniciada', max_length=20)),
                ('duracion', models.IntegerField(default=0, help_text='Duración en segundos')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_inicio', models.DateTimeField(blank=True, null=True)),
                ('fecha_fin', models.DateTimeField(blank=True, null=True)),
                ('transcripcion', models.TextField(blank=True, help_text='Transcripción completa de la conversación')),
                ('notas', models.TextField(blank=True, help_text='Notas adicionales sobre la llamada')),
            ],
            options={
                'verbose_name': 'Llamada',
                'verbose_name_plural': 'Llamadas',
                'ordering': ['-fecha_creacion'],
            },
        ),
        migrations.CreateModel(
            name='MensajeConversacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('usuario', 'Usuario'), ('ia', 'IA')], max_length=10)),
                ('contenido', models.TextField(help_text='Contenido del mensaje')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('llamada', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensajes', to='llamadas.llamada')),
            ],
            options={
                'verbose_name': 'Mensaje de Conversación',
                'verbose_name_plural': 'Mensajes de Conversación',
                'ordering': ['timestamp'],
            },
        ),
    ]

