from flask import Flask, request, render_template, redirect, jsonify, session, url_for
from werkzeug.exceptions import BadRequest
import secrets
import json
from datetime import datetime, timedelta
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url, options_to_json

from config import Config
from database import db
from saml_handler import saml_handler
from passkey_manager import passkey_manager

app = Flask(__name__)
app.config.from_object(Config)

# Store challenges temporarily (in production, use Redis or similar)
challenges = {}


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

# ============================================================================
# SAML IdP Endpoints
# ============================================================================


@app.route('/saml/metadata')
def saml_metadata():
    """SAML IdP metadata endpoint"""
    metadata = saml_handler.get_metadata()
    return metadata, 200, {'Content-Type': 'application/xml'}


@app.route('/saml/sso', methods=['GET', 'POST'])
def saml_sso():
    """SAML Single Sign-On endpoint"""
    # Determine binding (HTTP-Redirect for GET, HTTP-POST for POST)
    binding = BINDING_HTTP_POST if request.method == 'POST' else BINDING_HTTP_REDIRECT

    # Get SAML request
    if binding == BINDING_HTTP_POST:
        saml_request = request.form.get('SAMLRequest')
    else:
        saml_request = request.args.get('SAMLRequest')

    if not saml_request:
        return "Missing SAMLRequest parameter", 400

    try:
        # Parse SAML authentication request
        req_info = saml_handler.idp.parse_authn_request(saml_request, binding)

        # Store SAML request info in session
        session_id = secrets.token_urlsafe(32)
        session['saml_session_id'] = session_id
        session['saml_request'] = {
            'id': req_info.message.id,
            'destination': req_info.message.assertion_consumer_service_url,
            'issuer': req_info.message.issuer.text,
            'binding': binding,
        }

        # Redirect to passkey authentication
        return redirect(url_for('passkey_auth'))

    except Exception as e:
        print(f"Error processing SAML request: {e}")
        return f"Error processing SAML request: {str(e)}", 400

# ============================================================================
# Magic Link Endpoints
# ============================================================================


@app.route('/magic-link/generate', methods=['POST'])
def generate_magic_link():
    """Generate a magic link for passkey registration (for demo, just returns the token)"""
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    # Check if user exists, create if not
    user = db.get_user_by_email(email)
    if not user:
        user_id = secrets.token_urlsafe(16)
        user = db.create_user(email, user_id)

    # Generate magic link token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(seconds=Config.MAGIC_LINK_EXPIRATION)

    # Store token in session (in production, use database)
    db.create_session(
        session_id=token,
        user_id=user['user_id'],
        saml_request=None,
        expires_at=expires_at
    )

    # In production, you would send this link via email
    magic_link = f"{Config.BASE_URL}/register-passkey?token={token}"

    return jsonify({
        'message': 'Magic link generated (in production, this would be sent via email)',
        'magic_link': magic_link,
        'email': email
    })


@app.route('/register-passkey')
def register_passkey_page():
    """Passkey registration page (accessed via magic link)"""
    token = request.args.get('token')

    if not token:
        return "Invalid or missing token", 400

    # Verify token
    session_data = db.get_session(token)
    if not session_data or session_data['expires_at'] < datetime.utcnow():
        return "Token expired or invalid", 400

    user = db.get_user_by_id(session_data['user_id'])
    if not user:
        return "User not found", 404

    return render_template('register_passkey.html',
                           email=user['email'],
                           user_id=user['user_id'],
                           token=token)

# ============================================================================
# Passkey Registration Endpoints
# ============================================================================


@app.route('/api/passkey/register/options', methods=['POST'])
def passkey_register_options():
    """Generate passkey registration options"""
    data = request.json
    user_id = data.get('user_id')
    token = data.get('token')

    if not user_id or not token:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Verify token
    session_data = db.get_session(token)
    if not session_data or session_data['user_id'] != user_id:
        return jsonify({'error': 'Invalid token'}), 400

    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get existing credentials to exclude
    existing_creds = db.get_user_credentials(user_id)

    # Generate registration options
    options = passkey_manager.generate_registration_options(
        user_id=user_id,
        email=user['email'],
        existing_credentials=existing_creds
    )

    # Store challenge
    challenge = options.challenge
    challenges[user_id] = challenge

    return jsonify(json.loads(options_to_json(options)))


@app.route('/api/passkey/register/verify', methods=['POST'])
def passkey_register_verify():
    """Verify passkey registration"""
    data = request.json
    user_id = data.get('user_id')
    credential = data.get('credential')

    if not user_id or not credential:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Get stored challenge
    challenge = challenges.pop(user_id, None)
    if not challenge:
        return jsonify({'error': 'Challenge not found or expired'}), 400

    # Verify registration
    credential_data = passkey_manager.verify_registration(
        credential, challenge)

    if not credential_data:
        return jsonify({'error': 'Registration verification failed'}), 400

    # Store credential in database
    db.add_passkey_credential(user_id, credential_data)

    return jsonify({'success': True, 'message': 'Passkey registered successfully'})

# ============================================================================
# Passkey Authentication Endpoints
# ============================================================================


@app.route('/auth/passkey')
def passkey_auth():
    """Passkey authentication page"""
    # Check if there's a SAML session
    saml_session_id = session.get('saml_session_id')
    saml_request = session.get('saml_request')

    return render_template('authenticate_passkey.html',
                           has_saml_session=bool(saml_session_id))


@app.route('/api/passkey/auth/options', methods=['POST'])
def passkey_auth_options():
    """Generate usernameless passkey authentication options"""
    options = passkey_manager.generate_authentication_options()

    # Store challenge
    challenge = options.challenge
    challenge_key = secrets.token_urlsafe(16)
    challenges[challenge_key] = {
        'challenge': challenge
    }

    response_data = json.loads(options_to_json(options))
    response_data['challenge_key'] = challenge_key

    return jsonify(response_data)


@app.route('/api/passkey/auth/verify', methods=['POST'])
def passkey_auth_verify():
    """Verify passkey authentication"""
    data = request.json
    challenge_key = data.get('challenge_key')
    credential = data.get('credential')

    if not challenge_key or not credential:
        return jsonify({'error': 'Missing required parameters'}), 400

    # Get stored challenge
    challenge_data = challenges.pop(challenge_key, None)
    if not challenge_data:
        return jsonify({'error': 'Challenge not found or expired'}), 400

    challenge = challenge_data['challenge']

    credential_raw_id = credential.get('rawId') or credential.get('id')
    if not credential_raw_id:
        return jsonify({'error': 'Credential rawId is required'}), 400

    try:
        credential_id_hex = base64url_to_bytes(credential_raw_id).hex()
    except Exception:
        return jsonify({'error': 'Invalid credential ID format'}), 400

    user, matching_cred = db.get_user_and_credential_by_credential_id(
        credential_id_hex)
    if not user or not matching_cred:
        return jsonify({'error': 'Credential not found'}), 404

    user_id = user['user_id']
    email = user['email']

    # Verify authentication
    verification = passkey_manager.verify_authentication(
        credential, challenge, matching_cred)

    if not verification['verified']:
        return jsonify({'error': 'Authentication verification failed'}), 400

    # Update signature counter
    db.update_credential_counter(
        user_id, credential_id_hex, verification['new_sign_count'])

    # Check if there's a SAML session
    saml_session_id = session.get('saml_session_id')
    saml_request = session.get('saml_request')

    if saml_session_id and saml_request:
        # Store authenticated user in session
        session['authenticated_user'] = {
            'user_id': user_id,
            'email': email
        }
        return jsonify({
            'success': True,
            'redirect_url': url_for('saml_response')
        })

    return jsonify({
        'success': True,
        'message': 'Authentication successful',
        'user_id': user_id,
        'email': email
    })


@app.route('/saml/response')
def saml_response():
    """Generate and send SAML response after authentication"""
    saml_request = session.get('saml_request')
    authenticated_user = session.get('authenticated_user')

    if not saml_request or not authenticated_user:
        return "Invalid session", 400

    try:
        # Create SAML response
        saml_response_data = saml_handler.create_authn_response(
            user_id=authenticated_user['user_id'],
            email=authenticated_user['email'],
            request_id=saml_request['id'],
            destination=saml_request['destination'],
            sp_entity_id=saml_request['issuer']
        )

        if not saml_response_data:
            raise Exception("Failed to create SAML response")

        # Clear session
        session.pop('saml_session_id', None)
        session.pop('saml_request', None)
        session.pop('authenticated_user', None)

        # Return HTML form that auto-submits to SP
        return render_template('saml_post.html',
                               action=saml_request['destination'],
                               saml_response=saml_response_data)

    except Exception as e:
        print(f"Error creating SAML response: {e}")
        return f"Error creating SAML response: {str(e)}", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
