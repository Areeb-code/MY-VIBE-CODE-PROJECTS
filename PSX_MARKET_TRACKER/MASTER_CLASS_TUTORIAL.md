# 🎓 Python Master Class: The PSX Market Tracker Deep Dive
**A Complete Guide for Python Scripters transitioning to GUI Development**

Welcome! If you are reading this, you probably know how to write Python scripts—code that runs in a black terminal window, takes input, and gives an output. But building a **High-Fidelity Desktop Application** (like the PSX Market Tracker) requires a complete shift in how you think about code.

This is your **Master Class**. We will break down every complex piece of this app so you can build your own.

---

## 🏗️ Part 1: The "Mental Shift" (Terminal vs. GUI)

In a normal script, you control the time. You say: `input("Name: ")`. The computer stops and waits for you. 

In a **GUI (Graphical User Interface)**, the **User controls the time**. 

### 1. The Event Loop
A GUI app is basically a `while True:` loop that runs at 60 frames per second. It is constantly asking: 
- "Did they click the Close button?"
- "Did they hover over the Search bar?"
- "Is it time to refresh the price data?"

This is why we use **PyQt6**. It handles this massive loop for us.

### 2. The "Lego" Architecture
Everything you see on screen is a **Widget** (`QWidget`). 
- A Button is a `QPushButton`.
- A Text label is a `QLabel`.
- A Window is a `QMainWindow`.

Think of them as Legos. You take a big Lego board (The Window) and you snap smaller Legos onto it.

---

## 📂 Part 2: Project Architecture (Professional Folder Structure)

We didn't just dump all files in one folder. We separated them based on their **Job**.

```text
PSX_SCRAPPER/
├── run.py                 # The entry point (where the app starts)
├── app/
│   ├── core/              # The "Invisible" Logic (Saving, Scraping, Math)
│   │   ├── managers.py    # Handles Settings and System Tray
│   │   └── workers.py     # Background threads for scraping
│   └── ui/                # The "Visible" Interface (What you see)
│       ├── onboarding.py  # The 3-step intro sequence
│       ├── dialogs.py     # Popups and Settings windows
│       └── pages/         # Individual app screens (Dashboard, Search, etc.)
└── assets/                # Images, Icons, and Logos
```

**Why do this?** If you want to change the "Begin Journey" button color, you know exactly where to go: `app/ui/onboarding.py`. You don't have to sift through the code that downloads stock prices.

---

## 🎨 Part 3: Styling like a Pro (The CSS Magic)

You mentioned you know a bit about HTML/CSS. In PyQt, we use **QSS (Qt Style Sheets)**. It is almost identical to CSS.

### 1. The Global Theme (`app/core/theme.py`)
Instead of styling every button individually, we define a "Global CSS" string.

```css
QPushButton {
    background-color: #1a1a2e; /* Dark Blue */
    color: white;              /* White Text */
    border: 2px solid #10b981; /* Green Neon Border */
    border-radius: 10px;       /* Rounded Corners */
    font-weight: bold;
}

QPushButton:hover {
    background-color: #21213a; /* Slightly lighter on hover */
    border-color: #0d9668;     /* Darker green border */
}
```

### 2. Layouts (The Invisible Skeleton)
Screens have different sizes. You can't just say "put this button at 100 pixels from the left." If someone stretches the window, the button will be in the wrong place.

We use **Layouts**:
- `QVBoxLayout`: Stacks things like a tower (Top to Bottom).
- `QHBoxLayout`: Stacks things like a train (Left to Right).

---

## ✨ Part 4: Deep Dive into "Cool" Features

Let's look at the actual code for the effects we built.

### 1. The Gaussian Blur Entry (`app/ui/onboarding.py`)
When Step 1 opens, it starts blurry and slowly becomes clear. How?

```python
# 1. Create the effect
self.blur_effect = QGraphicsBlurEffect()
self.setGraphicsEffect(self.blur_effect) # Apply it to the whole window

# 2. Create an "Animator"
self.anim = QPropertyAnimation(self.blur_effect, b"blurRadius")
self.anim.setDuration(400)   # 400 milliseconds
self.anim.setStartValue(30)  # Start very blurry (30px)
self.anim.setEndValue(0)     # End perfectly clear (0px)
self.anim.start()            # GO!
```

### 2. The "Glow Below" Button (`app/ui/onboarding.py` -> `GlowButton`)
The user wanted a neon glow *only below* the button on hover. We used a **Shadow Effect** with an **Offset**.

```python
# On Hover (enterEvent)
self.shadow.setBlurRadius(25)
self.shadow.setOffset(0, 4) # 0px left/right, 4px DOWN
self.shadow.setColor(QColor(16, 185, 129, 200)) # Green with some transparency
```

### 3. The Intensive Title Glow
To make the titles (like "Who are we tracking for?") pop, we used a high-intensity white glow.

```python
glow = QGraphicsDropShadowEffect()
glow.setBlurRadius(30) # Massive spread
glow.setOffset(0, 0)   # Glow in all directions
glow.setColor(QColor(255, 255, 255, 255)) # Pure white, NO transparency
title.setGraphicsEffect(glow)
```

---

## 🧵 Part 5: Threads (Keeping the App Fast)

This is the most "Senior Level" concept in the app. 

**The Problem:** Scraping the PSX website takes 2-3 seconds. If you do this in the `on_click` function of a button, the whole app will freeze for 3 seconds while it waits for the data. The user will think the app crashed.

**The Solution:** The `ScraperThread` (`app/core/workers.py`).

1. We create a "Worker" that lives outside the main app.
2. The Worker goes to the internet, gets the data.
3. When it's done, it sends a **Signal** (like a text message) back to the main app: `"Hey, I have the data! Here it is."`
4. The main app receives the signal and updates the table.

```python
# The Signal definition
data_received = pyqtSignal(list)

# Sending the signal
self.data_received.emit(my_list_of_stocks)
```

---

## 🧪 Part 6: How to Master This

You have the full source code. Here is how you should practice:

1. **Color Swap**: Go to `app/ui/onboarding.py` and change the Green `#10b981` to a Gold `#ffd700`. Run the app.
2. **Timing Tweak**: Change the `animate_step_entry` duration from `400` to `2000`. Watch the titles slowly become clear.
3. **Add a Label**: Try to add a new `QLabel` to the Dashboard page with your name.

### Where is the Code? (Cheat Sheet)
- **Colors & Styles**: `app/core/theme.py`
- **What happens on click**: Look for `.clicked.connect(...)` in the files.
- **The Main Screen**: `app/ui/main_window.py`
- **Exporting PDF/Excel**: `app/ui/pages/portfolio_page.py`

**You are now the builder.** The code is your workshop. Happy coding!
