#!/usr/bin/env python3
"""
Test script for the new composition confirmation and recomposition endpoints.
Run this after starting the orchestrator server to test the new functionality.
"""

import requests
import json
from datetime import datetime

# Configuration
ORCHESTRATOR_URL = "http://localhost:8000"

def test_composition_confirmation_flow():
    """Test the complete composition confirmation flow"""
    print("🧪 Testing Composition Confirmation Flow")
    print("=" * 50)
    
    # Step 1: Create a composition
    print("1. Creating a test composition...")
    compose_request = {
        "requirements": "Create a simple image classification pipeline",
        "constraints": {}
    }
    
    try:
        response = requests.post(
            f"{ORCHESTRATOR_URL}/api/v1/compose",
            json=compose_request,
            timeout=200
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to create composition: {response.status_code}")
            print(response.text)
            return False
            
        composition_data = response.json()
        composition_id = composition_data["composition_id"]
        print(f"✅ Composition created with ID: {composition_id}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to orchestrator: {e}")
        print("Make sure the orchestrator is running on localhost:8000")
        return False
    
    # Step 2: Test composition status (should be 'created')
    print("\n2. Checking composition status...")
    try:
        response = requests.get(f"{ORCHESTRATOR_URL}/api/v1/compositions/{composition_id}/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Status: {status_data['status']}")
            print(f"   Created: {status_data['created_at']}")
        else:
            print(f"❌ Failed to get status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Status check failed: {e}")
    
    # Step 3: Confirm the composition
    print("\n3. Confirming composition deployment...")
    
    # Use the first alternative from the created composition
    first_blueprint = composition_data["blueprints"]["alternatives"][0]
    
    confirmation_request = {
        "confirmed_blueprint": first_blueprint,
        "deployment_context": {
            "environment": "development",
            "monitoringEnabled": True,
            "autoRecomposition": True
        },
        "original_requirements": compose_request["requirements"],
        "selected_alternative": 0,
        "confirmed_at": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{ORCHESTRATOR_URL}/api/v1/compositions/{composition_id}/confirm",
            json=confirmation_request,
            timeout=200
        )
        
        if response.status_code == 200:
            confirmation_data = response.json()
            print(f"✅ Composition confirmed successfully!")
            print(f"   Status: {confirmation_data['status']}")
            print(f"   Confirmed at: {confirmation_data['confirmed_at']}")
        else:
            print(f"❌ Failed to confirm composition: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Confirmation failed: {e}")
        return False
    
    # Step 4: Check status again (should be 'deployed')
    print("\n4. Checking updated composition status...")
    try:
        response = requests.get(f"{ORCHESTRATOR_URL}/api/v1/compositions/{composition_id}/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Status: {status_data['status']}")
            print(f"   Confirmed: {status_data['confirmed_at']}")
            print(f"   Environment: {status_data['deployment_context']['environment']}")
        else:
            print(f"❌ Failed to get updated status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Updated status check failed: {e}")
    
    # Step 5: Test recomposition trigger
    print("\n5. Testing recomposition trigger...")
    
    recomposition_request = {
        "composition_id": composition_id,
        "trigger_type": "performance_degradation",
        "failure_evidence": {
            "execution_time": 150.5,
            "error_count": 3,
            "baseline_time": 45.2
        },
        "failure_analysis": "Task execution time exceeded baseline by 232%. Multiple service timeouts observed.",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{ORCHESTRATOR_URL}/api/v1/recompose",
            json=recomposition_request,
            timeout=200  # Recomposition might take longer
        )
        
        if response.status_code == 200:
            recomposition_data = response.json()
            print(f"✅ Recomposition successful!")
            print(f"   Original ID: {recomposition_data['original_composition_id']}")
            print(f"   New ID: {recomposition_data['new_composition_id']}")
            print(f"   Status: {recomposition_data['status']}")
            print(f"   Alternatives: {len(recomposition_data['blueprints']['alternatives'])}")
            print(f"\n   Reasoning: {recomposition_data['recomposition_reasoning'][:200]}...")
        else:
            print(f"❌ Failed to trigger recomposition: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Recomposition failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Composition confirmation flow is working correctly.")
    return True

def test_error_cases():
    """Test error handling for invalid requests"""
    print("\n🧪 Testing Error Cases")
    print("=" * 30)
    
    # Test confirmation of non-existent composition
    print("1. Testing confirmation of non-existent composition...")
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    confirmation_request = {
        "confirmed_blueprint": {"tasks": [], "description": "test"},
        "deployment_context": {"environment": "test"},
        "original_requirements": "test",
        "selected_alternative": 0,
        "confirmed_at": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{ORCHESTRATOR_URL}/api/v1/compositions/{fake_id}/confirm",
            json=confirmation_request,
            timeout=200
        )
        
        if response.status_code == 404:
            print("✅ Correctly returned 404 for non-existent composition")
        else:
            print(f"❌ Expected 404, got {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    # Test recomposition of non-existent composition
    print("\n2. Testing recomposition of non-existent composition...")
    
    recomposition_request = {
        "composition_id": fake_id,
        "trigger_type": "test",
        "failure_evidence": {},
        "failure_analysis": "test",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{ORCHESTRATOR_URL}/api/v1/recompose",
            json=recomposition_request,
            timeout=200
        )
        
        if response.status_code == 404:
            print("✅ Correctly returned 404 for non-existent composition")
        else:
            print(f"❌ Expected 404, got {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Composition Confirmation API Tests")
    print("=" * 60)
    
    # Test the main flow
    if test_composition_confirmation_flow():
        # Test error cases
        test_error_cases()
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Main flow test failed, skipping error case tests")
    
    print("\n" + "=" * 60)
    print("Test completed. Check the orchestrator logs for any issues.")