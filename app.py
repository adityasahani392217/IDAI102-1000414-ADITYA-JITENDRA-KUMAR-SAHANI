import streamlit as st
import datetime
import os
import random
import pandas as pd

# ===================== CONFIG / CONSTANTS =====================

AGE_GUIDELINES = {
    "Child (4-8)": 1200,
    "Teen (9-13)": 1700,
    "Adult (14-64)": 2200,   # middle of 2000–2500
    "Senior (65+)": 1800     # middle of 1700–2000
}

HYDRATION_TIPS = [
    "Drink a glass of water after you wake up.",
    "Sip water regularly instead of chugging.",
    "Keep a water bottle near your study or work desk.",
    "Drink one glass of water with every meal.",
    "Thirst is a late sign — drink before you feel thirsty.",
    "Water helps with focus, mood, and energy.",
    "Add lemon or cucumber slices for taste.",
    "Eat water-rich foods like watermelon and cucumber."
]

DATA_FILE = "water_log.txt"   # simple text-file history


# ===================== STATE INIT / FILE I/O =====================

def init_state():
    if "age_group" not in st.session_state:
        st.session_state.age_group = "Adult (14-64)"
    if "goal_ml" not in st.session_state:
        st.session_state.goal_ml = AGE_GUIDELINES[st.session_state.age_group]
    if "total_ml" not in st.session_state:
        st.session_state.total_ml = 0
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "_ask_reset" not in st.session_state:
        st.session_state._ask_reset = False


def load_today_from_file():
    """Restore today's total + goal from DATA_FILE, if present."""
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
                    total = int(total_str)
                    goal = int(goal_str)
                    st.session_state.total_ml = total
                    if goal > 0:
                        st.session_state.goal_ml = goal
                except ValueError:
                    pass


def save_today_to_file():
    """
    Store daily total + goal to DATA_FILE.
    Format per line: YYYY-MM-DD,total,goal
    """
    today = datetime.date.today().isoformat()
    history = {}

    # read existing
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) != 3:
                    continue
                d, total_str, goal_str = parts
                try:
                    history[d] = (int(total_str), int(goal_str))
                except ValueError:
                    continue

    # update today's
    history[today] = (st.session_state.total_ml, st.session_state.goal_ml)

    # write back
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for d, (t, g) in sorted(history.items()):
            f.write(f"{d},{t},{g}\n")


def load_history():
    """Return dict: date_str -> (total, goal)."""
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
            d, total_str, goal_str = parts
            try:
                history[d] = (int(total_str), int(goal_str))
            except ValueError:
                continue
    return history


# ===================== CORE LOGIC =====================

def recalc_goal_from_age():
    """Set goal from selected age group."""
    st.session_state.goal_ml = AGE_GUIDELINES.get(
        st.session_state.age_group,
        st.session_state.goal_ml
    )


def set_manual_goal(new_goal_str: str):
    """Set manual goal from text input."""
    try:
        val = int(new_goal_str)
        if val <= 0:
            raise ValueError
        st.session_state.goal_ml = val
        save_today_to_file()
        st.success(f"Daily goal set to {val} ml")
    except ValueError:
        st.error("Enter a positive integer for goal (ml).")


def add_water(amount: int):
    """Add water, update file."""
    if amount <= 0:
        return
    st.session_state.total_ml += amount
    save_today_to_file()


def reset_day():
    """Reset today’s progress but keep history file."""
    st.session_state.total_ml = 0
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
    """
    Replace Turtle mascot with simple emoji + description
    (Neutral / Smile / Wave / Celebrate).
    """
    if percent < 50:
        return "😐", "Mascot: Neutral (keep going!)"
    elif percent < 75:
        return "😊", "Mascot: Smiling (good progress!)"
    elif percent < 100:
        return "👋😄", "Mascot: Waving (almost there!)"
    else:
        return "🎉😄", "Mascot: Celebrating (goal reached!)"


def compute_history_stats(history: dict):
    """
    history: {date_str: (intake, goal)}
    Returns: streak_days, best_date, best_intake, completion_rate, total_days, total_litres
    """
    if not history:
        return 0, None, 0, 0.0, 0, 0.0

    # sort dates ascending
    dates = sorted(history.keys())
    total_days = len(dates)

    # completion info
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

    # streak: consecutive days with goal met up to the most recent date
    streak = 0
    # Walk backwards from latest date
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


# ===================== DARK MODE (CSS) =====================

def apply_dark_mode():
    if st.session_state.dark_mode:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #0f172a;
                color: #f9fafb;
            }
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            </style>
            """,
            unsafe_allow_html=True
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
            unsafe_allow_html=True
        )


# ===================== MAIN APP =====================

def main():
    st.set_page_config(page_title="WaterBuddy", page_icon="💧", layout="wide")
    init_state()

    if not st.session_state.data_loaded:
        load_today_from_file()
        st.session_state.data_loaded = True

    apply_dark_mode()

    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        # Feature 1: Goal Selection (Age group + manual)
        st.markdown("#### Age Group")
        new_age = st.selectbox(
            "Select Age Group",
            list(AGE_GUIDELINES.keys()),
            index=list(AGE_GUIDELINES.keys()).index(st.session_state.age_group),
            label_visibility="collapsed"
        )
        if new_age != st.session_state.age_group:
            st.session_state.age_group = new_age
            recalc_goal_from_age()
            save_today_to_file()
            st.experimental_rerun()

        st.markdown("#### Daily Goal (ml)")
        goal_input = st.text_input(
            "Manual goal (ml)",
            value=str(st.session_state.goal_ml),
            label_visibility="collapsed"
        )
        if st.button("Set Goal"):
            set_manual_goal(goal_input)

        st.markdown("---")

        # Feature 5: Reset function (with confirmation)
        if st.button("🗓️ New Day / Reset"):
            st.session_state._ask_reset = True

        if st.session_state._ask_reset:
            st.warning("Reset today's progress?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes"):
                    reset_day()
                    st.session_state._ask_reset = False
                    st.experimental_rerun()
            with c2:
                if st.button("❌ No"):
                    st.session_state._ask_reset = False
                    st.experimental_rerun()

        st.markdown("---")

        # Hydration tip
        if st.button("💡 Hydration Tip"):
            st.info(random.choice(HYDRATION_TIPS))

        # Dark mode toggle
        st.markdown("---")
        st.session_state.dark_mode = st.checkbox(
            "🌙 Dark Mode", value=st.session_state.dark_mode
        )
        apply_dark_mode()

    # ---------- MAIN LAYOUT ----------
    # Header
    st.markdown(
        """
        <h1 style='margin-bottom:0'>💧 WaterBuddy</h1>
        <p style='margin-top:4px;font-size:0.95rem;opacity:0.75'>
        Daily hydration companion with goals, history & progress insights.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Progress calculations
    goal, total, remaining, percent = compute_progress()

    # Top stats row
    top1, top2, top3, top4 = st.columns(4)
    top1.metric("Daily Goal", f"{goal} ml")
    top2.metric("Drank Today", f"{total} ml")
    top3.metric("Remaining", f"{remaining} ml")
    top4.metric("Progress", f"{percent:.1f} %")

    st.progress(min(1.0, percent / 100.0))

    # Mascot + message row
    col_mascot, col_msg = st.columns([1, 2])
    with col_mascot:
        emoji, mascot_text = mascot_state(percent)
        st.markdown(f"### {emoji}")
        st.caption(mascot_text)

    with col_msg:
        st.markdown("##### Status")
        st.info(motivational_message(percent))

    st.markdown("---")

    # ---------- LOGGING CONTROLS ----------
    st.markdown("### Log Water")

    c_fast, c_custom = st.columns([2, 1])

    with c_fast:
        st.markdown("**Quick add**")
        b1, b2, b3, b4 = st.columns(4)
        if b1.button("+100 ml"):
            add_water(100)
            st.experimental_rerun()
        if b2.button("+250 ml"):
            add_water(250)
            st.experimental_rerun()
        if b3.button("+500 ml"):
            add_water(500)
            st.experimental_rerun()
        if b4.button("+1 L"):
            add_water(1000)
            st.experimental_rerun()

    with c_custom:
        st.markdown("**Custom amount**")
        custom_amt = st.number_input(
            "Amount (ml)", min_value=1, step=50, value=150, label_visibility="collapsed"
        )
        if st.button("Add Custom"):
            add_water(int(custom_amt))
            st.experimental_rerun()

    st.markdown("---")

    # ---------- HISTORY & ANALYTICS ----------
    history = load_history()
    streak_days, best_date, best_intake, completion_rate, total_days, total_litres = (
        compute_history_stats(history)
    )

    st.markdown("### 📊 History & Insights")

    stats1, stats2, stats3 = st.columns(3)
    stats1.metric("Active Days Logged", total_days)
    stats2.metric("Current Streak (days)", streak_days)
    stats3.metric("Days Goal Met", f"{completion_rate:.1f} %")

    if best_date:
        st.caption(
            f"Best day: **{best_date}** with **{best_intake} ml**. "
            f"Total water recorded: **{total_litres:.2f} L**"
        )
    else:
        st.caption("Start logging to unlock streaks and stats.")

    # Graph + table
    with st.expander("📅 View Hydration History (Chart & Table)", expanded=False):
        if not history:
            st.write("No history yet. Drink some water and it will be saved automatically.")
        else:
            # Build DataFrame
            rows = []
            for d, (t, g) in sorted(history.items()):
                rows.append({"date": d, "intake_ml": t, "goal_ml": g})
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])

            st.markdown("#### Trend")
            chart_df = df.set_index("date")[["intake_ml", "goal_ml"]]
            st.line_chart(chart_df)

            st.markdown("#### Raw data")
            st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)

            st.caption(
                f"History is stored locally in `{DATA_FILE}` (simple text file, no login or cloud DB)."
            )


if __name__ == "__main__":
    main()
