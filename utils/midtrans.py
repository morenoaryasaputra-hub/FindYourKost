import midtransclient

from config import Config

snap = midtransclient.Snap(

    is_production=Config.MIDTRANS_IS_PRODUCTION,

    server_key=Config.MIDTRANS_SERVER_KEY,

    client_key=Config.MIDTRANS_CLIENT_KEY

)