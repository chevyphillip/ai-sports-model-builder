#!/usr/bin/env python
"""Test runner script with different configurations."""
import subprocess
import sys
import argparse
from pathlib import Path
from src.core.logger import logger


def run_tests(args: argparse.Namespace) -> bool:
    """Run tests with specified configuration."""
    pytest_args = ["pytest"]

    # Add coverage options
    if args.coverage:
        pytest_args.extend(
            ["--cov=src", "--cov-report=term-missing", "--cov-report=html"]
        )

    # Add test selection options
    if args.smoke:
        pytest_args.append("-m smoke")
    elif args.unit:
        pytest_args.append("-m unit")
    elif args.integration:
        pytest_args.append("-m integration")

    # Add verbosity
    if args.verbose:
        pytest_args.append("-v")

    # Add parallel execution
    if args.parallel:
        pytest_args.extend(["-n", "auto"])

    # Add test output
    if args.output:
        pytest_args.extend(["--junitxml", f"test-results/{args.output}.xml"])

    try:
        logger.info(f"Running tests with arguments: {' '.join(pytest_args)}")
        result = subprocess.run(pytest_args, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Tests failed with exit code: {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return False


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Run tests with different configurations"
    )

    # Test selection options
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--smoke", action="store_true", help="Run only smoke tests")
    group.add_argument("--unit", action="store_true", help="Run only unit tests")
    group.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )

    # Test execution options
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--parallel", "-n", action="store_true", help="Run tests in parallel"
    )
    parser.add_argument("--output", "-o", help="Output file name for test results")

    args = parser.parse_args()

    # Create test results directory if needed
    if args.output:
        Path("test-results").mkdir(exist_ok=True)

    success = run_tests(args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
