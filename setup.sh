#!/bin/bash

echo "================================================"
echo "SAML Passkey IdP - Quick Setup Script"
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Check if MongoDB is installed
if ! command -v mongod &> /dev/null; then
    echo "⚠️  MongoDB not found in PATH. Please ensure MongoDB is installed and running."
else
    echo "✓ MongoDB found"
fi

# Check if OpenSSL is installed
if ! command -v openssl &> /dev/null; then
    echo "❌ OpenSSL is not installed. Please install OpenSSL to generate certificates."
    exit 1
fi

echo "✓ OpenSSL found: $(openssl version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Generate SAML certificates
echo "🔐 Generating SAML certificates..."
chmod +x generate_certs.sh
./generate_certs.sh
echo "✓ Certificates generated"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/your-secret-key-change-in-production/$SECRET_KEY/" .env
    echo "✓ .env file created with random secret key"
else
    echo "✓ .env file already exists"
fi
echo ""

echo "================================================"
echo "✅ Setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Make sure MongoDB is running"
echo "2. Review and adjust settings in .env file"
echo "3. Run: source venv/bin/activate"
echo "4. Run: python app.py"
echo "5. Open: http://localhost:5000"
echo ""
echo "For more information, see README.md"
