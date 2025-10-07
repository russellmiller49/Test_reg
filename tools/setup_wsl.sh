#!/bin/bash
# WSL Setup Script for Bronchoscopy Registry Annotation
# Run this script in WSL to set up the annotation environment

set -e

echo "🚀 Setting up Bronchoscopy Registry annotation environment in WSL..."

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install Python and pip if not already installed
echo "🐍 Installing Python and pip..."
sudo apt install -y python3 python3-pip python3-venv

# Install git if not already installed
echo "📋 Installing git..."
sudo apt install -y git

# Clone repository if not already present
if [ ! -d "Test_reg" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/russellmiller49/Test_reg.git
    cd Test_reg
else
    echo "📁 Repository already exists, updating..."
    cd Test_reg
    git pull
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Install watchdog for better performance
echo "👀 Installing watchdog for better performance..."
pip install watchdog

# Verify installation
echo "✅ Verifying installation..."
python3 -c "import streamlit; print(f'Streamlit version: {streamlit.__version__}')"
python3 -c "import faker; print('Faker installed successfully')"

echo ""
echo "🎉 Setup complete! You can now run:"
echo "   cd Test_reg"
echo "   source venv/bin/activate"
echo "   streamlit run tools/annotate_streamlit.py"
echo ""
echo "🌐 The annotation tool will be available at:"
echo "   http://localhost:8501"
echo ""
echo "💡 To start annotating, run the commands above in your WSL terminal."
