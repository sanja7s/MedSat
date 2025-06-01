#!/bin/bash
# Run NHS Prescription Parser test suite

echo "🧪 NHS Prescription Parser Test Suite"
echo "====================================="

# Check if we're in the right directory
if [ ! -d "tests" ]; then
    echo "❌ Error: tests directory not found. Run this script from the code/ directory."
    exit 1
fi

# Activate environment
echo "🔄 Activating environment..."
source ../venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to activate virtual environment."
    echo "   Make sure to run bootstrap.sh first to set up the environment."
    exit 1
fi

echo "✅ Virtual environment activated"

# Check if required packages are available
echo ""
echo "📦 Checking test dependencies..."
python -c "
import sys
packages = ['pandas', 'numpy', 'unittest']
missing = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f'  ✅ {pkg}')
    except ImportError:
        print(f'  ❌ {pkg} (missing)')
        missing.append(pkg)

if missing:
    print(f'\n❌ Missing packages: {missing}')
    sys.exit(1)
else:
    print('\n✅ All test dependencies available')
"

if [ $? -ne 0 ]; then
    echo "❌ Error: Missing required packages for testing."
    exit 1
fi

# Run the test suite
echo ""
echo "🏃 Running test suite..."
echo "========================"

python -m unittest discover tests -v

test_result=$?

echo ""
if [ $test_result -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed (exit code: $test_result)"
fi

echo ""
echo "📊 Test Summary:"
echo "   Test runner: python -m unittest discover tests -v"
echo "   Test directory: $(pwd)/tests"
echo "   Python executable: $(which python)"

deactivate
exit $test_result