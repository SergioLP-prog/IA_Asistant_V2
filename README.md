# Bot de Twitch con Speakerbot y Gemini

Este proyecto es un bot para Twitch que utiliza TwitchIO, Speakerbot y Gemini para responder mensajes en el chat y enviar texto a Speakerbot.

## Requisitos

- Python 3.10+
- Instalar dependencias con:
  ```
  pip install -r requirements.txt
  ```

## Uso

1. Configura tus credenciales en el archivo `credenciales.py`.
2. Ejecuta el bot:
   ```
   python main.py
   ```
3. El bot responde a mensajes que comiencen con `!IA` y envía la respuesta a Speakerbot.

## Archivos principales

- `main.py`: Código principal del bot.
- `credenciales.py` : Aloja las credenciales utilizadas para autorizar el bot
- `requirements.txt`: Lista de dependencias.

## Configuración de Speakerbot

Asegúrate de que Speakerbot esté ejecutándose y configurado para recibir mensajes por WebSocket en `ws://127.0.0.1:7580/chatbot`.

## Licencia

MIT