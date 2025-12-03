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

DATA_FILE = "water_log.txt"          # per-day intake history
PROFILE_FILE = "water_profile.txt"   # XP + cosmetics

XP_PER_ML_DIVISOR = 10
XP_PER_LEVEL = 500


# ===================== STATE INIT / FILE I/O =====================

def init_state():
    s = st.session_state
    if "age_group" not in s:
        s.age_group = "Adult (14-64)"
    if "goal_ml" not in s:
        s.goal_ml = AGE_GUIDELINES[s.age_group]
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
    if "has_bandana" not in s:
        s.has_bandana = False
    if "has_sunglasses" not in s:
        s.has_sunglasses = False
    if "has_crown" not in s:
        s.has_crown = False
    if "has_party_shell" not in s:
        s.has_party_shell = False


def load_today_from_file():
    today = datetime.date.today().isoformat()
    if not os.path.exists(DATA_FILE):
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
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
    """YYYY-MM-DD,total,goal per line."""
    today = datetime.date.today().isoformat()
    history = {}

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
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

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for d, (t, g) in sorted(history.items()):
            f.write(f"{d},{t},{g}\n")


def load_history():
    history = {}
    if not os.path.exists(DATA_FILE):
        return history
    with open(DATA_FILE, "r", encoding="utf-8") as f:
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
    if not os.path.exists(PROFILE_FILE):
        return
    s = st.session_state
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
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
                    setattr(s, k, v == "True")
    except Exception:
        pass


def save_profile():
    s = st.session_state
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        f.write(f"xp={s.xp}\n")
        f.write(f"level={s.level}\n")
        f.write(f"has_bandana={s.has_bandana}\n")
        f.write(f"has_sunglasses={s.has_sunglasses}\n")
        f.write(f"has_crown={s.has_crown}\n")
        f.write(f"has_party_shell={s.has_party_shell}\n")


# ===================== CORE LOGIC =====================

def recalc_goal_from_age():
    st.session_state.goal_ml = AGE_GUIDELINES.get(
        st.session_state.age_group,
        st.session_state.goal_ml,
    )


def set_manual_goal(goal_str: str):
    try:
        val = int(goal_str)
        if val <= 0:
            raise ValueError
        st.session_state.goal_ml = val
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
    add_xp_from_amount(amount)
    save_today_to_file()


def reset_day():
    st.session_state.total_ml = 0
    st.session_state.last_xp_gain = 0
    save_today_to_file()


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


# ===================== TURTLE MASCOT (PIL IMAGE) =====================

def draw_turtle_image(percent: float) -> Image.Image:
    """
    Draw a simple cartoon turtle whose pose depends on progress.
    - Neutral: normal standing
    - Happy: smile
    - Wave: front leg up
    - Celebrate: confetti around
    Cosmetics from XP shop are layered on top.
    """
    s = st.session_state
    state = mascot_state(percent)
    p = max(0.0, min(1.5, percent / 100.0))  # clamp

    img = Image.new("RGBA", (320, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # water level (background)
    water_top = int(170 - 100 * min(1.0, p))
    d.rectangle([0, water_top, 320, 220], fill=(200, 230, 255, 255))

    # shell
    shell_center = (150, 130)
    shell_radius = 55
    shell_color = (80, 160, 80, 255)
    if s.has_party_shell:
        shell_color = (120, 180, 255, 255)  # party shell

    d.ellipse(
        [
            (shell_center[0] - shell_radius, shell_center[1] - shell_radius),
            (shell_center[0] + shell_radius, shell_center[1] + shell_radius),
        ],
        fill=shell_color,
        outline=(40, 100, 40, 255),
        width=3,
    )

    # shell pattern (simple grid)
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

    # legs: back legs fixed
    leg_y = shell_center[1] + shell_radius - 5
    d.rectangle([(shell_center[0] - 35, leg_y),
                 (shell_center[0] - 15, leg_y + 18)],
                fill=(140, 200, 120, 255))
    d.rectangle([(shell_center[0] + 15, leg_y),
                 (shell_center[0] + 35, leg_y + 18)],
                fill=(140, 200, 120, 255))

    # front/waving leg
    front_leg_base = (shell_center[0] + 5, shell_center[1])
    if state == "Wave":
        # raised leg
        d.rectangle([(front_leg_base[0], front_leg_base[1] - 30),
                     (front_leg_base[0] + 16, front_leg_base[1] - 5)],
                    fill=(140, 200, 120, 255))
    else:
        # normal leg
        d.rectangle([(front_leg_base[0], front_leg_base[1] + 3),
                     (front_leg_base[0] + 16, front_leg_base[1] + 28)],
                    fill=(140, 200, 120, 255))

    # bandana accessory
    if st.session_state.has_bandana:
        d.polygon([(shell_center[0] - 30, shell_center[1] - shell_radius - 5),
                   (shell_center[0] + 10, shell_center[1] - shell_radius - 5),
                   (shell_center[0] - 10, shell_center[1] - shell_radius + 15)],
                  fill=(220, 40, 90, 255))

    # crown accessory
    if st.session_state.has_crown:
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
                d.rectangle([(x, y), (x + 4, y + 8)], fill=(random.randint(50, 255),
                                                            random.randint(50, 255),
                                                            random.randint(50, 255), 255))

    return img


# ===================== DARK MODE (CSS) =====================

def apply_dark_mode():
    if st.session_state.dark_mode:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #020617;
                color: #f9fafb;
            }
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #f3f4f6;
                color: #020617;
            }
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


# ===================== MAIN APP =====================

def main():
    st.set_page_config(page_title="WaterBuddy", page_icon="💧", layout="wide")
    init_state()

    if not st.session_state.data_loaded:
        load_today_from_file()
        load_profile()
        st.session_state.data_loaded = True

    apply_dark_mode()

    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        st.markdown("#### Age Group")
        new_age = st.selectbox(
            "Select Age Group",
            list(AGE_GUIDELINES.keys()),
            index=list(AGE_GUIDELINES.keys()).index(st.session_state.age_group),
            label_visibility="collapsed",
        )
        if new_age != st.session_state.age_group:
            st.session_state.age_group = new_age
            recalc_goal_from_age()
            save_today_to_file()
            st.rerun()

        st.markdown("#### Daily Goal (ml)")
        goal_input = st.text_input(
            "Manual goal (ml)",
            value=str(st.session_state.goal_ml),
            label_visibility="collapsed",
        )
        if st.button("Set Goal"):
            set_manual_goal(goal_input)

        st.markdown("---")

        if st.button("🗓️ New Day / Reset"):
            st.session_state._ask_reset = True

        if st.session_state._ask_reset:
            st.warning("Reset today's progress?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes"):
                    reset_day()
                    st.session_state._ask_reset = False
                    st.rerun()
            with c2:
                if st.button("❌ No"):
                    st.session_state._ask_reset = False
                    st.rerun()

        st.markdown("---")

        if st.button("💡 Hydration Tip"):
            st.info(random.choice(HYDRATION_TIPS))

        st.markdown("---")
        st.session_state.dark_mode = st.checkbox(
            "🌙 Dark Mode", value=st.session_state.dark_mode
        )
        apply_dark_mode()

    # ---------- HEADER ----------
    st.markdown(
        """
        <h1 style='margin-bottom:0'>💧 WaterBuddy</h1>
        <p style='margin-top:4px;font-size:0.95rem;opacity:0.75'>
        Daily hydration companion with goals, XP, shop and progress insights.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # progress
    goal, total, remaining, percent = compute_progress()
    xp = st.session_state.xp
    level = st.session_state.level
    xp_prev = (level - 1) * XP_PER_LEVEL
    xp_next = level * XP_PER_LEVEL
    xp_into_level = xp - xp_prev
    xp_progress = xp_into_level / XP_PER_LEVEL if XP_PER_LEVEL else 0.0

    top0, top1, top2, top3, top4 = st.columns(5)
    top0.metric("Level", level)
    top1.metric("Daily Goal", f"{goal} ml")
    top2.metric("Drank Today", f"{total} ml")
    top3.metric("Remaining", f"{remaining} ml")
    top4.metric("Progress", f"{percent:.1f} %")

    st.progress(min(1.0, percent / 100.0))

    st.markdown("##### XP Progress")
    st.progress(min(1.0, xp_progress))
    st.caption(
        f"XP: {xp} | Level {level} | {xp_into_level} / {XP_PER_LEVEL} XP to next level"
    )

    # ---------- MASCOT + STATUS ----------
    col_mascot, col_msg = st.columns([1.2, 2])

    with col_mascot:
        img = draw_turtle_image(percent)
        st.image(img, caption="Your Water Turtle", use_column_width=False)
        st.caption(f"Pose: {mascot_state(percent)}")

    with col_msg:
        st.markdown("##### Status")
        st.info(motivational_message(percent))

    st.markdown("---")

    # ---------- LOG WATER ----------
    st.markdown("### Log Water")

    c_fast, c_custom = st.columns([2, 1])

    with c_fast:
        st.markdown("**Quick add**")
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("+100 ml"):
            add_water(100)
            st.rerun()
        if b2.button("+250 ml"):
            add_water(250)
            st.rerun()
        if b3.button("+500 ml"):
            add_water(500)
            st.rerun()
        if b4.button("+1 L"):
            add_water(1000)
            st.rerun()

    with c_custom:
        st.markdown("**Custom amount**")
        custom_amt = st.number_input(
            "Amount (ml)", min_value=1, step=50, value=150, label_visibility="collapsed"
        )
        if st.button("Add Custom"):
            add_water(int(custom_amt))
            st.rerun()

    if st.session_state.last_xp_gain > 0:
        st.caption(f"⭐ You earned +{st.session_state.last_xp_gain} XP for that drink!")

    st.markdown("---")

    # ---------- XP SHOP ----------
    st.markdown("### 🛒 XP Shop – Style Your Turtle")

    def shop_item(col, key, label, cost, description):
        owned = getattr(st.session_state, key)
        xp = st.session_state.xp
        with col:
            st.markdown(f"**{label}**")
            st.caption(description)
            if owned:
                st.button("Owned", key=f"{key}_owned", disabled=True)
            else:
                if st.button(f"Buy ({cost} XP)", key=f"buy_{key}"):
                    if xp >= cost:
                        st.session_state.xp -= cost
                        setattr(st.session_state, key, True)
                        save_profile()
                        st.success(f"Bought {label}!")
                        st.rerun()
                    else:
                        st.error("Not enough XP")

    s1, s2, s3, s4 = st.columns(4)
    shop_item(s1, "has_bandana", "Bandana", 150, "Give your turtle a red bandana.")
    shop_item(s2, "has_sunglasses", "Sunglasses", 200, "Cool shades for sunny days.")
    shop_item(s3, "has_crown", "Crown", 400, "Royal turtle energy.")
    shop_item(
        s4,
        "has_party_shell",
        "Party Shell",
        600,
        "Colorful shell pattern for celebrations.",
    )

    st.markdown("---")

    # ---------- HISTORY + ANALYTICS ----------
    history = load_history()
    streak, best_date, best_intake, completion_rate, total_days, total_litres = \
        compute_history_stats(history)

    st.markdown("### 📊 History & Insights")

    stats1, stats2, stats3 = st.columns(3)
    stats1.metric("Active Days Logged", total_days)
    stats2.metric("Current Streak (days)", streak)
    stats3.metric("Days Goal Met", f"{completion_rate:.1f} %")

    if best_date:
        st.caption(
            f"Best day: **{best_date}** with **{best_intake} ml**. "
            f"Total water recorded: **{total_litres:.2f} L**."
        )
    else:
        st.caption("Start logging to unlock streaks and stats.")

    with st.expander("📅 View Hydration History (Chart & Table)", expanded=False):
        if not history:
            st.write("No history yet. Drink some water and it will be saved automatically.")
        else:
            rows = [
                {"date": d, "intake_ml": t, "goal_ml": g}
                for d, (t, g) in sorted(history.items())
            ]
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])

            st.markdown("#### Trend")
            chart_df = df.set_index("date")[["intake_ml", "goal_ml"]]
            st.line_chart(chart_df)

            st.markdown("#### Raw data")
            st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)

            st.caption(
                f"History stored in `{DATA_FILE}` and XP profile in `{PROFILE_FILE}` "
                f"(simple local text files, no cloud database)."
            )


if __name__ == "__main__":
    main()
