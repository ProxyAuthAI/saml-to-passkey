import os
import tempfile
import base64
import platform
import subprocess
from saml2 import server, sigver
from saml2.response import StatusError
from saml2.saml import NAMEID_FORMAT_UNSPECIFIED, NameID
from saml2.config import Config as Saml2Config
from saml2.metadata import create_metadata_string
from saml_config import get_saml_config


# ============================================================================
# Windows Compatibility Patch for PySAML2 / xmlsec
# ============================================================================
if platform.system() == "Windows":
    original_make_temp = sigver.make_temp

    def patched_make_temp(content, suffix="", decode=True, delete_tmpfiles=True):
        """Replacement for make_temp that closes the file so xmlsec can access it on Windows."""
        content_encoded = content.encode("utf-8") if not isinstance(content, bytes) else content
        content_raw = base64.b64decode(content_encoded) if decode else content_encoded
        
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, 'wb') as f:
            f.write(content_raw)
        
        # We need to return an object that has a .name attribute
        class TempFileProxy:
            def __init__(self, name):
                self.name = name
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                if delete_tmpfiles:
                    try: os.remove(self.name)
                    except: pass
            def close(self): pass
            def seek(self, *args): pass
            def read(self):
                with open(self.name, 'rb') as f:
                    return f.read()

        return TempFileProxy(path)

    sigver.make_temp = patched_make_temp

    # Also need to patch CryptoBackendXmlSec1._run_xmlsec to handle the output file lock
    original_run_xmlsec = sigver.CryptoBackendXmlSec1._run_xmlsec

    def patched_run_xmlsec(self, com_list, extra_args):
        """Replacement for _run_xmlsec that handles output file locking on Windows."""
        fd, ntf_path = tempfile.mkstemp(suffix=".xml")
        os.close(fd) # Close it so xmlsec can write to it
        
        try:
            # Update the command list with the new output path
            # The original code might have already added an --output, so we find and replace it
            if "--output" in com_list:
                idx = com_list.index("--output")
                com_list[idx + 1] = ntf_path
            else:
                com_list.extend(["--output", ntf_path])
                
            if self.version_nums >= (1, 3) and '--lax-key-search' not in com_list:
                com_list.extend(['--lax-key-search'])
            
            com_list += extra_args
            
            # Use shell=True on Windows can sometimes help, but let's try without first
            pof = subprocess.Popen(com_list, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            p_out, p_err = pof.communicate()
            
            if pof.returncode != 0:
                return p_out.decode(), p_err.decode(), None
            
            with open(ntf_path, 'rb') as f:
                output_data = f.read()
            
            return p_out.decode(), p_err.decode(), output_data
        finally:
            try: os.remove(ntf_path)
            except: pass

    sigver.CryptoBackendXmlSec1._run_xmlsec = patched_run_xmlsec


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
            name_id = NameID(format=NAMEID_FORMAT_UNSPECIFIED, text=email)
            resp_args = {
                'in_response_to': request_id,
                'destination': destination,
                'sp_entity_id': sp_entity_id,
                'name_id': name_id,
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
