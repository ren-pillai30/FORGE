import sqlite3
import os

def setup_database():
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "telemetry.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT,
            level_name TEXT,
            gold_earned INTEGER,
            enemies_defeated INTEGER,
            item_drop_rate REAL
        )
    """)
    
    mock_data = [
        ('P_001', 'Tutorial_Cave', 150, 12, 0.05),
        ('P_002', 'Tutorial_Cave', 120, 10, 0.04),
        ('P_001', 'Lava_Core', 500, 45, 0.15),
        ('P_003', 'Forest_Edge', 200, 18, 0.08),
        ('P_004', 'Lava_Core', 800, 60, 0.20)
    ]
    
    cursor.execute("DELETE FROM telemetry")
    cursor.executemany("""
        INSERT INTO telemetry 
        (player_id, level_name, gold_earned, enemies_defeated, item_drop_rate) 
        VALUES (?, ?, ?, ?, ?)
    """, mock_data)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()