#!/usr/bin/env python3
import sqlite3
import os
import random
import argparse
from datetime import datetime, timedelta

def main():
    parser = argparse.ArgumentParser(description="Generate mock data for Plumb stats testing.")
    parser.add_argument("--clear", action="store_true", help="Clear all existing sessions and non-default projects")
    args = parser.parse_args()

    db_path = os.path.join(os.path.expanduser("~"), ".local", "share", "plumb", "plumb.db")
    if not os.path.exists(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    print(f"Connecting to Plumb database at: {db_path}")
    with sqlite3.connect(db_path) as conn:
        # Ensure tables exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        conn.execute('INSERT OR IGNORE INTO projects (id, name) VALUES (1, "Default Project")')
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                type TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            )
        """)

        if args.clear:
            conn.execute("DELETE FROM sessions")
            conn.execute("DELETE FROM projects WHERE id != 1")
            print("Successfully cleared all mock data! Database is reset.")
            return

        # 1. Create realistic test projects
        project_names = ["Plumb Development", "Open Source Contribute", "Reading & Research", "System Architecture"]
        project_ids = [1]  # Default Project
        for name in project_names:
            try:
                conn.execute("INSERT OR IGNORE INTO projects (name) VALUES (?)", (name,))
            except Exception:
                pass
            cursor = conn.execute("SELECT id FROM projects WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row and row[0] not in project_ids:
                project_ids.append(row[0])

        # 2. Clear existing sessions first to ensure clean test data set
        conn.execute("DELETE FROM sessions")

        now = datetime.now()
        sessions_added = 0

        # 3. Generate past 180 days of activity for Heatmap, Year, and Month views
        print("Generating 180 days of contribution history and stats...")
        for day_offset in range(1, 181):
            target_day = now - timedelta(days=day_offset)
            # Skip some random days so heatmap looks organic and realistic
            if random.random() < 0.25:
                continue

            # Random number of sessions per day (2 to 7 sessions)
            num_sessions = random.randint(2, 7)
            for _ in range(num_sessions):
                p_id = random.choice(project_ids)
                hour = random.randint(9, 18)
                minute = random.randint(0, 50)
                ts = datetime(target_day.year, target_day.month, target_day.day, hour, minute)
                
                # 25m or 45m Focus session
                duration = random.choice([1500, 1500, 2700, 3000])
                conn.execute("INSERT INTO sessions (project_id, type, duration_seconds, timestamp) VALUES (?, ?, ?, ?)",
                             (p_id, "Focus", duration, ts.strftime("%Y-%m-%d %H:%M:%S")))
                sessions_added += 1

                # Log occasional breaks
                if random.random() < 0.6:
                    break_ts = ts + timedelta(seconds=duration)
                    conn.execute("INSERT INTO sessions (project_id, type, duration_seconds, timestamp) VALUES (?, ?, ?, ?)",
                                 (p_id, "Break", 300, break_ts.strftime("%Y-%m-%d %H:%M:%S")))
                    sessions_added += 1

        # 4. Generate curated activity specifically for TODAY so Today view looks incredible!
        print("Generating curated workflow for Today view...")
        today_schedule = [
            (9, 15, 1500, "Focus"),   # 9:15 AM - 25m Focus
            (9, 45, 300, "Break"),    # 9:45 AM - 5m Break
            (10, 0, 1500, "Focus"),   # 10:00 AM - 25m Focus
            (10, 30, 1500, "Focus"),  # 10:30 AM - 25m Focus (total 50m in hour 10)
            (11, 15, 2700, "Focus"),  # 11:15 AM - 45m Focus
            (12, 5, 900, "Break"),    # 12:05 PM - 15m Break
            (14, 0, 1500, "Focus"),   # 2:00 PM - 25m Focus
            (14, 30, 300, "Break"),   # 2:30 PM - 5m Break
            (15, 10, 1200, "Focus"),  # 3:10 PM - 20m Focus
        ]
        
        for hour, minute, duration, stype in today_schedule:
            p_id = random.choice(project_ids)
            ts = datetime(now.year, now.month, now.day, hour, minute)
            conn.execute("INSERT INTO sessions (project_id, type, duration_seconds, timestamp) VALUES (?, ?, ?, ?)",
                         (p_id, stype, duration, ts.strftime("%Y-%m-%d %H:%M:%S")))
            sessions_added += 1

        conn.commit()
        print(f"Successfully generated {sessions_added} mock sessions across {len(project_ids)} projects!")
        print("Run Plumb now to explore Today, Week, Month, Year, and Heatmap visualizations!")
        print("(To reset/clear all mock data later, run: python3 generate_mock_data.py --clear)")

if __name__ == "__main__":
    main()
