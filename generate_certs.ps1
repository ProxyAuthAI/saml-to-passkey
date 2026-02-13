# PowerShell script to generate SAML certificates

# Create directory for SAML certificates
New-Item -ItemType Directory -Force -Path saml_certs | Out-Null

# Generate private key
openssl genrsa -out saml_certs/idp_key.pem 2048

# Generate self-signed certificate (valid for 10 years)
openssl req -new -x509 -key saml_certs/idp_key.pem -out saml_certs/idp_cert.pem -days 3650 -subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=localhost"

Write-Host "SAML certificates generated successfully!"
