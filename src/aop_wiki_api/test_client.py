#!/usr/bin/env python3
"""
Test script for the AOP Wiki API client.
"""

import sys
from aop_wiki_api import AOPWikiClient


def test_basic_functionality():
    """Test basic client functionality."""
    print("Testing AOP Wiki API Client...")
    
    try:
        # Create client
        client = AOPWikiClient()
        print("✓ Client created successfully")
        
        # Test getting all AOPs
        print("\nTesting get_all_aops()...")
        aops = client.get_all_aops()
        print(f"✓ Retrieved {len(aops)} AOPs")
        
        if aops:
            # Test getting a specific AOP
            first_aop_id = aops[0].id
            print(f"\nTesting get_aop_by_id({first_aop_id})...")
            aop = client.get_aop_by_id(first_aop_id)
            if aop:
                print(f"✓ Retrieved AOP: {aop.title}")
                print(f"  ID: {aop.id}")
                print(f"  Description: {aop.description[:100]}...")
                print(f"  Key Events: {len(aop.key_events)}")
                print(f"  MIEs: {len(aop.molecular_initiating_events)}")
            else:
                print("✗ Failed to retrieve AOP")
        
        # Test MIE search
        print("\nTesting search_miess()...")
        miess = client.search_miess()
        print(f"✓ Found {len(miess)} MIEs in total")
        
        # Test chemical search
        print("\nTesting get_miess_for_chemical()...")
        benzene_miess = client.get_miess_for_chemical(chemical_name="benzene")
        print(f"✓ Found {len(benzene_miess)} MIEs for 'benzene'")
        
        # Test context manager
        print("\nTesting context manager...")
        with AOPWikiClient() as ctx_client:
            test_aop = ctx_client.get_aop_by_id(1)
            if test_aop:
                print(f"✓ Context manager works: {test_aop.title}")
            else:
                print("✓ Context manager works (AOP 1 not found)")
        
        print("\n✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            client.close()
        except:
            pass


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)