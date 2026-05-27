import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st

st.set_page_config(
    page_title="Nassau Candy — Profitability Dashboard",
    page_icon="🍬", layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* ── Sidebar ─────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] { background:#1a1a2e; border-right:1px solid #2d2d4e; }
section[data-testid="stSidebar"] * { color:#ffffff !important; }
section[data-testid="stSidebar"] [data-baseweb="select"] { background:#2d2d4e !important; border-radius:6px; }
section[data-testid="stSidebar"] [data-baseweb="select"] > div { background:#2d2d4e !important; border-color:#3d3d6e !important; }
section[data-testid="stSidebar"] [data-baseweb="input"] { background:#2d2d4e !important; border-color:#3d3d6e !important; }
section[data-testid="stSidebar"] input { background:#2d2d4e !important; color:#ffffff !important; }
section[data-testid="stSidebar"] [data-baseweb="select"] p { color:#ffffff !important; font-weight:600 !important; }
section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label {
    font-size:0.72rem !important; color:#ffffff !important;
    letter-spacing:0.01em; text-transform:none !important;
}

/* ── Expander — border, radius, overflow clipped so scrollbar stays inside ── */
section[data-testid="stSidebar"] div[data-testid="stExpander"] {
    border:1px solid #3d3d6e !important;
    border-radius:6px !important;
    overflow: hidden !important;
}

/* ── Scrollbar — always visible, clipped inside expander ─────────────── */
section[data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stVerticalBlockBorderWrapper"] > div {
    overflow-y: scroll !important;
    scrollbar-width: thin !important;
    scrollbar-color: #4a4a7a #2d2d4e !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar {
    width: 4px !important;
    display: block !important;
    opacity: 1 !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar-track {
    background: #2d2d4e !important;
    border-radius: 0 0 6px 0 !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar-thumb {
    background: #4a4a7a !important;
    border-radius: 4px !important;
    min-height: 40px !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar-thumb:hover {
    background: #6a6aaa !important;
}

/* ── General sidebar scrollbar (thin, subtle) ────────────────────────── */
section[data-testid="stSidebar"] ::-webkit-scrollbar { width:4px; }
section[data-testid="stSidebar"] ::-webkit-scrollbar-track { background:transparent; }
section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
    background:#4a4a7a;
    border-radius:4px;
}

/* ── Product filter scrollable container — target every plausible selector ── */
/* Streamlit renders st.container(height=N) as a div with overflow:auto inline  */
/* We override with !important on every property and cast a wide selector net.  */
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] > div,
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] div[style*="overflow"],
section[data-testid="stSidebar"] div[style*="overflow: auto"],
section[data-testid="stSidebar"] div[style*="overflow:auto"],
section[data-testid="stSidebar"] div[style*="height: 220"],
section[data-testid="stSidebar"] div[style*="height:220"] {
    scrollbar-width: auto !important;
    scrollbar-color: #b0b0ff #1a1a3e !important;
}

/* webkit — must repeat selectors; pseudo-elements can't share rules */
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar,
section[data-testid="stSidebar"] div[style*="overflow: auto"]::-webkit-scrollbar,
section[data-testid="stSidebar"] div[style*="overflow:auto"]::-webkit-scrollbar,
section[data-testid="stSidebar"] div[style*="height: 220"]::-webkit-scrollbar,
section[data-testid="stSidebar"] div[style*="height:220"]::-webkit-scrollbar {
    width: 12px !important;
    display: block !important;
}
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar-track,
section[data-testid="stSidebar"] div[style*="overflow: auto"]::-webkit-scrollbar-track,
section[data-testid="stSidebar"] div[style*="overflow:auto"]::-webkit-scrollbar-track,
section[data-testid="stSidebar"] div[style*="height: 220"]::-webkit-scrollbar-track,
section[data-testid="stSidebar"] div[style*="height:220"]::-webkit-scrollbar-track {
    background: #1a1a3e !important;
    border-radius: 6px !important;
    border: 1px solid #4a4a8a !important;
}
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar-thumb,
section[data-testid="stSidebar"] div[style*="overflow: auto"]::-webkit-scrollbar-thumb,
section[data-testid="stSidebar"] div[style*="overflow:auto"]::-webkit-scrollbar-thumb,
section[data-testid="stSidebar"] div[style*="height: 220"]::-webkit-scrollbar-thumb,
section[data-testid="stSidebar"] div[style*="height:220"]::-webkit-scrollbar-thumb {
    background: #b0b0ff !important;
    border-radius: 6px !important;
    min-height: 40px !important;
    border: 2px solid #1a1a3e !important;
}
section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar-thumb:hover,
section[data-testid="stSidebar"] div[style*="overflow: auto"]::-webkit-scrollbar-thumb:hover,
section[data-testid="stSidebar"] div[style*="overflow:auto"]::-webkit-scrollbar-thumb:hover,
section[data-testid="stSidebar"] div[style*="height: 220"]::-webkit-scrollbar-thumb:hover,
section[data-testid="stSidebar"] div[style*="height:220"]::-webkit-scrollbar-thumb:hover {
    background: #d0d0ff !important;
}

section[data-testid="stSidebar"] [data-baseweb="tag"] span { color:#ffffff !important; font-weight:600 !important; }
[data-baseweb="popover"] ul { background:#1a1a2e !important; }
[data-baseweb="popover"] ul li { background:#1a1a2e !important; color:#ffffff !important; }
[data-baseweb="popover"] ul li:hover { background:#2d2d4e !important; }
[data-baseweb="menu"] { background:#1a1a2e !important; }
[data-baseweb="menu"] [role="option"] { color:#ffffff !important; background:#1a1a2e !important; }
[data-baseweb="menu"] [role="option"]:hover { background:#2d2d4e !important; }
section[data-testid="stSidebar"] label {
    color:#a0a0c0 !important; font-size:0.72rem;
    letter-spacing:0.08em; text-transform:uppercase;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button,
section[data-testid="stSidebar"] div[data-testid="stButton"] button:focus,
section[data-testid="stSidebar"] div[data-testid="stButton"] button:active {
    background:#2d2d4e !important; color:#ffffff !important;
    border:1px solid #4a4a7a !important; font-size:0.75rem !important;
    padding:2px 8px !important; border-radius:6px !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
    background:#3d3d6e !important; color:#ffffff !important;
    border:1px solid #6a6aaa !important;
}

/* ── Fix: expander header / search box white flash on click ──────────── */
section[data-testid="stSidebar"] div[data-testid="stExpander"] summary {
    background:#1a1a2e !important;
    border-radius:6px !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] summary:hover {
    background:#2d2d4e !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] summary * {
    color:#ffffff !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] details {
    background:#1a1a2e !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] input {
    background:#2d2d4e !important;
    color:#ffffff !important;
    border-color:#3d3d6e !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] input::placeholder {
    color:#a0a0c0 !important;
    opacity:1 !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] input:focus,
section[data-testid="stSidebar"] div[data-testid="stExpander"] input:active,
section[data-testid="stSidebar"] div[data-testid="stExpander"] input:focus-visible {
    background:#2d2d4e !important;
    color:#ffffff !important;
    outline:none !important;
    box-shadow:none !important;
    border-color:#6a6aaa !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] [data-baseweb="input"] {
    background:#2d2d4e !important;
    border-color:#3d3d6e !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] [data-baseweb="input"] > div {
    background:#2d2d4e !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] [data-baseweb="input"]:focus-within {
    background:#2d2d4e !important;
    border-color:#6a6aaa !important;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] div:has(> input) {
    background:#2d2d4e !important;
}

/* ── Equal-height KPI cards via CSS grid on the columns row ──────────── */
div[data-testid="stHorizontalBlock"] {
    align-items: stretch !important;
}
div[data-testid="column"] {
    display: flex;
    flex-direction: column;
}
div[data-testid="column"] > div {
    flex: 1;
    display: flex;
    flex-direction: column;
}
div[data-testid="column"] > div > div[data-testid="stVerticalBlock"] {
    flex: 1;
    display: flex;
    flex-direction: column;
}
div[data-testid="column"] > div > div > div[data-testid="stMarkdownContainer"] {
    flex: 1;
    display: flex;
    flex-direction: column;
}
div[data-testid="column"] > div > div > div[data-testid="stMarkdownContainer"] > div {
    flex: 1;
    display: flex;
    flex-direction: column;
}

/* ── KPI grid — single HTML block, bypasses Streamlit columns ────────── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 10px;
    margin-bottom: 16px;
    align-items: stretch;
}

.kpi-card {
    background: #ffffff;
    border: 1px solid #d8d8e8;
    border-radius: 12px;
    padding: 18px 14px 16px 14px;
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 5px;
    box-sizing: border-box;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent, #6c63ff);
    border-radius: 12px 12px 0 0;
}

.kpi-label {
    font-size: 0.64rem;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    color: #444455;
    font-weight: 700;
    line-height: 1.45;
    white-space: normal;
    overflow-wrap: anywhere;
    word-break: break-word;
    min-height: 2.65em;
    display: flex;
    align-items: flex-start;
}

.kpi-value {
    font-family: 'DM Serif Display', serif;
    font-size: 1.75rem;
    color: #12122a;
    line-height: 1.1;
    flex-shrink: 0;
    white-space: normal;
    word-break: break-word;
}

.kpi-formula {
    font-size: 0.70rem;
    color: #4a4a68;
    font-style: italic;
    white-space: normal;
    word-break: break-word;
    line-height: 1.35;
}

.kpi-sub {
    font-size: 0.73rem;
    color: #2a2a42;
    white-space: normal;
    word-break: break-word;
    line-height: 1.4;
}

.kpi-badge {
    display: inline-block;
    margin-top: 8px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.68rem;
    font-weight: 600;
    white-space: nowrap;
    width: fit-content;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.5;
}
.badge-green { background:#c8f0d4; color:#145a28; }
.badge-amber { background:#fdefc0; color:#7a5800; }
.badge-red   { background:#fcd8d8; color:#8b1a1a; }

/* ── Section / chart headers ─────────────────────────────────────────── */
.section-header {
    font-family: 'DM Serif Display', serif;
    font-size: 1.75rem;
    color: #1a1a2e;
    margin: 24px 0 4px 0;
    padding-left: 14px;
    border-left: 5px solid #6c63ff;
    line-height: 1.2;
}
.chart-header {
    font-family: 'DM Serif Display', serif;
    font-size: 1.1rem;
    color: #1a1a2e;
    margin: 20px 0 2px 0;
    padding-left: 10px;
    border-left: 3px solid #c4bfff;
    line-height: 1.3;
}
.section-sub {
    font-size: 0.82rem;
    color: #333344;
    margin: 2px 0 14px 11px;
    line-height: 1.5;
}
.chart-sub {
    font-size: 0.76rem;
    color: #333344;
    margin: 2px 0 12px 11px;
    line-height: 1.5;
}

/* ── Misc ────────────────────────────────────────────────────────────── */
.block-container { padding-top: 1.5rem !important; }
div[data-testid="stPlotlyChart"] { margin-bottom: 4px; }
.flag-healthy     { background:#c8f0d4; color:#145a28; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:500; }
.flag-monitor     { background:#fdefc0; color:#7a5800; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:500; }
.flag-reprice     { background:#fcd8d8; color:#8b1a1a; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:500; }
.flag-discontinue { background:#f5c6cb; color:#6c0d0d; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:500; }
</style>
""", unsafe_allow_html=True)

# ── Force scrollbar visible via JS — bright, wide, always on ────────────
st.markdown("""
<script>
(function() {
    // Inject one global style tag for the bright scrollbar
    function injectStyle() {
        if (document.getElementById('_nc_scrollbar_style')) return;
        const s = document.createElement('style');
        s.id = '_nc_scrollbar_style';
        s.textContent = `
            /* Target every scrollable container inside the sidebar */
            section[data-testid="stSidebar"] div[style*="overflow"] {
                scrollbar-width: auto !important;
                scrollbar-color: #b0b0ff #1a1a3e !important;
            }
            section[data-testid="stSidebar"] div[style*="overflow"]::-webkit-scrollbar {
                width: 12px !important;
                display: block !important;
            }
            section[data-testid="stSidebar"] div[style*="overflow"]::-webkit-scrollbar-track {
                background: #1a1a3e !important;
                border-radius: 6px !important;
                border: 1px solid #4a4a8a !important;
            }
            section[data-testid="stSidebar"] div[style*="overflow"]::-webkit-scrollbar-thumb {
                background: #b0b0ff !important;
                border-radius: 6px !important;
                min-height: 40px !important;
                border: 2px solid #1a1a3e !important;
            }
            section[data-testid="stSidebar"] div[style*="overflow"]::-webkit-scrollbar-thumb:hover {
                background: #d0d0ff !important;
            }
        `;
        document.head.appendChild(s);
    }

    function forceScrollbar() {
        injectStyle();
        // Find every div inside the sidebar that has overflow set inline
        const sidebar = document.querySelector('section[data-testid="stSidebar"]');
        if (!sidebar) return;
        sidebar.querySelectorAll('div').forEach(el => {
            const style = el.getAttribute('style') || '';
            if (style.includes('overflow')) {
                el.style.setProperty('overflow-y', 'scroll', 'important');
            }
        });
    }

    const observer = new MutationObserver(forceScrollbar);
    observer.observe(document.body, { childList: true, subtree: true });
    forceScrollbar();
    setTimeout(forceScrollbar, 300);
    setTimeout(forceScrollbar, 800);
    setTimeout(forceScrollbar, 2000);
})();
</script>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🍬 Nassau Candy")
    st.markdown("**Profitability Intelligence**")
    st.markdown("---")
    page = st.radio("Navigate", [
        "📊  Executive Overview",
        "🏷️  Product Profitability",
        "🏢  Division Performance",
        "📈  Profit Concentration",
        "🔬  Cost vs Margin Diagnostics",
    ], label_visibility="collapsed")
    st.markdown("---")
    st.caption("Nassau Candy Distributor · 2024–2025")

if   page == "📊  Executive Overview":
    from pages_code.p1_overview    import render; render()
elif page == "🏷️  Product Profitability":
    from pages_code.p2_product     import render; render()
elif page == "🏢  Division Performance":
    from pages_code.p3_division    import render; render()
elif page == "📈  Profit Concentration":
    from pages_code.p4_pareto      import render; render()
elif page == "🔬  Cost vs Margin Diagnostics":
    from pages_code.p5_diagnostics import render; render()