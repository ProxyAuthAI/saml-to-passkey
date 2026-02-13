#!/bin/bash

# Create directory for SAML certificates
mkdir -p saml_certs

# Generate private key
openssl genrsa -out saml_certs/idp_key.pem 2048

# Generate self-signed certificate (valid for 10 years)
openssl req -new -x509 -key saml_certs/idp_key.pem -out saml_certs/idp_cert.pem -days 3650 \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=IT/CN=localhost"

echo "SAML certificates generated successfully!"
