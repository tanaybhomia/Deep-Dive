import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio
from plumb.window import PlumbWindow


class PlumbApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.github.tanay.Plumb",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self._setup_actions()

    def _setup_actions(self):
        prefs_action = Gio.SimpleAction.new("preferences", None)
        prefs_action.connect("activate", self._on_preferences_action)
        self.add_action(prefs_action)
        self.set_accels_for_action("app.preferences", ["<Primary>comma"])

        take_break_action = Gio.SimpleAction.new("take-break", None)
        take_break_action.connect("activate", self._on_take_break)
        self.add_action(take_break_action)

        skip_break_action = Gio.SimpleAction.new("skip-break", None)
        skip_break_action.connect("activate", self._on_skip_break)
        self.add_action(skip_break_action)
        
        start_pomo_action = Gio.SimpleAction.new("start-pomodoro", None)
        start_pomo_action.connect("activate", self._on_start_pomodoro)
        self.add_action(start_pomo_action)

        skip_pomo_action = Gio.SimpleAction.new("skip-pomodoro", None)
        skip_pomo_action.connect("activate", self._on_skip_pomodoro)
        self.add_action(skip_pomo_action)

        toggle_compact_action = Gio.SimpleAction.new("toggle-compact", None)
        toggle_compact_action.connect("activate", self._on_toggle_compact)
        self.add_action(toggle_compact_action)
        self.set_accels_for_action("app.toggle-compact", ["<Primary>m"])

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self._on_quit_action)
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Primary>q"])

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about_action)
        self.add_action(about_action)

        toggle_ironclad_action = Gio.SimpleAction.new("toggle-submerge", None)
        toggle_ironclad_action.connect("activate", self._on_toggle_submerge)
        self.add_action(toggle_ironclad_action)
        self.set_accels_for_action("app.toggle-submerge", ["<Primary><Shift>i"])

        shortcuts_action = Gio.SimpleAction.new("shortcuts", None)
        shortcuts_action.connect("activate", self._on_shortcuts_action)
        self.add_action(shortcuts_action)
        self.set_accels_for_action("app.shortcuts", ["<Primary>question"])

        theme_sys_action = Gio.SimpleAction.new("theme-system", None)
        theme_sys_action.connect("activate", self._on_theme_system)
        self.add_action(theme_sys_action)

        theme_light_action = Gio.SimpleAction.new("theme-light", None)
        theme_light_action.connect("activate", self._on_theme_light)
        self.add_action(theme_light_action)

        theme_dark_action = Gio.SimpleAction.new("theme-dark", None)
        theme_dark_action.connect("activate", self._on_theme_dark)
        self.add_action(theme_dark_action)

    def _on_theme_system(self, action, param):
        from gi.repository import Adw, GLib
        from plumb.database import db
        win = self.props.active_window
        if win:
            win.add_css_class("no-transition")
            if hasattr(win, "compact_window") and win.compact_window:
                win.compact_window.add_css_class("no-transition")
                
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.DEFAULT)
        db.set_setting("theme", "system")
        
        if win:
            def remove_no_transition():
                win.remove_css_class("no-transition")
                if hasattr(win, "compact_window") and win.compact_window:
                    win.compact_window.remove_css_class("no-transition")
            GLib.timeout_add(500, remove_no_transition)

    def _on_theme_light(self, action, param):
        from gi.repository import Adw, GLib
        from plumb.database import db
        win = self.props.active_window
        if win:
            win.add_css_class("no-transition")
            if hasattr(win, "compact_window") and win.compact_window:
                win.compact_window.add_css_class("no-transition")
                
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        db.set_setting("theme", "light")
        
        if win:
            def remove_no_transition():
                win.remove_css_class("no-transition")
                if hasattr(win, "compact_window") and win.compact_window:
                    win.compact_window.remove_css_class("no-transition")
            GLib.timeout_add(500, remove_no_transition)

    def _on_theme_dark(self, action, param):
        from gi.repository import Adw, GLib
        from plumb.database import db
        win = self.props.active_window
        if win:
            win.add_css_class("no-transition")
            if hasattr(win, "compact_window") and win.compact_window:
                win.compact_window.add_css_class("no-transition")
                
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        db.set_setting("theme", "dark")
        
        if win:
            def remove_no_transition():
                win.remove_css_class("no-transition")
                if hasattr(win, "compact_window") and win.compact_window:
                    win.compact_window.remove_css_class("no-transition")
            GLib.timeout_add(500, remove_no_transition)

    def _do_quit(self):
        try:
            win = self.props.active_window
            if not win:
                windows = self.get_windows()
                if windows:
                    win = windows[0]

            if win:
                if hasattr(win, "main_window"):
                    win = win.main_window
                    
                if hasattr(win, "timer") and win.timer and getattr(win.timer, "dnd_sync", False):
                    win.timer._set_gnome_dnd(False)
                    
                if hasattr(win, "_unblock_websites"):
                    # Use a thread with timeout to prevent sudo from hanging the app
                    import threading
                    t = threading.Thread(target=win._unblock_websites)
                    t.start()
                    t.join(timeout=1.0)
                    
            self.quit()
        except Exception as e:
            print(f"Error during quit: {e}")
            self.quit()
            
        # Absolute failsafe: if GTK or PyGObject fails to terminate the process after self.quit(), nuke it.
        import os, threading
        def _nuke():
            import time
            time.sleep(0.5)
            os._exit(0)
        threading.Thread(target=_nuke, daemon=True).start()

    def _attempt_quit(self, win):
        try:
            if not win or not hasattr(win, "timer"):
                self._do_quit()
                return
            is_visible = win.get_visible()
            if hasattr(win, "compact_window") and win.compact_window:
                is_visible = is_visible or win.compact_window.get_visible()
                
            if not is_visible:
                # App is running in the background (both windows hidden). Don't show invisible dialogs, just quit.
                self._do_quit()
                return

            is_pomodoro_active = win.timer.is_running or win.timer.time_left < (win.timer.durations.get(win.timer.state, 0) * 60)
            is_stopwatch_active = win.stopwatch.is_running or win.stopwatch.elapsed_seconds > 0

            if is_pomodoro_active or is_stopwatch_active:
                dialog = Adw.MessageDialog(
                    heading="Active Session in Progress",
                )
                active_win = self.props.active_window
                dialog.set_transient_for(active_win if active_win else win)
                
                dialog.add_response("cancel", "Cancel")
                dialog.set_default_response("cancel")
                
                dialog.add_response("background", "Run in Background")
                
                if is_stopwatch_active and win.stopwatch.elapsed_seconds >= 300:
                    dialog.add_response("save_quit", "Save & Quit")
                    dialog.add_response("quit", "Discard & Quit")
                    dialog.set_response_appearance("quit", Adw.ResponseAppearance.DESTRUCTIVE)
                else:
                    dialog.add_response("quit", "Quit")
                    dialog.set_response_appearance("quit", Adw.ResponseAppearance.DESTRUCTIVE)
                    
                def on_response(dialog, response):
                    if response == "background":
                        win.set_visible(False)
                        if hasattr(win, "compact_window") and win.compact_window:
                            win.compact_window.set_visible(False)
                    elif response == "save_quit":
                        win._on_sw_save_clicked(None)
                        self._do_quit()
                    elif response == "quit":
                        self._do_quit()
                        
                dialog.connect("response", on_response)
                dialog.present()
            else:
                self._do_quit()
        except Exception as e:
            print(f"Error in _attempt_quit: {e}")
            self._do_quit()

    def _on_quit_action(self, action, param):
        win = self.props.active_window
        if win:
            if hasattr(win, "main_window"):
                self._attempt_quit(win.main_window)
            else:
                self._attempt_quit(win)
        else:
            self._do_quit()

    def _on_take_break(self, action, param):
        win = self.props.active_window
        if win and hasattr(win, "timer"):
            win.timer.start()

    def _on_skip_break(self, action, param):
        win = self.props.active_window
        if win and hasattr(win, "timer"):
            win.timer.next_state()
            win.timer.start()

    def _on_start_pomodoro(self, action, param):
        win = self.props.active_window
        if win and hasattr(win, "timer"):
            win.timer.start()

    def _on_skip_pomodoro(self, action, param):
        win = self.props.active_window
        if win and hasattr(win, "timer"):
            win.timer.next_state()
            win.timer.start()

    def _on_toggle_compact(self, action, param):
        win = self.props.active_window
        if win:
            if hasattr(win, "main_window"):
                win._on_restore_clicked(None)
            elif hasattr(win, "_on_compact_clicked"):
                win._on_compact_clicked(None)

    def _on_preferences_action(self, action, param):
        from plumb.preferences import PlumbPreferencesWindow

        win = self.props.active_window
        prefs_win = PlumbPreferencesWindow(timer=win.timer, transient_for=win)
        prefs_win.present()

    def _on_about_action(self, action, param):
        about = Adw.AboutWindow(
            application_name="Plumb",
            application_icon="com.github.tanay.Plumb",
            developer_name="Tanay",
            version="1.0.0",
            website="https://github.com/tanay/Plumb",
            issue_url="https://github.com/tanay/Plumb/issues",
            copyright="© 2026 Tanay Bhomia",
            license_type=Gtk.License.GPL_3_0,
            transient_for=self.props.active_window,
        )
        about.add_credit_section("Code by", ["Tanay Bhomia"])
        about.add_credit_section("Icon by", ["[Icon Designer Name]"])
        about.present()

    def _on_toggle_submerge(self, action, param):
        win = self.props.active_window
        if win:
            main_win = getattr(win, "main_window", win)
            if hasattr(main_win, "btn_submerge") and main_win.btn_submerge.get_sensitive():
                main_win.btn_submerge.set_active(not main_win.btn_submerge.get_active())

    def _on_shortcuts_action(self, action, param):
        win = self.props.active_window
        if win:
            main_win = getattr(win, "main_window", win)
            if hasattr(main_win, "get_help_overlay"):
                overlay = main_win.get_help_overlay()
                if overlay:
                    overlay.present()

    def do_activate(self):
        # Load CSS
        css_provider = Gtk.CssProvider()
        import os
        from gi.repository import Gdk

        css_path = os.path.join(os.path.dirname(__file__), "style.css")
        css_provider.load_from_path(css_path)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        icons_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons")
        icon_theme.add_search_path(os.path.abspath(icons_path))

        win = self.props.active_window
        if not win:
            windows = self.get_windows()
            if windows:
                win = windows[0]

        if not win:
            win = PlumbWindow(application=self)

            def _on_window_close(*args):
                self._attempt_quit(win)
                return True

            win.connect("close-request", _on_window_close)
            
            # Failsafe: Ensure websites are unblocked on startup in case of a crash/shutdown
            if hasattr(win, "_unblock_websites"):
                import threading
                def unblock_failsafe():
                    win._is_blocked = True
                    win._unblock_websites()
                threading.Thread(target=unblock_failsafe, daemon=True).start()
            
        if hasattr(win, "main_window"):
            win = win.main_window
            
        win.set_visible(True)
        win.present()
