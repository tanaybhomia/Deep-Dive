# Deep Dive: Brand & Feature Guidelines

## 1. Core Identity & Philosophy
**Name:** Deep Dive (formerly Plumb)
**The Philosophy:** Most productivity timers are passive—they count down while you get distracted. Deep Dive is *active*. Based on the concept of "Submerging," it operates on the principle that deep work requires strict, physical boundaries. When you start a timer, you are going underwater where surface-level distractions cannot reach you. You either finish the dive, or you deliberately "Give Up" and surface early.

## 2. Taglines & Positioning
**Primary Tagline:** 
* "The uncompromising Pomodoro timer for GNOME."

**Alternative Taglines:**
* "Submerge yourself. Get work done."
* "Built for deep work, strict discipline, and zero distractions."
* "A timer that actually forces you to focus."

## 3. The "Deep Dive" Lexicon
* **Submerge Mode:** The strict state where the user is locked into a focus block. 
* **Give Up:** The psychological friction button. Instead of a casual "Pause" or "Skip," users must actively admit defeat to break a session early.
* **Surface (Breaks):** The state of returning to regular desktop usage (notifications enabled, websites unblocked).

## 4. Main Features (The "Why")

### The Submerge Engine (Core Feature)
The heart of Deep Dive. When Submerge is active, the app removes the ability to pause or skip. It is a strict "commit or quit" contract between the user and their work.

### System-Level Distraction Blocking
Using a seamless Polkit integration, Deep Dive doesn't just ask you to stay focused—it modifies your `/etc/hosts` file at the system level to instantly block websites like Reddit, Twitter, or YouTube the second a dive begins. 

### Full-Screen Break Overlays
When it's time to surface, Deep Dive takes over the screen. A native, multi-monitor supported overlay physically forces the user to stop working and take a screen break, displaying a motivational quote.

### GNOME DND Sync
Deep integration with the Linux desktop. Starting a dive automatically triggers GNOME's "Do Not Disturb" mode, silencing all notifications, and seamlessly restores them during breaks.

### Fluid Mini-Mode
A sleek, floating compact window that keeps the timer visible without taking up valuable screen real estate, perfectly adapting to light/dark themes.

### Project Tracking
Built-in SQLite database tracking that silently logs focused time against user-defined projects, accessible via the active project selector.

## 5. Visual Identity (GNOME HIG)
* **Design System:** Strict adherence to GTK4 and Libadwaita.
* **Colors:** Deep blues, dark themes, and high-contrast accents to represent the ocean depths and focus states.
* **Typography:** Clean, native GNOME fonts (Inter/Cantarell), utilizing bold weights for active states to ensure readability at a glance.
