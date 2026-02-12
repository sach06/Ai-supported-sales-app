"""
Test script to verify dashboard implementation
Checks that all required components are properly configured
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_data_service_constants():
    """Test that data service has required constants"""
    from app.services.data_service import data_service
    
    print("Testing data_service constants...")
    
    # Test FIXED_EQUIPMENT_LIST
    assert hasattr(data_service, 'FIXED_EQUIPMENT_LIST'), "Missing FIXED_EQUIPMENT_LIST"
    assert len(data_service.FIXED_EQUIPMENT_LIST) == 38, f"Expected 38 equipment types, got {len(data_service.FIXED_EQUIPMENT_LIST)}"
    print(f"✓ FIXED_EQUIPMENT_LIST has {len(data_service.FIXED_EQUIPMENT_LIST)} items")
    
    # Test REGION_OPTIONS
    assert hasattr(data_service, 'REGION_OPTIONS'), "Missing REGION_OPTIONS"
    expected_regions = ["Americas", "APAC & MEA", "China", "Commonwealth", "Europe", "Not assigned"]
    assert data_service.REGION_OPTIONS == expected_regions, f"Region options mismatch"
    print(f"✓ REGION_OPTIONS has {len(data_service.REGION_OPTIONS)} items")
    
    # Test methods exist
    assert hasattr(data_service, 'get_all_countries'), "Missing get_all_countries method"
    assert hasattr(data_service, 'get_detailed_plant_data'), "Missing get_detailed_plant_data method"
    assert hasattr(data_service, 'get_match_quality_stats'), "Missing get_match_quality_stats method"
    print("✓ All required methods exist")
    
    print("✓ Data service constants test PASSED\n")

def test_equipment_list_content():
    """Test that equipment list contains expected items"""
    from app.services.data_service import data_service
    
    print("Testing equipment list content...")
    
    expected_items = [
        "AC-Electric Arc Furnace",
        "Continuous Annealing Line",
        "Blast Furnace",
        "Wire Rod Mill",
        "Temper- / Skin Pass Mill (CR)",
        "Vacuum Degassing Plant"
    ]
    
    for item in expected_items:
        assert item in data_service.FIXED_EQUIPMENT_LIST, f"Missing equipment: {item}"
        print(f"✓ Found: {item}")
    
    print("✓ Equipment list content test PASSED\n")

def test_dashboard_imports():
    """Test that dashboard module imports correctly"""
    print("Testing dashboard imports...")
    
    try:
        from app.ui import dashboard
        print("✓ Dashboard module imported successfully")
        
        assert hasattr(dashboard, 'render'), "Missing render function"
        print("✓ Dashboard has render function")
        
        print("✓ Dashboard imports test PASSED\n")
    except Exception as e:
        print(f"✗ Dashboard import failed: {e}")
        raise

def test_match_quality_stats_structure():
    """Test that match quality stats returns correct structure"""
    from app.services.data_service import data_service
    
    print("Testing match quality stats structure...")
    
    # Initialize database (in-memory for testing)
    data_service.initialize_database()
    
    # Get stats (should return empty stats if no data)
    stats = data_service.get_match_quality_stats()
    
    assert isinstance(stats, dict), "Stats should be a dictionary"
    assert 'excellent' in stats, "Missing 'excellent' key"
    assert 'good' in stats, "Missing 'good' key"
    assert 'okay' in stats, "Missing 'okay' key"
    assert 'poor' in stats, "Missing 'poor' key"
    
    print(f"✓ Match quality stats structure: {stats}")
    print("✓ Match quality stats test PASSED\n")

def test_region_mapping():
    """Test that region mapping is properly defined"""
    from app.services.data_service import data_service
    
    print("Testing region mapping...")
    
    assert hasattr(data_service, 'REGION_MAPPING'), "Missing REGION_MAPPING"
    
    # Check that all REGION_OPTIONS (except "All" and "Not assigned") are in mapping
    for region in data_service.REGION_OPTIONS:
        if region not in ["Not assigned"]:
            assert region in data_service.REGION_MAPPING, f"Missing mapping for region: {region}"
            print(f"✓ Region mapping exists for: {region}")
    
    print("✓ Region mapping test PASSED\n")

def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("Dashboard Implementation Verification Tests")
    print("="*60 + "\n")
    
    tests = [
        test_data_service_constants,
        test_equipment_list_content,
        test_dashboard_imports,
        test_match_quality_stats_structure,
        test_region_mapping
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ Test failed: {test.__name__}")
            print(f"  Error: {e}\n")
            failed += 1
    
    print("="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n✓ All tests PASSED! Dashboard implementation is ready.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) FAILED. Please review the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
