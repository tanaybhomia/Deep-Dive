import gi
import math
from datetime import datetime, timedelta

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gtk, Adw, GLib, Gdk, Pango, PangoCairo
from plumb.database import db

class HeatmapWidget(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(-1, 140)
        self.set_draw_func(self.on_draw)
        self.heatmap_data = {}
        self.accent_color = (0, 0, 0, 1)
        
    def set_data(self, data):
        self.heatmap_data = data
        self.queue_draw()
        
    def get_accent_rgba(self):
        context = self.get_style_context()
        success, rgba = context.lookup_color("accent_bg_color")
        if success:
            return (rgba.red, rgba.green, rgba.blue, rgba.alpha)
        return (0.2, 0.5, 0.9, 1.0)
        
    def on_draw(self, drawing_area, cr, width, height):
        self.accent_color = self.get_accent_rgba()
        r, g, b, a = self.accent_color
        
        cell_size = 12
        spacing = 4
        
        total_cols = 52
        total_rows = 7
        
        grid_width = total_cols * (cell_size + spacing) - spacing
        grid_height = total_rows * (cell_size + spacing) - spacing
        
        start_x = (width - grid_width) / 2
        start_y = (height - grid_height) / 2
        
        if start_x < 0: start_x = 0
        if start_y < 0: start_y = 0
        
        today = datetime.now()
        start_date = today - timedelta(days=364)
        
        for col in range(total_cols):
            for row in range(total_rows):
                date_offset = col * 7 + row
                current_date = start_date + timedelta(days=date_offset)
                date_str = current_date.strftime("%Y-%m-%d")
                
                seconds = self.heatmap_data.get(date_str, 0)
                
                x = start_x + col * (cell_size + spacing)
                y = start_y + row * (cell_size + spacing)
                
                cr.set_source_rgba(r, g, b, 0.1)
                
                if seconds > 0:
                    intensity = min(1.0, 0.2 + (seconds / 14400.0) * 0.8) # max intensity at ~4 hours
                    cr.set_source_rgba(r, g, b, intensity)
                
                radius = 2.5
                cr.new_path()
                cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
                cr.arc(x + cell_size - radius, y + radius, radius, 3 * math.pi / 2, 2 * math.pi)
                cr.arc(x + cell_size - radius, y + cell_size - radius, radius, 0, math.pi / 2)
                cr.arc(x + radius, y + cell_size - radius, radius, math.pi / 2, math.pi)
                cr.close_path()
                cr.fill()

class GraphWidget(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(-1, 240)
        self.set_draw_func(self.on_draw)
        self.graph_data = {}
        self.time_range = "day"
        self.accent_color = (0, 0, 0, 1)
        
    def set_data(self, data, time_range, ref_date=None):
        self.graph_data = data
        self.time_range = time_range
        self.ref_date = ref_date or datetime.now()
        self.queue_draw()

    def get_accent_rgba(self):
        context = self.get_style_context()
        success, rgba = context.lookup_color("accent_bg_color")
        if success:
            return (rgba.red, rgba.green, rgba.blue, rgba.alpha)
        return (0.2, 0.5, 0.9, 1.0)
        
    def on_draw(self, drawing_area, cr, width, height):
        self.accent_color = self.get_accent_rgba()
        r, g, b, a = self.accent_color
        
        margin_left = 50
        margin_right = 25
        margin_top = 20
        margin_bottom = 30
        
        graph_width = width - margin_left - margin_right
        graph_height = height - margin_top - margin_bottom
        
        if graph_width <= 0 or graph_height <= 0: return
        
        max_minutes = 60
        max_val_seconds = max(self.graph_data.values()) if (self.graph_data and self.graph_data.values()) else 0
        max_val_minutes = max_val_seconds / 60.0
        
        if max_val_minutes == 0:
            if self.time_range == "day": max_minutes = 60
            elif self.time_range == "week": max_minutes = 180
            elif self.time_range == "month": max_minutes = 720
            else: max_minutes = 1440
        elif max_val_minutes <= 15:
            max_minutes = 15
        elif max_val_minutes <= 30:
            max_minutes = 30
        elif max_val_minutes <= 60:
            max_minutes = 60
        else:
            target_hours = (max_val_minutes / 60.0) * 1.15
            nice_hours = [3, 6, 9, 12, 15, 18, 24, 30, 36, 45, 60, 75, 90, 120, 150, 180, 240, 300, 360, 450, 600, 900, 1200, 1500, 2400, 3000, 5000, 10000]
            for h in nice_hours:
                if h >= target_hours:
                    max_minutes = h * 60
                    break
            else:
                max_minutes = int(math.ceil(target_hours / 30.0) * 30) * 60

        if max_minutes <= 60:
            y_labels = [f"{int(max_minutes)}m", f"{int(max_minutes*2/3)}m", f"{int(max_minutes/3)}m", "0m"]
        else:
            mh = max_minutes // 60
            y_labels = [f"{int(mh)}h", f"{int(mh*2/3)}h", f"{int(mh/3)}h", "0h"]
        
        for i, label_text in enumerate(y_labels):
            y = margin_top + i * (graph_height / 3)
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.1)
            cr.set_line_width(1)
            cr.move_to(margin_left, y)
            cr.line_to(width - margin_right, y)
            cr.stroke()
            
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.6)
            layout = PangoCairo.create_layout(cr)
            layout.set_text(label_text, -1)
            layout.set_font_description(Pango.FontDescription.from_string("Sans 10"))
            _, extents = layout.get_pixel_extents()
            cr.move_to(margin_left - extents.width - 8, y - extents.height / 2)
            PangoCairo.show_layout(cr, layout)
            
        keys = []
        if self.time_range == "day":
            active_hours = [int(k) for k, v in self.graph_data.items() if v > 0] if self.graph_data else []
            if active_hours:
                start_hour = min(active_hours)
                end_hour = max(active_hours)
                # Expand range slightly if brief so the bar chart isn't cramped
                while (end_hour - start_hour) < 4:
                    if end_hour < 23:
                        end_hour += 1
                    elif start_hour > 0:
                        start_hour -= 1
                    else:
                        break
            else:
                # Default workday window when no sessions recorded yet
                start_hour = 9
                end_hour = 17
            keys = [f"{i:02d}" for i in range(start_hour, end_hour + 1)]
        elif self.time_range == "week":
            keys = [str(i) for i in range(7)]
        elif self.time_range == "month":
            ref_date = getattr(self, "ref_date", datetime.now())
            if ref_date.month == 12:
                num_days = 31
            else:
                num_days = (datetime(ref_date.year, ref_date.month + 1, 1) - timedelta(days=1)).day
            keys = [f"{i:02d}" for i in range(1, num_days + 1)]
        else:
            ref_year = getattr(self, "ref_date", datetime.now()).year
            keys = [f"{ref_year}-{i:02d}" for i in range(1, 13)]
            
        if not keys: return
        
        bar_width = min(40, (graph_width / len(keys)) * 0.8)
        bar_spacing = (graph_width - (bar_width * len(keys))) / max(1, (len(keys) - 1))
        
        cr.set_source_rgba(r, g, b, 0.8)
        for i, key in enumerate(keys):
            val_seconds = self.graph_data.get(key, 0)
            val_minutes = val_seconds / 60
            
            bar_h = (val_minutes / max_minutes) * graph_height if max_minutes > 0 else 0
            if bar_h > graph_height: bar_h = graph_height
            
            if bar_h > 0:
                x = margin_left + i * (bar_width + bar_spacing)
                y = height - margin_bottom - bar_h
                
                cr.new_path()
                radius = min(4, bar_width / 2)
                cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
                cr.arc(x + bar_width - radius, y + radius, radius, 3 * math.pi / 2, 2 * math.pi)
                cr.line_to(x + bar_width, height - margin_bottom)
                cr.line_to(x, height - margin_bottom)
                cr.close_path()
                cr.fill()
                
        cr.set_source_rgba(0.5, 0.5, 0.5, 0.6)
        
        def draw_x_label(idx, text):
            x = margin_left + idx * (bar_width + bar_spacing) + bar_width / 2
            layout = PangoCairo.create_layout(cr)
            layout.set_text(text, -1)
            layout.set_font_description(Pango.FontDescription.from_string("Sans 10"))
            _, extents = layout.get_pixel_extents()
            cr.move_to(x - extents.width / 2, height - margin_bottom + 8)
            PangoCairo.show_layout(cr, layout)
        
        if self.time_range == "day":
            dist = bar_width + bar_spacing
            step = max(1, int(math.ceil(45.0 / dist))) if dist > 0 else 1
            for i, key in enumerate(keys):
                if i % step == 0:
                    draw_x_label(i, f"{int(key)}:00")
        elif self.time_range == "week":
            x_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for i, label_text in enumerate(x_labels):
                draw_x_label(i, label_text)
        elif self.time_range == "month":
            for i, key in enumerate(keys):
                day_num = int(key)
                if day_num in [1, 8, 15, 22, 29]:
                    draw_x_label(i, str(day_num))
        else:
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            for i, month_text in enumerate(months):
                if i < len(keys):
                    if graph_width < 350 and i % 2 != 0:
                        continue
                    draw_x_label(i, month_text)

class StatsPage(Gtk.Box):
    def __init__(self, main_window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_halign(Gtk.Align.FILL)
        self.set_hexpand(True)
        self.main_window = main_window
        self.current_project_id = None
        self.current_time_range = "day"
        self.current_date = datetime.now()

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_halign(Gtk.Align.FILL)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(scrolled)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=32)
        self.main_box.set_halign(Gtk.Align.FILL)
        self.main_box.set_hexpand(True)
        self.main_box.set_margin_top(32)
        self.main_box.set_margin_bottom(32)
        self.main_box.set_margin_start(16)
        self.main_box.set_margin_end(16)
        scrolled.set_child(self.main_box)

        # 1. Top Toggle (Today | Week | Month | Year)
        self.mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.mode_box.add_css_class("linked")
        self.mode_box.set_halign(Gtk.Align.CENTER)
        
        self.btn_day = Gtk.ToggleButton(label="Day")
        self.btn_day.set_active(True)
        self.btn_week = Gtk.ToggleButton(label="Week")
        self.btn_month = Gtk.ToggleButton(label="Month")
        self.btn_year = Gtk.ToggleButton(label="Year")
        
        self.btn_day.connect("toggled", self._on_mode_toggled, "day")
        self.btn_week.connect("toggled", self._on_mode_toggled, "week")
        self.btn_month.connect("toggled", self._on_mode_toggled, "month")
        self.btn_year.connect("toggled", self._on_mode_toggled, "all")
        
        self.mode_box.append(self.btn_day)
        self.mode_box.append(self.btn_week)
        self.mode_box.append(self.btn_month)
        self.mode_box.append(self.btn_year)
        self.main_box.append(self.mode_box)
        
        # 2. Summary Metrics (Total Hours / Total Breaks)
        summary_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        def create_stat(val, desc):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            box.set_halign(Gtk.Align.CENTER)
            val_lbl = Gtk.Label(label=val)
            val_lbl.add_css_class("title-1")
            val_lbl.add_css_class("numeric")
            desc_lbl = Gtk.Label(label=desc)
            desc_lbl.add_css_class("dim-label")
            box.append(val_lbl)
            box.append(desc_lbl)
            return box, val_lbl
            
        focus_box, self.focus_lbl = create_stat("0h 0m", "Total focus time")
        break_box, self.breaks_lbl = create_stat("0h 0m", "Total break time")
        
        summary_box.append(focus_box)
        spacer1 = Gtk.Box()
        spacer1.set_hexpand(True)
        summary_box.append(spacer1)
        summary_box.append(break_box)
        self.main_box.append(summary_box)
        
        # 3. Controls Row (Date Picker + Nav + Project)
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls_box.set_valign(Gtk.Align.CENTER)
        controls_box.set_hexpand(True)
        
        self.cal_btn = Gtk.MenuButton()
        self.cal_btn.add_css_class("flat")
        self.cal_btn.set_size_request(150, -1)
        date_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.date_lbl = Gtk.Label(label="Today")
        self.date_lbl.set_halign(Gtk.Align.START)
        self.date_lbl.set_hexpand(True)
        self.date_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self.date_lbl.set_width_chars(12)
        self.date_lbl.set_max_width_chars(12)
        self.date_lbl.set_lines(1)
        date_btn_box.append(self.date_lbl)
        date_btn_box.append(Gtk.Image.new_from_icon_name("pan-down-symbolic"))
        self.cal_btn.set_child(date_btn_box)
        
        cal_popover = Gtk.Popover()
        self.calendar = Gtk.Calendar()
        self.calendar.connect("day-selected", self._on_calendar_date_selected)
        cal_popover.set_child(self.calendar)
        self.cal_btn.set_popover(cal_popover)
        
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        nav_box.add_css_class("linked")
        self.btn_prev = Gtk.Button(icon_name="go-previous-symbolic")
        self.btn_prev.connect("clicked", self._on_prev_clicked)
        self.btn_next = Gtk.Button(icon_name="go-next-symbolic")
        self.btn_next.connect("clicked", self._on_next_clicked)
        nav_box.append(self.btn_prev)
        nav_box.append(self.btn_next)
        
        date_nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        date_nav_box.append(nav_box)
        date_nav_box.append(self.cal_btn)
        controls_box.append(date_nav_box)
        
        spacer2 = Gtk.Box()
        spacer2.set_hexpand(True)
        controls_box.append(spacer2)
        
        self.project_model = Gtk.StringList.new(["All Projects"])
        self.project_dropdown = Gtk.DropDown(model=self.project_model)
        self.project_dropdown.set_size_request(150, -1)
        
        def setup_dropdown_cb(factory, item):
            lbl = Gtk.Label()
            lbl.set_halign(Gtk.Align.START)
            lbl.set_hexpand(True)
            lbl.set_ellipsize(Pango.EllipsizeMode.END)
            lbl.set_width_chars(12)
            lbl.set_max_width_chars(12)
            item.set_child(lbl)
            
        def bind_dropdown_cb(factory, item):
            obj = item.get_item()
            item.get_child().set_label(obj.get_string() if obj else "")
            
        dropdown_factory = Gtk.SignalListItemFactory()
        dropdown_factory.connect("setup", setup_dropdown_cb)
        dropdown_factory.connect("bind", bind_dropdown_cb)
        self.project_dropdown.set_factory(dropdown_factory)
        self.project_dropdown.connect("notify::selected", self._on_project_changed)
        
        controls_box.append(self.project_dropdown)
        
        self.main_box.append(controls_box)
        
        # 4. Graph Widget
        self.graph = GraphWidget()
        self.main_box.append(self.graph)
        
        # 5. Heatmap Widget
        heatmap_frame = Gtk.Frame()
        heatmap_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        heatmap_vbox.set_margin_top(16)
        heatmap_vbox.set_margin_bottom(16)
        heatmap_vbox.set_margin_start(16)
        heatmap_vbox.set_margin_end(16)
        
        hm_title = Gtk.Label(label="Contribution Graph")
        hm_title.add_css_class("heading")
        hm_title.set_halign(Gtk.Align.START)
        hm_title.set_margin_bottom(16)
        heatmap_vbox.append(hm_title)
        
        self.heatmap = HeatmapWidget()
        heatmap_vbox.append(self.heatmap)
        
        heatmap_frame.set_child(heatmap_vbox)
        self.main_box.append(heatmap_frame)

        self.load_projects()
        self.update_header()
        self.update_stats()

    def load_projects(self):
        projects = db.get_projects()
        self.project_map = {0: None}
        self.project_model.splice(0, self.project_model.get_n_items(), ["All Projects"])
        
        for i, (p_id, p_name) in enumerate(projects):
            self.project_model.append(p_name)
            self.project_map[i + 1] = p_id
            
    def _on_project_changed(self, dropdown, param):
        selected_idx = dropdown.get_selected()
        self.current_project_id = self.project_map.get(selected_idx)
        self.update_stats()

    def _on_mode_toggled(self, btn, mode):
        if not btn.get_active():
            if self.current_time_range == mode:
                btn.set_active(True)
            return
        self.current_time_range = mode
        self.current_date = datetime.now()
        buttons = [self.btn_day, self.btn_week, self.btn_month, self.btn_year]
        for b in buttons:
            if b != btn and b.get_active():
                b.set_active(False)
        self.update_header()
        self.update_stats()

    def _on_prev_clicked(self, btn):
        if not hasattr(self, "btn_prev") or not self.btn_prev.get_sensitive():
            return
        if self.current_time_range == "day":
            self.current_date -= timedelta(days=1)
        elif self.current_time_range == "week":
            self.current_date -= timedelta(days=7)
        elif self.current_time_range == "month":
            self.current_date -= timedelta(days=30)
            self.current_date = self.current_date.replace(day=1)
            
        self.update_header()
        self.update_stats()

    def _on_next_clicked(self, btn):
        if not hasattr(self, "btn_next") or not self.btn_next.get_sensitive():
            return
        if self.current_time_range == "day":
            self.current_date += timedelta(days=1)
        elif self.current_time_range == "week":
            self.current_date += timedelta(days=7)
        elif self.current_time_range == "month":
            self.current_date += timedelta(days=32)
            self.current_date = self.current_date.replace(day=1)
            
        self.update_header()
        self.update_stats()
        
    def _on_calendar_date_selected(self, cal):
        date = cal.get_date()
        new_date = datetime(date.get_year(), date.get_month(), date.get_day_of_month())
        if new_date.date() == self.current_date.date():
            return
            
        now = datetime.now()
        earliest_date = db.get_earliest_date()
        
        if new_date.date() > now.date():
            new_date = now
        elif new_date.date() < earliest_date:
            new_date = datetime(earliest_date.year, earliest_date.month, earliest_date.day)
            
        self.current_date = new_date
        self.cal_btn.get_popover().popdown()
        self.update_header()
        self.update_stats()

    def update_header(self):
        glib_date = GLib.DateTime.new_local(
            self.current_date.year, 
            self.current_date.month, 
            self.current_date.day, 
            0, 0, 0
        )
        self.calendar.set_date(glib_date)
        
        now = datetime.now()
        earliest_date = db.get_earliest_date()
        can_move_next = True
        can_move_prev = True
        
        if self.current_time_range == "day":
            cur_date = self.current_date.date()
            if cur_date == now.date():
                self.date_lbl.set_label("Today")
            elif cur_date == (now - timedelta(days=1)).date():
                self.date_lbl.set_label("Yesterday")
            elif cur_date == (now + timedelta(days=1)).date():
                self.date_lbl.set_label("Tomorrow")
            elif cur_date.year == now.year:
                self.date_lbl.set_label(self.current_date.strftime("%d %b"))
            else:
                self.date_lbl.set_label(self.current_date.strftime("%d %b %Y"))
            if cur_date >= now.date():
                can_move_next = False
            if cur_date <= earliest_date:
                can_move_prev = False
        elif self.current_time_range == "week":
            start = self.current_date - timedelta(days=self.current_date.weekday())
            end = start + timedelta(days=6)
            if start.year == end.year and start.year == now.year:
                if start.month == end.month:
                    self.date_lbl.set_label(f"{start.strftime('%d')} - {end.strftime('%d %b')}")
                else:
                    self.date_lbl.set_label(f"{start.strftime('%d %b')} - {end.strftime('%d %b')}")
            elif start.year == end.year:
                if start.month == end.month:
                    self.date_lbl.set_label(f"{start.strftime('%d')} - {end.strftime('%d %b %Y')}")
                else:
                    self.date_lbl.set_label(f"{start.strftime('%d %b')} - {end.strftime('%d %b %Y')}")
            else:
                self.date_lbl.set_label(f"{start.strftime('%d %b %Y')} - {end.strftime('%d %b %Y')}")
            now_start = now - timedelta(days=now.weekday())
            earliest_start = earliest_date - timedelta(days=earliest_date.weekday())
            if start.date() >= now_start.date():
                can_move_next = False
            if start.date() <= earliest_start:
                can_move_prev = False
        elif self.current_time_range == "month":
            if self.current_date.year == now.year:
                self.date_lbl.set_label(self.current_date.strftime("%b"))
            else:
                self.date_lbl.set_label(self.current_date.strftime("%b %Y"))
            if (self.current_date.year, self.current_date.month) >= (now.year, now.month):
                can_move_next = False
            if (self.current_date.year, self.current_date.month) <= (earliest_date.year, earliest_date.month):
                can_move_prev = False
        else:
            self.date_lbl.set_label("All Time")
            if self.current_date.year >= now.year:
                can_move_next = False
            if self.current_date.year <= earliest_date.year:
                can_move_prev = False
                
        if hasattr(self, "btn_prev"):
            self.btn_prev.set_sensitive(can_move_prev)
        if hasattr(self, "btn_next"):
            self.btn_next.set_sensitive(can_move_next)

    def _format_time(self, seconds):
        if seconds < 60:
            return f"{seconds}s" if seconds > 0 else "0m"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def update_stats(self):
        tr = self.current_time_range
        stats = db.get_total_stats(tr, self.current_project_id, self.current_date)
        
        self.focus_lbl.set_label(self._format_time(stats["total_focus_seconds"]))
        self.breaks_lbl.set_label(self._format_time(stats["total_break_seconds"]))
            
        graph_data = db.get_graph_data(tr, self.current_project_id, self.current_date)
        self.graph.set_data(graph_data, tr, self.current_date)
        
        heatmap_data = db.get_heatmap_data(self.current_project_id, days=365)
        self.heatmap.set_data(heatmap_data)
