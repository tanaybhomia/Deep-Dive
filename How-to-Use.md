# How to Use Deep Dive

Deep Dive isn't just a countdown timer—it's designed with strict, built-in friction to force you to focus. Below are the core workflows you need to understand to get the most out of the app.

---

## ⚓ Submerge Mode
**What it is:** Submerge Mode is the ultimate productivity contract. When you click the anchor icon before starting a Pomodoro, you are locked in. 

**Why it is there:** Standard timers let you casually pause them when you get a text message, or skip them when you feel lazy. Submerge Mode removes those buttons. Your only option to stop the timer early is to click a bright red **"Give Up"** button, which forces you to psychologically admit defeat and discards the session entirely.

**How to use it:** 
1. Select a Project from the dropdown.
2. Toggle the Anchor button next to the Play button so it is highlighted.
3. Click Play. You are now Submerged. There is no pausing until the timer hits zero.

---

## 🛡️ Web Blocker
**What it is:** A system-level blocker that prevents your browser from accessing distracting websites (like Reddit, YouTube, or Twitter) while a focus session is active.

**How it works:** Under the hood, Deep Dive uses Polkit to safely modify your Linux `/etc/hosts` file. It routes distracting domains to `0.0.0.0` the second a timer starts, and instantly restores the file the second a break begins. 

**How to use it:**
1. Click the hamburger menu (three dots) and open **Preferences**.
2. Navigate to the **Web Blocker** tab.
3. Click "Install Polkit Rule". You will be asked for your system password *once* so that the app can block websites seamlessly in the future without ever asking for your password again.
4. Toggle on "Enable Web Blocker". You can optionally check the box to enforce the blocker even when Submerge Mode is turned off.
5. Add your distracting domains (e.g., `reddit.com`, `twitter.com`) to the list.

---

## 📊 Project Tracking & Stats
**What it is:** A built-in dashboard that visualizes where your time went. It tracks completed Pomodoros (25-minute blocks) and logs your total focus time.

**How it works:** Every time a timer naturally completes (without you pressing "Give Up"), the time is securely logged into a local, private SQLite database stored directly on your machine.

**How to use it:**
1. Open **Preferences**.
2. Go to the **Projects** tab. Here, you can define different tags like "Coding", "Reading", or "Email".
3. Before starting a timer, select the relevant project from the dropdown selector on the main screen. 
4. The Stats page (accessible from the main window) will automatically generate charts and total hour breakdowns based on these projects, helping you review your productivity over the week.
