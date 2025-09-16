#!/bin/bash
# Setup script for AWS CDK environment

set -e

echo "Setting up AWS CDK environment for Total Life AI..."

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✅ Python3 found: $(python3 --version)"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "✅ Python found: $(python --version)"
else
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip

# Install requirements
echo "📚 Installing CDK dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt

# Verify installations
echo "✅ Verifying installations..."
$PYTHON_CMD -c "import aws_cdk; print(f'AWS CDK: {aws_cdk.__version__}')" || exit 1
$PYTHON_CMD -c "import constructs; print(f'Constructs: {constructs.__version__}')" || exit 1

echo ""
echo "🎉 CDK environment setup complete!"
echo "Testing CDK configuration..."

# Test CDK synth
if cdk synth --quiet > /dev/null 2>&1; then
    echo "✅ CDK synthesis test passed!"
else
    echo "⚠️ CDK synthesis test failed - check your configuration"
fi

echo ""
echo "You can now run: cdk synth or cdk deploy"
