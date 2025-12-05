import streamlit as st
import datetime
import os
import random
import pandas as pd
from PIL import Image, ImageDraw

# ===================== CONFIG / CONSTANTS =====================

AGE_GUIDELINES = {
    "Child (4-8)": 1200,
    "Teen (9-13)": 1700,
    "Adult (14-64)": 2200,
    "Senior (65+)": 1800,
}

HYDRATION_TIPS = [
    "Drink a glass of water after you wake up.",
    "Sip water regularly instead of chugging.",
    "Keep a water bottle near your study or work desk.",
    "Drink one glass of water with every meal.",
    "Thirst is a late sign — drink before you feel thirsty.",
    "Water helps with focus, mood, and energy.",
    "Add lemon or cucumber slices for taste.",
    "Eat water-rich foods like watermelon and cucumber.",
]

XP_PER_ML_DIVISOR = 10
XP_PER_LEVEL = 500

# ---------- file helpers (multi-profile) ----------

def get_profile_suffix() -> str:
    if "profile_name" in st.session_state:
        name = st.session_state.profile_name
        return name.replace(" ", "_").lower()
    return "default"

def get_data_file() -> str:
    return f"water_log_{get_profile_suffix()}.txt"

def get_profile_file() -> str:
    return f"water_profile_{get_profile_suffix()}.txt"


# ===================== STATE INIT / FILE I/O =====================

def init_state():
    s = st.session_state
    if "profile_name" not in s:
        s.profile_name = "Me"
    if "age_group" not in s:
        s.age_group = "Adult (14-64)"
    if "goal_ml" not in s:
        s.goal_ml = AGE_GUIDELINES[s.age_group]
    if "use_weight_goal" not in s:
        s.use_weight_goal = False
    if "weight_kg" not in s:
        s.weight_kg = 60
    if "total_ml" not in s:
        s.total_ml = 0
    if "dark_mode" not in s:
        s.dark_mode = False
    if "data_loaded" not in s:
        s.data_loaded = False
    if "_ask_reset" not in s:
        s._ask_reset = False

    if "xp" not in s:
        s.xp = 0
    if "level" not in s:
        s.level = 1
    if "last_xp_gain" not in s:
        s.last_xp_gain = 0

    # cosmetics from XP shop
    for key in ("has_bandana", "has_sunglasses", "has_crown", "has_party_shell"):
        if key not in s:
            s[key] = False

    # reminder minutes (0 = off)
    if "reminder_minutes" not in s:
        s.reminder_minutes = 0
    if "last_drink_iso" not in s:
        s.last_drink_iso = None

    # quick-add custom presets
    if "quick1" not in s:
        s.quick1 = 100
    if "quick2" not in s:
        s.quick2 = 250
    if "quick3" not in s:
        s.quick3 = 500


def load_today_from_file():
    data_file = get_data_file()
    today = datetime.date.today().isoformat()
    if not os.path.exists(data_file):
        return

    with open(data_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) != 3:
                continue
            date_str, total_str, goal_str = parts
            if date_str == today:
                try:
                    st.session_state.total_ml = int(total_str)
                    g = int(goal_str)
                    if g > 0:
                        st.session_state.goal_ml = g
                except ValueError:
                    pass


def save_today_to_file():
    data_file = get_data_file()
    today = datetime.date.today().isoformat()
    history = {}

    if os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) != 3:
                    continue
                d, t, g = parts
                try:
                    history[d] = (int(t), int(g))
                except ValueError:
                    continue

    history[today] = (st.session_state.total_ml, st.session_state.goal_ml)

    with open(data_file, "w", encoding="utf-8") as f:
        for d, (t, g) in sorted(history.items()):
            f.write(f"{d},{t},{g}\n")


def load_history():
    data_file = get_data_file()
    history = {}
    if not os.path.exists(data_file):
        return history
    with open(data_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) != 3:
                continue
            d, t, g = parts
            try:
                history[d] = (int(t), int(g))
            except ValueError:
                continue
    return history


def load_profile():
    profile_file = get_profile_file()
    if not os.path.exists(profile_file):
        return
    s = st.session_state
    try:
        with open(profile_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k == "xp":
                    s.xp = int(v)
                elif k == "level":
                    s.level = int(v)
                elif k in ("has_bandana", "has_sunglasses", "has_crown", "has_party_shell"):
                    s[k] = (v == "True")
                elif k == "last_drink_iso":
                    s.last_drink_iso = v if v else None
                elif k == "quick1":
                    s.quick1 = int(v)
                elif k == "quick2":
                    s.quick2 = int(v)
                elif k == "quick3":
                    s.quick3 = int(v)
    except Exception:
        pass


def save_profile():
    s = st.session_state
    profile_file = get_profile_file()
    with open(profile_file, "w", encoding="utf-8") as f:
        f.write(f"xp={s.xp}\n")
        f.write(f"level={s.level}\n")
        f.write(f"has_bandana={s.has_bandana}\n")
        f.write(f"has_sunglasses={s.has_sunglasses}\n")
        f.write(f"has_crown={s.has_crown}\n")
        f.write(f"has_party_shell={s.has_party_shell}\n")
        f.write(f"last_drink_iso={s.last_drink_iso or ''}\n")
        f.write(f"quick1={s.quick1}\n")
        f.write(f"quick2={s.quick2}\n")
        f.write(f"quick3={s.quick3}\n")


# ===================== CORE LOGIC =====================

def recalc_goal_from_age_or_weight():
    s = st.session_state
    if s.use_weight_goal:
        try:
            s.goal_ml = int(s.weight_kg) * 35
        except Exception:
            s.goal_ml = AGE_GUIDELINES.get(s.age_group, 2000)
    else:
        s.goal_ml = AGE_GUIDELINES.get(s.age_group, s.goal_ml)


def set_manual_goal(goal_str: str):
    try:
        val = int(goal_str)
        if val <= 0:
            raise ValueError
        st.session_state.goal_ml = val
        st.session_state.use_weight_goal = False
        save_today_to_file()
        st.success(f"Daily goal set to {val} ml")
    except ValueError:
        st.error("Enter a positive integer for goal (ml).")


def add_xp_from_amount(amount: int):
    gained = max(0, amount // XP_PER_ML_DIVISOR)
    st.session_state.last_xp_gain = gained
    if gained == 0:
        return

    s = st.session_state
    s.xp += gained
    old_level = s.level
    s.level = 1 + s.xp // XP_PER_LEVEL
    save_profile()
    if s.level > old_level:
        st.balloons()
        st.success(f"Level up! You reached Level {s.level} 🎉")


def add_water(amount: int):
    if amount <= 0:
        return
    st.session_state.total_ml += amount
    st.session_state.last_drink_iso = datetime.datetime.now().isoformat()
    add_xp_from_amount(amount)
    save_today_to_file()
    save_profile()


def reset_day():
    st.session_state.total_ml = 0
    st.session_state.last_xp_gain = 0
    st.session_state.last_drink_iso = None
    save_today_to_file()
    save_profile()


def compute_progress():
    goal = max(1, st.session_state.goal_ml)
    total = st.session_state.total_ml
    remaining = max(0, goal - total)
    percent = (total / goal) * 100
    return goal, total, remaining, percent


def motivational_message(percent: float) -> str:
    if percent <= 0:
        return "Start with one glass of water!"
    elif percent < 50:
        return "Good start! Keep sipping through the day."
    elif percent < 75:
        return "Nice! You're more than halfway there."
    elif percent < 100:
        return "Almost there! A few more sips to reach your goal."
    elif percent < 150:
        return "Goal completed! Great job staying hydrated!"
    else:
        return "Wow, you crossed your goal! Stay balanced."


def mascot_state(percent: float):
    if percent < 50:
        return "Neutral"
    elif percent < 75:
        return "Happy"
    elif percent < 100:
        return "Wave"
    else:
        return "Celebrate"


def compute_history_stats(history: dict):
    if not history:
        return 0, None, 0, 0.0, 0, 0.0

    dates = sorted(history.keys())
    total_days = len(dates)

    completed = 0
    total_litres = 0.0
    best_intake = 0
    best_date = None

    for d in dates:
        intake, goal = history[d]
        if intake >= goal:
            completed += 1
        if intake > best_intake:
            best_intake = intake
            best_date = d
        total_litres += intake / 1000.0

    completion_rate = completed / total_days * 100.0

    # streak from latest date
    streak = 0
    last_date = datetime.date.fromisoformat(dates[-1])
    current = last_date
    date_set = set(dates)

    while True:
        d_str = current.isoformat()
        if d_str not in date_set:
            break
        intake, goal = history[d_str]
        if intake < goal:
            break
        streak += 1
        current = current - datetime.timedelta(days=1)

    return streak, best_date, best_intake, completion_rate, total_days, total_litres


def compute_weekly_summary(history: dict):
    if not history:
        return 0, 0, 0, 0.0
    today = datetime.date.today()
    total_intake = 0
    days_count = 0
    days_goal_met = 0
    for i in range(7):
        d = (today - datetime.timedelta(days=i)).isoformat()
        if d in history:
            intake, goal = history[d]
            days_count += 1
            total_intake += intake
            if intake >= goal:
                days_goal_met += 1
    if days_count == 0:
        return 0, 0, 0, 0.0
    avg_intake = total_intake / days_count
    return days_count, total_intake, days_goal_met, avg_intake


def compute_badges(history: dict, streak: int):
    badges = {}
    first_complete = any(intake >= goal for intake, goal in history.values())
    double_goal = any(intake >= 2 * goal for intake, goal in history.values())
    badges["First Day Complete"] = (first_complete, "Finish goal on any day.")
    badges["3-Day Streak"] = (streak >= 3, "Hit your goal 3 days in a row.")
    badges["7-Day Streak"] = (streak >= 7, "Hit your goal 7 days in a row.")
    badges["Double Goal Day"] = (double_goal, "Drink at least 2× your goal in a day.")
    return badges


# ===================== TURTLE MASCOT (PIL IMAGE) =====================

def draw_turtle_image(percent: float) -> Image.Image:
    s = st.session_state
    state = mascot_state(percent)
    p = max(0.0, min(1.5, percent / 100.0))

    img = Image.new("RGBA", (320, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # --- GLOW FOR DARK MODE ---
    if s.dark_mode:
        glow_radius = 90
        center_x, center_y = 160, 110
        d.ellipse(
            [
                (center_x - glow_radius, center_y - glow_radius),
                (center_x + glow_radius, center_y + glow_radius),
            ],
            fill=(255, 255, 255, 30) 
        )
    # --------------------------

    # water level
    water_top = int(170 - 100 * min(1.0, p))
    d.rectangle([0, water_top, 320, 220], fill=(200, 230, 255, 255))

    # shell
    shell_center = (150, 130)
    shell_radius = 55
    shell_color = (80, 160, 80, 255)
    if s.has_party_shell:
        shell_color = (120, 180, 255, 255)

    d.ellipse(
        [
            (shell_center[0] - shell_radius, shell_center[1] - shell_radius),
            (shell_center[0] + shell_radius, shell_center[1] + shell_radius),
        ],
        fill=shell_color,
        outline=(40, 100, 40, 255),
        width=3,
    )
    # shell grid
    d.line([(shell_center[0] - shell_radius, shell_center[1]),
            (shell_center[0] + shell_radius, shell_center[1])],
           fill=(40, 100, 40, 255), width=2)
    d.line([(shell_center[0], shell_center[1] - shell_radius),
            (shell_center[0], shell_center[1] + shell_radius)],
           fill=(40, 100, 40, 255), width=2)

    # head
    head_center = (shell_center[0] + shell_radius + 25, shell_center[1] - 20)
    head_radius = 22
    d.ellipse(
        [
            (head_center[0] - head_radius, head_center[1] - head_radius),
            (head_center[0] + head_radius, head_center[1] + head_radius),
        ],
        fill=(140, 200, 120, 255),
        outline=(40, 100, 40, 255),
        width=2,
    )

    # eyes
    eye_y = head_center[1] - 5
    d.ellipse([(head_center[0] - 10, eye_y - 4),
               (head_center[0] - 4, eye_y + 2)],
              fill=(0, 0, 0, 255))
    d.ellipse([(head_center[0] + 4, eye_y - 4),
               (head_center[0] + 10, eye_y + 2)],
              fill=(0, 0, 0, 255))

    # sunglasses
    if s.has_sunglasses:
        d.rectangle([(head_center[0] - 12, eye_y - 6),
                     (head_center[0] - 2, eye_y + 4)],
                    fill=(0, 0, 0, 255))
        d.rectangle([(head_center[0] + 2, eye_y - 6),
                     (head_center[0] + 12, eye_y + 4)],
                    fill=(0, 0, 0, 255))
        d.line([(head_center[0] - 2, eye_y),
                (head_center[0] + 2, eye_y)], fill=(0, 0, 0, 255), width=2)

    # mouth
    mouth_top = head_center[1] + 8
    if state in ("Happy", "Wave", "Celebrate"):
        d.arc([(head_center[0] - 10, mouth_top - 4),
               (head_center[0] + 10, mouth_top + 8)],
              start=0, end=180, fill=(0, 0, 0, 255), width=2)
    else:
        d.line([(head_center[0] - 8, mouth_top),
                (head_center[0] + 8, mouth_top)], fill=(0, 0, 0, 255), width=2)

    # legs
    leg_y = shell_center[1] + shell_radius - 5
    d.rectangle([(shell_center[0] - 35, leg_y),
                 (shell_center[0] - 15, leg_y + 18)],
                fill=(140, 200, 120, 255))
    d.rectangle([(shell_center[0] + 15, leg_y),
                 (shell_center[0] + 35, leg_y + 18)],
                fill=(140, 200, 120, 255))

    front_leg_base = (shell_center[0] + 5, shell_center[1])
    if state == "Wave":
        d.rectangle([(front_leg_base[0], front_leg_base[1] - 30),
                     (front_leg_base[0] + 16, front_leg_base[1] - 5)],
                    fill=(140, 200, 120, 255))
    else:
        d.rectangle([(front_leg_base[0], front_leg_base[1] + 3),
                     (front_leg_base[0] + 16, front_leg_base[1] + 28)],
                    fill=(140, 200, 120, 255))

    # bandana
    if s.has_bandana:
        d.polygon([(shell_center[0] - 30, shell_center[1] - shell_radius - 5),
                   (shell_center[0] + 10, shell_center[1] - shell_radius - 5),
                   (shell_center[0] - 10, shell_center[1] - shell_radius + 15)],
                  fill=(220, 40, 90, 255))

    # crown
    if s.has_crown:
        cx, cy = head_center[0], head_center[1] - head_radius - 4
        d.polygon([(cx - 18, cy + 14),
                   (cx - 8, cy - 4),
                   (cx, cy + 14),
                   (cx + 8, cy - 4),
                   (cx + 18, cy + 14)],
                  fill=(250, 210, 80, 255),
                  outline=(160, 130, 30, 255))

    # confetti for celebrate
    if state == "Celebrate":
        for x in range(20, 300, 40):
            for y in range(20, 80, 20):
                d.rectangle([(x, y), (x + 4, y + 8)],
                            fill=(random.randint(50, 255),
                                  random.randint(50, 255),
                                  random.randint(50, 255), 255))
    return img


# ===================== STYLING ENGINE =====================

def apply_styles():
    """Enhanced styling with proper metric and badge visibility"""
    
    if st.session_state.dark_mode:
        st.markdown(
            """
            <style>
            /* Dark Mode Theme */
            .stApp {
                background: linear-gradient(135deg, #0a0e27 0%, #1a1d3a 100%);
                color: #FAFAFA;
            }
            
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #1e2139 0%, #2a2d4a 100%);
            }
            
            /* Force all text to white in dark mode */
            h1, h2, h3, h4, h5, h6, p, li, span, div, label {
                color: #FAFAFA !important;
            }
            
            /* Metric styling - CRITICAL FIX */
            [data-testid="stMetricLabel"] {
                color: #B0B8D4 !important;
                font-weight: 500 !important;
            }
            [data-testid="stMetricValue"] {
                color: #FFFFFF !important;
                font-size: 2rem !important;
                font-weight: 700 !important;
            }
            
            /* Inputs */
            .stTextInput input, .stNumberInput input {
                background-color: #2a2d4a !important;
                color: #FAFAFA !important;
                border: 1px solid #3d4163 !important;
            }
            
            /* Buttons */
            .stButton > button {
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white !important;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
            }
            
            /* Disabled buttons (badges) - CRITICAL FIX */
            .stButton > button:disabled {
                background: #2a2d4a !important;
                color: #6B7280 !important;
                opacity: 0.6 !important;
                border: 1px solid #3d4163 !important;
            }
            
            /* Progress bars */
            .stProgress > div > div {
                background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%);
            }
            
            /* Info/Warning boxes */
            .stAlert {
                background-color: #2a2d4a !important;
                border-left: 4px solid #4CAF50 !important;
                color: #FAFAFA !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <style>
            /* Light Mode Theme */
            .stApp {
                background: linear-gradient(135deg, #f8fafc 0%, #e0f2fe 100%);
                color: #1e293b;
            }

            /* Dark Sidebar */
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #1e293b 0%, #334155 100%) !important;
            }
            [data-testid="stSidebar"] * {
                color: #FFFFFF !important;
            }
            [data-testid="stSidebar"] input {
                background-color: #334155 !important;
                color: #FFFFFF !important;
                border: 1px solid #475569 !important;
            }

            /* Main content text */
            .main h1, .main h2, .main h3, .main h4, .main p, .main li, .main label {
                color: #1e293b !important;
            }

            /* Metric styling - CRITICAL FIX */
            [data-testid="stMetricLabel"] {
                color: #64748b !important;
                font-weight: 600 !important;
                font-size: 0.875rem !important;
            }
            [data-testid="stMetricValue"] {
                color: #0f172a !important;
                font-size: 2rem !important;
                font-weight: 700 !important;
            }
            
            /* Inputs */
            .main input, .main .stNumberInput input {
                background-color: #ffffff !important;
                color: #1e293b !important;
                border: 2px solid #e2e8f0 !important;
                border-radius: 8px !important;
            }

            /* Buttons */
            .stButton > button {
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                color: white !important;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
            }
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
            }

            /* Disabled buttons (badges) - CRITICAL FIX */
            .stButton > button:disabled {
                background: #e2e8f0 !important;
                color: #475569 !important;
                opacity: 1 !important;
                border: 2px solid #cbd5e1 !important;
                font-weight: 600 !important;
            }
            
            /* Progress bars */
            .stProgress > div > div {
                background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
            }
            
            /* Info boxes */
            .stAlert {
                background-color: #eff6ff !important;
                border-left: 4px solid #2563eb !important;
                color: #1e293b !important;
            }
            
            /* Cards/Containers */
            div[data-testid="stExpander"] {
                background-color: white !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 12px !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )


# ===================== MAIN APP =====================

def main():
    st.set_page_config(page_title="WaterBuddy", page_icon="💧", layout="wide")
    init_state()
    
    # Apply styles immediately
    apply_styles()

    # Profile selector
    with st.sidebar:
        st.markdown("## 👤 Profile")
        profiles = ["Me", "Family 2", "Family 3"]
        idx = profiles.index(st.session_state.profile_name) if st.session_state.profile_name in profiles else 0
        new_profile = st.selectbox("Select profile", profiles, index=idx)
        if new_profile != st.session_state.profile_name:
            st.session_state.profile_name = new_profile
            st.session_state.data_loaded = False
            st.rerun()

    if not st.session_state.data_loaded:
        load_today_from_file()
        load_profile()
        st.session_state.data_loaded = True

    # Sidebar settings
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        st.markdown("#### Age / Goal")
        new_age = st.selectbox(
            "Age Group",
            list(AGE_GUIDELINES.keys()),
            index=list(AGE_GUIDELINES.keys()).index(st.session_state.age_group),
        )
        if new_age != st.session_state.age_group:
            st.session_state.age_group = new_age
            recalc_goal_from_age_or_weight()
            save_today_to_file()
            st.rerun()

        st.checkbox("Use weight-based goal (ml = kg × 35)",
                    key="use_weight_goal", on_change=recalc_goal_from_age_or_weight)
        st.number_input("Weight (kg)", min_value=10, max_value=200,
                        key="weight_kg", on_change=recalc_goal_from_age_or_weight)

        goal_input = st.text_input(
            "Manual goal (ml)",
            value=str(st.session_state.goal_ml),
        )
        if st.button("Set Goal"):
            set_manual_goal(goal_input)

        st.markdown("---")

        st.markdown("#### Quick-add presets (ml)")
        st.number_input("Preset 1", min_value=10, max_value=5000, key="quick1")
        st.number_input("Preset 2", min_value=10, max_value=5000, key="quick2")
        st.number_input("Preset 3", min_value=10, max_value=5000, key="quick3")
        save_profile()

        st.markdown("---")

        if st.button("🗓️ New Day / Reset"):
            st.session_state._ask_reset = True

        if st.session_state._ask_reset:
            st.warning("Reset today's progress?")
            c1, c2 = st.columns(2
