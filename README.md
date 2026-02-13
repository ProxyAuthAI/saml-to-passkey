# SAML 2.0 Identity Provider with Passkey Authentication

A simple Python-based SAML 2.0 Identity Provider that uses passkeys (WebAuthn) for passwordless authentication instead of traditional username/password authentication.

## Features

- 🔐 **Passkey Authentication**: Uses WebAuthn/FIDO2 for secure, passwordless authentication
- 🎫 **SAML 2.0 IdP**: Full SAML 2.0 Identity Provider implementation using PySAML2
- 🔗 **Magic Link Registration**: Users receive a magic link to register their passkeys
- 💾 **MongoDB Storage**: Stores user data and passkey credentials in MongoDB
- 🎨 **Clean UI**: Simple, modern web interface for registration and authentication
- 🚀 **Easy Setup**: Minimal configuration required

## Architecture

1. **User Registration Flow**:
   - User requests a magic link via email
   - System generates a time-limited token
   - User clicks the magic link and registers their passkey
   - Passkey is stored in MongoDB

2. **SAML Authentication Flow**:
   - Service Provider initiates SAML request to IdP
   - IdP presents passkey authentication page
   - User authenticates with their passkey
   - IdP generates SAML response and redirects back to SP

## Requirements

- Python 3.8+
- MongoDB (local or remote)
- OpenSSL (for generating SAML certificates)

## Installation

### 1. Clone the repository or navigate to the project directory

```bash
cd c:\Projects\authcompany\saml-to-passkey
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**

```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Generate SAML certificates

**Windows (PowerShell):**

```powershell
.\generate_certs.ps1
```

**Linux/Mac:**

```bash
chmod +x generate_certs.sh
./generate_certs.sh
```

### 6. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and configure:

```env
MONGODB_URI=mongodb://localhost:27017/
DB_NAME=saml_passkey_idp
SECRET_KEY=your-random-secret-key-change-this
RP_ID=localhost
RP_NAME=SAML Passkey IdP
BASE_URL=http://localhost:5000
```

**Important**: Change `SECRET_KEY` to a random string in production!

### 7. Start MongoDB

Make sure MongoDB is running on your system:

**Windows:**

```powershell
# If installed as a service, it should already be running
# Otherwise, start it manually:
mongod
```

**Linux:**

```bash
sudo systemctl start mongod
```

**Mac:**

```bash
brew services start mongodb-community
```

### 8. Run the application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Usage

### For End Users

#### 1. Register a Passkey

1. Navigate to `http://localhost:5000`
2. Enter your email address
3. Click "Get Registration Link"
4. Click the generated magic link
5. Click "Create Passkey" and follow your browser's prompts
6. Your passkey is now registered!

#### 2. Authenticate with Passkey

1. When accessing a SAML-protected application, you'll be redirected to the IdP
2. Enter your email address on the authentication page
3. Use your passkey (fingerprint, face recognition, or security key)
4. You'll be authenticated and redirected back to the application

### For Developers

#### SAML Metadata

The IdP metadata is available at:

```
http://localhost:5000/saml/metadata
```

Configure your SAML Service Provider to use this metadata URL.

#### SAML SSO Endpoint

```
http://localhost:5000/saml/sso
```

#### Testing Without a Service Provider

You can test the passkey authentication directly:

1. Navigate to `http://localhost:5000/auth/passkey`
2. Enter your email and authenticate
3. You'll see a success message

## Project Structure

```
saml-to-passkey/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── database.py                 # MongoDB database wrapper
├── saml_config.py              # SAML IdP configuration
├── saml_handler.py             # SAML request/response handling
├── passkey_manager.py          # WebAuthn/Passkey operations
├── requirements.txt            # Python dependencies
├── .env.example               # Example environment variables
├── generate_certs.sh          # Certificate generation (Linux/Mac)
├── generate_certs.ps1         # Certificate generation (Windows)
├── saml_certs/                # SAML signing certificates
│   ├── idp_key.pem
│   └── idp_cert.pem
├── saml_attribute_maps/       # SAML attribute mappings
│   └── basic.py
└── templates/                 # HTML templates
    ├── base.html
    ├── index.html
    ├── register_passkey.html
    ├── authenticate_passkey.html
    └── saml_post.html
```

## Database Schema

### Users Collection

```json
{
  "_id": ObjectId,
  "email": "user@example.com",
  "user_id": "unique-user-id",
  "passkey_credentials": [
    {
      "credential_id": "hex-encoded-credential-id",
      "public_key": "hex-encoded-public-key",
      "sign_count": 0,
      "credential_type": "public-key",
      "credential_device_type": "platform",
      "credential_backed_up": false
    }
  ],
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### Sessions Collection

```json
{
  "_id": ObjectId,
  "session_id": "session-token",
  "user_id": "user-id",
  "saml_request": {},
  "created_at": ISODate,
  "expires_at": ISODate,
  "authenticated": false
}
```

## Security Considerations

### For Production Deployment

1. **Use HTTPS**: Passkeys require HTTPS in production
2. **Strong Secret Key**: Use a cryptographically strong secret key
3. **Secure MongoDB**: Use authentication and secure your MongoDB instance
4. **Valid Certificates**: Use proper SSL/TLS certificates, not self-signed
5. **Environment Variables**: Never commit `.env` file to version control
6. **Rate Limiting**: Implement rate limiting on authentication endpoints
7. **Session Management**: Use secure session storage (Redis, etc.)
8. **Email Validation**: Implement proper email sending and validation
9. **Logging**: Add audit logging for authentication attempts
10. **CORS**: Configure CORS properly for your domain

## Browser Support

Passkeys require modern browsers with WebAuthn support:

- ✅ Chrome 67+
- ✅ Firefox 60+
- ✅ Safari 13+
- ✅ Edge 18+

## Troubleshooting

### "Challenge not found or expired"

Challenges are stored in memory and expire quickly. Make sure to complete the registration/authentication flow without long delays.

For production, store challenges in Redis with proper expiration.

### "MongoDB connection failed"

Make sure MongoDB is running and accessible at the configured URI.

### "OpenSSL not found"

Install OpenSSL:

- **Windows**: Download from https://slproweb.com/products/Win32OpenSSL.html
- **Linux**: `sudo apt-get install openssl`
- **Mac**: `brew install openssl`

### Passkey not working

- Ensure you're using HTTPS in production (required by WebAuthn)
- Check browser console for errors
- Verify your device supports passkeys/biometric authentication

## Development

To run in development mode with auto-reload:

```bash
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows CMD
$env:FLASK_ENV="development"  # Windows PowerShell

python app.py
```

## API Endpoints

### Public Endpoints

- `GET /` - Home page
- `GET /saml/metadata` - SAML IdP metadata
- `GET /saml/sso` - SAML SSO endpoint (HTTP-Redirect)
- `POST /saml/sso` - SAML SSO endpoint (HTTP-POST)
- `GET /auth/passkey` - Passkey authentication page
- `GET /register-passkey` - Passkey registration page (requires token)

### API Endpoints

- `POST /magic-link/generate` - Generate magic link for registration
- `POST /api/passkey/register/options` - Get passkey registration options
- `POST /api/passkey/register/verify` - Verify passkey registration
- `POST /api/passkey/auth/options` - Get passkey authentication options
- `POST /api/passkey/auth/verify` - Verify passkey authentication

## License

MIT License - feel free to use this project for your own purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- SAML implementation using [PySAML2](https://github.com/IdentityPython/pysaml2)
- WebAuthn/Passkey support via [py_webauthn](https://github.com/duo-labs/py_webauthn)
- Database with [MongoDB](https://www.mongodb.com/)
