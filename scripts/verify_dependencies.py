#!/usr/bin/env python3
"""
Dependency Verification Script for real-intent SDK.
Run this after updating dependencies to verify everything works.

Usage:
    python scripts/verify_dependencies.py

With BigDBM credentials (for full test):
    CLIENT_ID=xxx CLIENT_SECRET=xxx python scripts/verify_dependencies.py
"""

import sys
import os
from importlib.metadata import version, PackageNotFoundError

# ============================================================================
# 1. Check Package Versions
# ============================================================================

EXPECTED_PACKAGES = {
    "pydantic": "2.12.0",
    "pandas": "2.0.0",
    "requests": "2.32.0",
    "logfire": "4.0.0",
    "openai": "2.14.0",
    "anthropic": "0.75.0",
    "httpx": "0.27.0",
    "pymongo": "4.16.0",
    "reportlab": "4.4.2",
}

def check_package_versions():
    """Check that all packages meet minimum version requirements."""
    print("\n📦 Checking Package Versions...")
    print("-" * 50)
    
    all_ok = True
    for package, min_version in EXPECTED_PACKAGES.items():
        try:
            installed = version(package)
            # Simple version comparison (works for most cases)
            installed_parts = [int(x) for x in installed.split(".")[:3]]
            min_parts = [int(x) for x in min_version.split(".")[:3]]
            
            if installed_parts >= min_parts:
                print(f"  ✅ {package}: {installed} (>= {min_version})")
            else:
                print(f"  ❌ {package}: {installed} (expected >= {min_version})")
                all_ok = False
        except PackageNotFoundError:
            print(f"  ⚠️  {package}: NOT INSTALLED")
            all_ok = False
        except ValueError:
            # Version parsing failed, just show what's installed
            print(f"  ℹ️  {package}: {installed} (couldn't compare)")
    
    return all_ok

# ============================================================================
# 2. Import Tests
# ============================================================================

def check_imports():
    """Try importing all major modules."""
    print("\n📥 Checking Imports...")
    print("-" * 50)
    
    imports = [
        ("real_intent.client", "BigDBMClient"),
        ("real_intent.schemas", "IABJob, PII, MD5WithPII"),
        ("real_intent.process.fill", "FillProcessor"),
        ("real_intent.deliver.csv", "CSVStringFormatter"),
        ("real_intent.validate.simple", "ContactableValidator"),
        ("real_intent.validate.pii", "HighIncomeValidator"),
        ("real_intent.validate.email", "EmailValidator"),
        ("real_intent.taxonomy", "code_to_category"),
    ]
    
    all_ok = True
    for module, items in imports:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            all_ok = False
    
    return all_ok

# ============================================================================
# 3. Functional Tests
# ============================================================================

def test_pydantic_schemas():
    """Test Pydantic schema functionality."""
    print("\n🔧 Testing Pydantic Schemas...")
    print("-" * 50)
    
    try:
        from real_intent.schemas import PII, IABJob
        
        # Test PII.create_fake()
        fake_pii = PII.create_fake(seed=42)
        assert fake_pii.first_name is not None
        print(f"  ✅ PII.create_fake() works: {fake_pii.first_name} {fake_pii.last_name}")
        
        # Test IABJob creation
        job = IABJob(
            intent_categories=["In-Market>Real Estate>First-Time Home Buyer"],
            zips=["90210"],
            n_hems=10
        )
        assert job.n_hems == 10
        print(f"  ✅ IABJob creation works: {job.n_hems} hems")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_csv_formatter():
    """Test CSV formatting with pandas."""
    print("\n📄 Testing CSV Formatter...")
    print("-" * 50)
    
    try:
        from real_intent.schemas import PII, MD5WithPII
        from real_intent.deliver.csv import CSVStringFormatter
        
        # Create test data
        pii = PII.create_fake(seed=123)
        md5_with_pii = MD5WithPII(
            md5="abc123def456",
            sentences=["Real Estate", "First-Time Buyer"],
            raw_sentences=["Real Estate", "First-Time Buyer"],
            pii=pii
        )
        
        # Format to CSV
        formatter = CSVStringFormatter()
        csv_output = formatter.deliver([md5_with_pii])
        
        assert len(csv_output) > 0
        assert "first_name" in csv_output.lower() or pii.first_name.lower() in csv_output.lower()
        print(f"  ✅ CSV generation works: {len(csv_output)} bytes")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_taxonomy():
    """Test IAB taxonomy lookup."""
    print("\n🏷️  Testing Taxonomy...")
    print("-" * 50)
    
    try:
        from real_intent.taxonomy import code_to_category, category_to_code
        
        # Test code to category
        category = code_to_category(1)
        assert category == "Automotive"
        print(f"  ✅ code_to_category(1) = '{category}'")
        
        # Test category to code
        code = category_to_code("Automotive")
        assert code == 1
        print(f"  ✅ category_to_code('Automotive') = {code}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_bigdbm_client():
    """Test BigDBM client (requires credentials)."""
    print("\n🔑 Testing BigDBM Client...")
    print("-" * 50)
    
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("  ⏭️  Skipped (no CLIENT_ID/CLIENT_SECRET env vars)")
        return True  # Not a failure, just skipped
    
    try:
        from real_intent.client import BigDBMClient
        
        client = BigDBMClient(
            client_id=client_id,
            client_secret=client_secret
        )
        print("  ✅ BigDBMClient authentication successful")
        
        # Test config dates
        dates = client.get_config_dates()
        print(f"  ✅ Config dates: {dates.start_date} to {dates.end_date}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 60)
    print("  real-intent Dependency Verification Script")
    print("=" * 60)
    
    results = []
    
    results.append(("Package Versions", check_package_versions()))
    results.append(("Imports", check_imports()))
    results.append(("Pydantic Schemas", test_pydantic_schemas()))
    results.append(("CSV Formatter", test_csv_formatter()))
    results.append(("Taxonomy", test_taxonomy()))
    results.append(("BigDBM Client", test_bigdbm_client()))
    
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All checks passed! Dependencies are working correctly.\n")
        sys.exit(0)
    else:
        print("\n⚠️  Some checks failed. Review the output above.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
