from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.urls import reverse
from twilio.twiml.voice_response import VoiceResponse
from .models import Llamada, MensajeConversacion
from .services import TwilioService, AIService
import json


def index(request):
    """Vista principal para iniciar llamadas"""
    llamadas = Llamada.objects.all()[:10]
    return render(request, 'llamadas/index.html', {'llamadas': llamadas})


@require_http_methods(["POST"])
def iniciar_llamada(request):
    """Inicia una llamada saliente"""
    numero_destino = request.POST.get('numero_destino', '').strip()
    
    if not numero_destino:
        return JsonResponse({'error': 'Número de destino requerido'}, status=400)
    
    # Validar configuración de Twilio
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return JsonResponse({'error': 'Twilio no está configurado'}, status=500)
    
    # Intentar detectar ngrok automáticamente si BASE_URL es localhost
    webhook_url_base = settings.BASE_URL
    if 'localhost' in settings.BASE_URL or '127.0.0.1' in settings.BASE_URL:
        # Intentar detectar ngrok automáticamente
        try:
            import requests
            response = requests.get('http://localhost:4040/api/tunnels', timeout=1)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                if tunnels:
                    https_tunnel = next((t for t in tunnels if t.get('proto') == 'https'), None)
                    if https_tunnel:
                        webhook_url_base = https_tunnel['public_url']
                    else:
                        webhook_url_base = tunnels[0]['public_url']
        except:
            pass
        
        # Si aún es localhost después de intentar detectar ngrok
        if 'localhost' in webhook_url_base or '127.0.0.1' in webhook_url_base:
            return JsonResponse({
                'error': 'BASE_URL no puede ser localhost. Twilio requiere una URL pública. Por favor, configura ngrok (ejecuta: ngrok http 8000) y actualiza BASE_URL en settings.py con la URL de ngrok, o ejecuta: python configurar_ngrok.py'
            }, status=400)
    
    try:
        twilio_service = TwilioService()
        
        # URL del webhook para manejar la llamada (usa webhook_url_base que puede ser ngrok detectado)
        webhook_url = f"{webhook_url_base}{reverse('llamadas:webhook_llamada')}"
        
        print(f"\n[DEBUG] Iniciando llamada:")
        print(f"  Destino: {numero_destino}")
        print(f"  Webhook URL: {webhook_url}")
        print(f"  BASE_URL: {settings.BASE_URL}")
        print(f"  webhook_url_base: {webhook_url_base}\n")
        
        # Hacer la llamada
        call = twilio_service.hacer_llamada(numero_destino, webhook_url)
        
        # Crear registro en la base de datos
        llamada = Llamada.objects.create(
            sid=call.sid,
            numero_destino=numero_destino,
            numero_origen=settings.TWILIO_PHONE_NUMBER,
            estado='iniciada'
        )
        
        return JsonResponse({
            'success': True,
            'llamada_sid': call.sid,
            'estado': call.status,
            'mensaje': 'Llamada iniciada correctamente'
        })
    
    except Exception as e:
        # Mejorar el mensaje de error
        error_msg = str(e)
        if 'Url is not a valid URL' in error_msg or 'localhost' in error_msg.lower():
            error_msg = 'Twilio no acepta URLs de localhost. Necesitas configurar ngrok y actualizar BASE_URL en settings.py con una URL pública (ej: https://abc123.ngrok.io)'
        elif 'Unable to create record' in error_msg:
            error_msg = f'Error de Twilio: {error_msg}. Verifica que el número de destino sea válido y esté verificado en tu cuenta de Twilio.'
        
        return JsonResponse({'error': error_msg}, status=500)


@csrf_exempt
def webhook_test(request):
    """
    Endpoint de prueba simple que siempre devuelve TwiML válido
    """
    from twilio.twiml.voice_response import VoiceResponse
    
    print("\n[WEBHOOK-TEST] Petición recibida en endpoint de prueba")
    response = VoiceResponse()
    response.say('Hola, este es un mensaje de prueba desde Django. ¿Puedes escucharme?', language='es-ES', voice='Polly.Lupe')
    response.hangup()
    
    return HttpResponse(str(response), content_type='text/xml; charset=utf-8')

@csrf_exempt
def webhook_llamada(request):
    """
    Webhook de Twilio para manejar eventos de la llamada
    NOTA: Removido @require_http_methods para permitir GET también (Twilio puede hacer GET)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log inicial para verificar que el webhook está siendo llamado
    # Verificar si es una petición de Twilio (debe tener CallSid o From/To) o es del desbloqueo
    post_params = dict(request.POST)
    get_params = dict(request.GET)
    is_twilio_request = bool(post_params.get('CallSid') or get_params.get('CallSid') or 
                             post_params.get('From') or get_params.get('From') or
                             post_params.get('To') or get_params.get('To'))
    
    print("\n" + "=" * 60)
    print("[WEBHOOK] Petición recibida")
    print(f"[WEBHOOK] Método: {request.method}")
    print(f"[WEBHOOK] URL: {request.path}")
    print(f"[WEBHOOK] Es petición de Twilio: {is_twilio_request}")
    print(f"[WEBHOOK] Todos los parámetros POST: {post_params}")
    print(f"[WEBHOOK] Todos los parámetros GET: {get_params}")
    print("=" * 60 + "\n")
    
    # Si no es una petición de Twilio y no tiene parámetros, puede ser del desbloqueo
    # En ese caso, devolver un TwiML simple para que ngrok se desbloquee
    # PERO si es POST sin parámetros, puede ser la primera llamada de Twilio cuando se contesta
    if not is_twilio_request and not post_params and not get_params and request.method == 'GET':
        print("[WEBHOOK] Petición de desbloqueo de ngrok detectada (GET)")
        response = VoiceResponse()
        response.say('OK', language='es-ES')
        return HttpResponse(str(response), content_type='text/xml; charset=utf-8')
    
    # Si es POST sin parámetros, puede ser la primera llamada de Twilio cuando se contesta
    # En ese caso, generar TwiML inicial de todas formas
    if request.method == 'POST' and not is_twilio_request and not post_params and not get_params:
        print("[WEBHOOK] POST sin parámetros - puede ser primera llamada de Twilio, generando TwiML inicial")
    
    try:
        # Obtener parámetros tanto de POST como GET (Twilio puede usar ambos)
        call_sid = request.POST.get('CallSid') or request.GET.get('CallSid', '')
        call_status = request.POST.get('CallStatus') or request.GET.get('CallStatus', '')
        speech_result = request.POST.get('SpeechResult') or request.GET.get('SpeechResult', '')
        digits = request.POST.get('Digits') or request.GET.get('Digits', '')  # Por si acaso usa DTMF
        
        print(f"[WEBHOOK] CallSid: {call_sid}")
        print(f"[WEBHOOK] CallStatus: {call_status}")
        print(f"[WEBHOOK] SpeechResult: {speech_result}")
        print(f"[WEBHOOK] Digits: {digits}")
        
        # Obtener o crear la llamada
        # Si no hay CallSid, intentar obtenerlo de otros parámetros o buscar la llamada más reciente
        if not call_sid:
            # Intentar obtener de otros parámetros
            call_sid = request.POST.get('CallSid') or request.GET.get('CallSid') or request.POST.get('CallSid') or ''
            # Si aún no hay CallSid, buscar la llamada más reciente que esté en progreso
            if not call_sid:
                try:
                    llamada_reciente = Llamada.objects.filter(estado__in=['iniciada', 'en_progreso']).order_by('-fecha_creacion').first()
                    if llamada_reciente:
                        call_sid = llamada_reciente.sid
                        print(f"[WEBHOOK] Usando CallSid de llamada reciente: {call_sid}")
                except:
                    pass
        
        try:
            llamada = Llamada.objects.get(sid=call_sid) if call_sid else None
        except Llamada.DoesNotExist:
            llamada = None
        
        # Si no existe la llamada, crear una nueva
        if not llamada:
            numero_destino = request.POST.get('To', '') or request.GET.get('To', '')
            numero_origen = request.POST.get('From', '') or request.GET.get('From', '')
            if call_sid or numero_destino:
                llamada = Llamada.objects.create(
                    sid=call_sid or f"TEMP_{request.META.get('REMOTE_ADDR', 'unknown')}",
                    numero_destino=numero_destino,
                    numero_origen=numero_origen,
                    estado='iniciada'
                )
                print(f"[WEBHOOK] Llamada creada: {llamada.sid}")
            else:
                print(f"[WEBHOOK] ERROR: No se puede crear llamada sin CallSid ni número de destino")
                # Aún así, generar TwiML inicial para que la llamada continúe
        
        # Actualizar estado solo si tenemos una llamada válida
        if llamada and call_status:
            estado_map = {
                'ringing': 'iniciada',
                'in-progress': 'en_progreso',
                'completed': 'completada',
                'failed': 'fallida',
                'busy': 'fallida',
                'no-answer': 'fallida',
                'canceled': 'cancelada'
            }
            llamada.estado = estado_map.get(call_status, 'en_progreso')
            llamada.save()
        
        twilio_service = TwilioService()
        ai_service = AIService()
        
        # Si hay resultado de voz del usuario
        if speech_result and speech_result.strip():
            if not llamada:
                print(f"[WEBHOOK] ERROR: SpeechResult recibido pero no hay llamada asociada")
                # Intentar encontrar la llamada más reciente
                try:
                    llamada = Llamada.objects.filter(estado__in=['iniciada', 'en_progreso']).order_by('-fecha_creacion').first()
                    if not llamada:
                        print(f"[WEBHOOK] ERROR: No se encontró ninguna llamada activa")
                        response = VoiceResponse()
                        response.say('Lo siento, hubo un error. Por favor, intenta más tarde.', language='es-ES', voice='Polly.Lupe')
                        response.hangup()
                        return HttpResponse(str(response), content_type='text/xml')
                except Exception as e:
                    print(f"[WEBHOOK] ERROR al buscar llamada: {e}")
                    response = VoiceResponse()
                    response.say('Lo siento, hubo un error. Por favor, intenta más tarde.', language='es-ES', voice='Polly.Lupe')
                    response.hangup()
                    return HttpResponse(str(response), content_type='text/xml')
            # Guardar mensaje del usuario
            MensajeConversacion.objects.create(
                llamada=llamada,
                tipo='usuario',
                contenido=speech_result
            )
            
            # Obtener historial de conversación (excluyendo el mensaje actual que acabamos de crear)
            mensajes_previos = MensajeConversacion.objects.filter(llamada=llamada).exclude(
                tipo='usuario', contenido=speech_result
            ).order_by('timestamp')
            historial = []
            for msg in mensajes_previos:
                historial.append({
                    "role": "user" if msg.tipo == "usuario" else "assistant",
                    "content": msg.contenido
                })
            print(f"[DEBUG] Historial de conversación: {len(historial)} mensajes previos")
            
            # Obtener respuesta de la IA
            print(f"[DEBUG] Obteniendo respuesta de IA para: {speech_result}")
            respuesta_ia = ai_service.obtener_respuesta(speech_result, historial)
            print(f"[DEBUG] Respuesta de IA: {respuesta_ia}")
            
            # Guardar respuesta de la IA
            MensajeConversacion.objects.create(
                llamada=llamada,
                tipo='ia',
                contenido=respuesta_ia
            )
            
            # Generar TwiML con la respuesta
            webhook_url = f"{settings.BASE_URL}{reverse('llamadas:webhook_llamada')}"
            twiml = twilio_service.generar_twiml_respuesta(respuesta_ia, webhook_url)
            print(f"[DEBUG] TwiML generado: {twiml[:200]}...")
            
            return HttpResponse(twiml, content_type='text/xml')
        
        # Primera llamada - saludo inicial (cuando no hay speech_result aún)
        else:
            print(f"[DEBUG] Primera llamada - generando TwiML inicial")
            if not llamada:
                print(f"[DEBUG] No hay llamada asociada, pero generando TwiML inicial de todas formas")
            webhook_url = f"{settings.BASE_URL}{reverse('llamadas:webhook_llamada')}"
            twiml = twilio_service.generar_twiml_inicial(webhook_url)
            print(f"[DEBUG] TwiML inicial generado: {len(twiml)} caracteres")
            print(f"[DEBUG] TwiML contiene 'Gather': {'Gather' in twiml}")
            print(f"[DEBUG] TwiML completo (primeros 500 chars): {twiml[:500]}")
            
            # Asegurar que el Content-Type sea correcto y agregar charset
            response = HttpResponse(twiml, content_type='text/xml; charset=utf-8')
            response['Content-Type'] = 'text/xml; charset=utf-8'
            print(f"[DEBUG] Response Content-Type: {response['Content-Type']}")
            return response
    
    except Exception as e:
        # En caso de error, generar TwiML de error
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Error en webhook_llamada: {str(e)}")
        print(f"[ERROR] Traceback: {error_trace}")
        
        response = VoiceResponse()
        response.say('Lo siento, hubo un error. Por favor, intenta más tarde.', language='es-ES', voice='Polly.Lupe')
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')


@csrf_exempt
@require_http_methods(["POST"])
def webhook_status(request):
    """
    Webhook para actualizar el estado de la llamada cuando finaliza
    """
    call_sid = request.POST.get('CallSid', '')
    call_status = request.POST.get('CallStatus', '')
    call_duration = request.POST.get('CallDuration', '0')
    
    try:
        llamada = Llamada.objects.get(sid=call_sid)
        
        estado_map = {
            'completed': 'completada',
            'failed': 'fallida',
            'busy': 'fallida',
            'no-answer': 'fallida',
            'canceled': 'cancelada'
        }
        
        if call_status in estado_map:
            llamada.estado = estado_map[call_status]
            llamada.duracion = int(call_duration) if call_duration else 0
        
        # Generar transcripción completa
        mensajes = MensajeConversacion.objects.filter(llamada=llamada).order_by('timestamp')
        transcripcion = "\n".join([f"{msg.get_tipo_display()}: {msg.contenido}" for msg in mensajes])
        llamada.transcripcion = transcripcion
        
        llamada.save()
        
        return HttpResponse('OK', status=200)
    
    except Llamada.DoesNotExist:
        return HttpResponse('Llamada no encontrada', status=404)
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)


def detalle_llamada(request, llamada_id):
    """Vista para ver detalles de una llamada"""
    try:
        llamada = Llamada.objects.get(id=llamada_id)
        mensajes = MensajeConversacion.objects.filter(llamada=llamada).order_by('timestamp')
        return render(request, 'llamadas/detalle.html', {
            'llamada': llamada,
            'mensajes': mensajes
        })
    except Llamada.DoesNotExist:
        return redirect('index')

