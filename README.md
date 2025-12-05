# 💧 WaterBuddy
### A Gamified Hydration Tracker & Wellness Companion

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

**WaterBuddy** is an open-source, gamified hydration tracking application built with Python and Streamlit. It uses a dynamic "Water Turtle" mascot and an XP system to motivate users to stay hydrated.

---

## 🚀 Live Demo

Try the application live in your browser without installing anything:

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](YOUR_STREAMLIT_SHARE_LINK_HERE)

> **Link:** Replace this with your actual Streamlit Cloud URL, for example:  
> `https://waterbuddy.streamlit.app`

---

## 1. Project Overview

WaterBuddy is designed to solve the problem of hydration neglect through positive reinforcement. Unlike standard trackers, it features a **procedurally generated mascot** that visually reacts to your water intake.

The app is built entirely in **Python** using the **Streamlit** framework, focusing on a lightweight, no-database architecture that stores data locally (`.txt` files) for privacy and ease of use. It includes an XP (Experience Points) system, a virtual shop to customize your mascot, and detailed historical insights.

---

## 2. Key Features

### 🎮 Gamification & Motivation
* **Dynamic Mascot:** A turtle drawn in real-time (using `PIL`) that changes poses (Neutral, Happy, Waving, Celebrating) based on your daily progress.
* **XP System:** Earn XP for every milliliter of water consumed.
* **Leveling Up:** Gain levels as you hit hydration milestones.
* **XP Shop:** Use earned XP to buy accessories like Sunglasses, Crowns, Party Shells, and Bandanas.

### 📊 Tracking & Analytics
* **Smart Goals:** Automatically calculate daily water needs based on **Age Group** or **Weight (kg)**.
* **Data Visualization:** Interactive line charts showing hydration trends over time.
* **Weekly Summary:** Automated statistics for the last 7 days (Average intake, days goal met).
* **Badges:** Unlock achievements like "7-Day Streak" or "Double Goal Day".

### ⚙️ User Experience
* **Dark/Light Mode:** A fully custom-themed UI that switches seamlessly between dark and light modes with high-contrast text.
* **Multi-Profile Support:** Manage hydration logs for multiple users (e.g., "Me", "Family 2") on the same device.
* **Smart Reminders:** Visual warnings if you haven't logged water for a set period (30/60/90 mins).

---

## 3. Installation & Setup

### Prerequisites
* Python 3.8 or higher installed.

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/waterbuddy.git
cd waterbuddy
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
streamlit run app.py
```

The app will open automatically at:  
`http://localhost:8501`

---

## 4. File Structure

- `app.py` — Main application code (UI, logic, styling, game mechanics)  
- `requirements.txt` — Python dependency list  
- `water_log_{profile}.txt` — Auto-generated hydration logs  
- `water_profile_{profile}.txt` — Auto-generated XP, level, inventory, and settings  

---

## 5. Technology Stack

| Component | Technology | Usage |
|----------|------------|--------|
| **Frontend** | Streamlit | UI, widgets, state management |
| **Data Handling** | Pandas | Historical data, charts |
| **Graphics** | Pillow (PIL) | Dynamic turtle mascot |
| **Styling** | CSS / Markdown | Custom themes |

---

## 6. How to Use

1. **Set Your Profile:** Choose a profile name in the sidebar.  
2. **Configure Goals:** Set age/weight-based hydration targets.  
3. **Log Water:** Use quick-add buttons or custom amounts.  
4. **Watch the Turtle:** Turtle becomes happier as you progress.  
5. **Spend XP:** Buy accessories in the XP Shop.  

---

## 7. Future Roadmap

- ☁️ Cloud Sync  
- 📱 Mobile App (native wrapper)  
- 🔔 Push Notifications  
- 🏆 Leaderboard system  

---

### License

This project is open-source and available under the MIT License.
