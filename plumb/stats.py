import gi
import math
import cairo
from datetime import datetime, timedelta

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gtk, Adw, GLib, Gdk, Pango, PangoCairo
from plumb.database import db

class GraphWidget(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(-1, 260)
        self.set_draw_func(self.on_draw)
        self.graph_data = {}
        self.tooltip_data = {}
        self.time_range = "day"
        self.accent_color = (0, 0, 0, 1)
        self.hovered_key = None
        self.column_bounds = {}
        
        self.set_has_tooltip(True)
        self.connect("query-tooltip", self.on_query_tooltip)
        
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self.on_motion)
        motion.connect("leave", self.on_leave)
        self.add_controller(motion)
        
    def set_data(self, data, time_range, ref_date=None, tooltip_data=None):
        self.graph_data = data
        self.tooltip_data = tooltip_data or {}
        self.time_range = time_range
        self.ref_date = ref_date or datetime.now()
        self.queue_draw()

    def on_query_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        if keyboard_mode or not self.column_bounds:
            return False
            
        for key, (cx_start, cx_end) in self.column_bounds.items():
            if cx_start <= x <= cx_end:
                text = self.tooltip_data.get(key)
                if text:
                    tooltip.set_text(text)
                    return True
        return False

    def on_motion(self, controller, x, y):
        new_hovered = None
        if self.column_bounds:
            for key, (cx_start, cx_end) in self.column_bounds.items():
                if cx_start <= x <= cx_end and self.graph_data.get(key, 0) > 0:
                    new_hovered = key
                    break
        if new_hovered != self.hovered_key:
            self.hovered_key = new_hovered
            self.queue_draw()

    def on_leave(self, controller):
        if self.hovered_key is not None:
            self.hovered_key = None
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
        
        if self.time_range == "day":
            max_minutes = 60
            y_labels = ["60m", "40m", "20m", "0m"]
        else:
            if max_val_minutes == 0:
                if self.time_range == "week": max_minutes = 180
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
        
        self.column_bounds = {}
        for i, key in enumerate(keys):
            val_seconds = self.graph_data.get(key, 0)
            val_minutes = val_seconds / 60
            
            x = margin_left + i * (bar_width + bar_spacing)
            col_start = x - (bar_spacing / 2 if i > 0 else 5)
            col_end = x + bar_width + (bar_spacing / 2 if i < len(keys) - 1 else 5)
            self.column_bounds[key] = (col_start, col_end)
            
            bar_h = (val_minutes / max_minutes) * graph_height if max_minutes > 0 else 0
            if bar_h > graph_height: bar_h = graph_height
            
            if bar_h > 0:
                y = height - margin_bottom - bar_h
                
                if key == getattr(self, "hovered_key", None):
                    cr.set_source_rgba(r, g, b, 1.0)
                else:
                    cr.set_source_rgba(r, g, b, 0.85)
                
                cr.new_path()
                radius = min(4, bar_width / 2)
                cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
                cr.arc(x + bar_width - radius, y + radius, radius, 3 * math.pi / 2, 2 * math.pi)
                cr.line_to(x + bar_width, height - margin_bottom)
                cr.line_to(x, height - margin_bottom)
                cr.close_path()
                cr.fill()
                
        active_vals = [self.graph_data.get(k, 0) / 60.0 for k in keys if self.graph_data.get(k, 0) > 0]
        if active_vals and max_minutes > 0:
            avg_val_minutes = sum(active_vals) / len(active_vals)
            avg_y = height - margin_bottom - (avg_val_minutes / max_minutes) * graph_height
            if margin_top <= avg_y <= (height - margin_bottom - 10):
                context = self.get_style_context()
                success, fg_rgba = context.lookup_color("theme_fg_color")
                is_dark = success and (fg_rgba.red > 0.5 and fg_rgba.green > 0.5)
                line_rgba = (0.9, 0.9, 0.95, 0.75) if is_dark else (0.15, 0.20, 0.25, 0.75)
                text_rgba = (0.95, 0.95, 1.0, 0.95) if is_dark else (0.15, 0.20, 0.25, 0.95)

                cr.save()
                cr.set_source_rgba(*line_rgba)
                cr.set_line_width(1.5)
                cr.set_dash([5, 4], 0)
                cr.move_to(margin_left, avg_y)
                cr.line_to(width - margin_right, avg_y)
                cr.stroke()
                cr.restore()
                
                # Format average text value
                rounded_avg = int(round(avg_val_minutes))
                if rounded_avg < 60:
                    avg_text = f"Avg {rounded_avg}m"
                else:
                    h = rounded_avg // 60
                    m = rounded_avg % 60
                    avg_text = f"Avg {h}h {m}m" if m > 0 else f"Avg {h}h"
                
                layout = PangoCairo.create_layout(cr)
                layout.set_text(avg_text, -1)
                layout.set_font_description(Pango.FontDescription.from_string("Sans Bold 9"))
                _, extents = layout.get_pixel_extents()
                
                tx = width - margin_right - extents.width - 4
                ty = avg_y - extents.height - 4
                
                # Display average numeric label directly above the dashed line with clean, high-contrast typography
                cr.set_source_rgba(*text_rgba)
                cr.move_to(tx, ty)
                PangoCairo.show_layout(cr, layout)
                
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
        
        # 2. Controls Row (Date Picker + Nav + Project)
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls_box.set_valign(Gtk.Align.CENTER)
        controls_box.set_hexpand(True)
        
        self.cal_btn = Gtk.MenuButton()
        self.cal_btn.set_size_request(150, -1)
        date_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.date_lbl = Gtk.Label(label="Day")
        self.date_lbl.set_halign(Gtk.Align.START)
        self.date_lbl.set_hexpand(True)
        self.date_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self.date_lbl.set_width_chars(12)
        self.date_lbl.set_max_width_chars(12)
        self.date_lbl.set_lines(1)
        date_btn_box.append(self.date_lbl)
        date_btn_box.append(Gtk.Image.new_from_icon_name("x-office-calendar-symbolic"))
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
        
        main_card = Gtk.Frame()
        main_card.add_css_class("card")
        main_card.add_css_class("stats-card")
        main_card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        summary_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        summary_box.set_margin_top(20)
        summary_box.set_margin_bottom(16)
        summary_box.set_margin_start(24)
        summary_box.set_margin_end(24)
        
        def create_stat(val, desc, align_right=False):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            align = Gtk.Align.END if align_right else Gtk.Align.START
            box.set_halign(align)
            val_lbl = Gtk.Label(label=val)
            val_lbl.add_css_class("title-1")
            val_lbl.add_css_class("numeric")
            val_lbl.set_halign(align)
            desc_lbl = Gtk.Label(label=desc)
            desc_lbl.add_css_class("dim-label")
            desc_lbl.set_halign(align)
            box.append(val_lbl)
            box.append(desc_lbl)
            return box, val_lbl
            
        focus_box, self.focus_lbl = create_stat("0h 0m", "Total focus time")
        break_box, self.breaks_lbl = create_stat("0h 0m", "Total break time", align_right=True)
        
        summary_box.append(focus_box)
        spacer1 = Gtk.Box()
        spacer1.set_hexpand(True)
        summary_box.append(spacer1)
        summary_box.append(break_box)
        main_card_box.append(summary_box)
        
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_card_box.append(sep)
        
        self.graph = GraphWidget()
        main_card_box.append(self.graph)
        
        main_card.set_child(main_card_box)
        self.main_box.append(main_card)
        
        # 4. Productivity Insights Section
        insights_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        insights_vbox.set_margin_top(16)
        
        ins_title = Gtk.Label(label="Insights")
        ins_title.add_css_class("title-2")
        ins_title.set_halign(Gtk.Align.START)
        insights_vbox.append(ins_title)
        
        def create_insight_card(icon_name=None):
            frame = Gtk.Frame()
            frame.add_css_class("card")
            frame.add_css_class("stats-card")
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            box.set_margin_top(16)
            box.set_margin_bottom(16)
            box.set_margin_start(18)
            box.set_margin_end(18)
            box.set_hexpand(True)
            
            header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            title_lbl = Gtk.Label(label="")
            title_lbl.add_css_class("dim-label")
            title_lbl.add_css_class("caption")
            title_lbl.set_halign(Gtk.Align.START)
            header_box.append(title_lbl)
            
            if icon_name:
                spacer = Gtk.Box()
                spacer.set_hexpand(True)
                header_box.append(spacer)
                icon = Gtk.Image.new_from_icon_name(icon_name)
                icon.add_css_class("dim-label")
                header_box.append(icon)
            
            val_lbl = Gtk.Label(label="-")
            val_lbl.add_css_class("title-2")
            val_lbl.add_css_class("numeric")
            val_lbl.set_halign(Gtk.Align.START)
            val_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            val_lbl.set_max_width_chars(15)
            val_lbl.set_margin_top(4)
            
            sub_lbl = Gtk.Label(label="-")
            sub_lbl.add_css_class("dim-label")
            sub_lbl.add_css_class("caption")
            sub_lbl.set_halign(Gtk.Align.START)
            sub_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            
            box.append(header_box)
            box.append(val_lbl)
            box.append(sub_lbl)
            frame.set_child(box)
            return frame, title_lbl, val_lbl, sub_lbl
            
        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row1.set_homogeneous(True)
        card_proj, self.lbl_proj_title, self.lbl_proj_val, self.lbl_proj_sub = create_insight_card("folder-documents-symbolic")
        card_peak, self.lbl_peak_title, self.lbl_peak_val, self.lbl_peak_sub = create_insight_card("starred-symbolic")
        row1.append(card_proj)
        row1.append(card_peak)
        
        row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row2.set_homogeneous(True)
        card_avg, self.lbl_avg_title, self.lbl_avg_val, self.lbl_avg_sub = create_insight_card("document-open-recent-symbolic")
        card_sess, self.lbl_sess_title, self.lbl_sess_val, self.lbl_sess_sub = create_insight_card("object-select-symbolic")
        row2.append(card_avg)
        row2.append(card_sess)
        
        insights_vbox.append(row1)
        insights_vbox.append(row2)
        # self.main_box.append(insights_vbox)  # Hidden for future refinement

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
        tooltip_data = db.get_graph_tooltips(tr, self.current_project_id, self.current_date)
        self.graph.set_data(graph_data, tr, self.current_date, tooltip_data)
