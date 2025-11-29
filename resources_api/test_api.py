"""
Script de prueba para Resources API
Ejecutar después de levantar los contenedores
"""
import requests
import json

BASE_URL = "http://localhost:8001/api/v1"

def test_health():
    """Test health check"""
    print("\n🔍 Testing Health Check...")
    response = requests.get("http://localhost:8001/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    return response.status_code == 200


def test_vlans():
    """Test VLAN endpoints"""
    print("\n📡 Testing VLAN Endpoints...")
    
    # 1. Get available VLANs
    print("\n1. Get available VLANs:")
    response = requests.get(f"{BASE_URL}/vlans/available?limit=5")
    print(f"Status: {response.status_code}")
    vlans = response.json()
    print(f"Available VLANs: {len(vlans)}")
    if vlans:
        print(f"First VLAN: {vlans[0]}")
        vlan_id = vlans[0]['vlan_id']
        
        # 2. Reserve VLAN
        print(f"\n2. Reserve VLAN {vlan_id}:")
        reserve_data = {
            "vlan_id": vlan_id,
            "slice_id": 1,
            "reserved_by": 1,
            "description": "Test reservation"
        }
        response = requests.post(f"{BASE_URL}/vlans/reserve", json=reserve_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # 3. Get specific VLAN
        print(f"\n3. Get VLAN {vlan_id} details:")
        response = requests.get(f"{BASE_URL}/vlans/{vlan_id}")
        print(f"Status: {response.status_code}")
        print(f"VLAN details: {response.json()}")
        
        # 4. Release VLAN
        print(f"\n4. Release VLAN {vlan_id}:")
        release_data = {"vlan_id": vlan_id}
        response = requests.post(f"{BASE_URL}/vlans/release", json=release_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    
    return True


def test_vnc_ports():
    """Test VNC Port endpoints"""
    print("\n🖥️  Testing VNC Port Endpoints...")
    
    # 1. Get available VNC ports
    print("\n1. Get available VNC Ports:")
    response = requests.get(f"{BASE_URL}/vnc-ports/available?limit=5")
    print(f"Status: {response.status_code}")
    ports = response.json()
    print(f"Available Ports: {len(ports)}")
    if ports:
        print(f"First Port: {ports[0]}")
        port_id = ports[0]['vnc_port_id']
        
        # 2. Reserve VNC port
        print(f"\n2. Reserve VNC Port {port_id}:")
        reserve_data = {
            "vnc_port_id": port_id,
            "vm_id": 1,
            "slice_id": 1,
            "reserved_by": 1,
            "description": "Test reservation for VM"
        }
        response = requests.post(f"{BASE_URL}/vnc-ports/reserve", json=reserve_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # 3. Get specific VNC port
        print(f"\n3. Get VNC Port {port_id} details:")
        response = requests.get(f"{BASE_URL}/vnc-ports/{port_id}")
        print(f"Status: {response.status_code}")
        print(f"Port details: {response.json()}")
        
        # 4. Release VNC port
        print(f"\n4. Release VNC Port {port_id}:")
        release_data = {"vnc_port_id": port_id}
        response = requests.post(f"{BASE_URL}/vnc-ports/release", json=release_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    
    return True


def test_create_resources():
    """Test creating new resources"""
    print("\n➕ Testing Resource Creation...")
    
    # Create new VLAN
    print("\n1. Create new VLAN:")
    new_vlan = {
        "vlan_number": 999,
        "az_id": None,
        "description": "Test VLAN created via API"
    }
    response = requests.post(f"{BASE_URL}/vlans", json=new_vlan)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        created_vlan = response.json()
        print(f"Created VLAN: {created_vlan}")
        
        # Delete it
        print(f"\n2. Delete VLAN {created_vlan['vlan_id']}:")
        response = requests.delete(f"{BASE_URL}/vlans/{created_vlan['vlan_id']}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    
    # Create new VNC port
    print("\n3. Create new VNC Port:")
    new_port = {
        "port_number": 6000,
        "az_id": None,
        "description": "Test VNC port created via API"
    }
    response = requests.post(f"{BASE_URL}/vnc-ports", json=new_port)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        created_port = response.json()
        print(f"Created Port: {created_port}")
        
        # Delete it
        print(f"\n4. Delete VNC Port {created_port['vnc_port_id']}:")
        response = requests.delete(f"{BASE_URL}/vnc-ports/{created_port['vnc_port_id']}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    
    return True


def main():
    """Run all tests"""
    print("="*60)
    print("🧪 Resources API - Test Suite")
    print("="*60)
    
    try:
        # Test health
        if not test_health():
            print("❌ Health check failed!")
            return
        
        # Test VLANs
        test_vlans()
        
        # Test VNC Ports
        test_vnc_ports()
        
        # Test creation
        test_create_resources()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API")
        print("Make sure the container is running: docker-compose up -d resources_api")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
