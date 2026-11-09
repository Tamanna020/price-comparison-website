import os
import sqlite3

conn = sqlite3.connect('data/pricewise.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print('=== DATABASE INTEGRITY CHECKS ===')
cur.execute('PRAGMA integrity_check;')
print('PRAGMA integrity_check:', cur.fetchall()[0][0])

cur.execute('PRAGMA foreign_key_check;')
fks = cur.fetchall()
print('PRAGMA foreign_key_check violations:', len(fks))

print('\n=== RECORD TOTALS ===')
cur.execute('SELECT COUNT(*) FROM products;')
print('Total Products:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM offers;')
print('Total Offers:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM price_history;')
print('Total Price History Records:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM manual_verification_requests;')
print('Total Manual Verification Requests:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM evidence_references;')
print('Total Evidence References:', cur.fetchone()[0])

print('\n=== PRICE HISTORY SEPARATION AUDIT ===')
cur.execute('SELECT data_status, data_source, COUNT(*) as cnt FROM price_history GROUP BY data_status, data_source;')
for row in cur.fetchall():
    print(f"  Status: {str(row['data_status']):20} Source: {str(row['data_source']):20} Count: {row['cnt']}")

print('\n=== OFFERS AVAILABILITY & STORES DISTRIBUTION ===')
cur.execute('SELECT availability, COUNT(*) as cnt FROM offers GROUP BY availability;')
for row in cur.fetchall():
    print(f"  Availability: {str(row['availability']):20} Count: {row['cnt']}")

cur.execute('SELECT s.name as store_name, COUNT(o.id) as offer_count FROM stores s LEFT JOIN offers o ON s.id = o.store_id GROUP BY s.name;')
for row in cur.fetchall():
    print(f"  Store: {str(row['store_name']):25} Offers: {row['offer_count']}")

print('\n=== EVIDENCE INTEGRITY & DISK ATTACHMENTS ===')
cur.execute('SELECT id, reference_type, reference_id, evidence_url FROM evidence_references;')
for row in cur.fetchall():
    fname = os.path.basename(row['evidence_url'])
    disk_path = os.path.join('data', 'evidence_uploads', fname)
    exists = os.path.exists(disk_path)
    print(f"  Evidence #{row['id']}: type={row['reference_type']} ref_id={row['reference_id']} file={fname} on_disk={exists}")
