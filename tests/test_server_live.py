import urllib.request
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def test_live_endpoints():
    base = "http://localhost:5000"
    
    # 1. State
    req = urllib.request.urlopen(f"{base}/api/erp/state")
    assert req.status == 200
    state = json.loads(req.read().decode())
    assert state["success"] is True
    print(f"[PASS] /api/erp/state OK — {len(state['data']['scenarios'])} scenarios, {len(state['data']['purchase_orders'])} POs")

    # 2. Analytics with Treasury
    req = urllib.request.urlopen(f"{base}/api/analytics")
    assert req.status == 200
    analytics = json.loads(req.read().decode())
    assert analytics["success"] is True
    treasury = analytics["metrics"]["treasury"]
    print(f"[PASS] /api/analytics OK — APR: {treasury['early_discount_apr_pct']}%, OpEx Reduction: {treasury['opex_reduction_pct']}%")

    # 3. Disburse with NetSuite GL & SHA-256
    data = json.dumps({"scenario_id": 1}).encode()
    req = urllib.request.Request(f"{base}/api/action/disburse", data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    assert resp.status == 200
    disburse_data = json.loads(resp.read().decode())
    assert disburse_data["success"] is True
    vch = disburse_data["voucher"]
    print(f"[PASS] /api/action/disburse OK — JE: {vch['journal_entry_id']}, Balanced: {vch['is_balanced']}, Hash: {vch['sox_section_404_hash'][:16]}...")

    print("ALL LIVE SERVER ENDPOINTS VERIFIED!")

if __name__ == "__main__":
    test_live_endpoints()
