import io
import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth_service import generate_session_token
from src.database.connection import get_connection

sys.stdout.reconfigure(encoding='utf-8')
client = TestClient(app)

# 1. Admin and Customer Tokens
admin_token = generate_session_token(user_id=1, email='demo@pricewise.ai')
admin_headers = {'Authorization': f'Bearer {admin_token}'}

customer_token = generate_session_token(user_id=2, email='phase7_test_1794208178@example.com')
customer_headers = {'Authorization': f'Bearer {customer_token}'}

print('=' * 80)
print('TASK 7 AUDIT: ADMIN & CUSTOMER JOURNEYS & USER ISOLATION')
print('=' * 80)

# Step A: Customer Evidence Upload
png_1x1 = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa74U\xa6\x00\x00\x00\x00IEND\xaeB`\x82'
files = {'file': ('audit_receipt.png', io.BytesIO(png_1x1), 'image/png')}
up_resp = client.post('/api/verification/upload-evidence', files=files, headers=customer_headers)
assert up_resp.status_code == 200, f'Upload failed: {up_resp.text}'
ev_url = up_resp.json()['evidence_url']
print(f'[A] Screenshot evidence uploaded by Customer: {ev_url}')

# Clean any existing pending requests for user 2 product 2 Purplle
with get_connection() as conn:
    conn.cursor().execute(
        "DELETE FROM manual_verification_requests WHERE user_id = 2 AND product_id = 2 AND retailer = 'Purplle'"
    )

# Step B: Customer Submits Verification Request
sub_data = {
    'product_id': 2,
    'retailer': 'Purplle',
    'product_url': 'https://www.purplle.com/product/derma-co-niacinamide-serum-30ml',
    'user_submitted_price': 449.0,
    'size_volume': '30ml',
    'notes': 'Spotted 25% off flash sale on Purplle app',
    'evidence_url': ev_url,
}
sub_resp = client.post('/api/verification/manual', json=sub_data, headers=customer_headers)
assert sub_resp.status_code == 200, f'Submission failed: {sub_resp.text}'
req_id = sub_resp.json()['id']
print(f'[B] Customer submitted manual verification request #{req_id} for product 2')

# Step C: Duplicate Submission Prevention
dup_resp = client.post('/api/verification/manual', json=sub_data, headers=customer_headers)
print(f'[C] Duplicate submission response: {dup_resp.status_code} (Expected: 409)')
assert dup_resp.status_code == 409, f'Duplicate was not blocked: {dup_resp.text}'
print(f'    Detail: {dup_resp.json()["detail"]}')

# Step D: User Isolation Check - Customer cannot access admin queue or approve
unauth_q = client.get('/api/admin/verifications', headers=customer_headers)
assert unauth_q.status_code == 403, f'Customer accessed admin queue: {unauth_q.status_code}'
unauth_app = client.post(f'/api/admin/verifications/{req_id}/approve', json={'verified_price': 449.0}, headers=customer_headers)
assert unauth_app.status_code == 403, f'Customer self-approved request: {unauth_app.status_code}'
print(f'[D] User isolation confirmed: Customer access to admin queue: 403, Customer self-approve: 403')

# Step E: Admin Inspects Queue
admin_q = client.get('/api/admin/verifications', headers=admin_headers)
assert admin_q.status_code == 200
pending_manuals = admin_q.json().get('pending_manual_verifications', [])
match = next((r for r in pending_manuals if r['id'] == req_id), None)
assert match is not None, f'Request #{req_id} not found in admin queue'
assert len(match['evidence']) > 0, 'No evidence attached'
assert match['evidence'][0]['evidence_url'] == ev_url
print(f'[E] Admin retrieved queue: Request #{req_id} visible with evidence_url: {match["evidence"][0]["evidence_url"]}')

# Step F: Admin Approves Verification Request
app_data = {
    'verified_price': 449.0,
    'verified_mrp': 599.0,
    'verified_discount_pct': 25.0,
    'verification_notes': 'Verified against customer screenshot proof. Flash sale price legitimate.',
}
app_resp = client.post(f'/api/admin/verifications/{req_id}/approve', json=app_data, headers=admin_headers)
assert app_resp.status_code == 200, f'Admin approval failed: {app_resp.text}'
app_json = app_resp.json()
print(f'[F] Admin approved request #{req_id}: status={app_json["status"]}, verification_status={app_json["verification_status"]}')

# Step G: Verify Database State & Evidence Linking
with get_connection() as conn:
    conn.row_factory = __import__('sqlite3').Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM manual_verification_requests WHERE id = ?", (req_id,))
    v_row = dict(cur.fetchone())
    print(f'[G] DB Request Row: status={v_row["status"]}, reviewed_by={v_row["reviewed_by"]}, verified_price={v_row["verified_price"]}')
    assert v_row['status'] == 'verified'
    assert v_row['reviewed_by'] == 1

    cur.execute("SELECT * FROM evidence_references WHERE reference_type = 'manual_verification' AND reference_id = ?", (req_id,))
    ev_row = cur.fetchone()
    assert ev_row is not None, 'Evidence reference was not linked to request!'
    print(f'    Evidence Reference Linked: id={ev_row["id"]}, reference_id={ev_row["reference_id"]}, url={ev_row["evidence_url"]}')

    cur.execute("SELECT * FROM price_history WHERE data_source = 'manual_verification' ORDER BY id DESC LIMIT 1")
    ph_row = cur.fetchone()
    assert ph_row is not None, 'Price history entry was not created!'
    print(f'    Price History Appended: id={ph_row["id"]}, offer_id={ph_row["offer_id"]}, price={ph_row["price"]}, data_status={ph_row["data_status"]}, recorded_at={ph_row["recorded_at"]}')

print('=' * 80)
print('ALL ADMIN & CUSTOMER JOURNEY CHECKS PASSED PERFECTLY!')
print('=' * 80)
