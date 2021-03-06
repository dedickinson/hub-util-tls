"""Module for creating (minting) RSA Keys
"""

import typing
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.padding import AsymmetricPadding
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption, NoEncryption, Encoding, PrivateFormat, PublicFormat)

from interface import implements

from ..interfaces import KeyMinter, PrivateKey, PublicKey

CONST_DEFAULT_KEY_SIZE: int = 2048
CONST_DEFAULT_KEY_PUBLIC_EXPONENT: int = 65537
CONST_DEFAULT_ENCRYPTION_PADDING = padding.OAEP(
    mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
CONST_DEFAULT_SIGNING_PADDING = padding.PSS(
    mgf=padding.MGF1, salt_length=padding.PSS.MAX_LENGTH)


class RsaPublicKey(implements(PublicKey)):
    """An RSA Public Key

    Implements :class:`PublicKey <quickcert.interfaces.PublicKey>`
    """

    def __init__(self, rsa_public_key: rsa.RSAPublicKey):
        self.key = rsa_public_key

    def serialize(self) -> bytes:
        return self.key.public_bytes(encoding=Encoding.PEM,
                                     format=PublicFormat.SubjectPublicKeyInfo)

    @property
    def key_size(self) -> int:
        return self.key.key_size

    def encrypt(self, plaintext: bytes,
                padding: AsymmetricPadding) -> bytes: pass


class RsaPrivateKey(implements(PrivateKey)):
    """An RSA Private Key

    Implements :class:`PrivateKey <quickcert.interfaces.PrivateKey>`
    """

    def __init__(self, rsa_key: rsa.RSAPrivateKey):
        self._key = rsa_key

    @classmethod
    def deserialize(cls, key_path: Path, password: str = None) -> PrivateKey:
        """Loads a private key from a file

        :param key_path: the file path of the key file
        :type key_path: Path
        :param password: the key password, defaults to None
        :type password: str, optional
        :return: the deserialized key
        :rtype: PrivateKey
        """
        if password:
            p = password.encode()
        else:
            p = None

        with open(key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=p,
                backend=default_backend()
            )

        return RsaPrivateKey(private_key)

    @property
    def public_key(self) -> PublicKey:
        return RsaPublicKey(self._key.public_key())

    def decrypt(self, ciphertext: bytes,
                padding: AsymmetricPadding) -> bytes: pass

    def serialize(self, password: str = None) -> bytes:
        if password:
            enc = BestAvailableEncryption(password=password.encode())
        else:
            enc = NoEncryption()
        return self.underlying_key.private_bytes(encoding=Encoding.PEM,
                                                 format=PrivateFormat.PKCS8,
                                                 encryption_algorithm=enc)

    @property
    def key_size(self) -> int:
        return self.key.key_size

    @property
    def underlying_key(self):
        return self._key


class RsaKeyMinter(implements(KeyMinter)):
    """Used to create an RSA key
    """

    def prepare_mint_args(
            self,
            key_size: int = CONST_DEFAULT_KEY_SIZE,
            key_public_exponent: int = CONST_DEFAULT_KEY_PUBLIC_EXPONENT) -> dict:
        """Sets up the minting arguments

        :param key_size: the key size in bits, defaults to CONST_DEFAULT_KEY_SIZE
        :type key_size: int, optional
        :param key_public_exponent: an attribute in key generation, defaults to CONST_DEFAULT_KEY_PUBLIC_EXPONENT
        :type key_public_exponent: int, optional
        :return: a set of parameters to pass to :meth:`mint`
        :rtype: dict
        """
        return {
            'key_size': key_size,
            'key_public_exponent': key_public_exponent
        }

    def mint(self,
             **kwargs) -> PrivateKey:
        """Generates an RSA key

        Use :meth:`prepare_mint_args` to prepare the ``**kwargs``

        :return: an RSA private key
        :rtype: PrivateKey
        """

        key_public_exponent = kwargs.get(
            'key_public_exponent', CONST_DEFAULT_KEY_PUBLIC_EXPONENT)
        key_size = kwargs.get('key_size', CONST_DEFAULT_KEY_SIZE)

        key = RsaPrivateKey(rsa.generate_private_key(
            public_exponent=key_public_exponent,
            key_size=key_size,
            backend=default_backend()
        ))
        return key
