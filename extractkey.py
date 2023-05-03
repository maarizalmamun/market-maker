from solders.keypair import Keypair
from solana.rpc.async_api import AsyncClient

def get_base64_key(base58str) -> bytes:
    """Convert base58 private keystring to base64 key in bytes 
    Arg:
        base58str (string): base58 private key
    Return:
        bytes: base64 private key in bytes
    """
    kp = Keypair.from_base58_string(base58str)
    return kp.__bytes__()