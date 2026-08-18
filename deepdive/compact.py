import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib


class CompactWindow(Gtk.ApplicationWindow):
    def __init__(self, application, main_window):
        super().__init__(application=application)
        self.main_window = main_window

        self.set_decorated(False)
        self.set_resizable(False)
        self.add_css_class("compact-window")
        if self.main_window.is_submerged:
            self.add_css_class("submerge-theme")

        # Main layout
        window_handle = Gtk.WindowHandle()
        self.set_child(window_handle)

        self.connect("close-request", self._on_close_request)

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        window_handle.set_child(main_box)

        # Left section (Timer details)
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left_box.set_margin_top(16)
        left_box.set_margin_bottom(12)
        left_box.set_margin_start(16)
        left_box.set_margin_end(16)
        left_box.set_hexpand(True)
        main_box.append(left_box)

        # Top row: Title and Time
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.title_label = Gtk.Label(label="Pomodoro")
        self.title_label.add_css_class("compact-title")
        self.title_label.set_halign(Gtk.Align.START)
        
        spacer = Gtk.Box()
        spacer.set_hexpand(True)

        self.time_label = Gtk.Label(label="24:55")
        self.time_label.add_css_class("compact-time")
        self.time_label.set_halign(Gtk.Align.END)

        top_row.append(self.title_label)
        top_row.append(spacer)
        top_row.append(self.time_label)
        left_box.append(top_row)

        # Middle row: Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.5)
        self.progress_bar.add_css_class("compact-progress")
        left_box.append(self.progress_bar)

        # Bottom row: Controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        controls_box.set_halign(Gtk.Align.CENTER)

        self.btn_restart = Gtk.Button(icon_name="view-refresh-symbolic")
        self.btn_restart.add_css_class("flat")
        self.btn_restart.add_css_class("compact-btn")
        self.btn_restart.connect("clicked", self._on_restart_clicked)

        self.btn_play_pause = Gtk.Button(icon_name="media-playback-start-symbolic")
        self.btn_play_pause.add_css_class("flat")
        self.btn_play_pause.add_css_class("compact-btn")
        self.btn_play_pause.connect("clicked", self._on_play_pause_clicked)

        self.btn_skip = Gtk.Button(icon_name="media-playback-stop-symbolic")
        self.btn_skip.add_css_class("flat")
        self.btn_skip.add_css_class("compact-btn")
        self.btn_skip.connect("clicked", self._on_skip_clicked)

        controls_box.append(self.btn_restart)
        controls_box.append(self.btn_play_pause)
        controls_box.append(self.btn_skip)
        left_box.append(controls_box)

        # Right section (Separator and Restore button)
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(separator)

        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right_box.set_valign(Gtk.Align.CENTER)
        right_box.set_margin_start(8)
        right_box.set_margin_end(8)
        
        self.btn_restore = Gtk.Button(icon_name="view-restore-symbolic")
        self.btn_restore.add_css_class("flat")
        self.btn_restore.add_css_class("compact-btn")
        self.btn_restore.connect("clicked", self._on_restore_clicked)
        
        right_box.append(self.btn_restore)
        main_box.append(right_box)

    def update_display(self):
        # Read state from main window
        is_pomodoro_tab = self.main_window.view_stack.get_visible_child_name() == "pomodoro"
        
        if is_pomodoro_tab:
            title = self.main_window.timer.state
            if title in ["Short Break", "Long Break"]:
                title = "Break"
            self.title_label.set_label(title)
            
            # Progress and time
            time_left = self.main_window.timer.time_left
            total_time = getattr(self.main_window.timer, "current_total_time", self.main_window.timer.durations[self.main_window.timer.state] * 60)
            elapsed = total_time - time_left
            fraction = elapsed / total_time if total_time > 0 else 0
            self.progress_bar.set_fraction(fraction)
            
            time_str = f"{time_left // 60:02d}:{time_left % 60:02d}"
            self.time_label.set_label(time_str)
            
            # Buttons
            if self.main_window.timer.is_running:
                is_submerged = getattr(self.main_window, "is_submerged", False)
                if self.main_window.timer.state == "Focus" and is_submerged:
                    self.btn_play_pause.set_icon_name("io.github.tanaybhomia.DeepDive-symbolic")
                    self.btn_play_pause.set_sensitive(False)
                    self.btn_skip.set_label("Give Up")
                    self.btn_skip.add_css_class("destructive-action")
                    self.btn_skip.set_sensitive(True)
                else:
                    self.btn_play_pause.set_icon_name("media-playback-pause-symbolic")
                    self.btn_skip.set_label("")
                    self.btn_skip.set_icon_name("media-skip-forward-symbolic")
                    self.btn_skip.remove_css_class("destructive-action")
                    self.btn_skip.set_sensitive(self.main_window.timer.state != "Focus")
                
                self.btn_restart.set_sensitive(self.main_window.timer.state != "Focus")
            else:
                self.btn_play_pause.set_icon_name("media-playback-start-symbolic")
                self.btn_play_pause.set_sensitive(True)
                self.btn_restart.set_sensitive(True)
                self.btn_skip.set_label("")
                self.btn_skip.set_icon_name("media-skip-forward-symbolic")
                self.btn_skip.remove_css_class("destructive-action")
                self.btn_skip.set_sensitive(True)
            
            # Color
            self.progress_bar.remove_css_class("short-break-state")
            self.progress_bar.remove_css_class("long-break-state")
            self.progress_bar.remove_css_class("focus-state")
            
            if self.main_window.timer.state == "Focus":
                self.progress_bar.add_css_class("focus-state")
            elif self.main_window.timer.state == "Short Break":
                self.progress_bar.add_css_class("short-break-state")
            else:
                self.progress_bar.add_css_class("long-break-state")
                
        else:
            self.title_label.set_label("Stopwatch")
            
            secs = self.main_window.stopwatch.elapsed_seconds
            time_str = f"{secs // 3600:02d}:{(secs % 3600) // 60:02d}:{secs % 60:02d}"
            if secs < 3600:
                time_str = f"{secs // 60:02d}:{secs % 60:02d}"
                
            self.time_label.set_label(time_str)
            self.progress_bar.set_fraction(0.0) # Stopwatch doesn't have a max
            self.progress_bar.remove_css_class("short-break-state")
            self.progress_bar.remove_css_class("long-break-state")
            self.progress_bar.add_css_class("focus-state")
            
            if self.main_window.stopwatch.is_running:
                self.btn_play_pause.set_icon_name("media-playback-pause-symbolic")
                self.btn_restart.set_sensitive(False)
                self.btn_skip.set_sensitive(False)
            else:
                self.btn_play_pause.set_icon_name("media-playback-start-symbolic")
                self.btn_restart.set_sensitive(True)
                self.btn_skip.set_sensitive(True)
                
            self.btn_skip.set_icon_name("document-save-symbolic")

    def _on_play_pause_clicked(self, button):
        is_pomodoro_tab = self.main_window.view_stack.get_visible_child_name() == "pomodoro"
        if is_pomodoro_tab:
            self.main_window._on_play_pause_clicked(button)
        else:
            self.main_window._on_sw_play_pause_clicked(button)
        self.update_display()

    def _on_restart_clicked(self, button):
        is_pomodoro_tab = self.main_window.view_stack.get_visible_child_name() == "pomodoro"
        if is_pomodoro_tab:
            self.main_window._on_restart_clicked(button)
        else:
            self.main_window._on_sw_restart_clicked(button)
        self.update_display()

    def _on_skip_clicked(self, button):
        is_pomodoro_tab = self.main_window.view_stack.get_visible_child_name() == "pomodoro"
        if is_pomodoro_tab:
            self.main_window._on_break_clicked(button)
        else:
            self.main_window._on_sw_save_clicked(button)
        self.update_display()

    def _on_restore_clicked(self, button):
        self.set_visible(False)
        self.main_window.present()

    def _on_close_request(self, *args):
        app = self.get_application()
        if app:
            app._attempt_quit(self.main_window)
        return True
