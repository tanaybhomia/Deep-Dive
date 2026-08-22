# How to Use Deep Dive

Deep Dive is a timer that stops you from getting distracted. Here is how to use its main features.

---

## Submerge Mode
**What it is:** When you turn this on, you can't pause or skip your work session. 

**Why we made it:** Regular timers let you pause whenever you want. Submerge Mode removes the pause button. If you really need to stop early, you have to click a **"Give Up"** button. This deletes your current session and makes you think twice before quitting.

**How to use it:** 
1. Pick a project from the dropdown list.
2. Click the Anchor button next to the Play button to turn it on.
3. Click Play. The timer starts and you can't pause it until the time is up.

---

## Minimum Session Time
**What it is:** A setting that requires you to work for a certain amount of time (like 5 minutes) before a session is counted and saved to your stats.

**Why we made it:** If you start a timer and immediately get distracted or stop it, that time shouldn't count toward your productive hours. 

**How to use it:**
1. Click the menu button (three dots) and open **Preferences**.
2. Set your preferred minimum time limit. 
3. When you are in Submerge Mode, if you click "Give Up" before this minimum time has passed, the session will be discarded completely. If you pass the minimum time and then give up, the time you spent working will still be saved.

---

## Web Blocker
**What it is:** A tool that stops you from opening distracting websites like Reddit or YouTube while you are working.

**How it works:** The app edits your computer's `/etc/hosts` file to block the websites when a timer starts, and unblocks them when a break starts.

**How to use it:**
1. Click the menu button (three dots) and open **Preferences**.
2. Go to the **Web Blocker** tab.
3. Click "Install Polkit Rule". It will ask for your password once. This allows the app to block websites automatically in the future without asking for your password every time.
4. Turn on "Enable Web Blocker". You can also choose to block websites even when Submerge Mode is off.
5. Type in the websites you want to block (like `reddit.com` or `twitter.com`).

---

## Project Tracking & Stats
**What it is:** A page that shows how much time you spent working on different things. 

**How it works:** When a timer finishes normally, the app saves that time on your computer.

**How to use it:**
1. Open **Preferences**.
2. Go to the **Projects** tab. Add tags for your work, like "Coding", "Reading", or "Email".
3. Before starting a timer, pick one of these projects from the dropdown menu. 
4. Click the Stats button on the main window to see charts of your focused time for the week.
