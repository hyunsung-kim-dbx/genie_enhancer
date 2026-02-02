"""Validation script to test setup and imports."""

import sys
import os
from pathlib import Path

# Change to project root directory (parent of scripts/)
project_root = Path(__file__).parent.parent
os.chdir(project_root)
# Add project root to Python path for imports
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import pydantic
        print("  ✓ pydantic")
    except ImportError as e:
        print(f"  ✗ pydantic: {e}")
        return False
    
    try:
        import requests
        print("  ✓ requests")
    except ImportError as e:
        print(f"  ✗ requests: {e}")
        return False
    
    try:
        import dotenv
        print("  ✓ python-dotenv")
    except ImportError as e:
        print(f"  ✗ python-dotenv: {e}")
        return False
    
    try:
        from genie import models
        print("  ✓ src.models")
    except ImportError as e:
        print(f"  ✗ src.models: {e}")
        return False
    
    try:
        from genie.prompt import prompt_builder
        print("  ✓ src.prompt.prompt_builder")
    except ImportError as e:
        print(f"  ✗ src.prompt.prompt_builder: {e}")
        return False
    
    try:
        from genie.llm import databricks_llm
        print("  ✓ src.llm.databricks_llm")
    except ImportError as e:
        print(f"  ✗ src.llm.databricks_llm: {e}")
        return False
    
    try:
        from genie.api import genie_space_client
        print("  ✓ src.api.genie_space_client")
    except ImportError as e:
        print(f"  ✗ src.api.genie_space_client: {e}")
        return False
    
    print()
    return True


def test_files():
    """Test that required files exist."""
    print("Testing required files...")
    
    required_files = [
        "genie.py",
        "scripts/validate_setup.py",
        "requirements.txt",
        ".env.example",
        "src/prompt/templates/curate_effective_genie.md",
        "src/prompt/templates/genie_api.md",
        "data/demo_requirements.md",
        "src/__init__.py",
        "src/models.py",
        "src/prompt_builder.py",
        "src/databricks_llm.py",
        "src/genie_space_client.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        exists = Path(file_path).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False
    
    print()
    return all_exist


def test_env_file():
    """Test environment file."""
    print("Testing environment configuration...")
    
    env_example_exists = Path(".env.example").exists()
    env_exists = Path(".env").exists()
    
    if env_example_exists:
        print("  ✓ .env.example exists")
    else:
        print("  ✗ .env.example not found")
    
    if env_exists:
        print("  ✓ .env exists")
        from dotenv import load_dotenv
        load_dotenv()
        
        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")
        
        if host and host != "https://your-workspace.databricks.com":
            print("  ✓ DATABRICKS_HOST is set")
        else:
            print("  ⚠ DATABRICKS_HOST not configured (using example value)")
        
        if token and token != "your-personal-access-token":
            print("  ✓ DATABRICKS_TOKEN is set")
        else:
            print("  ⚠ DATABRICKS_TOKEN not configured (using example value)")
    else:
        print("  ⚠ .env not found (copy from .env.example and configure)")
    
    print()
    return True


def test_client_initialization():
    """Test that clients can be initialized (without making API calls)."""
    print("Testing client initialization...")
    
    try:
        from genie.api.genie_space_client import GenieSpaceClient
        
        # Try to initialize with explicit credentials (won't make any API calls)
        try:
            client = GenieSpaceClient(
                databricks_host="https://test.databricks.com",
                databricks_token="test-token"
            )
            print("  ✓ GenieSpaceClient initialization")
        except ValueError as e:
            print(f"  ✗ GenieSpaceClient initialization: {e}")
            return False
        
        # Check that URLs are constructed correctly
        expected_base = "https://test.databricks.com/api/2.0/genie/spaces"
        if client.api_base == expected_base:
            print(f"  ✓ API base URL: {client.api_base}")
        else:
            print(f"  ✗ API base URL incorrect: {client.api_base} (expected: {expected_base})")
            return False
        
    except Exception as e:
        print(f"  ✗ Client initialization failed: {e}")
        return False
    
    print()
    return True


def test_config_file():
    """Test that the generated config file exists and is valid."""
    print("Testing configuration file...")
    
    config_path = Path("output/genie_space_config.json")
    
    if not config_path.exists():
        print(f"  ⚠ {config_path} not found (generate it with main.py)")
        print()
        return True  # Not a failure, just not generated yet
    
    print(f"  ✓ {config_path} exists")
    
    try:
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("  ✓ Valid JSON format")
        
        if "genie_space_config" in config:
            print("  ✓ Contains 'genie_space_config'")
            
            genie_config = config["genie_space_config"]
            
            # Check key fields
            required_fields = ["space_name", "description", "tables", "warehouse_id"]
            for field in required_fields:
                if field in genie_config:
                    print(f"  ✓ Has '{field}'")
                else:
                    print(f"  ✗ Missing '{field}'")
            
            # Check warehouse_id
            warehouse_id = genie_config.get("warehouse_id")
            if warehouse_id and warehouse_id != "REPLACE_WITH_YOUR_SQL_WAREHOUSE_ID":
                print("  ✓ warehouse_id is configured")
            else:
                print("  ⚠ warehouse_id needs to be set before creating space")
        else:
            print("  ✗ Missing 'genie_space_config' key")
    
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error reading config: {e}")
        return False
    
    print()
    return True


def main():
    """Run all validation tests."""
    print("=" * 80)
    print("Setup Validation")
    print("=" * 80)
    print()
    
    results = []
    
    # Run all tests
    results.append(("Imports", test_imports()))
    results.append(("Required Files", test_files()))
    results.append(("Environment", test_env_file()))
    results.append(("Client Initialization", test_client_initialization()))
    results.append(("Configuration File", test_config_file()))
    
    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    
    all_passed = all(result for _, result in results)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {status}: {name}")
    
    print()
    
    if all_passed:
        print("✓ All validation tests passed!")
        print()
        print("Next steps:")
        print("  1. Configure .env with your Databricks credentials")
        print("  2. Run: genie.py create --requirements data/demo_requirements.md")
        print("     Or step-by-step:")
        print("       - genie.py generate --requirements data/demo_requirements.md")
        print("       - genie.py validate")
        print("       - genie.py deploy")
        print()
        return 0
    else:
        print("✗ Some validation tests failed. Please fix the issues above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
