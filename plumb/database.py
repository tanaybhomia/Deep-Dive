import sqlite3
import os
from datetime import datetime, timedelta


class Database:
    def __init__(self):
        data_dir = os.path.join(os.path.expanduser("~"), ".local", "share", "plumb")
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = os.path.join(data_dir, "plumb.db")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)

            # Ensure at least one default project exists
            conn.execute(
                'INSERT OR IGNORE INTO projects (id, name) VALUES (1, "Default Project")'
            )

            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

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

            conn.execute("""
                CREATE TABLE IF NOT EXISTS blocked_websites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE NOT NULL
                )
            """)

    def get_projects(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, name FROM projects ORDER BY id")
            return cursor.fetchall()

    def add_project(self, name):
        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.execute("INSERT INTO projects (name) VALUES (?)", (name,))
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def delete_project(self, project_id):
        # Prevent deleting the default project (ID 1)
        if project_id == 1:
            return False
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return True

    def log_session(self, project_id, session_type, duration_seconds):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO sessions (project_id, type, duration_seconds)
                VALUES (?, ?, ?)
            """,
                (project_id, session_type, duration_seconds),
            )

    def get_setting(self, key, default=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key, value):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, str(value)),
            )

    def get_websites(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, domain FROM blocked_websites ORDER BY domain")
            return cursor.fetchall()

    def add_website(self, domain):
        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.execute("INSERT INTO blocked_websites (domain) VALUES (?)", (domain,))
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def remove_website(self, website_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM blocked_websites WHERE id = ?", (website_id,))



    
    def get_total_stats(self, time_range="all", project_id=None, ref_date=None):
        if ref_date is None: ref_date = datetime.now()
        date_str = ref_date.strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT type, SUM(duration_seconds), COUNT(id)
                FROM sessions
            """
            conditions = []
            params = []
            
            if project_id is not None:
                conditions.append("project_id = ?")
                params.append(project_id)
                
            if time_range == "day":
                conditions.append("date(timestamp, 'localtime') = ?")
                params.append(date_str)
            elif time_range == "week":
                start_of_week = ref_date - timedelta(days=ref_date.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                conditions.append("date(timestamp, 'localtime') >= ? AND date(timestamp, 'localtime') <= ?")
                params.extend([start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d")])
            elif time_range == "month":
                start_of_month = ref_date.replace(day=1)
                # Next month - 1 day
                next_month = (start_of_month + timedelta(days=32)).replace(day=1)
                end_of_month = next_month - timedelta(days=1)
                conditions.append("date(timestamp, 'localtime') >= ? AND date(timestamp, 'localtime') <= ?")
                params.extend([start_of_month.strftime("%Y-%m-%d"), end_of_month.strftime("%Y-%m-%d")])
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " GROUP BY type"
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            stats = {
                "total_focus_seconds": 0,
                "total_break_seconds": 0,
                "completed_pomodoros": 0
            }
            
            for row in rows:
                session_type = row[0]
                total_duration = row[1]
                count = row[2]
                
                if session_type == "Focus":
                    stats["total_focus_seconds"] += total_duration
                    stats["completed_pomodoros"] += count
                elif session_type in ["Short Break", "Long Break"]:
                    stats["total_break_seconds"] += total_duration
                    
            return stats

    def get_insights(self, time_range="day", project_id=None, ref_date=None):
        if ref_date is None: ref_date = datetime.now()
        date_str = ref_date.strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            conditions = ["s.type = 'Focus'"]
            params = []
            if project_id is not None:
                conditions.append("s.project_id = ?")
                params.append(project_id)
                
            if time_range == "day":
                conditions.append("date(s.timestamp, 'localtime') = ?")
                params.append(date_str)
            elif time_range == "week":
                start_of_week = ref_date - timedelta(days=ref_date.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                conditions.append("date(s.timestamp, 'localtime') >= ? AND date(s.timestamp, 'localtime') <= ?")
                params.extend([start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d")])
            elif time_range == "month":
                start_of_month = ref_date.replace(day=1)
                next_month = (start_of_month + timedelta(days=32)).replace(day=1)
                end_of_month = next_month - timedelta(days=1)
                conditions.append("date(s.timestamp, 'localtime') >= ? AND date(s.timestamp, 'localtime') <= ?")
                params.extend([start_of_month.strftime("%Y-%m-%d"), end_of_month.strftime("%Y-%m-%d")])
                
            where_clause = " WHERE " + " AND ".join(conditions)
            
            # 1. Top Project
            query_top_proj = f"""
                SELECT p.name, SUM(s.duration_seconds) as total
                FROM sessions s
                LEFT JOIN projects p ON s.project_id = p.id
                {where_clause}
                GROUP BY s.project_id
                ORDER BY total DESC
                LIMIT 1
            """
            cur = conn.execute(query_top_proj, params)
            row_proj = cur.fetchone()
            top_proj_name = (row_proj[0] or "General") if row_proj and row_proj[0] is not None else ("General" if row_proj else "None")
            top_proj_sec = row_proj[1] if row_proj else 0
            if top_proj_name == "None" and top_proj_sec == 0:
                top_proj_name = "-"
                
            # 2. Peak Period (Hour for day view, Day for week/month/year)
            if time_range == "day":
                query_peak = f"""
                    SELECT strftime('%H:00', s.timestamp, 'localtime') as hr, SUM(s.duration_seconds) as total
                    FROM sessions s
                    {where_clause}
                    GROUP BY hr
                    ORDER BY total DESC
                    LIMIT 1
                """
                cur = conn.execute(query_peak, params)
                row_peak = cur.fetchone()
                peak_label = "Peak Hour"
                peak_val = row_peak[0] if row_peak and row_peak[0] else "-"
                peak_sec = row_peak[1] if row_peak else 0
            else:
                query_peak = f"""
                    SELECT date(s.timestamp, 'localtime') as dt, SUM(s.duration_seconds) as total
                    FROM sessions s
                    {where_clause}
                    GROUP BY dt
                    ORDER BY total DESC
                    LIMIT 1
                """
                cur = conn.execute(query_peak, params)
                row_peak = cur.fetchone()
                peak_label = "Peak Day"
                if row_peak and row_peak[0]:
                    try:
                        dt_obj = datetime.strptime(row_peak[0], "%Y-%m-%d")
                        peak_val = dt_obj.strftime("%a, %d %b")
                    except Exception:
                        peak_val = row_peak[0]
                    peak_sec = row_peak[1]
                else:
                    peak_val = "-"
                    peak_sec = 0
                    
            # 3 & 4. Average Time & Session Count
            query_totals = f"""
                SELECT SUM(s.duration_seconds), COUNT(s.id), COUNT(DISTINCT date(s.timestamp, 'localtime'))
                FROM sessions s
                {where_clause}
            """
            cur = conn.execute(query_totals, params)
            row_totals = cur.fetchone()
            total_sec = row_totals[0] or 0
            total_count = row_totals[1] or 0
            active_days = row_totals[2] or 0
            
            if time_range == "day":
                avg_label = "Avg Session"
                avg_sec = (total_sec // total_count) if total_count > 0 else 0
                avg_sub = "per focus session"
            else:
                avg_label = "Daily Average"
                avg_sec = (total_sec // active_days) if active_days > 0 else 0
                avg_sub = f"across {active_days} active day{'s' if active_days != 1 else ''}" if active_days > 0 else "no active days"
                
            return {
                "top_proj_name": top_proj_name,
                "top_proj_sec": top_proj_sec,
                "peak_label": peak_label,
                "peak_val": peak_val,
                "peak_sec": peak_sec,
                "avg_label": avg_label,
                "avg_sec": avg_sec,
                "avg_sub": avg_sub,
                "total_count": total_count
            }

    def get_graph_data(self, time_range="day", project_id=None, ref_date=None):
        if ref_date is None: ref_date = datetime.now()
        date_str = ref_date.strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            query = ""
            params = []
            
            conditions = ["type = 'Focus'"]
            if project_id is not None:
                conditions.append("project_id = ?")
                params.append(project_id)
                
            if time_range == "day":
                conditions.append("date(timestamp, 'localtime') = ?")
                params.append(date_str)
                query = "SELECT strftime('%H', timestamp, 'localtime') as hour, SUM(duration_seconds) FROM sessions WHERE " + " AND ".join(conditions) + " GROUP BY hour ORDER BY hour ASC"
            elif time_range == "week":
                start_of_week = ref_date - timedelta(days=ref_date.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                conditions.append("date(timestamp, 'localtime') >= ? AND date(timestamp, 'localtime') <= ?")
                params.extend([start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d")])
                query = "SELECT strftime('%w', timestamp, 'localtime') as dow, SUM(duration_seconds) FROM sessions WHERE " + " AND ".join(conditions) + " GROUP BY dow ORDER BY dow ASC"
                
                # sqlite strftime('%w') returns 0-6 where 0 is Sunday.
                # Adjust to 0-6 where 0 is Monday so it matches our UI.
                
            elif time_range == "month":
                start_of_month = ref_date.replace(day=1)
                next_month = (start_of_month + timedelta(days=32)).replace(day=1)
                end_of_month = next_month - timedelta(days=1)
                conditions.append("date(timestamp, 'localtime') >= ? AND date(timestamp, 'localtime') <= ?")
                params.extend([start_of_month.strftime("%Y-%m-%d"), end_of_month.strftime("%Y-%m-%d")])
                query = "SELECT strftime('%d', timestamp, 'localtime') as dom, SUM(duration_seconds) FROM sessions WHERE " + " AND ".join(conditions) + " GROUP BY dom ORDER BY dom ASC"
            else:
                query = "SELECT strftime('%Y-%m', timestamp, 'localtime') as month, SUM(duration_seconds) FROM sessions WHERE " + " AND ".join(conditions) + " GROUP BY month ORDER BY month ASC"
                
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            graph_data = {}
            for row in rows:
                if time_range == "week":
                    # Convert Sunday=0 to Monday=0
                    dow = int(row[0])
                    dow = (dow - 1) % 7
                    graph_data[str(dow)] = row[1]
                else:
                    graph_data[row[0]] = row[1]
                
            return graph_data

    def get_earliest_date(self):
        earliest_dt = None
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT MIN(date(timestamp, 'localtime')) FROM sessions")
                row = cursor.fetchone()
                if row and row[0]:
                    earliest_dt = datetime.strptime(row[0], "%Y-%m-%d").date()
        except Exception:
            pass
            
        if not earliest_dt:
            try:
                if os.path.exists(self.db_path):
                    mtime = os.path.getmtime(self.db_path)
                    earliest_dt = datetime.fromtimestamp(mtime).date()
            except Exception:
                pass
                
        if not earliest_dt:
            earliest_dt = datetime.now().date()
            
        return earliest_dt


db = Database()
