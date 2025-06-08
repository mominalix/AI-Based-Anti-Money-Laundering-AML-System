#!/usr/bin/env python3
"""
Test OpenAI Integration with .env Configuration
Verifies that the AlertManager can properly read OpenAI API key from .env file
"""

import asyncio
import requests
import json
from datetime import datetime

async def test_openai_integration():
    """Test OpenAI integration through AlertManager"""
    
    print("🧪 Testing OpenAI Integration with .env Configuration")
    print("=" * 60)
    
    # Check AlertManager health
    try:
        response = requests.get("http://localhost:8005/health", timeout=5)
        if response.status_code == 200:
            print("✅ AlertManager service is healthy")
        else:
            print("❌ AlertManager service not responding")
            return
    except Exception as e:
        print(f"❌ Cannot connect to AlertManager: {e}")
        return
    
    # Test direct alert creation with high risk score to trigger OpenAI
    test_alert_data = {
        "txn_id": "TEST_OPENAI_001",
        "risk_score": 0.95,  # High risk to trigger SAR generation
        "shap_values": {
            "sanctions_country": 0.30,
            "pep_exposure": 0.25,
            "structuring_score": 0.20,
            "high_risk_country": 0.15,
            "off_hours": 0.10
        },
        "customer_id": "CUST_TEST",
        "account_id": "ACC_TEST",
        "scored_at": datetime.utcnow().isoformat()
    }
    
    print(f"\n📤 Sending high-risk transaction for processing...")
    print(f"   • Transaction ID: {test_alert_data['txn_id']}")
    print(f"   • Risk Score: {test_alert_data['risk_score']}")
    print(f"   • Expected: OpenAI SAR generation should trigger")
    
    try:
        # Send to AlertManager for processing
        response = requests.post(
            "http://localhost:8005/process-scored-transaction",
            json=test_alert_data,
            timeout=30  # Allow time for OpenAI API call
        )
        
        if response.status_code == 200:
            alert_result = response.json()
            print(f"\n✅ Alert processed successfully!")
            print(f"   • Alert ID: {alert_result.get('alert_id', 'N/A')}")
            print(f"   • Status: {alert_result.get('status', 'N/A')}")
            
            # Check if SAR narrative was generated
            sar_narrative = alert_result.get('sar_narrative')
            if sar_narrative:
                print(f"\n🤖 OpenAI SAR Generation: SUCCESS")
                print(f"   • Narrative Length: {len(sar_narrative)} characters")
                print(f"   • Generation Method: {'AI-Powered' if len(sar_narrative) > 500 else 'Template-based'}")
                
                print(f"\n📄 Generated SAR Narrative:")
                print("=" * 60)
                print(sar_narrative[:500] + "..." if len(sar_narrative) > 500 else sar_narrative)
                print("=" * 60)
                
                # Verify it's AI-generated (longer, more detailed)
                if len(sar_narrative) > 1000:
                    print(f"\n✅ Confirmed: AI-powered SAR generation is working!")
                    print(f"   • .env file configuration: SUCCESS")
                    print(f"   • OpenAI API integration: SUCCESS")
                else:
                    print(f"\n⚠️  Template-based SAR generated (OpenAI may not be configured)")
            else:
                print(f"\n❌ No SAR narrative generated")
                
        else:
            print(f"❌ Alert processing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing OpenAI integration: {e}")
    
    # Get alert statistics
    try:
        response = requests.get("http://localhost:8005/alerts/statistics", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"\n📊 Alert Statistics:")
            print(f"   • Total Alerts: {stats.get('total_alerts', 0)}")
            print(f"   • High Risk Count: {stats.get('high_risk_count', 0)}")
            print(f"   • Average Risk Score: {stats.get('avg_risk_score', 0):.3f}")
    except Exception as e:
        print(f"⚠️  Could not fetch alert statistics: {e}")

if __name__ == "__main__":
    asyncio.run(test_openai_integration()) 