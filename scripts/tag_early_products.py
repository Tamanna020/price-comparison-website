"""Tag early products (prod-01 to prod-23) with partially_verified status."""

with open('frontend/src/data/products.ts', 'r', encoding='utf-8') as f:
    text = f.read()

prod_chunks = text.split("id: 'prod-")
new_chunks = [prod_chunks[0]]

for chunk in prod_chunks[1:]:
    pid_str = chunk.split("'")[0]
    pid = int(pid_str)
    
    # If early product (<= 23) and doesn't already have dataStatus
    if pid <= 23 and "dataStatus:" not in chunk[:500]:
        # Insert dataStatus, dataSource, evidenceType right after description
        desc_pos = chunk.find("description: '")
        if desc_pos != -1:
            end_desc = chunk.find("',", desc_pos)
            if end_desc != -1:
                insert_idx = end_desc + 2
                tag_block = (
                    "\n    dataSource: 'Commercial Catalog Reference / Brand Specification',"
                    "\n    dataStatus: 'partially_verified',"
                    "\n    evidenceType: 'Commercial Listing / Key Actives Declaration',"
                )
                chunk = chunk[:insert_idx] + tag_block + chunk[insert_idx:]
    
    new_chunks.append(chunk)

updated_text = "id: 'prod-".join(new_chunks)

with open('frontend/src/data/products.ts', 'w', encoding='utf-8', newline='\n') as f:
    f.write(updated_text)

print("Successfully tagged prod-01 through prod-23 with partially_verified status.")
