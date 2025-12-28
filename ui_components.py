import streamlit as st

def custom_bar(label, current, maximum, color):
    """
    Recreates the compact bar widget used in the sidebar.
    """
    # guard division by zero
    percent = min(100, max(0, (current / (maximum or 1)) * 100))
    st.markdown(
        f"<div style='display:flex;justify-content:space-between;font-size:0.7rem;font-weight:bold;margin-bottom:2px;'><span>{label}</span><span>{int(current)}/{maximum}</span></div>"
        f"<div class='bar-container'><div class='bar-fill' style='width:{percent}%; background:{color};'></div></div>",
        unsafe_allow_html=True
    )

def render_condition_badge(condition, cond_data, timer=0):
    """
    Render a condition badge exactly like the original inline markup.
    """
    badge_class = "buff-badge" if cond_data.get('type') == "buff" else "debuff-badge-red"
    timer_info = f" ({timer} turns)" if timer else ""
    severity = cond_data.get("severity", 1)
    severity_text = "★" * severity
    st.markdown(f"<span class='debuff-badge {badge_class}'>{condition}{timer_info} {severity_text}</span>", unsafe_allow_html=True)
