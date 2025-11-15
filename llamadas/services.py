"""
Servicios para manejar Twilio y OpenAI
"""
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from django.conf import settings
from openai import OpenAI
import json


class TwilioService:
    """Servicio para manejar operaciones con Twilio"""
    
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.client = Client(self.account_sid, self.auth_token) if self.account_sid else None
    
    def hacer_llamada(self, numero_destino, webhook_url):
        """
        Realiza una llamada saliente usando Twilio
        
        Args:
            numero_destino: Número de teléfono destino
            webhook_url: URL del webhook para manejar la llamada
            
        Returns:
            Objeto Call de Twilio
        """
        if not self.client:
            raise ValueError("Twilio no está configurado correctamente")
        
        print(f"[TwilioService] Haciendo llamada a {numero_destino}")
        print(f"[TwilioService] Webhook URL: {webhook_url}")
        
        # Desbloquear ngrok antes de hacer la llamada (para evitar página de advertencia)
        # Solo hacer GET para desbloquear, no POST (para no interferir con Twilio)
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            # Solo GET para desbloquear ngrok (no POST para no interferir)
            response_get = requests.get(webhook_url, timeout=5, headers=headers, allow_redirects=True)
            print(f"[TwilioService] Ngrok desbloqueado (GET) - Status: {response_get.status_code}")
        except Exception as e:
            print(f"[TwilioService] Advertencia: No se pudo desbloquear ngrok: {e}")
        
        # IMPORTANTE: Twilio necesita que el webhook sea accesible cuando se contesta la llamada
        # Asegurarnos de que la URL sea HTTPS y accesible
        if not webhook_url.startswith('https://'):
            raise ValueError(f"El webhook URL debe ser HTTPS: {webhook_url}")
        
        print(f"[TwilioService] Creando llamada con webhook: {webhook_url}")
        
        # Crear la llamada con el webhook
        # Twilio llamará a esta URL cuando se conteste la llamada
        call = self.client.calls.create(
            to=numero_destino,
            from_=self.phone_number,
            url=webhook_url,
            method='POST',
            status_callback=f"{webhook_url.replace('/webhook/', '/webhook-status/')}",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            status_callback_method='POST'
        )
        
        print(f"[TwilioService] Llamada creada - SID: {call.sid}, Status: {call.status}")
        
        return call
    
    def generar_twiml_inicial(self, webhook_url):
        """
        Genera TwiML para el inicio de la llamada
        """
        response = VoiceResponse()
        
        # Saludo inicial más corto y directo
        response.say(
            'Hola, soy tu asistente virtual. ¿En qué puedo ayudarte?',
            language='es-ES',
            voice='Polly.Lupe'
        )
        
        # Pausa breve antes de capturar
        response.pause(length=1)
        
        # Gather para capturar la voz del usuario
        gather = Gather(
            input='speech',
            language='es-ES',
            speech_timeout='auto',
            action=webhook_url,
            method='POST',
            timeout=10,  # Timeout de 10 segundos
            finish_on_key='#'  # Opcional: terminar con #
        )
        # No agregar otro Say dentro del Gather, solo esperar
        response.append(gather)
        
        # Si no hay respuesta, redirigir al webhook para intentar de nuevo
        response.say('No escuché tu respuesta. Por favor, intenta de nuevo.', language='es-ES', voice='Polly.Lupe')
        response.redirect(webhook_url)
        
        return str(response)
    
    def generar_twiml_respuesta(self, mensaje_ia, webhook_url):
        """
        Genera TwiML con la respuesta de la IA y espera más input
        """
        response = VoiceResponse()
        
        # Pausa breve antes de responder
        response.pause(length=1)
        
        # Decir la respuesta de la IA
        response.say(
            mensaje_ia,
            language='es-ES',
            voice='Polly.Lupe'
        )
        
        # Pausa después de la respuesta
        response.pause(length=1)
        
        # Gather para capturar más input del usuario
        gather = Gather(
            input='speech',
            language='es-ES',
            speech_timeout='auto',
            action=webhook_url,
            method='POST',
            timeout=10,  # Timeout de 10 segundos
            finish_on_key='#'  # Opcional: terminar con #
        )
        gather.say('¿Algo más en lo que pueda ayudarte?', language='es-ES', voice='Polly.Lupe')
        response.append(gather)
        
        # Si no hay respuesta, finalizar
        response.pause(length=2)
        response.say('Gracias por llamar. Hasta luego.', language='es-ES', voice='Polly.Lupe')
        response.hangup()
        
        return str(response)
    
    def generar_twiml_final(self, mensaje_ia):
        """
        Genera TwiML final para cerrar la llamada
        """
        response = VoiceResponse()
        response.say(
            mensaje_ia,
            language='es-ES',
            voice='Polly.Lupe'
        )
        response.say('Gracias por llamar. Hasta luego.', language='es-ES', voice='Polly.Lupe')
        response.hangup()
        
        return str(response)


class AIService:
    """Servicio para manejar conversaciones con IA"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
    
    def obtener_respuesta(self, mensaje_usuario, historial_conversacion=None):
        """
        Obtiene una respuesta de la IA basada en el mensaje del usuario
        
        Args:
            mensaje_usuario: Texto del mensaje del usuario
            historial_conversacion: Lista de mensajes previos en formato [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            Respuesta de la IA como string
        """
        if not self.client:
            return "Lo siento, el servicio de IA no está configurado correctamente."
        
        # Preparar el historial de conversación
        messages = [
            {
                "role": "system",
                "content": "Eres un asistente virtual amigable y profesional que habla en español. Responde de manera concisa y natural, como si estuvieras hablando por teléfono. Mantén las respuestas breves (máximo 2-3 frases) y claras. Siempre responde en español."
            }
        ]
        
        # Agregar historial si existe (solo los últimos 5 mensajes para no exceder tokens)
        if historial_conversacion:
            # Tomar solo los últimos mensajes para mantener el contexto pero no exceder tokens
            historial_limitado = historial_conversacion[-5:] if len(historial_conversacion) > 5 else historial_conversacion
            messages.extend(historial_limitado)
        
        # Agregar el mensaje actual del usuario
        messages.append({
            "role": "user",
            "content": mensaje_usuario
        })
        
        try:
            print(f"[DEBUG] Enviando a OpenAI: {len(messages)} mensajes")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,  # Aumentado un poco para respuestas más completas
                temperature=0.7
            )
            
            respuesta = response.choices[0].message.content.strip()
            print(f"[DEBUG] Respuesta recibida de OpenAI: {respuesta}")
            return respuesta
        except Exception as e:
            print(f"[ERROR] Error en OpenAI: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Lo siento, hubo un error al procesar tu solicitud. Por favor, intenta de nuevo."

