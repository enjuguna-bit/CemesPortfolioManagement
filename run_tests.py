"""
Test runner script
Runs all integration tests and generates coverage report
"""
import sys
import pytest


def run_tests():
    """Run all tests with coverage"""
    args = [
        'tests/',
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--cov=.',  # Coverage for all modules
        '--cov-report=html',  # HTML coverage report
        '--cov-report=term-missing',  # Terminal report with missing lines
        '-x',  # Stop on first failure
    ]
    
    return pytest.main(args)


if __name__ == '__main__':
    sys.exit(run_tests())
