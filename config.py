import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DB_NAME = os.getenv('DB_NAME', 'saml_passkey_idp')

    # WebAuthn/Passkey configuration
    RP_ID = os.getenv('RP_ID', 'localhost')
    RP_NAME = os.getenv('RP_NAME', 'SAML Passkey IdP')
    RP_EXPECTED_ORIGIN = os.getenv('BASE_URL', 'http://localhost:5000')

    # SAML configuration
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    SAML_IDP_ENTITY_ID = f"{BASE_URL}/saml/metadata"
    SAML_IDP_SSO_URL = f"{BASE_URL}/saml/sso"

    # Magic link expiration (in seconds)
    MAGIC_LINK_EXPIRATION = 3600  # 1 hour
