import gi

gi.require_version("GLib", "2.0")
gi.require_version("Gio", "2.0")
from gi.repository import GLib, Gio
from plumb.database import db


class TimerState:
    FOCUS = "Focus"
    SHORT_BREAK = "Short Break"
    LONG_BREAK = "Long Break"


class TimerLogic:
    def __init__(self):
        self.state = TimerState.FOCUS
        self.is_running = False

        # Default durations (in minutes)
        self.durations = {
            TimerState.FOCUS: int(db.get_setting("duration_focus", 25)),
            TimerState.SHORT_BREAK: int(db.get_setting("duration_short_break", 5)),
            TimerState.LONG_BREAK: int(db.get_setting("duration_long_break", 15)),
        }

        self.time_left = self.durations[self.state] * 60
        self.current_total_time = self.time_left
        self.focus_sessions_completed = 0
        self.cycles = int(db.get_setting("cycles", 4))

        self.auto_start_breaks = db.get_setting("auto_start_breaks", "False") == "True"
        self.auto_start_pomodoros = (
            db.get_setting("auto_start_pomodoros", "False") == "True"
        )
        self.pause_on_lock = db.get_setting("pause_on_lock", "True") == "True"

        self.notify_running_out = db.get_setting("notify_running_out", "True") == "True"
        self.enable_screen_overlay = (
            db.get_setting("enable_screen_overlay", "False") == "True"
        )
        self.lock_delay = db.get_setting("lock_delay", "Never")
        self.reopen_delay = db.get_setting("reopen_delay", "30 seconds")
        self.show_overlay_quotes = (
            db.get_setting("show_overlay_quotes", "True") == "True"
        )

        # Callbacks that the UI can hook into
        self.on_tick_callback = None
        self.on_finish_callback = None
        self.on_state_change_callback = None
        self.on_warning_callback = None
        self.on_run_state_change_callback = None

        self.dnd_sync = db.get_setting("dnd_sync", "False") == "True"
        self._original_dnd_state = None

        self._timeout_id = None

    def _cleanup_dnd(self):
        if self.dnd_sync:
            self._set_gnome_dnd(False)

    def set_duration(self, state, duration_minutes, update_active=True):
        old_duration = self.durations.get(state, 0)
        self.durations[state] = duration_minutes

        if state == TimerState.FOCUS:
            db.set_setting("duration_focus", duration_minutes)
        elif state == TimerState.SHORT_BREAK:
            db.set_setting("duration_short_break", duration_minutes)
        elif state == TimerState.LONG_BREAK:
            db.set_setting("duration_long_break", duration_minutes)

        if self.state == state and update_active:
            delta_minutes = duration_minutes - old_duration
            self.time_left += delta_minutes * 60
            self.current_total_time = duration_minutes * 60
            if self.time_left < 0:
                self.time_left = 0

            if self.on_tick_callback:
                self.on_tick_callback(self.time_left)

    def start(self):
        if not self.is_running:
            self.is_running = True
            if self.dnd_sync and self.state == TimerState.FOCUS:
                self._set_gnome_dnd(True)
            if self.on_run_state_change_callback:
                self.on_run_state_change_callback(True)
            self._timeout_id = GLib.timeout_add(1000, self._on_tick)

    def pause(self):
        if self.is_running:
            self.is_running = False
            if self.dnd_sync:
                self._set_gnome_dnd(False)
            if self.on_run_state_change_callback:
                self.on_run_state_change_callback(False)
            if self._timeout_id:
                GLib.source_remove(self._timeout_id)
                self._timeout_id = None

    def reset(self):
        self.pause()
        self.time_left = self.durations[self.state] * 60
        self.current_total_time = self.time_left
        if self.on_tick_callback:
            self.on_tick_callback(self.time_left)

    def next_state(self):
        """Automatically transitions to the next Pomodoro state."""
        if self.state == TimerState.FOCUS:
            self.focus_sessions_completed += 1
            if self.focus_sessions_completed % self.cycles == 0:
                self.state = TimerState.LONG_BREAK
            else:
                self.state = TimerState.SHORT_BREAK
        else:
            self.state = TimerState.FOCUS

        self.time_left = self.durations[self.state] * 60
        self.current_total_time = self.time_left

        if self.on_state_change_callback:
            self.on_state_change_callback(self.state)

    def _on_tick(self):
        if not self.is_running:
            return GLib.SOURCE_REMOVE

        if self.time_left > 0:
            self.time_left -= 1
            if (
                self.time_left == 10
                and self.on_warning_callback
                and self.notify_running_out
            ):
                self.on_warning_callback()
            if self.on_tick_callback:
                self.on_tick_callback(self.time_left)
            return GLib.SOURCE_CONTINUE

        # Timer hit 0
        completed_state = self.state
        completed_duration = self.durations[self.state]

        self.is_running = False

        if self.dnd_sync:
            self._set_gnome_dnd(False)

        self.next_state()  # Automatically prep the next state

        if self.state == TimerState.FOCUS and self.auto_start_pomodoros:
            self.start()
        elif self.state != TimerState.FOCUS and self.auto_start_breaks:
            self.start()

        if self.on_finish_callback:
            self.on_finish_callback(completed_state, completed_duration)

        return GLib.SOURCE_REMOVE

    def _set_gnome_dnd(self, enable):
        try:
            settings = Gio.Settings.new("org.gnome.desktop.notifications")
            if enable:
                self._original_dnd_state = settings.get_boolean("show-banners")
                if self._original_dnd_state:
                    settings.set_boolean("show-banners", False)
            else:
                if self._original_dnd_state is not None:
                    settings.set_boolean("show-banners", self._original_dnd_state)
                    self._original_dnd_state = None
            Gio.Settings.sync()
        except Exception as e:
            print("Failed to toggle DND:", e)


class StopwatchLogic:
    def __init__(self):
        self.elapsed_seconds = 0
        self.is_running = False
        self.on_tick_callback = None
        self._timeout_id = None
        self.dnd_sync = db.get_setting("dnd_sync", "False") == "True"
        self._original_dnd_state = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            if self.dnd_sync:
                self._set_gnome_dnd(True)
            self._timeout_id = GLib.timeout_add(1000, self._on_tick)

    def pause(self):
        if self.is_running:
            self.is_running = False
            if self.dnd_sync:
                self._set_gnome_dnd(False)
            if self._timeout_id:
                GLib.source_remove(self._timeout_id)
                self._timeout_id = None

    def reset(self):
        self.pause()
        self.elapsed_seconds = 0
        if self.on_tick_callback:
            self.on_tick_callback(self.elapsed_seconds)

    def _on_tick(self):
        if not self.is_running:
            return GLib.SOURCE_REMOVE

        self.elapsed_seconds += 1
        if self.on_tick_callback:
            self.on_tick_callback(self.elapsed_seconds)
        return GLib.SOURCE_CONTINUE

    def _set_gnome_dnd(self, enable):
        try:
            settings = Gio.Settings.new("org.gnome.desktop.notifications")
            if enable:
                self._original_dnd_state = settings.get_boolean("show-banners")
                if self._original_dnd_state:
                    settings.set_boolean("show-banners", False)
            else:
                if self._original_dnd_state is not None:
                    settings.set_boolean("show-banners", self._original_dnd_state)
                    self._original_dnd_state = None
            Gio.Settings.sync()
        except Exception as e:
            print("Failed to toggle DND:", e)
