#!/bin/bash
# Quick start script for annotation tool
# Run this in WSL after setup is complete

set -e

echo "🚀 Starting Bronchoscopy Registry annotation tool..."

# Check if we're in the right directory
if [ ! -f "tools/annotate_streamlit.py" ]; then
    echo "❌ Error: Please run this script from the Test_reg directory"
    echo "   cd Test_reg"
    echo "   ./tools/start_annotation.sh"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "⚡ Activating virtual environment..."
    source venv/bin/activate
fi

# Check if dependencies are installed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "❌ Streamlit not found. Please run setup first:"
    echo "   ./tools/setup_wsl.sh"
    exit 1
fi

# Start the annotation tool
echo "🌐 Starting Streamlit annotation tool..."
echo "   URL: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""

streamlit run tools/annotate_streamlit.py
