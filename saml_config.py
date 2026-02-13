from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from saml2.saml import NAMEID_FORMAT_UNSPECIFIED
from saml2.sigver import get_xmlsec_binary
from config import Config


def get_saml_config():
    """Generate SAML IdP configuration"""

    config = {
        'entityid': Config.SAML_IDP_ENTITY_ID,
        'service': {
            'idp': {
                'name': 'SAML Passkey IdP',
                'endpoints': {
                    'single_sign_on_service': [
                        (Config.SAML_IDP_SSO_URL, BINDING_HTTP_REDIRECT),
                        (Config.SAML_IDP_SSO_URL, BINDING_HTTP_POST),
                    ],
                },
                'name_id_format': [NAMEID_FORMAT_UNSPECIFIED],
                'sign_response': True,
                'sign_assertion': True,
                'want_authn_requests_signed': False,
            },
        },
        'key_file': './saml_certs/idp_key.pem',
        'cert_file': './saml_certs/idp_cert.pem',
        'xmlsec_binary': get_xmlsec_binary(['/usr/bin', '/usr/local/bin', 'C:\\xmlsec\\xmlsec\\bin']),
        'encryption_keypairs': [{
            'key_file': './saml_certs/idp_key.pem',
            'cert_file': './saml_certs/idp_cert.pem',
        }],
        'attribute_map_dir': './saml_attribute_maps',
        'metadata': {
            'local': [],
        },
    }

    return config
