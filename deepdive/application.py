import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio
from deepdive.window import DeepDiveWindow


class DeepDiveApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="io.github.tanaybhomia.DeepDive",
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

        donate_action = Gio.SimpleAction.new("donate", None)
        donate_action.connect("activate", self._on_donate_action)
        self.add_action(donate_action)

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
        from deepdive.database import db
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
        from deepdive.database import db
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
        from deepdive.database import db
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
                    
                if hasattr(win, "stopwatch") and win.stopwatch and getattr(win.stopwatch, "dnd_sync", False):
                    win.stopwatch._set_gnome_dnd(False)
                    
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
        from deepdive.preferences import DeepDivePreferencesWindow

        win = self.props.active_window
        prefs_win = DeepDivePreferencesWindow(
            timer=win.timer if hasattr(win, "timer") else None,
            stopwatch=win.stopwatch if hasattr(win, "stopwatch") else None,
            transient_for=win
        )
        prefs_win.present()

    def _on_donate_action(self, action, param):
        Gio.AppInfo.launch_default_for_uri("https://tanaybhomia.github.io/Deep-Dive/donate.html", None)

    def _on_about_action(self, action, param):
        about = Adw.AboutWindow(
            application_name="Deep Dive",
            application_icon="io.github.tanaybhomia.DeepDive",
            developer_name="Tanay Bhomia",
            version="1.0.0",
            website="https://tanaybhomia.github.io/Deep-Dive/",
            issue_url="https://github.com/tanaybhomia/Deep-Dive/issues",
            support_url="https://github.com/tanaybhomia/Deep-Dive/discussions",
            copyright="© 2026 Tanay Bhomia",
            license_type=Gtk.License.GPL_3_0,
            transient_for=self.props.active_window,
        )
        
        about.set_release_notes("""<ul>
  <li>Initial Release of Deep Dive!</li>
  <li>Includes Submerge Mode, Web Blocker, and Project Tracking.</li>
</ul>""")

        about.add_link("Wiki", "https://github.com/tanaybhomia/Deep-Dive/wiki")
        about.add_link("Donate", "https://tanaybhomia.github.io/Deep-Dive/donate.html")

        debug_info = (
            "os: Fedora Linux 44 (Workstation Edition)\n"
            "prefix: /usr\n"
            "flatpak: false\n"
            "version: 1.4.0\n"
            "python: 3.14.6\n"
            "gtk: 4.22.4\n"
            "libadwaita: 1.9.3\n"
            "tesseract: 5.5.3\n"
            "pillow: 12.3.0"
        )
        about.set_debug_info(debug_info)
        about.set_debug_info_filename("DeepDive_Debug_Info.txt")

        about.add_credit_section("Code by", ["Tanay Bhomia https://tanaybhomia.github.io/"])
        about.add_credit_section("Artwork by", ["gnoman"])

        about.add_acknowledgement_section("Special thanks", ["Special thanks to gnoman for helping me throughout the design process of the app. from icon to theme to brand of the app itself"])

        def on_activate_link(window, uri):
            Gio.AppInfo.launch_default_for_uri(uri, None)
            return True

        about.connect("activate-link", on_activate_link)

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
            win = DeepDiveWindow(application=self)

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
