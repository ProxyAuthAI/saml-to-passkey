from saml2 import server
from saml2.response import StatusError
from saml2.saml import NAMEID_FORMAT_UNSPECIFIED
from saml2.config import Config as Saml2Config
from saml2.metadata import create_metadata_string
from saml_config import get_saml_config
import os


class SAMLHandler:
    def __init__(self):
        self.config = Saml2Config()
        self.config.load(get_saml_config())
        self.idp = server.Server(config=self.config)

    def parse_authn_request(self, saml_request, binding):
        """Parse incoming SAML authentication request"""
        try:
            request = self.idp.parse_authn_request(saml_request, binding)
            return request
        except Exception as e:
            print(f"Error parsing SAML request: {e}")
            return None

    def create_authn_response(self, user_id, email, request_id, destination, sp_entity_id):
        """Create SAML authentication response after successful authentication"""
        try:
            # User attributes to include in SAML response
            attributes = {
                'email': [email],
                'uid': [user_id],
            }

            # Create the response
            resp_args = {
                'in_response_to': request_id,
                'destination': destination,
                'sp_entity_id': sp_entity_id,
                'name_id': email,
                'name_id_format': NAMEID_FORMAT_UNSPECIFIED,
                'authn': {
                    'class_ref': 'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport',
                    'authn_instant': None,
                },
            }

            response = self.idp.create_authn_response(
                identity=attributes,
                **resp_args
            )

            return response
        except Exception as e:
            print(f"Error creating SAML response: {e}")
            return None

    def get_metadata(self):
        """Get IdP metadata XML"""
        try:
            original_xmlsec_binary = self.config.xmlsec_binary
            self.config.xmlsec_binary = None

            metadata_xml = create_metadata_string(
                None,
                config=self.config,
                valid=365,
                sign=False,
            )

            if isinstance(metadata_xml, bytes):
                metadata_xml = metadata_xml.decode('utf-8')

            return metadata_xml
        except Exception as e:
            print(f"Error generating metadata: {e}")
            return None
        finally:
            self.config.xmlsec_binary = original_xmlsec_binary


# Global SAML handler instance
saml_handler = SAMLHandler()
