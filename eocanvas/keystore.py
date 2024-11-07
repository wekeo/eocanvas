import os
import subprocess
import tempfile

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


def load_public_key(public_key_str):
    public_key = serialization.load_pem_public_key(
        bytes(public_key_str), backend=default_backend()
    )
    return public_key


def encrypt_data(data, public_key):
    with tempfile.NamedTemporaryFile(delete=False) as fp_pem, tempfile.NamedTemporaryFile(
        delete=False
    ) as fp_data:
        fp_pem.write(public_key)
        fp_pem.close()
        fp_data.write(data),
        fp_data.close()
        command = [
            "openssl",
            "pkeyutl",
            "-encrypt",
            "-inkey",
            fp_pem.name,
            "-pubin",
            "-in",
            fp_data.name,
        ]
        encrypt_data = subprocess.check_output(command)
        os.remove(fp_data.name)
        os.remove(fp_pem.name)
        return encrypt_data
