# Sistema de Llamadas con IA - MVP

Sistema Django que permite realizar llamadas salientes (outbound) donde el cliente puede hablar con una IA usando Twilio y OpenAI.

## Características

- ✅ Llamadas salientes con Twilio
- ✅ Integración con OpenAI para conversaciones de voz
- ✅ Almacenamiento de llamadas y conversaciones en SQLite
- ✅ Interfaz web para iniciar llamadas y ver historial
- ✅ Webhooks de Twilio para manejar eventos de llamadas
- ✅ Transcripción completa de conversaciones

## Requisitos

- Python 3.8+
- SQLite (incluido en Python)
- Cuenta de Twilio con número de teléfono
- API Key de OpenAI

## Instalación

1. Clonar el repositorio y crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

4. Ejecutar migraciones:
```bash
python manage.py migrate
```

6. Crear superusuario (opcional):
```bash
python manage.py createsuperuser
```

7. Ejecutar servidor:
```bash
python manage.py runserver
```

## Configuración

### Variables de Entorno (.env)

- `SECRET_KEY`: Clave secreta de Django
- `DEBUG`: True/False
- `ALLOWED_HOSTS`: Hosts permitidos separados por comas
- `BASE_URL`: URL base para webhooks (ej: http://localhost:8000 o https://tudominio.com)
- `CSRF_TRUSTED_ORIGINS`: Orígenes confiables para CSRF separados por comas
- `TWILIO_ACCOUNT_SID`: Account SID de Twilio
- `TWILIO_AUTH_TOKEN`: Auth Token de Twilio
- `TWILIO_PHONE_NUMBER`: Número de teléfono de Twilio (formato: +1234567890)
- `OPENAI_API_KEY`: API Key de OpenAI
- `OPENAI_MODEL`: Modelo de OpenAI a usar (por defecto: gpt-4)

### Configurar Webhooks en Twilio

1. En el panel de Twilio, ve a tu número de teléfono
2. Configura el webhook de voz con la URL: `https://tudominio.com/webhook/`
3. Configura el webhook de status con la URL: `https://tudominio.com/webhook-status/`

**Nota para desarrollo local:** Usa ngrok o similar para exponer tu servidor local:
```bash
ngrok http 8000
# Usa la URL de ngrok en BASE_URL y en los webhooks de Twilio
```

## Uso

1. Accede a `http://localhost:8000`
2. Ingresa un número de teléfono (formato: +1234567890)
3. Haz clic en "Iniciar Llamada"
4. El sistema realizará la llamada y conectará al destinatario con la IA
5. Puedes ver el historial y detalles de las llamadas en la interfaz

## Estructura del Proyecto

```
noxus/
├── llamadas/          # App principal
│   ├── models.py      # Modelos de Llamada y MensajeConversacion
│   ├── views.py       # Vistas y webhooks
│   ├── services.py    # Servicios de Twilio y OpenAI
│   └── urls.py        # URLs de la app
├── templates/         # Templates HTML
├── static/           # CSS y JavaScript
└── noxus/           # Configuración del proyecto
```

## Próximos Pasos

- [ ] Soporte para múltiples idiomas
- [ ] Personalización de prompts de IA
- [ ] Análisis de sentimiento
- [ ] Grabación de llamadas
- [ ] Dashboard con estadísticas
- [ ] API REST para integraciones

## Licencia

MIT

