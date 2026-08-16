import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
from deepdive.timer import TimerState
from deepdive.database import db


class DeepDivePreferencesWindow(Adw.PreferencesWindow):
    def __init__(self, timer=None, stopwatch=None, **kwargs):
        super().__init__(**kwargs)
        self.timer = timer
        self.stopwatch = stopwatch
        self.set_title("Preferences")
        self.set_default_size(600, 700)

        timer_page = Adw.PreferencesPage(
            title="Timer", icon_name="document-open-recent-symbolic"
        )
        self.add(timer_page)

        session_group = Adw.PreferencesGroup(title="Pomodoro")
        timer_page.add(session_group)

        pomo_val = self.timer.durations[TimerState.FOCUS] if self.timer else 55
        self.pomo_row = self._create_spin_row(
            "Pomodoro Duration", "In minutes (Max: 120)", 1, 120, pomo_val, self._on_pomo_changed
        )
        session_group.add(self.pomo_row)

        short_val = self.timer.durations[TimerState.SHORT_BREAK] if self.timer else 5
        self.short_break_row = self._create_spin_row(
            "Short Break Duration",
            "In minutes (Max: 30)",
            1,
            30,
            short_val,
            self._on_short_break_changed,
        )
        session_group.add(self.short_break_row)

        long_val = (
            self.timer.durations.get(TimerState.LONG_BREAK, 10) if self.timer else 10
        )
        self.long_break_row = self._create_spin_row(
            "Long Break Duration",
            "In minutes (Max: 60)",
            1,
            60,
            long_val,
            self._on_long_break_changed,
        )
        session_group.add(self.long_break_row)

        sw_min_val = int(db.get_setting("sw_min_save_time", "25"))
        self.sw_min_row = self._create_spin_row(
            "Minimum Save Time",
            "In minutes (Max: 120)",
            1,
            120,
            sw_min_val,
            self._on_sw_min_changed,
        )
        
        if hasattr(Adw, "SpinRow"):
            adj = Gtk.Adjustment(
                value=self.timer.cycles if self.timer else 4,
                lower=1,
                upper=10,
                step_increment=1,
                page_increment=1,
                page_size=0,
            )
            self.cycles_row = Adw.SpinRow(title="Number of Cycles", subtitle="Max: 10", adjustment=adj)
            self.cycles_row.connect("notify::value", lambda r, p: self._on_cycles_changed(int(r.get_value())))
        else:
            self.cycles_row = Adw.ActionRow(title="Number of Cycles", subtitle="Max: 10")
            self.cycles_spin = Gtk.SpinButton.new_with_range(1, 10, 1)
            self.cycles_spin.set_valign(Gtk.Align.CENTER)
            self.cycles_spin.set_value(self.timer.cycles if self.timer else 4)
            self.cycles_spin.connect("value-changed", lambda s: self._on_cycles_changed(int(s.get_value())))
            self.cycles_row.add_suffix(self.cycles_spin)

        session_group.add(self.cycles_row)

        self.summary_label = Gtk.Label()
        self.summary_label.set_halign(Gtk.Align.START)
        self.summary_label.set_margin_top(16)
        self.summary_label.set_margin_bottom(0)
        self.summary_label.add_css_class("dim-label")
        session_group.add(self.summary_label)
        self._update_summary_label()

        timer_group = Adw.PreferencesGroup(title="Timer")
        timer_page.add(timer_group)
        timer_group.add(self.sw_min_row)

        behavior_group = Adw.PreferencesGroup(title="Behavior")
        timer_page.add(behavior_group)

        self.pause_lock_row = Adw.ActionRow(title="Pause By Locking The Screen")
        self.pause_lock_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.pause_lock_switch.set_active(
            self.timer.pause_on_lock if self.timer else True
        )
        self.pause_lock_switch.connect("notify::active", self._on_pause_lock_changed)
        self.pause_lock_row.add_suffix(self.pause_lock_switch)
        behavior_group.add(self.pause_lock_row)

        self.confirm_break_row = Adw.ActionRow(title="Confirm Starting a Break")
        self.confirm_break_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.confirm_break_switch.set_active(
            not self.timer.auto_start_breaks if self.timer else True
        )
        self.confirm_break_switch.connect(
            "notify::active", self._on_confirm_break_changed
        )
        self.confirm_break_row.add_suffix(self.confirm_break_switch)
        behavior_group.add(self.confirm_break_row)

        self.confirm_pomo_row = Adw.ActionRow(title="Confirm Starting a Pomodoro")
        self.confirm_pomo_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.confirm_pomo_switch.set_active(
            not self.timer.auto_start_pomodoros if self.timer else True
        )
        self.confirm_pomo_switch.connect(
            "notify::active", self._on_confirm_pomo_changed
        )
        self.confirm_pomo_row.add_suffix(self.confirm_pomo_switch)
        behavior_group.add(self.confirm_pomo_row)

        notif_page = Adw.PreferencesPage(
            title="Notifications", icon_name="preferences-system-notifications-symbolic"
        )

        ann_group = Adw.PreferencesGroup(title="Announcements")
        self.notify_row = Adw.ActionRow(
            title="Time Running Out",
            subtitle="Notify when Pomodoro or break is about to end.",
        )
        self.notify_switch = Gtk.Switch(
            active=self.timer.notify_running_out if self.timer else True,
            valign=Gtk.Align.CENTER,
        )
        self.notify_switch.connect(
            "notify::active", self._on_notify_running_out_changed
        )
        self.notify_row.add_suffix(self.notify_switch)
        ann_group.add(self.notify_row)

        self.dnd_row = Adw.ActionRow(
            title="System Do Not Disturb",
            subtitle="Automatically mute system notifications during a focus session.",
        )
        self.dnd_switch = Gtk.Switch(
            active=self.timer.dnd_sync if self.timer else False, valign=Gtk.Align.CENTER
        )
        self.dnd_switch.connect("notify::active", self._on_dnd_sync_changed)
        self.dnd_row.add_suffix(self.dnd_switch)
        ann_group.add(self.dnd_row)

        notif_page.add(ann_group)

        overlay_group = Adw.PreferencesGroup(
            title="Screen Overlay",
            description="A full-screen notification intended to enforce taking a break.",
        )

        self.overlay_row = Adw.ActionRow(title="Screen Overlay")
        self.overlay_switch = Gtk.Switch(
            active=self.timer.enable_screen_overlay if self.timer else False,
            valign=Gtk.Align.CENTER,
        )
        self.overlay_switch.connect("notify::active", self._on_overlay_changed)
        self.overlay_row.add_suffix(self.overlay_switch)
        overlay_group.add(self.overlay_row)

        self.quotes_row = Adw.ActionRow(
            title="Show Fun Quotes",
            subtitle="Display a random quote at the bottom of the screen overlay.",
        )
        self.quotes_switch = Gtk.Switch(
            active=self.timer.show_overlay_quotes if self.timer else True,
            valign=Gtk.Align.CENTER,
        )
        self.quotes_switch.connect("notify::active", self._on_quotes_changed)
        self.quotes_row.add_suffix(self.quotes_switch)
        overlay_group.add(self.quotes_row)

        self.lock_row = Adw.ComboRow(
            title="Lock Delay", subtitle="Period of inactivity to lock the screen."
        )
        self.lock_model = Gtk.StringList.new(["Never", "1 minute", "5 minutes"])
        self.lock_row.set_model(self.lock_model)
        self._set_combo_selected_string(
            self.lock_row,
            self.lock_model,
            self.timer.lock_delay if self.timer else "Never",
        )
        self.lock_row.connect("notify::selected-item", self._on_lock_delay_changed)
        overlay_group.add(self.lock_row)

        self.reopen_row = Adw.ComboRow(
            title="Reopen Delay",
            subtitle="Period of inactivity to reopen the overlay after it gets dismissed.",
        )
        self.reopen_model = Gtk.StringList.new(["30 seconds", "1 minute", "5 minutes"])
        self.reopen_row.set_model(self.reopen_model)
        self._set_combo_selected_string(
            self.reopen_row,
            self.reopen_model,
            self.timer.reopen_delay if self.timer else "30 seconds",
        )
        self.reopen_row.connect("notify::selected-item", self._on_reopen_delay_changed)
        overlay_group.add(self.reopen_row)

        notif_page.add(overlay_group)
        self.add(notif_page)
        
        self._build_projects_page()
        self._build_blocker_page()

    def _create_spin_row(
        self, title_text, subtitle_text, min_val, max_val, default_val, callback
    ):
        if hasattr(Adw, "SpinRow"):
            adj = Gtk.Adjustment(
                value=default_val,
                lower=min_val,
                upper=max_val,
                step_increment=1,
                page_increment=1,
                page_size=0,
            )
            row = Adw.SpinRow(title=title_text, subtitle=subtitle_text, adjustment=adj)
            row.adj = adj
            row.connect("notify::value", lambda r, p: callback(int(r.get_value())))
            return row
        else:
            row = Adw.ActionRow(title=title_text, subtitle=subtitle_text)
            spin = Gtk.SpinButton.new_with_range(min_val, max_val, 1)
            spin.set_value(default_val)
            spin.set_valign(Gtk.Align.CENTER)
            spin.connect("value-changed", lambda s: callback(int(s.get_value())))
            row.add_suffix(spin)
            return row

    def _handle_duration_change(self, state, value, row_ref):
        if not self.timer:
            return
        if value == self.timer.durations.get(state, 0):
            return

        if self.timer.is_running and self.timer.state == state:
            self.timer.set_duration(state, value, update_active=False)
            toast = Adw.Toast.new("Changes will apply to the next session")
            self.add_toast(toast)
        else:
            self.timer.set_duration(state, value)
            
        main_win = self.get_transient_for()
        if main_win and hasattr(main_win, "_update_time_display"):
            main_win._update_time_display()

    def _on_pomo_changed(self, value):
        self._handle_duration_change(
            TimerState.FOCUS, value, getattr(self, "pomo_row", None)
        )
        self._update_summary_label()

    def _on_short_break_changed(self, value):
        self._handle_duration_change(
            TimerState.SHORT_BREAK, value, getattr(self, "short_break_row", None)
        )
        self._update_summary_label()

    def _on_long_break_changed(self, value):
        self._handle_duration_change(
            TimerState.LONG_BREAK, value, getattr(self, "long_break_row", None)
        )
        self._update_summary_label()
        
    def _on_sw_min_changed(self, value):
        db.set_setting("sw_min_save_time", str(int(value)))
        
    def _on_cycles_changed(self, value):
        if self.timer:
            self.timer.cycles = value
            db.set_setting("cycles", value)
        self._update_summary_label()
        
        main_win = self.get_transient_for()
        if main_win and hasattr(main_win, "_update_time_display"):
            main_win._update_time_display()

    def _update_summary_label(self):
        pomo_min = self.timer.durations[TimerState.FOCUS] if self.timer else 25
        short_min = self.timer.durations[TimerState.SHORT_BREAK] if self.timer else 5
        long_min = self.timer.durations.get(TimerState.LONG_BREAK, 15) if self.timer else 15
        cycles = self.timer.cycles if self.timer else 4

        focus_time = cycles * pomo_min
        break_time = ((cycles - 1) * short_min) + long_min
        total_time = focus_time + break_time
        
        hours = total_time // 60
        mins = total_time % 60
        
        time_str = ""
        if hours > 0:
            time_str += f"{hours} hour{'s' if hours > 1 else ''} "
        if mins > 0:
            time_str += f"{mins} minute{'s' if mins > 1 else ''}"
        time_str = time_str.strip()
        
        if total_time > 0:
            break_percent = int((break_time / total_time) * 100)
        else:
            break_percent = 0
            
        self.summary_label.set_markup(
            f"A single session will take <b>{time_str}</b>.\n<b>{break_percent}%</b> of the time will be allocated for breaks."
        )

    def _on_pause_lock_changed(self, switch, param):
        if self.timer:
            self.timer.pause_on_lock = switch.get_active()
            db.set_setting("pause_on_lock", str(self.timer.pause_on_lock))

    def _on_confirm_break_changed(self, switch, param):
        if self.timer:
            self.timer.auto_start_breaks = not switch.get_active()
            db.set_setting("auto_start_breaks", str(self.timer.auto_start_breaks))

    def _on_confirm_pomo_changed(self, switch, param):
        if self.timer:
            self.timer.auto_start_pomodoros = not switch.get_active()
            db.set_setting("auto_start_pomodoros", str(self.timer.auto_start_pomodoros))

    def _set_combo_selected_string(self, combo, model, target_string):
        for i in range(model.get_n_items()):
            if model.get_string(i) == target_string:
                combo.set_selected(i)
                return

    def _on_notify_running_out_changed(self, switch, param):
        if self.timer:
            self.timer.notify_running_out = switch.get_active()
            db.set_setting("notify_running_out", str(self.timer.notify_running_out))

    def _on_dnd_sync_changed(self, switch, param):
        is_active = switch.get_active()
        db.set_setting("dnd_sync", str(is_active))
        
        if self.timer:
            self.timer.dnd_sync = is_active
            if self.timer.is_running and self.timer.state == TimerState.FOCUS:
                self.timer._set_gnome_dnd(is_active)
                
        if self.stopwatch:
            self.stopwatch.dnd_sync = is_active
            if self.stopwatch.is_running:
                self.stopwatch._set_gnome_dnd(is_active)

    def _on_overlay_changed(self, switch, param):
        if self.timer:
            self.timer.enable_screen_overlay = switch.get_active()
            db.set_setting(
                "enable_screen_overlay", str(self.timer.enable_screen_overlay)
            )

    def _on_quotes_changed(self, switch, param):
        if self.timer:
            self.timer.show_overlay_quotes = switch.get_active()
            db.set_setting("show_overlay_quotes", str(self.timer.show_overlay_quotes))

    def _on_lock_delay_changed(self, combo, param):
        if self.timer:
            selected_str = self.lock_model.get_string(combo.get_selected())
            self.timer.lock_delay = selected_str
            db.set_setting("lock_delay", selected_str)

    def _on_reopen_delay_changed(self, dropdown, param):
        selected = dropdown.get_selected()
        db.set_setting("reopen_delay", selected)

    def _build_projects_page(self):
        projects_page = Adw.PreferencesPage(
            title="Projects", icon_name="folder-symbolic"
        )
        self.add(projects_page)
        
        group = Adw.PreferencesGroup(
            title="Manage Projects",
            description="Add or remove projects from the main dropdown."
        )
        projects_page.add(group)
        
        add_row = Adw.ActionRow(title="Create New Project")
        self.new_project_entry = Gtk.Entry()
        self.new_project_entry.set_placeholder_text("Project Name")
        self.new_project_entry.set_valign(Gtk.Align.CENTER)
        
        add_btn = Gtk.Button(label="Add")
        add_btn.set_valign(Gtk.Align.CENTER)
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add_project)
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.append(self.new_project_entry)
        box.append(add_btn)
        
        add_row.add_suffix(box)
        group.add(add_row)
        
        self.projects_list_group = Adw.PreferencesGroup(title="Existing Projects")
        projects_page.add(self.projects_list_group)
        self._project_rows = []
        
        self._refresh_projects_list()

    def _refresh_projects_list(self):
        for row in self._project_rows:
            self.projects_list_group.remove(row)
        self._project_rows = []
            
        for p_id, name in db.get_projects():
            row = Adw.ActionRow(title=name)
            if p_id != 1:  # Default Project
                del_btn = Gtk.Button(icon_name="user-trash-symbolic")
                del_btn.set_valign(Gtk.Align.CENTER)
                del_btn.add_css_class("destructive-action")
                del_btn.connect("clicked", self._create_delete_cb(p_id, row, is_project=True))
                row.add_suffix(del_btn)
            self.projects_list_group.add(row)
            self._project_rows.append(row)

    def _on_add_project(self, btn):
        name = self.new_project_entry.get_text().strip()
        if not name:
            return
            
        p_id = db.add_project(name)
        if p_id:
            self.new_project_entry.set_text("")
            self._refresh_projects_list()
            main_win = self.get_transient_for()
            if main_win and hasattr(main_win, "_load_projects"):
                main_win._load_projects()
        else:
            toast = Adw.Toast.new("Project already exists")
            self.add_toast(toast)

    def _create_delete_cb(self, item_id, row, is_project=True):
        def on_delete(btn):
            if is_project:
                db.delete_project(item_id)
                self.projects_list_group.remove(row)
                self._project_rows.remove(row)
                main_win = self.get_transient_for()
                if main_win and hasattr(main_win, "_load_projects"):
                    main_win._load_projects()
            else:
                db.remove_website(item_id)
                self.websites_list_group.remove(row)
                self._website_rows.remove(row)
        return on_delete

    def _build_blocker_page(self):
        blocker_page = Adw.PreferencesPage(
            title="Web Blocker", icon_name="network-workgroup-symbolic"
        )
        self.add(blocker_page)
        
        enable_group = Adw.PreferencesGroup()
        blocker_page.add(enable_group)
        
        self._is_initializing = True
        
        self.enable_blocker_row = Adw.ActionRow(
            title="Enable Web Blocker",
            subtitle="Master switch to enable blocking distracting websites."
        )
        self.enable_blocker_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        
        is_enabled = db.get_setting("web_blocker_enabled", "False") == "True"
        self.enable_blocker_switch.set_active(is_enabled)
        self.enable_blocker_switch.connect("notify::active", self._on_enable_blocker_changed)
        
        self.enable_blocker_row.add_suffix(self.enable_blocker_switch)
        enable_group.add(self.enable_blocker_row)
        
        self.block_normal_row = Adw.ActionRow(
            title="Block in Normal Mode",
            subtitle="Block websites even when Submerge mode is disabled."
        )
        self.block_normal_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        
        is_normal_blocked = db.get_setting("web_blocker_normal_mode", "False") == "True"
        self.block_normal_switch.set_active(is_normal_blocked)
        self.block_normal_switch.connect("notify::active", self._on_block_normal_changed)
        
        self.block_normal_row.add_suffix(self.block_normal_switch)
        enable_group.add(self.block_normal_row)
        
        self._is_initializing = False
        
        group = Adw.PreferencesGroup(
            title="Blocked Websites",
            description="Domains to block (e.g. twitter.com)"
        )
        blocker_page.add(group)
        
        add_row = Adw.ActionRow(title="Add Website")
        self.new_website_entry = Gtk.Entry()
        self.new_website_entry.set_placeholder_text("example.com")
        self.new_website_entry.set_valign(Gtk.Align.CENTER)
        
        add_btn = Gtk.Button(label="Block")
        add_btn.set_valign(Gtk.Align.CENTER)
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add_website)
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.append(self.new_website_entry)
        box.append(add_btn)
        
        add_row.add_suffix(box)
        group.add(add_row)
        
        self.websites_list_group = Adw.PreferencesGroup()
        blocker_page.add(self.websites_list_group)
        self._website_rows = []
        
        self._refresh_websites_list()

    def _refresh_websites_list(self):
        for row in self._website_rows:
            self.websites_list_group.remove(row)
        self._website_rows = []
            
        for w_id, domain in db.get_websites():
            row = Adw.ActionRow(title=domain)
            del_btn = Gtk.Button(icon_name="user-trash-symbolic")
            del_btn.set_valign(Gtk.Align.CENTER)
            del_btn.add_css_class("destructive-action")
            del_btn.connect("clicked", self._create_delete_cb(w_id, row, is_project=False))
            row.add_suffix(del_btn)
            self.websites_list_group.add(row)
            self._website_rows.append(row)

    def _show_msg(self, heading, body):
        dialog = Adw.MessageDialog(
            heading=heading,
            body=body,
        )
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        try:
            dialog.set_transient_for(self.get_root())
        except Exception:
            pass
        dialog.present()
        
    def _on_add_website(self, btn):
        domain = self.new_website_entry.get_text().strip()
        if not domain:
            return
            
        domain = domain.lower()
        if "://" in domain:
            from urllib.parse import urlparse
            domain = urlparse(domain).netloc
        elif "/" in domain:
            domain = domain.split("/")[0]
            
        if domain.startswith("www."):
            domain = domain[4:]
            
        w_id = db.add_website(domain)
        if w_id:
            self.new_website_entry.set_text("")
            self._refresh_websites_list()
        else:
            toast = Adw.Toast.new("Website already in list")
            self.add_toast(toast)

    def _on_enable_blocker_changed(self, switch, param):
        if getattr(self, "_is_initializing", False) or getattr(self, "_is_reverting", False):
            return
        is_enabled = switch.get_active()
        
        if is_enabled:
            if db.get_setting("polkit_installed", "False") != "True":
                self._check_install_polkit(switch, is_normal=False)
            else:
                db.set_setting("web_blocker_enabled", "True")
        else:
            db.set_setting("web_blocker_enabled", "False")

    def _on_block_normal_changed(self, switch, param):
        if getattr(self, "_is_initializing", False) or getattr(self, "_is_reverting", False):
            return
        is_enabled = switch.get_active()
        
        if is_enabled:
            if db.get_setting("polkit_installed", "False") != "True":
                self._check_install_polkit(switch, is_normal=True)
            else:
                db.set_setting("web_blocker_normal_mode", "True")
        else:
            db.set_setting("web_blocker_normal_mode", "False")

    def _revert_switch(self, switch):
        self._is_reverting = True
        switch.set_active(False)
        self._is_reverting = False

    def _check_install_polkit(self, switch, is_normal):
        if db.get_setting("polkit_installed", "False") == "True":
            return

        if getattr(self, "_install_dialog_open", False):
            self._revert_switch(switch)
            return
            
        self._install_dialog_open = True

        dialog = Adw.MessageDialog(
            heading="Install Web Blocker?",
            body="To block websites seamlessly without asking for your password on every session, Deep Dive needs to install a one-time security rule.\n\nThis will require your password once to complete the setup.",
        )
        dialog.set_transient_for(self.get_root())
        dialog.add_response("cancel", "Not Now")
        dialog.add_response("install", "Install Rule")
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dlg, response):
            self._install_dialog_open = False
            if response == "install":
                import subprocess, sys, threading, os
                from gi.repository import GLib
                script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "blocker.py"))
                
                def run_installation(pref_win):
                    try:
                        result = subprocess.run(
                            ["pkexec", "/usr/bin/python3", script_path, "install"],
                            capture_output=True, text=True
                        )
                        if result.returncode == 0:
                            print("Installation successful!")
                            GLib.idle_add(lambda: db.set_setting("polkit_installed", "True"))
                            if is_normal:
                                GLib.idle_add(lambda: db.set_setting("web_blocker_normal_mode", "True"))
                            else:
                                GLib.idle_add(lambda: db.set_setting("web_blocker_enabled", "True"))
                            GLib.idle_add(lambda: pref_win._show_msg("Success", "Web Blocker rule fully installed!"))
                        else:
                            GLib.idle_add(lambda: pref_win._revert_switch(switch))
                            err = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                            print(f"Installation failed: {result.returncode} - {err}")
                            GLib.idle_add(lambda: pref_win._show_msg("Installation Failed", f"Error ({result.returncode}): {err}"))
                    except Exception as e:
                        print(f"Installation exception: {e}")
                        GLib.idle_add(lambda: pref_win._revert_switch(switch))
                        GLib.idle_add(lambda: pref_win._show_msg("Exception", str(e)))
                        
                threading.Thread(target=run_installation, args=(self,), daemon=True).start()
            else:
                self._revert_switch(switch)
        
        dialog.connect("response", on_response)
        dialog.present()

