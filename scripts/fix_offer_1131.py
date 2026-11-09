with open('src/database/expanded_beauty_data.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('"current_price": 551.25,', '"current_price": 550.0,')

with open('src/database/expanded_beauty_data.py', 'w', encoding='utf-8') as f:
    f.write(text)

from src.database.connection import get_connection

with get_connection() as conn:
    c = conn.cursor()
    c.execute("UPDATE offers SET current_price = 550.0 WHERE id = 1131")
    c.execute("UPDATE price_history SET price = 550.0 WHERE offer_id = 1131")
    conn.commit()

print("Offer 1131 and file updated successfully.")
