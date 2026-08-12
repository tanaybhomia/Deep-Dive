import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gdk, Gio, GObject, GLib
from plumb.timer import TimerLogic, StopwatchLogic
from plumb.database import db

import random
import math
import cairo


class SegmentedProgressBar(Gtk.DrawingArea):
    def __init__(self, segments=4):
        super().__init__()
        self.set_size_request(-1, 56)
        self.set_hexpand(True)
        self.fraction = 0.0
        self.current_segment = 1
        self.total_segments = segments
        self.set_draw_func(self.on_draw)

    def set_fraction(self, fraction):
        new_frac = max(0.0, min(1.0, fraction))
        if abs(self.fraction - new_frac) > 0.001 or (new_frac in (0.0, 1.0) and self.fraction != new_frac):
            self.fraction = new_frac
            self.queue_draw()

    def set_cycle_info(self, current_cycle, total_cycles):
        if total_cycles > 0 and (self.current_segment != current_cycle or self.total_segments != total_cycles):
            self.current_segment = current_cycle
            self.total_segments = total_cycles
            self.queue_draw()

    def add_css_class(self, css_class):
        super().add_css_class(css_class)
        self.queue_draw()

    def remove_css_class(self, css_class):
        super().remove_css_class(css_class)
        self.queue_draw()

    def on_draw(self, drawing_area, cr, width, height):
        if width <= 0 or height <= 0 or self.total_segments <= 0:
            return
            
        radius = min(14, height / 2, width / 2)
        
        context = self.get_style_context()
        if self.has_css_class("short-break-state") or self.has_css_class("long-break-state"):
            success, col = context.lookup_color("success_color")
            if not success: col = Gdk.RGBA(0.18, 0.76, 0.49, 1.0)
        else:
            success, col = context.lookup_color("accent_bg_color")
            if not success: col = Gdk.RGBA(0.2, 0.5, 0.9, 1.0)
        active_rgba = (col.red, col.green, col.blue, 1.0)
        
        success, fg = context.lookup_color("theme_fg_color")
        is_dark = (fg.red > 0.6) if success else True
        if is_dark:
            trough_rgba = (1.0, 1.0, 1.0, 0.12)
        else:
            trough_rgba = (0.0, 0.0, 0.0, 0.08)
            
        root = self.get_root()
        is_submerge = root and root.has_css_class("submerge-theme")
        if is_submerge:
            if is_dark:
                sep_rgba = (0.031, 0.129, 0.243, 1.0)
            else:
                sep_rgba = (0.800, 0.894, 0.969, 1.0)
        else:
            success, bg = context.lookup_color("window_bg_color")
            if success:
                sep_rgba = (bg.red, bg.green, bg.blue, 1.0)
            else:
                sep_rgba = (0.14, 0.14, 0.14, 1.0) if is_dark else (0.98, 0.98, 0.98, 1.0)
            
        def draw_rounded_rect(cx, cy, cw, ch, rad):
            cr.new_path()
            cr.arc(cx + rad, cy + rad, rad, math.pi, 3 * math.pi / 2)
            cr.arc(cx + cw - rad, cy + rad, rad, 3 * math.pi / 2, 2 * math.pi)
            cr.arc(cx + cw - rad, cy + ch - rad, rad, 0, math.pi / 2)
            cr.arc(cx + rad, cy + ch - rad, rad, math.pi / 2, math.pi)
            cr.close_path()
            
        # 1. Draw Background Trough
        cr.set_source_rgba(*trough_rgba)
        draw_rounded_rect(0, 0, width, height, radius)
        cr.fill()
        
        # 2. Draw Continuous Active Fill
        is_break = self.has_css_class("short-break-state") or self.has_css_class("long-break-state")
        
        if self.fraction > 0 or (self.current_segment > 1 and not is_break):
            cr.save()
            draw_rounded_rect(0, 0, width, height, radius)
            cr.clip()
            
            success, focus_col = context.lookup_color("accent_bg_color")
            if not success: focus_col = Gdk.RGBA(0.2, 0.5, 0.9, 1.0)
            focus_rgba = (focus_col.red, focus_col.green, focus_col.blue, 1.0)
            
            if is_break:
                # Break mode: single unified bar representing the break duration
                if self.fraction > 0:
                    cr.set_source_rgba(*active_rgba)
                    cr.rectangle(0, 0, width * self.fraction, height)
                    cr.fill()
            else:
                # Focus mode: Fill previous segments completely in focus color
                base_fraction = (self.current_segment - 1) / max(1, self.total_segments)
                if base_fraction > 0:
                    cr.set_source_rgba(*focus_rgba)
                    cr.rectangle(0, 0, width * base_fraction, height)
                    cr.fill()
                
                # Draw the current segment in active color
                if self.fraction > 0:
                    segment_fraction = self.fraction / max(1, self.total_segments)
                    cr.set_source_rgba(*active_rgba)
                    cr.rectangle(width * base_fraction, 0, width * segment_fraction, height)
                    cr.fill()
                
            cr.restore()
            
        # 3. Draw Engraved Separators
        if self.total_segments > 1 and not is_break:
            for idx in range(1, self.total_segments):
                x = (width * idx) / self.total_segments
                cr.set_source_rgba(*sep_rgba)
                cr.rectangle(x - 1.25, 0, 2.5, height)
                cr.fill()


class BreakOverlayWindow(Gtk.Window):
    def __init__(self, on_dismiss_cb, show_quotes=True, **kwargs):
        super().__init__(**kwargs)
        self.on_dismiss_cb = on_dismiss_cb
        self.set_decorated(False)
        self.remove_css_class("background")
        self.add_css_class("break-overlay-window")

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        center_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=48)
        center_vbox.set_valign(Gtk.Align.CENTER)
        center_vbox.set_halign(Gtk.Align.CENTER)
        center_vbox.set_vexpand(True)

        title = Gtk.Label(label="Take a Break")
        title.add_css_class("title-1")

        self.time_label = Gtk.Label(label="00:00")
        self.time_label.add_css_class("huge-timer")

        dismiss_btn = Gtk.Button(label="Dismiss (Esc)")
        dismiss_btn.add_css_class("pill")
        dismiss_btn.connect("clicked", self._on_dismiss)

        center_vbox.append(title)
        center_vbox.append(self.time_label)
        center_vbox.append(dismiss_btn)

        main_vbox.append(center_vbox)

        if show_quotes:
            quotes = [
                "Time to stretch those legs!",
                "Grab a glass of water.",
                "Look away from the screen for 20 seconds.",
                "Your eyes will thank you.",
                "Resting is productive too.",
                "Take a deep breath and relax.",
            ]
            quote_label = Gtk.Label(label=random.choice(quotes))
            quote_label.add_css_class("overlay-quote")
            quote_label.set_margin_bottom(48)
            quote_label.set_halign(Gtk.Align.CENTER)
            main_vbox.append(quote_label)

        self.set_child(main_vbox)

        key_ctrl = Gtk.EventControllerKey.new()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self._on_dismiss(None)
            return True
        return False

    def _on_dismiss(self, button):
        if self.on_dismiss_cb:
            self.on_dismiss_cb()

    def update_time(self, time_str):
        self.time_label.set_label(time_str)


class PlumbWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Plumb")
        self.set_default_size(435, 640)
        self.set_size_request(360, 500)

        self.timer = TimerLogic()
        self.timer.on_tick_callback = self._on_timer_tick
        self.timer.on_state_change_callback = self._on_state_change
        self.timer.on_finish_callback = self._on_timer_finish
        self.timer.on_warning_callback = self._on_timer_warning
        self.timer.on_run_state_change_callback = self._set_running_ui_state

        self._overlays = []

        self.stopwatch = StopwatchLogic()
        self.stopwatch.on_tick_callback = self._on_stopwatch_tick

        self.toolbar_view = Adw.ToolbarView()
        self.toolbar_view.set_size_request(435, 640)
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toolbar_view)

        self.header = Adw.HeaderBar()
        self.toolbar_view.add_top_bar(self.header)
        
        self.btn_compact = Gtk.Button(icon_name="view-restore-symbolic")
        self.btn_compact.set_tooltip_text("Mini Player")
        self.btn_compact.connect("clicked", self._on_compact_clicked)
        self.header.pack_start(self.btn_compact)
        
        self.is_submerged = db.get_setting("submerge_mode", "False") == "True"
        self.btn_submerge = Gtk.ToggleButton(icon_name="anchor-symbolic")
        self.btn_submerge.set_active(self.is_submerged)
        self.btn_submerge.set_tooltip_text("Submerge Mode")
        self.btn_submerge.set_can_focus(False)
        self.btn_submerge.set_can_focus(False)
        self.btn_submerge.connect("toggled", self._on_submerge_toggled)
        self.header.pack_start(self.btn_submerge)
        self._update_submerge_theme()
        style_manager = Adw.StyleManager.get_default()
        style_manager.connect("notify::dark", self._on_dark_changed)
        self._on_dark_changed(style_manager, None)

        self.view_stack = Adw.ViewStack()
        self.view_stack.add_titled_with_icon(Gtk.Box(), "pomodoro", "Pomodoro", "alarm-symbolic")
        self.view_stack.add_titled_with_icon(Gtk.Box(), "timer", "Timer", "document-open-recent-symbolic")
        self.view_stack.add_titled_with_icon(Gtk.Box(), "stats", "Stats", "graph-symbolic")
        
        self.main_stack = Gtk.Stack()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        self.swipe_gesture = Gtk.GestureSwipe.new()
        self.swipe_gesture.connect("swipe", self._on_swipe)
        self.main_stack.add_controller(self.swipe_gesture)

        self.toast_overlay.set_child(self.main_stack)
        self.toolbar_view.set_content(self.toast_overlay)

        self.key_ctrl = Gtk.EventControllerKey.new()
        self.key_ctrl.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self.key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(self.key_ctrl)

        self.switcher_bar = Adw.ViewSwitcherBar(stack=self.view_stack)
        self.switcher_bar.set_reveal(True)
        self.toolbar_view.add_bottom_bar(self.switcher_bar)

        self.view_stack.connect("notify::visible-child", self._on_view_stack_changed)

        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_icon_name("open-menu-symbolic")

        menu = Gio.Menu()

        theme_menu = Gio.Menu()
        theme_menu.append("System Default", "app.theme-system")
        theme_menu.append("Light", "app.theme-light")
        theme_menu.append("Dark", "app.theme-dark")
        menu.append_submenu("Theme", theme_menu)

        menu.append("Keyboard Shortcuts", "app.shortcuts")
        menu.append("Preferences", "app.preferences")
        menu.append("About Plumb", "app.about")

        self.menu_button.set_menu_model(menu)
        self.header.pack_end(self.menu_button)

        self._build_shortcuts_window()

        self.balance_button = Gtk.MenuButton()
        self.balance_button.set_icon_name("open-menu-symbolic")
        self.balance_button.set_opacity(0)
        self.balance_button.set_sensitive(False)
        self.header.pack_start(self.balance_button)

        self._project_list = Gtk.StringList()
        self._projects_map = []
        self._load_projects()

        self.pomodoro_page = self._build_pomodoro_page()
        self.timer_page = self._build_timer_page()
        from plumb.stats import StatsPage
        self.stats_page = StatsPage(main_window=self)

        pomo_clamp = Adw.Clamp(maximum_size=500, child=self.pomodoro_page)
        timer_clamp = Adw.Clamp(maximum_size=500, child=self.timer_page)
        stats_clamp = Adw.Clamp(maximum_size=750, child=self.stats_page)

        self.main_stack.add_named(pomo_clamp, "pomodoro")
        self.main_stack.add_named(timer_clamp, "timer")
        self.main_stack.add_named(stats_clamp, "stats")

        self._update_time_display()
        self._set_running_ui_state(False)
        self.add_css_class("focus-window")



        saved_theme = db.get_setting("theme", "system")
        style_mgr = Adw.StyleManager.get_default()
        if saved_theme == "light":
            style_mgr.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif saved_theme == "dark":
            style_mgr.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_mgr.set_color_scheme(Adw.ColorScheme.DEFAULT)

        self._update_sw_time_display()
        self._set_sw_running_ui_state(False)

        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            bus.signal_subscribe(
                "org.gnome.ScreenSaver",
                "org.gnome.ScreenSaver",
                "ActiveChanged",
                "/org/gnome/ScreenSaver",
                None,
                Gio.DBusSignalFlags.NONE,
                self._on_screensaver_active_changed,
            )
        except Exception as e:
            pass

    # self.connect("close-request", self._on_close_request) is now handled by application.py

    def _on_screensaver_active_changed(
        self,
        connection,
        sender_name,
        object_path,
        interface_name,
        signal_name,
        parameters,
    ):
        is_active = parameters.unpack()[0]
        if is_active and self.timer.pause_on_lock and self.timer.is_running:
            self.timer.pause()
            self._set_running_ui_state(False)

    def _on_swipe(self, gesture, velocity_x, velocity_y):
        if self.timer.is_running or (hasattr(self, 'stopwatch') and self.stopwatch.elapsed_seconds > 0):
            return
        if abs(velocity_x) > abs(velocity_y) and abs(velocity_x) > 200:
            pages = ["pomodoro", "timer", "stats"]
            current = self.view_stack.get_visible_child_name()
            if current in pages:
                idx = pages.index(current)
                if velocity_x < 0 and idx < len(pages) - 1:
                    self.view_stack.set_visible_child_name(pages[idx + 1])
                elif velocity_x > 0 and idx > 0:
                    self.view_stack.set_visible_child_name(pages[idx - 1])

    def _build_shortcuts_window(self):
        xml = """
        <interface>
          <object class="GtkShortcutsWindow" id="shortcuts">
            <property name="modal">True</property>
            <child>
              <object class="GtkShortcutsSection">
                <property name="section-name">shortcuts</property>
                <property name="title">General</property>
                <child>
                  <object class="GtkShortcutsGroup">
                    <property name="title">Navigation</property>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title">Go to Pomodoro</property>
                        <property name="accelerator">&lt;Alt&gt;1</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title">Go to Timer</property>
                        <property name="accelerator">&lt;Alt&gt;2</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title">Go to Stats</property>
                        <property name="accelerator">&lt;Alt&gt;3</property>
                      </object>
                    </child>
                  </object>
                </child>
                <child>
                  <object class="GtkShortcutsGroup">
                    <property name="title">Application</property>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title">Preferences</property>
                        <property name="accelerator">&lt;Primary&gt;comma</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title">Keyboard Shortcuts</property>
                        <property name="accelerator">&lt;Primary&gt;question</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title">Toggle Mini Player</property>
                        <property name="accelerator">&lt;Primary&gt;m</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title">Toggle Submerge Mode</property>
                        <property name="accelerator">&lt;Primary&gt;&lt;Shift&gt;i</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title">Quit</property>
                        <property name="accelerator">&lt;Primary&gt;q</property>
                      </object>
                    </child>
                  </object>
                </child>
                <child>
                  <object class="GtkShortcutsGroup">
                    <property name="title">Timer</property>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title">Play / Pause Timer</property>
                        <property name="accelerator">space</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title">Restart Timer</property>
                        <property name="accelerator">r</property>
                      </object>
                    </child>
                    <child>
                      <object class="GtkShortcutsShortcut">
                        <property name="title">Save / Skip Session</property>
                        <property name="accelerator">s</property>
                      </object>
                    </child>
                  </object>
                </child>
              </object>
            </child>
          </object>
        </interface>
        """
        builder = Gtk.Builder.new_from_string(xml, -1)
        shortcuts = builder.get_object("shortcuts")
        self.set_help_overlay(shortcuts)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        is_alt = (state & Gdk.ModifierType.ALT_MASK) != 0
        
        if is_alt:
            if keyval == Gdk.KEY_1:
                self.view_stack.set_visible_child_name("pomodoro")
                return True
            elif keyval == Gdk.KEY_2:
                self.view_stack.set_visible_child_name("timer")
                return True
            elif keyval == Gdk.KEY_3:
                self.view_stack.set_visible_child_name("stats")
                return True

        current_page = self.view_stack.get_visible_child_name()

        if keyval == Gdk.KEY_space:
            if current_page == "pomodoro":
                self._on_play_pause_clicked(None)
                return True
            elif current_page == "timer":
                self._on_sw_play_pause_clicked(None)
                return True
                
        elif keyval in (Gdk.KEY_r, Gdk.KEY_R):
            if current_page == "pomodoro" and self.restart_btn.get_sensitive() and self.restart_btn.get_visible():
                self.restart_btn.emit("clicked")
                return True
            elif current_page == "timer" and self.sw_restart_btn.get_sensitive() and self.sw_restart_btn.get_visible():
                self.sw_restart_btn.emit("clicked")
                return True
                
        elif keyval in (Gdk.KEY_s, Gdk.KEY_S):
            if current_page == "pomodoro" and self.break_btn.get_sensitive() and self.break_btn.get_visible():
                self.break_btn.emit("clicked")
                return True
            elif current_page == "timer" and self.sw_save_btn.get_sensitive() and self.sw_save_btn.get_visible():
                self.sw_save_btn.emit("clicked")
                return True

        return False



    def _on_view_stack_changed(self, stack, param):
        name = stack.get_visible_child_name()
        if hasattr(self, 'main_stack') and name:
            self.main_stack.set_visible_child_name(name)
        if name == "stats" and hasattr(self, 'stats_page'):
            self.stats_page.update_stats()

    def _build_pomodoro_page(self):
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=48)
        page_box.set_valign(Gtk.Align.CENTER)
        page_box.set_halign(Gtk.Align.CENTER)
        page_box.set_margin_start(32)
        page_box.set_margin_end(32)
        page_box.set_margin_top(32)
        page_box.set_margin_bottom(32)

        self.project_dropdown_stack = Gtk.Stack()
        self.project_dropdown_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.project_dropdown_stack.set_halign(Gtk.Align.CENTER)
        self.project_dropdown_stack.set_hhomogeneous(False)

        self.project_dropdown = Gtk.DropDown.new(model=self._project_list)
        self.project_dropdown.connect("notify::selected", self._on_project_selected)
        popover = self.project_dropdown.get_last_child()
        if popover:
            popover.set_halign(Gtk.Align.CENTER)
            
        self.project_dropdown_stack.add_named(self.project_dropdown, "dropdown")
        
        self.break_state_label = Gtk.Label(label="Short Break")
        self.break_state_label.add_css_class("title-4")
        self.project_dropdown_stack.add_named(self.break_state_label, "break_label")

        page_box.append(self.project_dropdown_stack)

        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)

        self.progress_bar = SegmentedProgressBar(4)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_hexpand(True)
        self.progress_bar.add_css_class("focus-state")
        progress_box.append(self.progress_bar)

        time_labels_box = Gtk.CenterBox()

        self.elapsed_label = Gtk.Label(label="00:00")
        self.elapsed_label.add_css_class("title-1")

        self.cycle_label = Gtk.Label(label="1/4")
        self.cycle_label.add_css_class("cycle-indicator")

        self.total_label = Gtk.Label(label="25:00")
        self.total_label.add_css_class("title-1")

        time_labels_box.set_start_widget(self.elapsed_label)
        time_labels_box.set_center_widget(self.cycle_label)
        time_labels_box.set_end_widget(self.total_label)

        progress_box.append(time_labels_box)

        middle_container = Gtk.CenterBox()
        middle_container.set_size_request(-1, 140)
        middle_container.set_center_widget(progress_box)
        page_box.append(middle_container)

        self.action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.action_box.set_halign(Gtk.Align.CENTER)

        self.restart_btn = Gtk.Button(label="Restart")
        self.restart_btn.add_css_class("action-pill")
        self.restart_btn.connect("clicked", self._on_restart_clicked)

        self.play_pause_btn = Gtk.Button()
        self.play_pause_btn.set_icon_name("media-playback-start-symbolic")
        self.play_pause_btn.add_css_class("play-circular")
        self.play_pause_btn.connect("clicked", self._on_play_pause_clicked)

        self.break_btn = Gtk.Button(label="Skip")
        self.break_btn.add_css_class("action-pill")
        self.break_btn.connect("clicked", self._on_break_clicked)

        self.action_box.append(self.restart_btn)
        self.action_box.append(self.play_pause_btn)
        self.action_box.append(self.break_btn)

        page_box.append(self.action_box)

        return page_box

    def _build_timer_page(self):
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=48)
        page_box.set_valign(Gtk.Align.CENTER)
        page_box.set_halign(Gtk.Align.CENTER)
        page_box.set_margin_start(32)
        page_box.set_margin_end(32)
        page_box.set_margin_top(32)
        page_box.set_margin_bottom(32)

        self.sw_project_dropdown = Gtk.DropDown.new(model=self._project_list)
        self.sw_project_dropdown.connect("notify::selected", self._on_project_selected)
        self.sw_project_dropdown.set_halign(Gtk.Align.CENTER)

        popover = self.sw_project_dropdown.get_last_child()
        if popover:
            popover.set_halign(Gtk.Align.CENTER)
        page_box.append(self.sw_project_dropdown)

        self.sw_time_label = Gtk.Label(label="00:00")
        self.sw_time_label.add_css_class("huge-timer")
        self.sw_time_label.set_halign(Gtk.Align.CENTER)
        self.sw_time_label.set_valign(Gtk.Align.CENTER)
        self.sw_time_label.set_margin_bottom(24)

        spacer = Gtk.Box()
        spacer.set_size_request(-1, 140)

        middle_container = Gtk.Overlay()
        middle_container.set_child(spacer)
        middle_container.add_overlay(self.sw_time_label)
        middle_container.set_measure_overlay(self.sw_time_label, False)
        page_box.append(middle_container)

        self.sw_action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.sw_action_box.set_halign(Gtk.Align.CENTER)

        self.sw_restart_btn = Gtk.Button(label="Restart")
        self.sw_restart_btn.add_css_class("action-pill")
        self.sw_restart_btn.connect("clicked", self._on_sw_restart_clicked)

        self.sw_play_pause_btn = Gtk.Button()
        self.sw_play_pause_btn.set_icon_name("media-playback-start-symbolic")
        self.sw_play_pause_btn.add_css_class("play-circular")
        self.sw_play_pause_btn.connect("clicked", self._on_sw_play_pause_clicked)

        self.sw_save_btn = Gtk.Button(label="Save")
        self.sw_save_btn.add_css_class("action-pill")
        self.sw_save_btn.connect("clicked", self._on_sw_save_clicked)

        self.sw_action_box.append(self.sw_restart_btn)
        self.sw_action_box.append(self.sw_play_pause_btn)
        self.sw_action_box.append(self.sw_save_btn)

        page_box.append(self.sw_action_box)

        return page_box

    def _set_running_ui_state(self, is_running):
        self.switcher_bar.set_sensitive(not is_running)
        
        is_active = is_running or self.timer.time_left < (self.timer.durations.get(self.timer.state, 0) * 60)

        self.project_dropdown.set_sensitive(not is_active)
        self.project_dropdown.set_show_arrow(not is_active)
        
        if is_active:
            self.project_dropdown.remove_css_class("pill")
            self.project_dropdown.add_css_class("flat")
            self.project_dropdown.add_css_class("title-4")
        else:
            self.project_dropdown.remove_css_class("flat")
            self.project_dropdown.remove_css_class("title-4")
            self.project_dropdown.add_css_class("pill")

        if is_running:
            self.btn_submerge.set_sensitive(False)
            master_enabled = db.get_setting("web_blocker_enabled", "False") == "True"
            normal_enabled = db.get_setting("web_blocker_normal_mode", "False") == "True"
            
            if self.timer.state == "Focus" and master_enabled and (self.is_submerged or normal_enabled):
                self._block_websites()

            if self.is_submerged and self.timer.state == "Focus":
                self.play_pause_btn.set_icon_name("anchor-symbolic")
                self.play_pause_btn.set_sensitive(False)
                
                self.break_btn.set_label("Give Up")
                self.break_btn.add_css_class("destructive-action")
                self.break_btn.set_sensitive(True)
            else:
                self.play_pause_btn.set_icon_name("media-playback-pause-symbolic")
                self.play_pause_btn.set_sensitive(True)
                
                self.break_btn.set_label("Skip")
                self.break_btn.remove_css_class("destructive-action")
                self.break_btn.set_sensitive(False)
                
            self.restart_btn.set_sensitive(False)

            if (
                self.timer.state in ["Short Break", "Long Break"]
                and self.timer.enable_screen_overlay
            ):
                self._show_overlays()
        else:
            self._unblock_websites()
            sw_active = getattr(self, "stopwatch", None) and self.stopwatch.elapsed_seconds > 0
            self.btn_submerge.set_sensitive(not (is_active or sw_active))
                
            self._unblock_websites()
            if self.is_submerged:
                self.play_pause_btn.set_icon_name("anchor-symbolic")
            else:
                self.play_pause_btn.set_icon_name("media-playback-start-symbolic")
            self.play_pause_btn.set_sensitive(True)
            
            total_time = self.timer.durations[self.timer.state] * 60
            has_started = self.timer.time_left < total_time
            self.restart_btn.set_sensitive(has_started)
            self.break_btn.set_label("Skip")
            self.break_btn.remove_css_class("destructive-action")
            self.break_btn.set_sensitive(True)

    def _on_play_pause_clicked(self, button):
        if self.stopwatch.is_running or self.stopwatch.elapsed_seconds > 0:
            self._show_toast("Timer session is active")
            return

        if self.timer.is_running:
            if self.is_submerged and self.timer.state == "Focus":
                return
            self.timer.pause()
            self._set_running_ui_state(False)
        else:
            self.timer.start()
            self._set_running_ui_state(True)

    def _on_restart_clicked(self, button):
        self.timer.reset()
        self._set_running_ui_state(False)
        self._update_time_display()

    def _block_websites(self):
        is_enabled = db.get_setting("web_blocker_enabled", "False") == "True"
        if not is_enabled:
            return
            
        websites = [d for _, d in db.get_websites()]
        if not websites:
            return
            
        domains_str = ",".join(websites)
        import os, subprocess
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "blocker.py"))
        
        try:
            result = subprocess.run(["sudo", "-n", "/usr/bin/python3", script_path, "block", domains_str], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Failed to start blocker: {result.stderr}")
                from gi.repository import GLib, Adw
                GLib.idle_add(lambda: self.toast_overlay.add_toast(Adw.Toast.new(f"Blocker Error: {result.stderr.strip()}"[:80])))
            self._is_blocked = True
        except Exception as e:
            print(f"Exception starting blocker: {e}")

    def _unblock_websites(self):
        import os, subprocess
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "blocker.py"))
        
        try:
            result = subprocess.run(["sudo", "-n", "/usr/bin/python3", script_path, "unblock"], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Failed to unblock: {result.stderr}")
                from gi.repository import GLib, Adw
                GLib.idle_add(lambda: self.toast_overlay.add_toast(Adw.Toast.new(f"Unblock Error: {result.stderr.strip()}"[:80])))
            self._is_blocked = False
        except Exception as e:
            print(f"Exception unblocking: {e}")

    def _on_break_clicked(self, button):
        if self.timer.state == "Focus" and self.is_submerged and self.timer.is_running:
            dialog = Adw.MessageDialog(
                heading="Give Up?",
                body="You are in Submerge Mode. Giving up will discard this session entirely.",
            )
            dialog.set_transient_for(self)
            dialog.add_response("cancel", "Keep Focusing")
            dialog.add_response("give_up", "Give Up")
            dialog.set_response_appearance("give_up", Adw.ResponseAppearance.DESTRUCTIVE)
            
            def on_response(dialog, response):
                if response == "give_up":
                    self.timer.pause()
                    self.timer.next_state()
                    self._set_running_ui_state(False)
                    self._update_time_display()
            dialog.connect("response", on_response)
            dialog.present()
            return

        total_secs = self.timer.durations.get(self.timer.state, 0) * 60
        worked_secs = total_secs - self.timer.time_left
        if worked_secs > 0:
            selected_idx = self.project_dropdown.get_selected()
            if selected_idx < len(self._projects_map):
                project_id = self._projects_map[selected_idx][0]
                db.log_session(project_id, self.timer.state, worked_secs)
                if hasattr(self, 'stats_page'):
                    self.stats_page.update_stats()

        self.timer.pause()
        self.timer.next_state()
        self._set_running_ui_state(False)
        self._update_time_display()

    def _update_time_display(self):
        time_left = self.timer.time_left
        total_time = getattr(
            self.timer,
            "current_total_time",
            self.timer.durations[self.timer.state] * 60,
        )
        elapsed_time = total_time - time_left

        el_min = elapsed_time // 60
        el_sec = elapsed_time % 60
        self.elapsed_label.set_label(f"{el_min:02d}:{el_sec:02d}")

        tot_min = total_time // 60
        tot_sec = total_time % 60
        self.total_label.set_label(f"{tot_min:02d}:{tot_sec:02d}")
        
        completed_mod = self.timer.focus_sessions_completed % self.timer.cycles
        if self.timer.state == "Focus":
            current_cycle = completed_mod + 1
        else:
            current_cycle = completed_mod if completed_mod > 0 else self.timer.cycles
            
        self.cycle_label.set_label(f"{current_cycle}/{self.timer.cycles}")

        time_str = f"{time_left // 60:02d}:{time_left % 60:02d}"
        for o in self._overlays:
            if o.get_visible():
                o.update_time(time_str)
                
        if hasattr(self, 'compact_window') and self.compact_window.get_visible():
            self.compact_window.update_display()

        if hasattr(self.progress_bar, "set_cycle_info"):
            self.progress_bar.set_cycle_info(current_cycle, self.timer.cycles)

        if total_time > 0:
            self.progress_bar.set_fraction(elapsed_time / total_time)
        else:
            self.progress_bar.set_fraction(0.0)

    def _on_compact_clicked(self, button):
        if not hasattr(self, 'compact_window'):
            from plumb.compact import CompactWindow
            self.compact_window = CompactWindow(self.get_application(), self)
            
        self.compact_window.present()
        self.compact_window.update_display()
        self.set_visible(False)

    def _on_submerge_toggled(self, button):
        self.is_submerged = button.get_active()
        db.set_setting("submerge_mode", str(self.is_submerged))
        
        # Update theme first so the toast renders with the correct CSS context
        self._update_submerge_theme()
        
        if self.is_submerged:
            self._show_toast("Submerged into deep focus")
        else:
            self._show_toast("Surfaced from Submerge Mode")
        
        # Refresh UI states to instantly update play/pause button icons
        if hasattr(self, 'timer'):
            self._set_running_ui_state(self.timer.is_running)
        if hasattr(self, 'stopwatch'):
            self._set_sw_running_ui_state(self.stopwatch.is_running)

    def _update_submerge_theme(self):
        if self.is_submerged:
            self.add_css_class("submerge-theme")
            if hasattr(self, 'compact_window'):
                self.compact_window.add_css_class("submerge-theme")
        else:
            self.remove_css_class("submerge-theme")
            if hasattr(self, 'compact_window'):
                self.compact_window.remove_css_class("submerge-theme")

    def _on_dark_changed(self, style_manager, param):
        if style_manager.get_dark():
            self.add_css_class("dark-theme")
            if hasattr(self, "compact_window") and self.compact_window:
                self.compact_window.add_css_class("dark-theme")
        else:
            self.remove_css_class("dark-theme")
            if hasattr(self, "compact_window") and self.compact_window:
                self.compact_window.remove_css_class("dark-theme")

    def _on_timer_tick(self, time_left):
        self._update_time_display()

    def _on_state_change(self, new_state):
        self.progress_bar.remove_css_class("focus-state")
        self.progress_bar.remove_css_class("short-break-state")
        self.progress_bar.remove_css_class("long-break-state")

        self.remove_css_class("focus-window")
        self.remove_css_class("short-break-window")
        self.remove_css_class("long-break-window")

        if new_state == "Focus":
            self.progress_bar.add_css_class("focus-state")
            self.add_css_class("focus-window")
            self.project_dropdown_stack.set_visible_child_name("dropdown")
            self._hide_overlays()
        elif new_state == "Short Break":
            self.progress_bar.add_css_class("short-break-state")
            self.add_css_class("short-break-window")
            self.break_state_label.set_label("Short Break")
            self.project_dropdown_stack.set_visible_child_name("break_label")
        elif new_state == "Long Break":
            self.progress_bar.add_css_class("long-break-state")
            self.add_css_class("long-break-window")
            self.break_state_label.set_label("Long Break")
            self.project_dropdown_stack.set_visible_child_name("break_label")

        self._update_time_display()
        self._set_running_ui_state(False)

    def _show_overlays(self):
        self._hide_overlays()
        display = Gdk.Display.get_default()
        monitors = display.get_monitors()
        app = self.get_application()

        for i in range(monitors.get_n_items()):
            monitor = monitors.get_item(i)
            overlay = BreakOverlayWindow(
                self._hide_overlays,
                show_quotes=self.timer.show_overlay_quotes,
                application=app,
            )
            overlay.fullscreen_on_monitor(monitor)
            overlay.present()
            self._overlays.append(overlay)

        self._update_time_display()

    def _hide_overlays(self):
        for o in self._overlays:
            o.close()
        self._overlays.clear()

    def _on_timer_warning(self):
        msg = (
            "Get ready to take a break."
            if self.timer.state == "Focus"
            else "Get ready to focus."
        )
        title = (
            "Pomodoro Finishing Soon"
            if self.timer.state == "Focus"
            else "Break Finishing Soon"
        )
        self._send_notification(title, f"10 seconds remaining! {msg}", False)

    def _send_notification(self, title, body, action_type=None):
        notification = Gio.Notification.new(title)
        notification.set_body(body)
        notification.set_icon(Gio.ThemedIcon.new("alarm-symbolic"))
        notification.set_priority(Gio.NotificationPriority.URGENT)

        if action_type == "break":
            notification.add_button("Skip Break", "app.skip-break")
            notification.add_button("Take a Break", "app.take-break")
        elif action_type == "pomodoro":
            notification.add_button("Skip Pomodoro", "app.skip-pomodoro")
            notification.add_button("Start Pomodoro", "app.start-pomodoro")

        app = self.get_application()
        if app:
            app.send_notification("plumb-timer", notification)

    def _on_timer_finish(self, completed_state, completed_duration):
        if not self.timer.is_running:
            self._set_running_ui_state(False)
        self._update_time_display()

        selected_idx = self.project_dropdown.get_selected()
        if selected_idx < len(self._projects_map):
            project_id = self._projects_map[selected_idx][0]
            db.log_session(project_id, completed_state, completed_duration * 60)

        if completed_state == "Focus":

            if not self.timer.auto_start_breaks:
                self._send_notification(
                    "Pomodoro is over!", "Confirm the start of a short break...", "break"
                )
        else:
            if not self.timer.auto_start_pomodoros:
                self._send_notification(
                    "Break is over!", "Time to get back to focus.", "pomodoro"
                )

    def _set_sw_running_ui_state(self, is_running):
        self.switcher_bar.set_sensitive(not is_running)
        
        is_active = is_running or self.stopwatch.elapsed_seconds > 0

        self.sw_project_dropdown.set_sensitive(not is_active)
        self.sw_project_dropdown.set_show_arrow(not is_active)
        
        if is_active:
            self.sw_project_dropdown.remove_css_class("pill")
            self.sw_project_dropdown.add_css_class("flat")
            self.sw_project_dropdown.add_css_class("title-4")
        else:
            self.sw_project_dropdown.remove_css_class("flat")
            self.sw_project_dropdown.remove_css_class("title-4")
            self.sw_project_dropdown.add_css_class("pill")

        if is_running:
            self.btn_submerge.set_sensitive(False)
            master_enabled = db.get_setting("web_blocker_enabled", "False") == "True"
            normal_enabled = db.get_setting("web_blocker_normal_mode", "False") == "True"
            
            if master_enabled and (self.is_submerged or normal_enabled):
                self._block_websites()

            if self.is_submerged:
                self.sw_play_pause_btn.set_icon_name("anchor-symbolic")
                self.sw_play_pause_btn.set_sensitive(False)
                
                self.sw_restart_btn.set_label("Give Up")
                self.sw_restart_btn.add_css_class("destructive-action")
                self.sw_restart_btn.set_sensitive(True)
                
                min_save_time = int(db.get_setting("sw_min_save_time", "25")) * 60
                self.sw_save_btn.set_sensitive(self.stopwatch.elapsed_seconds >= min_save_time)
            else:
                self.sw_play_pause_btn.set_icon_name("media-playback-pause-symbolic")
                self.sw_play_pause_btn.set_sensitive(True)
                
                self.sw_restart_btn.set_label("Restart")
                self.sw_restart_btn.remove_css_class("destructive-action")
                self.sw_restart_btn.set_sensitive(False)
                
                self.sw_save_btn.set_sensitive(False)
        else:
            self._unblock_websites()
            pomo_active = getattr(self, "timer", None) and self.timer.time_left < (self.timer.durations.get(self.timer.state, 0) * 60)
            self.btn_submerge.set_sensitive(not (is_active or pomo_active))
                
            if self.is_submerged:
                self.sw_play_pause_btn.set_icon_name("anchor-symbolic")
            else:
                self.sw_play_pause_btn.set_icon_name("media-playback-start-symbolic")
            self.sw_play_pause_btn.set_sensitive(True)
            
            self.sw_restart_btn.set_label("Restart")
            self.sw_restart_btn.remove_css_class("destructive-action")
            
            has_started = self.stopwatch.elapsed_seconds > 0
            self.sw_restart_btn.set_sensitive(has_started)
            self.sw_save_btn.set_sensitive(has_started)

    def _on_sw_play_pause_clicked(self, button):
        is_pomodoro_active = self.timer.is_running or self.timer.time_left < (self.timer.durations.get(self.timer.state, 0) * 60)
        if is_pomodoro_active:
            self._show_toast("Pomodoro session is active")
            return

        if self.stopwatch.is_running:
            self.stopwatch.pause()
            self._set_sw_running_ui_state(False)
        else:
            self.stopwatch.start()
            self._set_sw_running_ui_state(True)

    def _on_sw_restart_clicked(self, button):
        if self.is_submerged and self.stopwatch.is_running:
            dialog = Adw.MessageDialog(
                heading="Give Up?",
                body="You are in Submerge Mode. Giving up will discard this tracked time entirely.",
            )
            dialog.set_transient_for(self)
            dialog.add_response("cancel", "Keep Working")
            dialog.add_response("give_up", "Give Up")
            dialog.set_response_appearance("give_up", Adw.ResponseAppearance.DESTRUCTIVE)
            
            def on_response(dialog, response):
                if response == "give_up":
                    self.stopwatch.pause()
                    self.stopwatch.reset()
                    self._set_sw_running_ui_state(False)
                    self._update_sw_time_display()
            dialog.connect("response", on_response)
            dialog.present()
            return

        self.stopwatch.reset()
        self._set_sw_running_ui_state(False)
        self._update_sw_time_display()

    def _on_sw_save_clicked(self, button):
        selected_idx = self.sw_project_dropdown.get_selected()
        if selected_idx < len(self._projects_map):
            project_id = self._projects_map[selected_idx][0]
            min_save_time = int(db.get_setting("sw_min_save_time", "25")) * 60
            if self.stopwatch.elapsed_seconds >= min_save_time:
                db.log_session(project_id, "Focus", self.stopwatch.elapsed_seconds)
                self._show_toast("Timer session saved")
                if hasattr(self, 'stats_page'):
                    self.stats_page.update_stats()
            else:
                self._show_toast(f"Session discarded (less than {min_save_time//60} mins)")

        self.stopwatch.reset()
        self._set_sw_running_ui_state(False)
        self._update_sw_time_display()

    def _show_toast(self, message):
        if hasattr(self, '_current_toast') and self._current_toast:
            self._current_toast.dismiss()
        self._current_toast = Adw.Toast.new(message)
        self._current_toast.set_timeout(2)
        self.toast_overlay.add_toast(self._current_toast)

    def _update_sw_time_display(self):
        secs = self.stopwatch.elapsed_seconds
        m = secs // 60
        s = secs % 60
        self.sw_time_label.set_label(f"{m:02d}:{s:02d}")
        
        if self.is_submerged and self.stopwatch.is_running:
            min_save_time = int(db.get_setting("sw_min_save_time", "25")) * 60
            self.sw_save_btn.set_sensitive(secs >= min_save_time)
        
        if hasattr(self, 'compact_window') and self.compact_window.get_visible():
            self.compact_window.update_display()

    def _on_stopwatch_tick(self, elapsed_seconds):
        self._update_sw_time_display()

    def _load_projects(self):
        self._project_list.splice(0, self._project_list.get_n_items(), [])
        self._projects_map = db.get_projects()
        for pid, name in self._projects_map:
            self._project_list.append(name)
        self._project_list.append("+ Create New Project...")

    def _show_create_project_dialog(self, dropdown):
        dialog = Adw.MessageDialog.new(
            self, "New Project", "Enter the name of the new project:"
        )
        entry = Gtk.Entry(placeholder_text="Project Name")
        entry.set_hexpand(True)
        entry.set_margin_top(12)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(entry)
        dialog.set_extra_child(box)

        dialog.add_response("cancel", "Cancel")
        dialog.add_response("create", "Create")
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)

        def on_response(d, response):
            if response == "create":
                name = entry.get_text().strip()
                if name:
                    new_id = db.add_project(name)
                    if new_id:
                        self._load_projects()
                        self.project_dropdown.set_selected(len(self._projects_map) - 1)
                        self.sw_project_dropdown.set_selected(
                            len(self._projects_map) - 1
                        )
                        return
            dropdown.set_selected(0)

        dialog.connect("response", on_response)
        dialog.present()

    def _on_project_selected(self, dropdown, param):
        selected = dropdown.get_selected()
        if selected == len(self._projects_map):
            self._show_create_project_dialog(dropdown)
