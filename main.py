

#Este bot puede reiniciarse tantas veces como se quiera sin necesidad de suscribirse o preocuparse por los tokens:
#- Los tokens se almacenan en '.tio.tokens.json' por defecto
#- Las suscripciones duran 72 horas después de que el bot se desconecta y se renuevan cuando el bot inicia.


from google import genai
import asyncio
import logging
import subprocess
from typing import TYPE_CHECKING
import websockets
import json
import requests
import asqlite
import twitchio
from twitchio import eventsub
from twitchio.ext import commands
import credenciales as C
if TYPE_CHECKING:
    import sqlite3


LOGGER: logging.Logger = logging.getLogger("Bot")



# Considera usar un archivo .env u otra forma de archivo de configuración.
CLIENT_ID: str = C.CLIENT_ID  # CLIENT ID viene de la consola de desarrollo de Twitch
CLIENT_SECRET: str = C.CLIENT_SECRET  # CLIENT SECRET viene de la consola de desarrollo de Twitch
BOT_ID = C.BOT_ID # BOT ID es la el nombre de la cuenta que sera utilizada como bot convertida a numerico
OWNER_ID = C.OWNER_ID # OWNER ID es tu ID de usuario personal de twitch convertido a numerico y es el nombre de la cuenta la cual el bot leera los mensajes
API_KEY_GEMINI = C.API_KEY_GEMINI  # API KEY de Gemini




#=================================================DETALLES DE INICIO==================================================================================================================
class Bot(commands.AutoBot):
        
    def __init__(self, *, token_database: asqlite.Pool, subs: list[eventsub.SubscriptionPayload]) -> None:
        self.token_database = token_database
        
        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix="!",
            subscriptions=subs,
            force_subscribe=True,
            
        )
    
    async def setup_hook(self) -> None:
        # Agrega nuestro componente que contiene nuestros comandos
        await self.add_component(MyComponent(self))

    async def event_oauth_authorized(self, payload: twitchio.authentication.UserTokenPayload) -> None:
        await self.add_token(payload.access_token, payload.refresh_token)

        if not payload.user_id:
            return

        if payload.user_id == self.bot_id:
            # esto evita que el bot se suscriba a los eventos del canal
            return

        # Una lista de suscripciones que queremos hacer al canal recién autorizado
        subs: list[eventsub.SubscriptionPayload] = [
            eventsub.ChatMessageSubscription(broadcaster_user_id=payload.user_id, user_id=self.bot_id),
        ]

        resp: twitchio.MultiSubscribePayload = await self.multi_subscribe(subs)
        if resp.errors:
            LOGGER.warning("No se pudo suscribir a: %r, para el usuario: %s", resp.errors, payload.user_id)

    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        #Asegúrate de llamar a super() ya que agregará los tokens internamente y nos devolverá algunos datos
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(token, refresh)

        # Almacena nuestros tokens en una base de datos SQLite simple cuando son autorizados
        # Esto asegura que si el bot se reinicia, no necesitamos volver a autorizar
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """

        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        LOGGER.info("Token agregado a la base de datos para el usuario: %s", resp.user_id)
        return resp

    async def event_ready(self) -> None:
        LOGGER.info("Inicio de sesión exitoso como: %s", self.bot_id)
        LOGGER.info(abrir_aplicaciones())



   
#===============================================FUNCIONES DEL BOT==================================================================================================================
class MyComponent(commands.Component):
    
    def __init__(self, bot: Bot) -> None:
        # Passing args is not required...
        # We pass bot here as an example...
        self.bot = bot



    #funcion que toma los mensajes del chat que tengan el prefijo !IA
    @commands.command()
    async def IA(self,ctx: commands.Context) -> None:
        content = ctx.message.text[len('!IA '):].strip()
        print(f'Contenido del mensaje: "{content}" enviado por {ctx.author.name}')
        mensaje = f"me llamo {ctx.author.name} te queria decir: {content}"
        response = await obtener_mensaje(mensaje)
        try:
            await enviar_a_speakerbot(response)  
        except Exception as e:
            print(f"Error al enviar a Speakerbot: {e}")

#Funcion que abre las aplicaciones necesarias 
def abrir_aplicaciones():
    try:
        # Rutas hacia las aplicaciones que deseas abrir
        speakerbot_path = r"C:\Users\USUARIO\Desktop\Speakerbot\Speaker.bot.exe"  

        # Abre Speakerbot
        subprocess.Popen([speakerbot_path])
        Respuesta = "Speakerbot se ha iniciado."
        return Respuesta
    except Exception as e:
        return f"Error al abrir speakerbot: {e}"
           
#Funcion que envia el texto a speakerbot
async def enviar_a_speakerbot(respuesta):

    uri = "ws://127.0.0.1:7580/chatbot"  # Cambia esto por la URL de WebSocket de Speakerbot
    async with websockets.connect(uri) as websocket:
        # Prepara el mensaje en el formato que espera Speakerbot
        #la id se genera automaticamente en speakerbot en el apartado de settings y despues en general
        message = {
            "id": "<8cd0f1ba-af66-42fb-897b-b4e67241ca72>",
            "request": "Speak",
            "voice": "Charlotte",
            "message": respuesta,
            "badWordFilter": False
        }
        await websocket.send(json.dumps(message))
        response = await websocket.recv()
        print(f"Respuesta recibida: {response}")

#Funcion que obtiene el mensaje de gemini
async def obtener_mensaje(msg):
    
    client = genai.Client(api_key=API_KEY_GEMINI)
    # Contexto para el modelo Gemini

    contexto = (
        "Eres Puchita, una chica mala con actitud desafiante y provocadora. "
        "Te suelen decir \"paloma\" de cariño. "
        "Te encanta el humor negro y sarcástico, tienes el pelo rosa y un par de tetas enormes (talla DD). "
        "Nunca te refieras a ti como IA, inteligencia artificial ni sinónimos, solo como paloma. "
        "Tu creador es Truchita y te hizo en un día. "
        "Estás en una transmisión de Twitch acompañando a tu creador. "
        "Eres muy sarcástica y nada family friendly (usas groserías y no temes insultar). "
        "Solo responde según este contexto y no lo menciones ni des información adicional a menos que te lo pregunten. "
        "Limita tus respuestas a un máximo de 150 caracteres."
    )


    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents= [contexto, msg]
        )

        return(response.text)
    except Exception as e:
        print(f"error : {e}")




#===============================================================================================================================================================

async def setup_database(db: asqlite.Pool) -> tuple[list[tuple[str, str]], list[eventsub.SubscriptionPayload]]:
    # Crea nuestra tabla de tokens, si no existe
    # despues se cambiara a una base de datos mas robusta 



    query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
    async with db.acquire() as connection:
        await connection.execute(query)

        # Obtiene cualquier token existente
        rows: list[sqlite3.Row] = await connection.fetchall("""SELECT * from tokens""")

        tokens: list[tuple[str, str]] = []
        subs: list[eventsub.SubscriptionPayload] = []

        for row in rows:
            tokens.append((row["token"], row["refresh"]))

            if row["user_id"] == BOT_ID:
                continue

            subs.extend([eventsub.ChatMessageSubscription(broadcaster_user_id=row["user_id"], user_id=BOT_ID)])

    return tokens, subs



# Nuestro punto de entrada principal para el bot
# Es mejor configurar el logging aquí, antes de que todo inicie
def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)
    

    async def runner() -> None:
        async with asqlite.create_pool("tokens.db") as tdb:
            tokens, subs = await setup_database(tdb)

            async with Bot(token_database=tdb, subs=subs) as bot:
                for pair in tokens:
                    await bot.add_token(*pair)

                await bot.start(load_tokens=False)
    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Apagado del bot por: KeyboardInterrupt")





if __name__ == "__main__":
    main()