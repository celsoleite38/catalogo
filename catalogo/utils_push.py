from django.conf import settings

from cryptography.hazmat.primitives import serialization
import base64


def get_vapid_public_key_urlsafe():
    """
    Lê a chave privada do arquivo .pem e extrai a chave pública
    no formato raw urlsafe-base64 exigido por pushManager.subscribe().
    """
    with open(settings.VAPID_PRIVATE_KEY_PATH, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    public_key = private_key.public_key()
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("utf-8")