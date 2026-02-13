# Quick Start Guide

## Prerequisites

- Python 3.8+
- MongoDB running
- OpenSSL installed

## Setup (Windows)

```powershell
# Run the automated setup script
.\setup.ps1

# Or manually:
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\generate_certs.ps1
cp .env.example .env
# Edit .env with your settings
```

## Setup (Linux/Mac)

```bash
# Run the automated setup script
chmod +x setup.sh
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x generate_certs.sh
./generate_certs.sh
cp .env.example .env
# Edit .env with your settings
```

## Run

```bash
python app.py
```

Visit: http://localhost:5000

## Test Flow

### 1. Register a Passkey

1. Go to http://localhost:5000
2. Enter email: `test@example.com`
3. Click "Get Registration Link"
4. Click the generated magic link
5. Click "Create Passkey"
6. Follow browser prompts to create passkey

### 2. Test Authentication

1. Go to http://localhost:5000/auth/passkey
2. Enter email: `test@example.com`
3. Click "Sign In with Passkey"
4. Use your passkey to authenticate

### 3. Test SAML Flow

To test with a real Service Provider:

1. Configure your SP to use: `http://localhost:5000/saml/metadata`
2. Initiate login from SP
3. You'll be redirected to IdP for authentication
4. Use your passkey
5. You'll be redirected back to SP with SAML assertion

## Environment Variables

Key settings in `.env`:

```env
# MongoDB connection
MONGODB_URI=mongodb://localhost:27017/
DB_NAME=saml_passkey_idp

# Security
SECRET_KEY=generate-a-random-secret-key

# WebAuthn/Passkey settings
RP_ID=localhost
RP_NAME=SAML Passkey IdP

# Base URL (must be HTTPS in production!)
BASE_URL=http://localhost:5000
```

## Troubleshooting

### Port 5000 already in use

```bash
# Change port in app.py or set environment variable
export FLASK_RUN_PORT=5001
```

### MongoDB not running

```bash
# Windows (if installed as service)
net start MongoDB

# Linux
sudo systemctl start mongod

# Mac
brew services start mongodb-community
```

### Certificate errors

```bash
# Regenerate certificates
rm -rf saml_certs
./generate_certs.sh  # or .\generate_certs.ps1 on Windows
```

## API Quick Reference

| Endpoint                        | Method   | Description               |
| ------------------------------- | -------- | ------------------------- |
| `/`                             | GET      | Home page                 |
| `/saml/metadata`                | GET      | SAML IdP metadata         |
| `/saml/sso`                     | GET/POST | SAML SSO endpoint         |
| `/auth/passkey`                 | GET      | Passkey auth page         |
| `/register-passkey`             | GET      | Passkey registration page |
| `/magic-link/generate`          | POST     | Generate magic link       |
| `/api/passkey/register/options` | POST     | Get registration options  |
| `/api/passkey/register/verify`  | POST     | Verify registration       |
| `/api/passkey/auth/options`     | POST     | Get auth options          |
| `/api/passkey/auth/verify`      | POST     | Verify authentication     |

## Production Checklist

- [ ] Use HTTPS (required for WebAuthn)
- [ ] Set strong `SECRET_KEY`
- [ ] Secure MongoDB with authentication
- [ ] Use proper SSL certificates (not self-signed)
- [ ] Implement email sending for magic links
- [ ] Add rate limiting
- [ ] Use Redis for session/challenge storage
- [ ] Enable audit logging
- [ ] Configure CORS properly
- [ ] Set up monitoring and alerts
