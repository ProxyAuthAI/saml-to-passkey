import secrets
import json
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from config import Config


class PasskeyManager:
    def __init__(self):
        self.rp_id = Config.RP_ID
        self.rp_name = Config.RP_NAME
        self.expected_origin = Config.RP_EXPECTED_ORIGIN

    def generate_registration_options(self, user_id, email, existing_credentials=None):
        """Generate options for passkey registration"""

        # Exclude existing credentials to prevent duplicate registrations
        exclude_credentials = []
        if existing_credentials:
            for cred in existing_credentials:
                exclude_credentials.append(
                    PublicKeyCredentialDescriptor(
                        id=bytes.fromhex(cred['credential_id']))
                )

        options = generate_registration_options(
            rp_id=self.rp_id,
            rp_name=self.rp_name,
            user_id=user_id.encode('utf-8'),
            user_name=email,
            user_display_name=email,
            exclude_credentials=exclude_credentials,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.REQUIRED,
                user_verification=UserVerificationRequirement.PREFERRED,
            ),
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier.ECDSA_SHA_256,
                COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
            ],
        )

        return options

    def verify_registration(self, credential, challenge):
        """Verify passkey registration response"""
        try:
            verification = verify_registration_response(
                credential=credential,
                expected_challenge=challenge,
                expected_rp_id=self.rp_id,
                expected_origin=self.expected_origin,
            )

            # Return credential data to store
            return {
                'credential_id': verification.credential_id.hex(),
                'public_key': verification.credential_public_key.hex(),
                'sign_count': verification.sign_count,
                'credential_type': verification.credential_type,
                'credential_device_type': verification.credential_device_type,
                'credential_backed_up': verification.credential_backed_up,
            }
        except Exception as e:
            print(f"Registration verification failed: {e}")
            return None

    def generate_authentication_options(self, user_credentials=None):
        """Generate options for passkey authentication"""

        allow_credentials = None
        if user_credentials:
            allow_credentials = []
            for cred in user_credentials:
                allow_credentials.append(
                    PublicKeyCredentialDescriptor(
                        id=bytes.fromhex(cred['credential_id']))
                )

        options = generate_authentication_options(
            rp_id=self.rp_id,
            allow_credentials=allow_credentials,
            user_verification=UserVerificationRequirement.PREFERRED,
        )

        return options

    def verify_authentication(self, credential, challenge, credential_data):
        """Verify passkey authentication response"""
        try:
            verification = verify_authentication_response(
                credential=credential,
                expected_challenge=challenge,
                expected_rp_id=self.rp_id,
                expected_origin=self.expected_origin,
                credential_public_key=bytes.fromhex(
                    credential_data['public_key']),
                credential_current_sign_count=credential_data['sign_count'],
                require_user_verification=False,
            )

            return {
                'verified': True,
                'new_sign_count': verification.new_sign_count,
            }
        except Exception as e:
            print(f"Authentication verification failed: {e}")
            return {'verified': False}


# Global passkey manager instance
passkey_manager = PasskeyManager()
