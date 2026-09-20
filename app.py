import streamlit as st
import pandas as pd
import numpy as np
from backend.api import AnalyticalBackend, keys, estimate_degradation

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TwinAero-X | Digital Twin Engine Monitor",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Professional CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Force light background + dark text everywhere */
    .stApp, .main, [data-testid="stAppViewContainer"] {
        background-color: #f8f9fa !important;
        color: #1a1a2e !important;
    }
    
    /* Force ALL text dark */
    .stApp p, .stApp span, .stApp label, .stApp div,
    .stMarkdown, .stMarkdown p, .stMarkdown span,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stCaptionContainer"],
    .stCaption, .stCaption p {
        color: #1a1a2e !important;
    }
    
    /* Sidebar: white bg + dark text & lock always open at 320px width */
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e5e7eb;
        min-width: 320px !important;
        width: 320px !important;
    }
    section[data-testid="stSidebar"] > div {
        background: #ffffff !important;
        width: 100% !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #1a1a2e !important;
    }
    section[data-testid="stSidebar"] .stCaption p,
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: #6b7280 !important;
    }
    
    /* Hide Streamlit collapse buttons so sidebar cannot be hidden */
    button[data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Metric cards */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e0e4e8;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    div[data-testid="stMetric"] label {
        color: #6b7280 !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1a1a2e !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #6b7280 !important;
    }
    
    /* Status pill classes */
    .status-pill {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
    }
    .pill-green { background: #d1fae5; color: #065f46 !important; }
    .pill-red { background: #fee2e2; color: #991b1b !important; }
    .pill-amber { background: #fef3c7; color: #92400e !important; }
    
    /* Section headers */
    .section-header {
        font-size: 0.8rem;
        font-weight: 700;
        color: #6b7280 !important;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 2px solid #e5e7eb;
    }
    
    /* Hero banner */
    .hero-banner {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 24px 32px;
        border-radius: 16px;
        margin-bottom: 20px;
    }
    .hero-banner h1 {
        margin: 0; font-size: 1.8rem; font-weight: 800;
        letter-spacing: -0.02em; color: #ffffff !important;
    }
    .hero-banner p {
        margin: 6px 0 0 0; font-size: 0.9rem;
        color: #94a3b8 !important; font-weight: 400;
    }
    
    /* Pipeline breadcrumb */
    .pipeline-bar {
        background: #ffffff;
        border: 1px solid #e0e4e8;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 20px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 3px;
        font-size: 0.72rem;
    }
    .pipeline-step {
        background: #f1f5f9;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: 600;
        color: #94a3b8 !important;
        white-space: nowrap;
    }
    .pipeline-step.active {
        background: #1a1a2e;
        color: #ffffff !important;
    }
    .pipeline-arrow { color: #cbd5e1 !important; margin: 0 1px; }
    
    /* Risk cards */
    .risk-card {
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .risk-card-green { background: #ecfdf5; border: 1px solid #a7f3d0; }
    .risk-card-red { background: #fef2f2; border: 1px solid #fecaca; }
    .risk-card-amber { background: #fffbeb; border: 1px solid #fde68a; }
    .risk-card h4 {
        margin: 0 0 4px 0; font-size: 0.72rem;
        color: #6b7280 !important; text-transform: uppercase;
        letter-spacing: 0.06em; font-weight: 600;
    }
    .risk-card .risk-value { font-size: 1.3rem; font-weight: 800; margin: 0; }
    .risk-card-green .risk-value { color: #065f46 !important; }
    .risk-card-red .risk-value { color: #991b1b !important; }
    .risk-card-amber .risk-value { color: #92400e !important; }
    
    /* Evidence table */
    .evidence-table {
        width: 100%; border-collapse: collapse; font-size: 0.85rem;
    }
    .evidence-table td {
        padding: 6px 0; border-bottom: 1px solid #f3f4f6;
        color: #1a1a2e !important;
    }
    .evidence-table td:first-child {
        color: #6b7280 !important; font-weight: 500; width: 45%;
    }
    .evidence-table td:last-child {
        color: #1a1a2e !important; font-weight: 600; text-align: right;
    }
    
    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.85rem;
        border: 1px solid #e0e4e8;
        background: #f8f9fa;
        color: #1a1a2e !important;
        transition: all 0.15s;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        /* Fix for black-on-black text contrast on hover:
           Using a light gray background with black text instead of black background. */
        background: #e2e8f0;
        color: #1a1a2e !important;
        border-color: #cbd5e1;
    }
    
    /* Description text helper */
    .desc-text {
        color: #6b7280 !important;
        font-size: 0.85rem;
        line-height: 1.5;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Session State ───────────────────────────────────────────────────────────
if "api" not in st.session_state:
    st.session_state.api = AnalyticalBackend()
    st.session_state.env = {"throttle": 80, "load": 50, "altitude": 1000, "ambient_temp": 25, "injection_timing": 0}
    st.session_state.mission_results = None

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ✈️ TwinAero-X")
    st.caption("SIH Problem Statement 26054")
    st.markdown("---")
    
    st.markdown('<p class="section-header">Demo Controls</p>', unsafe_allow_html=True)
    
    if st.button("▶  Start Healthy Engine", use_container_width=True):
        st.session_state.api = AnalyticalBackend()
        st.session_state.mission_results = None
        for _ in range(25):
            st.session_state.api.step(1.0, st.session_state.env, st.session_state.api.twin.healthy_engine.step(1.0, st.session_state.env, {}))
        st.rerun()
    
    st.markdown("")
    st.markdown('<p class="section-header">Inject Fault</p>', unsafe_allow_html=True)
    
    fault_map = {
        "🔥  Overheating": "overheating",
        "🛢️  Lubrication Degradation": "lubrication",
        "📳  Vibration Fault": "vibration",
        "⚙️  Injector Fault": "injector"
    }
    for btn, fault in fault_map.items():
        if st.button(btn, use_container_width=True):
            from backend.simulator.wear_simulator import WearSimulator
            sim = WearSimulator(seed=42)
            sim.time = st.session_state.api.current_time
            sim.set_wear(fault, 0.8)
            for _ in range(15):
                res = sim.step(1.0, st.session_state.env)
                st.session_state.api.step(1.0, st.session_state.env, res["observed"], res["true_state"])
            st.session_state.mission_results = None
            st.rerun()

    st.markdown("")
    st.markdown('<p class="section-header">Mission Simulation</p>', unsafe_allow_html=True)
    
    missions = {
        "Conservative": [
            {"T": 20, "e": {"throttle": 85, "load": 50, "altitude": 0, "ambient_temp": 25, "injection_timing": 0}},
            {"T": 50, "e": {"throttle": 60, "load": 40, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}
        ],
        "Nominal": [
            {"T": 20, "e": {"throttle": 85, "load": 50, "altitude": 0, "ambient_temp": 25, "injection_timing": 0}},
            {"T": 50, "e": {"throttle": 75, "load": 50, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}
        ],
        "Aggressive": [
            {"T": 20, "e": {"throttle": 100, "load": 80, "altitude": 0, "ambient_temp": 25, "injection_timing": 0}},
            {"T": 50, "e": {"throttle": 95, "load": 80, "altitude": 2000, "ambient_temp": 15, "injection_timing": 0}}
        ]
    }
    
    mission_choice = st.selectbox("Mission Profile", list(missions.keys()), index=1)
    if st.button("🚀  Simulate Future Risk", use_container_width=True):
        diag = st.session_state.api.get_diagnostic_status()
        f = diag["fault"].lower() if diag["fault"] != "NORMAL" else "normal"
        try:
            risk_str, m, f_t, _ = st.session_state.api.simulate_mission(missions[mission_choice], f)
            adv = st.session_state.api.get_advisory(missions[mission_choice], f)
            st.session_state.mission_results = {"risk": risk_str, "margin": m, "f_t": f_t, "adv": adv, "profile": mission_choice}
        except Exception as e:
            st.session_state.mission_results = {"error": str(e)}
        st.rerun()

    st.markdown("")
    st.markdown("---")
    if st.button("🔄  Reset Demo", use_container_width=True):
        st.session_state.api = AnalyticalBackend()
        st.session_state.mission_results = None
        st.rerun()
    
    st.markdown("")
    debug_mode = st.checkbox("Developer Debug Mode", value=False)

# ─── Hero Banner ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <h1>✈️ TwinAero-X</h1>
    <p>Physics-Informed Digital Twin for Predictive Health Monitoring of MALE UAV Aero-Piston Engines</p>
</div>
""", unsafe_allow_html=True)

# ─── Pipeline Breadcrumb ────────────────────────────────────────────────────
api = st.session_state.api
diag = api.get_diagnostic_status() if api.current_time > 0 else None

if api.current_time == 0:
    active_step = 0
elif diag and diag["anomaly"] == "YES" and diag.get("confirmed"):
    if st.session_state.mission_results and "error" not in st.session_state.mission_results:
        active_step = 8
    else:
        active_step = 5
elif diag and diag["anomaly"] == "YES":
    active_step = 3
else:
    active_step = 1

steps = ["Telemetry", "Digital Twin", "Residuals", "Anomaly", "Confirmation", "Diagnosis", "Degradation", "RUL", "Mission Risk"]
step_html = ""
for i, s in enumerate(steps):
    cls = "pipeline-step active" if i <= active_step else "pipeline-step"
    step_html += f'<span class="{cls}">{s}</span>'
    if i < len(steps) - 1:
        step_html += '<span class="pipeline-arrow">→</span>'
st.markdown(f'<div class="pipeline-bar">{step_html}</div>', unsafe_allow_html=True)

# ─── Uninitialized State ────────────────────────────────────────────────────
if api.current_time == 0:
    st.markdown("")
    _, col_empty_c, _ = st.columns([1, 2, 1])
    with col_empty_c:
        st.markdown("""
        <div style="text-align:center; padding:60px 0;">
            <p style="font-size:3rem; margin-bottom:8px;">✈️</p>
            <h3 style="color:#1a1a2e !important; margin-bottom:8px;">Ready to Monitor</h3>
            <p style="color:#6b7280 !important; font-size:0.95rem;">Click <b>▶ Start Healthy Engine</b> in the sidebar to begin ingesting telemetry.</p>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ─── Get All Data ────────────────────────────────────────────────────────────
hi = api.get_health_index()
f_type = diag["fault"].lower() if diag["fault"] != "NORMAL" else "normal"
z_scores = api.get_z_scores()
proxy_val = api.get_degradation_proxy(f_type)

# ─── Top Status Cards ───────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    if diag["fault"] == "NORMAL":
        status_text = "NOMINAL"
    elif diag.get("confirmed"):
        status_text = "FAULT DETECTED"
    else:
        status_text = "ANALYZING..."
    st.metric("Engine Status", status_text)

with c2:
    st.metric("Health Index", f"{hi:.1f}")

with c3:
    fault_display = diag["fault"] if diag["fault"] != "NORMAL" else "—"
    st.metric("Fault", fault_display)

with c4:
    rul = api.get_rul_estimate(f_type, st.session_state.env) if f_type not in ["normal", "injector"] else None
    rul_str = f"{rul:.0f}s" if rul is not None else "—"
    st.metric("Prototype RUL", rul_str)

with c5:
    if st.session_state.mission_results and "error" not in st.session_state.mission_results:
        risk_str = st.session_state.mission_results["risk"]
        c_risk = risk_str.split("|")[0].split(":")[1].strip() if "|" in risk_str else "—"
    else:
        c_risk = "—"
    st.metric("Current Risk", c_risk)

st.markdown("")

# ─── Main Content: 3 Columns ────────────────────────────────────────────────
col_twin, col_diag, col_risk = st.columns([2.2, 1.4, 1.4])

# ── Column 1: Digital Twin vs Telemetry ──────────────────────────────────────
with col_twin:
    st.markdown('<p class="section-header">Digital Twin vs Actual Telemetry</p>', unsafe_allow_html=True)
    st.markdown('<p class="desc-text">The Digital Twin calculates what each sensor <b>should</b> read. The gap between expected and actual is the <b>residual</b> — the signal our AI analyzes.</p>', unsafe_allow_html=True)
    
    friendly_names = {
        'cht': 'Cylinder Head Temp (Avg)', 'oil_temp': 'Oil Temp',
        'vibration': 'Vibration', 'rpm': 'RPM', 'fuel_flow': 'Fuel Flow',
        'egt': 'Exhaust Gas Temp (Avg)', 'oil_pressure': 'Oil Pressure',
        'map': 'Manifold Abs. Pressure (MAP)', 'knock_index': 'Detonation / Knock Index',
        'cht1': 'Cylinder 1 CHT', 'cht2': 'Cylinder 2 CHT', 'cht3': 'Cylinder 3 CHT', 'cht4': 'Cylinder 4 CHT',
        'egt1': 'Cylinder 1 EGT', 'egt2': 'Cylinder 2 EGT', 'egt3': 'Cylinder 3 EGT', 'egt4': 'Cylinder 4 EGT'
    }
    telemetry_key = st.selectbox("Sensor", list(friendly_names.keys()), format_func=lambda x: friendly_names[x], label_visibility="collapsed")
    
    df_chart = pd.DataFrame()
    df_chart["Time Step"] = range(len(api.obs_history))
    df_chart["Actual"] = [obs.get(telemetry_key, 0.0) for obs in api.obs_history]
    df_chart["Twin Expected"] = [obs.get(telemetry_key, 0.0) - res.get(f"res_{telemetry_key}", 0.0) for obs, res in zip(api.obs_history, api.res_history)]
    
    st.line_chart(df_chart.set_index("Time Step"), use_container_width=True)
    
    # Residual summary
    last_res_val = api.res_history[-1].get(f"res_{telemetry_key}", 0.0) if api.res_history else 0
    z_val = z_scores.get(telemetry_key, 0.0)
    
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        st.metric("Actual", f"{api.obs_history[-1].get(telemetry_key, 0.0):.1f}")
    with rc2:
        exp_val = api.obs_history[-1].get(telemetry_key, 0.0) - last_res_val
        st.metric("Expected", f"{exp_val:.1f}")
    with rc3:
        st.metric("Residual", f"{last_res_val:.2f}", delta=f"Z = {z_val:.1f}")
        
    # Multi-Cylinder & Aero Engine Domain Panel
    st.markdown("")
    st.markdown('<p class="section-header">Aero Engine Domain Fidelity (Rotax 914/915 Specs)</p>', unsafe_allow_html=True)
    
    mc1, mc2, mc3 = st.columns(3)
    last_obs = api.obs_history[-1] if api.obs_history else {}
    c1_v = last_obs.get("cht1", 0.0)
    c2_v = last_obs.get("cht2", 0.0)
    c3_v = last_obs.get("cht3", 0.0)
    c4_v = last_obs.get("cht4", 0.0)
    spread = max(c1_v, c2_v, c3_v, c4_v) - min(c1_v, c2_v, c3_v, c4_v)
    
    with mc1:
        st.metric("4-Cyl CHT Spread", f"{spread:.1f}°C", delta="Misfire Warning" if spread > 35 else "Nominal")
    with mc2:
        map_val = last_obs.get("map", 29.92)
        st.metric("Manifold Pressure", f"{map_val:.1f} inHg", delta="Boost Active" if map_val > 30.0 else "Sea Level")
    with mc3:
        knock_v = last_obs.get("knock_index", 0.0)
        st.metric("Knock / Detonation", f"{knock_v:.1f}%", delta="DETONATION!" if knock_v > 30 else "Safe")
        
    df_cyl = pd.DataFrame({
        "Cylinder": ["Cyl 1", "Cyl 2", "Cyl 3", "Cyl 4"],
        "CHT (°C)": [c1_v, c2_v, c3_v, c4_v],
        "EGT (°C)": [last_obs.get("egt1", 0), last_obs.get("egt2", 0), last_obs.get("egt3", 0), last_obs.get("egt4", 0)]
    })
    st.bar_chart(df_cyl.set_index("Cylinder"))

# ── Column 2: Diagnostic Pipeline ───────────────────────────────────────────
with col_diag:
    st.markdown('<p class="section-header">AI Diagnostic Pipeline</p>', unsafe_allow_html=True)
    
    if diag["anomaly"] == "YES" and diag.get("confirmed"):
        st.markdown(f'<span class="status-pill pill-red">⚠ CONFIRMED FAULT</span>', unsafe_allow_html=True)
        st.markdown("")
        
        st.markdown(f"""
        <table class="evidence-table">
            <tr><td>Fault Type</td><td><b>{diag['fault']}</b></td></tr>
            <tr><td>AI Confidence</td><td>{diag.get('model_probability', 0)*100:.0f}%</td></tr>
            <tr><td>3-Sample Confirmed</td><td>✅ Yes</td></tr>
        </table>
        """, unsafe_allow_html=True)
        
        ev = diag.get("evidence", {})
        if ev:
            st.markdown("")
            st.markdown('<p class="section-header" style="font-size:0.7rem;">Primary Evidence</p>', unsafe_allow_html=True)
            z_ev = z_scores.get(ev['key'], 0.0)
            st.markdown(f"""
            <table class="evidence-table">
                <tr><td>Key Sensor</td><td><code>{friendly_names.get(ev['key'], ev['key'])}</code></td></tr>
                <tr><td>Actual</td><td>{ev['observed']:.1f}</td></tr>
                <tr><td>Expected</td><td>{ev['expected']:.1f}</td></tr>
                <tr><td>Residual</td><td>{ev['residual']:.1f}</td></tr>
                <tr><td>Z-Score</td><td><b>{z_ev:.1f}</b></td></tr>
            </table>
            """, unsafe_allow_html=True)
        
        # Degradation + RUL
        st.markdown("")
        st.markdown('<p class="section-header" style="font-size:0.7rem;">Degradation & RUL</p>', unsafe_allow_html=True)
        
        if f_type not in ["normal", "injector"]:
            st.markdown(f"""
            <table class="evidence-table">
                <tr><td>Degradation Proxy</td><td><b>{proxy_val:.3f}</b></td></tr>
                <tr><td>Prototype RUL</td><td><b>{rul_str}</b></td></tr>
            </table>
            """, unsafe_allow_html=True)
            st.markdown('<p class="desc-text" style="font-size:0.75rem; margin-top:8px;">Prototype forecast on simulated trajectories.</p>', unsafe_allow_html=True)
        elif f_type == "injector":
            st.markdown(f"""
            <table class="evidence-table">
                <tr><td>Degradation Proxy</td><td>0.00</td></tr>
                <tr><td>Prototype RUL</td><td><i>Unavailable for this fault</i></td></tr>
            </table>
            """, unsafe_allow_html=True)
    
    elif diag["anomaly"] == "YES":
        st.markdown(f'<span class="status-pill pill-amber">⏳ ANOMALY DETECTED</span>', unsafe_allow_html=True)
        st.markdown("")
        st.markdown('<p class="desc-text">Awaiting 3-sample temporal confirmation to suppress transient false alarms.</p>', unsafe_allow_html=True)
    
    else:
        st.markdown(f'<span class="status-pill pill-green">✓ ALL SYSTEMS NOMINAL</span>', unsafe_allow_html=True)
        st.markdown("")
        st.markdown('<p class="desc-text">Telemetry aligns with Digital Twin expectations. No anomaly detected.</p>', unsafe_allow_html=True)

# ── Column 3: Mission Risk ──────────────────────────────────────────────────
with col_risk:
    st.markdown('<p class="section-header">Mission Risk Assessment</p>', unsafe_allow_html=True)
    
    if st.session_state.mission_results:
        m_res = st.session_state.mission_results
        if "error" in m_res:
            st.error(f"Simulation failed: {m_res['error']}")
        else:
            risk_str = m_res["risk"]
            c_risk_full = risk_str.split("|")[0].strip() if "|" in risk_str else risk_str
            f_risk_full = risk_str.split("|")[1].strip() if "|" in risk_str else ""
            c_label = c_risk_full.replace("Current Risk:", "").strip()
            f_label = f_risk_full.replace("Future Mission Risk:", "").strip()
            
            # Current Condition card
            c_cls = "risk-card-red" if c_label == "RED" else ("risk-card-amber" if c_label == "AMBER" else "risk-card-green")
            c_icon = '🔴' if c_label == 'RED' else ('🟡' if c_label == 'AMBER' else '🟢')
            st.markdown(f"""
            <div class="risk-card {c_cls}">
                <h4>Current Engine Condition</h4>
                <p class="risk-value">{c_icon} {c_label}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Future Mission card
            f_cls = "risk-card-red" if f_label == "RED" else ("risk-card-amber" if f_label == "AMBER" else "risk-card-green")
            f_icon = '🔴' if f_label == 'RED' else ('🟡' if f_label == 'AMBER' else '🟢')
            st.markdown(f"""
            <div class="risk-card {f_cls}">
                <h4>Future Mission — {m_res.get('profile', 'Nominal')}</h4>
                <p class="risk-value">{f_icon} {f_label}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <table class="evidence-table">
                <tr><td>Mission Profile</td><td>{m_res.get('profile', '—')}</td></tr>
                <tr><td>Future Min. Margin</td><td>{m_res['margin']:.2f}</td></tr>
            </table>
            """, unsafe_allow_html=True)
            
            st.markdown("")
            adv_text = m_res["adv"]
            if "RED" in adv_text or c_label == "RED":
                st.error(f"**{adv_text}**")
            else:
                st.success(f"**{adv_text}**")
    else:
        st.markdown("""
        <div style="text-align:center; padding:40px 0;">
            <p style="font-size:2rem; margin-bottom:4px;">🚀</p>
            <p class="desc-text" style="text-align:center;">Select a mission profile and click<br/><b>"Simulate Future Risk"</b> in the sidebar.</p>
        </div>
        """, unsafe_allow_html=True)

# ─── Debug Mode ──────────────────────────────────────────────────────────────
if debug_mode:
    st.markdown("---")
    st.warning("⚠️ **Developer Debug Mode** — Not for presentation")
    dc1, dc2 = st.columns(2)
    with dc1:
        st.json(api.obs_history[-1] if api.obs_history else {})
    with dc2:
        st.json(api.get_current_engine_state(debug=True) or {})
