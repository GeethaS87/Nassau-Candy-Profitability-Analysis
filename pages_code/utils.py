import os
import pandas as pd
import numpy as np
import streamlit as st


@st.cache_data
def load_data():
    _HERE = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(_HERE, "Nassau_Candy_Distributor.csv"))
    df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True, errors='coerce')
    df['Ship Date']  = pd.to_datetime(df['Ship Date'],  dayfirst=True, errors='coerce')

    df = df[df['Sales'] > 0]
    df = df[df['Cost']  > 0]
    df = df.dropna(subset=['Sales', 'Gross Profit', 'Cost'])
    df['Units']        = df['Units'].fillna(1).replace(0, 1)
    df['Product Name'] = df['Product Name'].str.strip().str.title()
    df['Division']     = df['Division'].str.strip().str.title()
    df['Region']       = df['Region'].str.strip().str.title()
    df['Ship Mode']    = df['Ship Mode'].str.strip().str.title()

    df['Gross_Margin_Pct'] = (df['Gross Profit'] / df['Sales'] * 100).round(2)
    df['Profit_Per_Unit']  = (df['Gross Profit'] / df['Units']).round(2)
    df['Cost_Ratio']       = (df['Cost'] / df['Sales'] * 100).round(2)
    df['Year']             = df['Order Date'].dt.year
    df['Month']            = df['Order Date'].dt.to_period('M').astype(str)
    df['Quarter']          = df['Order Date'].dt.to_period('Q').astype(str)
    return df


def build_product_summary(df):
    ps = df.groupby(['Division', 'Product Name']).agg(
        Avg_Gross_Margin = ('Gross_Margin_Pct', 'mean'),
        Total_Sales      = ('Sales',            'sum'),
        Total_Profit     = ('Gross Profit',     'sum'),
        Total_Cost       = ('Cost',             'sum'),
        Total_Units      = ('Units',            'sum'),
        Order_Count      = ('Order ID',         'count'),
    ).round(2).reset_index()

    ps['Profit_Per_Unit']   = (ps['Total_Profit'] / ps['Total_Units']).round(2)
    ps['Revenue_Share_Pct'] = (ps['Total_Sales']  / ps['Total_Sales'].sum()  * 100).round(2)
    ps['Profit_Share_Pct']  = (ps['Total_Profit'] / ps['Total_Profit'].sum() * 100).round(2)
    ps['Cost_Ratio']        = (ps['Total_Cost']   / ps['Total_Sales']        * 100).round(2)

    healthy_threshold = round(ps['Avg_Gross_Margin'].mean(), 1)
    warning_threshold = round(ps['Avg_Gross_Margin'].mean() - ps['Avg_Gross_Margin'].std(), 1)
    risk_threshold    = round(ps['Avg_Gross_Margin'].mean() - 2 * ps['Avg_Gross_Margin'].std(), 1)

    sales_median  = ps['Total_Sales'].median()
    orders_median = ps['Order_Count'].median()

    def action_flag(mg):
        if mg >= healthy_threshold:    return '✅ Healthy'
        elif mg >= warning_threshold:  return '🟡 Monitor'
        elif mg >= risk_threshold:     return '🔴 Reprice'
        else:                          return '⛔ Discontinue'

    ps['Action_Flag'] = ps['Avg_Gross_Margin'].apply(action_flag)

    def cost_action(row):
        cr = row['Cost_Ratio']
        mg = row['Avg_Gross_Margin']
        if cr > 80:                              return 'Renegotiate Cost'
        elif cr > 60 and mg < warning_threshold: return 'Review Pricing'
        elif mg >= healthy_threshold:            return 'Maintain'
        else:                                    return 'Monitor'

    ps['Cost_Action'] = ps.apply(cost_action, axis=1)

    def assign_action(row):
        high_sales  = row['Total_Sales']  >= sales_median
        high_orders = row['Order_Count']  >= orders_median
        mg          = row['Avg_Gross_Margin']
        if mg >= healthy_threshold:
            return 'Maintain' if (high_sales or high_orders) else 'Promote'
        elif mg >= warning_threshold:
            return 'Monitor' if (high_sales and high_orders) else 'Discontinue'
        elif mg >= risk_threshold:
            return 'Reprice' if (high_sales or high_orders) else 'Discontinue'
        else:
            return 'Renegotiate Cost' if (high_sales or high_orders) else 'Discontinue'

    ps['Recommended_Action'] = ps.apply(assign_action, axis=1)

    ps['Sales_Tier']  = np.where(ps['Total_Sales']      >= sales_median,      'High', 'Low')
    ps['Margin_Tier'] = np.where(ps['Avg_Gross_Margin'] >= healthy_threshold, 'High', 'Low')

    cat_conditions = [
        (ps['Sales_Tier'] == 'High') & (ps['Margin_Tier'] == 'High'),
        (ps['Sales_Tier'] == 'High') & (ps['Margin_Tier'] == 'Low'),
        (ps['Sales_Tier'] == 'Low')  & (ps['Margin_Tier'] == 'High'),
        (ps['Sales_Tier'] == 'Low')  & (ps['Margin_Tier'] == 'Low'),
    ]
    cat_labels = [
        '⭐ High Sales / High Margin',
        '⚠️ High Sales / Low Margin',
        '📊 Low Sales / High Margin',
        '🔻 Low Sales / Low Margin',
    ]
    ps['Product_Category'] = np.select(cat_conditions, cat_labels, default='❓ Uncategorised')

    ps.attrs['healthy_threshold'] = healthy_threshold
    ps.attrs['warning_threshold'] = warning_threshold
    ps.attrs['risk_threshold']    = risk_threshold
    return ps


def sidebar_filters(df, show_product_filter=True):
    with st.sidebar:
        st.markdown("### Filters")
        divisions = ['All'] + sorted(df['Division'].unique().tolist())
        if '_div_key' not in st.session_state:
            st.session_state['_div_key'] = 0
        _div_col, _div_reset_col = st.columns([4, 1])
        with _div_col:
            sel_div = st.selectbox("Division", divisions,
                                   key=f"division_{st.session_state['_div_key']}")
        with _div_reset_col:
            st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
            if st.button("↺", key="reset_div", help="Reset division filter"):
                st.session_state['_div_key'] += 1
                st.rerun()
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

        min_d      = df['Order Date'].min().date()
        max_d      = df['Order Date'].max().date()

        if '_date_key' not in st.session_state:
            st.session_state['_date_key'] = 0

        _date_col, _reset_col = st.columns([4, 1])
        with _date_col:
            date_range = st.date_input(
                "Select Date Range",
                value=(min_d, max_d),
                key=f"date_input_{st.session_state['_date_key']}"
            )
        with _reset_col:
            st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
            if st.button("↺", key="reset_date", help="Reset to full date range"):
                st.session_state['_date_key'] += 1
                st.rerun()

        import datetime as _dt
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            sel_start, sel_end = date_range
            out_before = sel_start < min_d
            out_after  = sel_end > max_d
            no_overlap = sel_end < min_d or sel_start > max_d

            if no_overlap:
                msg = f"⚠️ No data available for this range. Data exists from {min_d} to {max_d}."
                color = "#e05252"
                bg    = "#3a1a1a"
                border= "#e05252"
            elif out_before and out_after:
                msg = f"⚠️ Range exceeds data on both ends. Data available: {min_d} to {max_d}."
                color = "#e8963a"
                bg    = "#3a2a1a"
                border= "#e8963a"
            elif out_before:
                msg = f"⚠️ No data before {min_d}. Showing from {min_d} onwards."
                color = "#e8963a"
                bg    = "#3a2a1a"
                border= "#e8963a"
            elif out_after:
                msg = f"⚠️ No data after {max_d}. Showing up to {max_d}."
                color = "#e8963a"
                bg    = "#3a2a1a"
                border= "#e8963a"
            else:
                msg = None

            if msg:
                st.markdown(
                    f'<div style="background:{bg};border:1px solid {border};border-radius:6px;'
                    f'padding:8px 12px;margin-top:4px;font-size:0.75rem;color:{color};line-height:1.5;">'
                    f'{msg}</div>',
                    unsafe_allow_html=True
                )

        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        margin_min = st.slider("Gross Margin %", 0, 100, 0)
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        if not show_product_filter:
            selected_products = []
        else:
            all_products = sorted(df['Product Name'].unique().tolist())

            if '_product_key' not in st.session_state:
                st.session_state['_product_key'] = 0
            if 'selected_products' not in st.session_state:
                st.session_state['selected_products'] = []
            if '_filter_open' not in st.session_state:
                st.session_state['_filter_open'] = False

            st.markdown('<p style="font-size:0.875rem;letter-spacing:0.05em;text-transform:uppercase;'
                        'color:#fafafa;font-weight:400;margin-bottom:4px;">Filter Products</p>',
                        unsafe_allow_html=True)

            # ── Checkboxes rendered BEFORE the toggle label ───────────────────
            # This ensures selected_products is fully synced BEFORE we compute
            # the count shown on the toggle button — fixes the off-by-one lag.
            if st.session_state['_filter_open']:
                container = st.container(height=220, border=True)
                new_selection = []
                for product in all_products:
                    chk_key = f"chk_{product}_{st.session_state['_product_key']}"
                    default = product in st.session_state['selected_products']
                    if container.checkbox(product, value=default, key=chk_key):
                        new_selection.append(product)
                # Sync immediately — no rerun, list stays open for multi-select
                st.session_state['selected_products'] = new_selection

            # ── Toggle + clear on the same row, mirroring date range layout ──
            n_selected = len(st.session_state['selected_products'])
            expander_label = "All products shown" if n_selected == 0 else f"{n_selected} product{'s' if n_selected > 1 else ''} selected"
            chevron = "▼" if st.session_state['_filter_open'] else "▶"
            _tog_col, _clr_col = st.columns([4, 1], vertical_alignment="center")
            with _tog_col:
                if st.button(
                    f"{chevron}  {expander_label}",
                    key="toggle_filter_open",
                    use_container_width=True,
                ):
                    st.session_state['_filter_open'] = not st.session_state['_filter_open']
                    st.rerun()
            with _clr_col:
                if st.button("↺", key="clear_products", help="Clear product filter"):
                    # Full reset: clear selections, close panel, regenerate checkbox keys
                    st.session_state['selected_products'] = []
                    st.session_state['_filter_open'] = False
                    st.session_state['_product_key'] += 1
                    st.rerun()

            selected_products = st.session_state['selected_products']

    filtered = df.copy()
    if sel_div != 'All':
        filtered = filtered[filtered['Division'] == sel_div]
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        filtered = filtered[
            (filtered['Order Date'].dt.date >= date_range[0]) &
            (filtered['Order Date'].dt.date <= date_range[1])]
    filtered = filtered[filtered['Gross_Margin_Pct'] >= margin_min]
    if selected_products:
        filtered = filtered[filtered['Product Name'].isin(selected_products)]
    return filtered, sel_div


def kpi_card(label, value, formula, sub="", accent="#6c63ff",
             badge=None, badge_color="green", grayed=False):
    badge_map = {
        'green': ('#c8f0d4', '#145a28'),
        'amber': ('#fdefc0', '#7a5800'),
        'red':   ('#fcd8d8', '#8b1a1a'),
        'gray':  ('#e8e8ee', '#888899'),
    }

    # When grayed, blank out content — only the note remains
    _accent        = '#c8c8d8' if grayed else accent
    _bg            = '#f5f5f8' if grayed else '#ffffff'
    _border        = '#e0e0e8' if grayed else '#d8d8e8'
    _label_color   = '#a0a0b0' if grayed else '#1a1a2e'
    _value_color   = '#c8c8d8' if grayed else '#12122a'
    _formula_color = '#c8c8d8' if grayed else '#1a1a2e'
    _sub_color     = '#c8c8d8' if grayed else '#000000'
    _opacity       = '0.72'    if grayed else '1'
    _badge_color   = 'gray'    if grayed else badge_color

    # Suppress all content when grayed
    _value   = '—' if grayed else value
    _formula = ''  if grayed else formula
    _sub     = ''  if grayed else sub
    _badge   = None if grayed else badge

    badge_html = ""
    if _badge:
        bg, fg = badge_map.get(_badge_color, badge_map['green'])
        badge_html = (
            f'<div style="display:inline-block;margin-top:8px;padding:3px 10px;'
            f'border-radius:20px;font-size:0.68rem;font-weight:600;'
            f'background:{bg};color:{fg};white-space:nowrap;">'
            f'{_badge}</div>'
        )

    gray_note = (
        '<div style="font-size:0.62rem;color:#a0a0b0;margin-top:auto;padding-top:12px;font-style:italic;">'
        'Reflects full portfolio &#8212; not division-specific</div>'
    ) if grayed else ""

    st.markdown(
        f"""
<div style="
    background:{_bg};
    border:1px solid {_border};
    border-radius:12px;
    padding:18px 14px 16px 14px;
    position:relative;
    display:flex;
    flex-direction:column;
    gap:4px;
    box-sizing:border-box;
    margin-bottom:4px;
    border-top:3px solid {_accent};
    height:100%;
    min-height:200px;
    opacity:{_opacity};
">
  <div style="
      font-size:0.62rem;
      letter-spacing:0.10em;
      text-transform:uppercase;
      color:{_label_color};
      font-weight:700;
      line-height:1.45;
      min-height:2.5em;
      margin-bottom:2px;
  ">{label}</div>
  <div style="
      font-size:1.60rem;
      color:{_value_color};
      line-height:1.1;
      font-weight:600;
      font-family:'Times New Roman', Georgia, serif;
      white-space:normal;
      overflow:hidden;
      text-overflow:ellipsis;
  ">{_value}</div>
  <div style="
      font-size:0.70rem;
      color:{_formula_color};
      font-style:italic;
      line-height:1.35;
      min-height:2.6em;
  ">{_formula}</div>
  <div style="
      font-size:0.72rem;
      color:{_sub_color};
      font-weight:600;
      line-height:1.4;
      display:-webkit-box;
      -webkit-line-clamp:2;
      -webkit-box-orient:vertical;
      overflow:hidden;
      min-height:2.0em;
  ">{_sub}</div>
  {badge_html}
  {gray_note}
</div>""",
        unsafe_allow_html=True,
    )


def section(title, sub=None):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)


def chart(title, sub=None):
    st.markdown(f'<div class="chart-header">{title}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="chart-sub">{sub}</div>', unsafe_allow_html=True)