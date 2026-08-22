# About Deep Dive

## 1. What is Deep Dive?
**Name:** Deep Dive (formerly Plumb)

**The Idea:** Regular timers just count down the minutes, but they don't stop you from getting distracted. Deep Dive is different. When you start a timer, it's like going underwater—distractions can't reach you. You either finish the timer, or you have to click a button that says "Give Up" to stop early.

## 2. Taglines
* "A strict Pomodoro timer for GNOME."
* "A timer that actually makes you focus."

## 3. Terms We Use
* **Submerge Mode:** The mode where you can't pause the timer. 
* **Give Up:** The button you press to stop a session early. We use "Give Up" instead of "Pause" or "Stop" to make you think before quitting.
* **Surface (Breaks):** When your work timer ends and you take a break. Notifications turn back on and websites are unblocked.

## 4. Main Features

### Submerge Mode
When you turn this on, you can't pause or skip your timer. You have to finish your work or click "Give Up".

### Web Blocker
The app edits your computer's `/etc/hosts` file to block websites like Reddit or YouTube while your timer is running.

### Break Screen
When it's time for a break, the app covers your entire screen so you are forced to stop working. 

### Do Not Disturb
When you start a timer, the app turns on GNOME's "Do Not Disturb" mode so you don't get notifications. It turns them back on when you take a break.

### Mini Mode
You can shrink the app into a small window that stays on top of your other apps so you can always see the timer.

### Project Tracking
The app remembers how much time you spend on different projects and shows you charts of your progress.

## 5. Design
* **Style:** The app is built to look like a normal GNOME app using GTK4.
* **Colors:** We use deep blues and dark colors to match the underwater theme.
* **Fonts:** We use the standard GNOME fonts so it fits in perfectly with your desktop.
