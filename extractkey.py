
import os
import json
import datetime, time
from copy import deepcopy

from typing import Union, Any, List, Dict
import asyncio
from subprocess import run
from solana.publickey import PublicKey
from driftpy.constants.config import configs
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION, QUOTE_PRECISION, PEG_PRECISION, FUNDING_RATE_PRECISION
import importlib

import sys
from pathlib import Path
base_path = Path(__file__).resolve().parent
sys.path.append(str(base_path.parent))
from src import *


# Private key handler
def extractKey(base58str) -> bytes:
    """
    Private Key: TypeConversion from (base58,string) to (base64, bytes)

    Args:
        base58str (str): The private key as a base58 encoded string.

    Returns:
        bytes: The private key as a base64 encoded bytes.
    """    
    from solders.keypair import Keypair
    kp = Keypair.from_base58_string(base58str)
    return kp.__bytes__()
