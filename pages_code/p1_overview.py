import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import gaussian_kde
import numpy as np
from pages_code.utils import (
    load_data, sidebar_filters, build_product_summary,
    kpi_card, section, chart,
)

DIV   = {'Chocolate': '#7B4F2E', 'Sugar': '#E8963A', 'Other': '#6C63FF'}
_DARK = '#1a1a2e'
_GRID = '#ebebf0'
_TF   = dict(color='#1a1a2e', size=11, family='DM Sans, sans-serif')
_LF   = dict(color='#333333', size=12, family='DM Sans, sans-serif')
_BASE = dict(
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(color='#1a1a2e', family='DM Sans, sans-serif', size=11),
)


def hex_to_rgba(hex_color: str, alpha: float = 0.15) -> str:
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def money_label(v: float) -> str:
    if v >= 100_000:
        return f"${v / 1_000:.0f}k"
    elif v > 0:
        return f"${v:,.0f}"
    return "$0"


def render():
    df_full = load_data()                  # full unfiltered dataset
    df, sel_div = sidebar_filters(df_full)     # filtered dataset
    df_div = df_full if sel_div == 'All' else df_full[df_full['Division'] == sel_div]  # division-only filtered (no product filter)
    _product_filtered = set(df['Product Name'].unique()) != set(df_div['Product Name'].unique())  # True only when product filter narrows the product set

    if df.empty:
        section("Executive Overview",
                "Portfolio-level financial performance summary across all product divisions")
        st.warning("No records found for the selected criteria. Consider revising the filter selections.", icon="⚠️")
        return

    # Build product summary on filtered data for raw metrics
    ps = build_product_summary(df)

    # Build product summary on FULL data for stable classifications
    ps_full = build_product_summary(df_full)
    action_map   = ps_full.set_index('Product Name')['Recommended_Action'].to_dict()
    category_map = ps_full.set_index('Product Name')['Product_Category'].to_dict()

    # Override action and category in filtered ps with full-data classifications
    ps['Recommended_Action'] = ps['Product Name'].map(action_map).fillna(ps['Recommended_Action'])
    ps['Product_Category']   = ps['Product Name'].map(category_map).fillna(ps['Product_Category'])

    # Always use full-data thresholds — never shift with any filter
    healthy_threshold = ps_full.attrs['healthy_threshold']
    warning_threshold = ps_full.attrs['warning_threshold']
    risk_threshold    = ps_full.attrs['risk_threshold']

    section("Executive Overview",
            "Portfolio-level financial performance summary across all product divisions")

    # ── Calculations ──────────────────────────────────────────────────────────
    total_rev   = df['Sales'].sum()
    total_pft   = df['Gross Profit'].sum()
    total_units = df['Units'].sum()
    avg_margin  = (total_pft / total_rev * 100) if total_rev else 0
    ppu         = total_pft / total_units if total_units else 0

    # Portfolio totals from FULL data for contribution denominators
    full_total_rev = df_full['Sales'].sum()
    full_total_pft = df_full['Gross Profit'].sum()

    monthly_margin = df.groupby('Month')['Gross_Margin_Pct'].mean()
    margin_vol   = (monthly_margin.max() - monthly_margin.min()) if len(monthly_margin) > 1 else 0
    margin_best  = monthly_margin.max() if len(monthly_margin) else df["Gross_Margin_Pct"].max()
    margin_worst = monthly_margin.min() if len(monthly_margin) else df["Gross_Margin_Pct"].min()

    prod_rev    = df.groupby('Product Name')['Sales'].sum()
    top_rev_prd = prod_rev.idxmax()
    top_rev_pct = prod_rev.max() / full_total_rev * 100   # top product vs full portfolio

    prod_pft    = df.groupby('Product Name')['Gross Profit'].sum()
    top_pft_prd = prod_pft.idxmax()
    top_pft_pct = prod_pft.max() / full_total_pft * 100   # top product vs full portfolio

    def trim(name: str, n: int = 28) -> str:
        import re
        parts = re.split(r'\s*-\s*', name, maxsplit=1)
        s = parts[-1].strip()
        return s[:n] + "..." if len(s) > n else s

    # Critical zone always reflects full portfolio — never filtered
    critical_count = (ps_full["Avg_Gross_Margin"] < risk_threshold).sum()
    critical_names = ps_full[ps_full["Avg_Gross_Margin"] < risk_threshold]["Product Name"].tolist()
    if critical_count == 0:
        crit_sub = "No products in critical zone"
    elif critical_count == 1:
        crit_sub = f"{trim(critical_names[0])} - Immediate review"
    else:
        crit_sub = ", ".join(trim(n) for n in critical_names[:2])
        if critical_count > 2:
            crit_sub += f" +{critical_count - 2} more"
        crit_sub += " - Immediate review"

    margin_badge, margin_badge_color = (
        ("Healthy", "green") if avg_margin >= healthy_threshold else
        ("Monitor", "amber") if avg_margin >= warning_threshold else
        ("At risk", "red")
    )
    _vol_note = '<span style="font-size:0.60rem;color:#7a7a9a;font-weight:400;"> · Portfolio-level; division variance exists</span>'
    vol_badge, vol_color, vol_sub = (
        ("High vol.", "red",   f"Best: {margin_best:.1f}%  /  Worst: {margin_worst:.1f}%")
        if margin_vol > 5 else
        ("Moderate",  "amber", f"Best: {margin_best:.1f}%  /  Worst: {margin_worst:.1f}%")
        if margin_vol > 2 else
        ("Stable",    "green", f"Best: {margin_best:.1f}%  /  Worst: {margin_worst:.1f}%" + _vol_note)
    )
    crit_badge = "Action needed" if critical_count > 0 else "All clear"
    crit_color = "red"           if critical_count > 0 else "green"

    # ── 6 KPI Cards ───────────────────────────────────────────────────────────
    def _badge(text, color):
        bg = {'green': '#c8f0d4', 'amber': '#fdefc0', 'red': '#fcd8d8'}.get(color, '#c8f0d4')
        fg = {'green': '#145a28', 'amber': '#7a5800', 'red': '#8b1a1a'}.get(color, '#145a28')
        return (
            f'<div style="margin-top:auto;padding-top:8px;">'
            f'<span style="background:{bg};color:{fg};padding:3px 10px;'
            f'border-radius:20px;font-size:0.68rem;font-weight:600;">'
            f'{text}</span></div>'
        )

    def _card(label, value, formula, sub, accent, badge_text=None, badge_color=None):
        b = _badge(badge_text, badge_color) if badge_text else ''
        return (
            f'<div style="background:#fff;border:1px solid #d8d8e8;border-radius:12px;'
            f'padding:18px 14px 16px;border-top:3px solid {accent};'
            f'display:flex;flex-direction:column;gap:4px;box-sizing:border-box;">'
            f'<div style="font-size:0.62rem;letter-spacing:0.10em;text-transform:uppercase;'
            f'color:#1a1a2e;font-weight:700;line-height:1.45;min-height:2.5em;">{label}</div>'
            f'<div style="font-size:1.60rem;color:#12122a;font-family:\'Times New Roman\',Georgia,serif;'
            f'font-weight:600;letter-spacing:0.01em;'
            f'line-height:1.1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{value}</div>'
            f'<div style="font-size:0.70rem;color:#4a4a68;font-style:italic;line-height:1.35;'
            f'min-height:1.9em;">{formula}</div>'
            f'<div style="font-size:0.72rem;color:#0a0a1a;font-weight:600;line-height:1.4;'
            f'min-height:2.0em;word-break:break-word;">{sub}</div>'
            f'{b}</div>'
        )

    # ── Low data flag ─────────────────────────────────────────────────────────
    import pandas as _pd
    low_data = (
        df['Product Name'].nunique() < 2 or
        len(df) < 10 or
        df['Gross_Margin_Pct'].nunique() < 2 or
        df['Month'].nunique() < 2 or
        _pd.isna(warning_threshold) or
        _pd.isna(risk_threshold) or
        ps_full['Recommended_Action'].isna().any()
    )

    def _faded_card(label, value, formula, sub, accent):
        return (
            f'<div style="background:#f8f8f8;border:1px solid #e0e0e8;border-radius:12px;'
            f'padding:18px 14px 16px;border-top:3px solid #cccccc;'
            f'display:flex;flex-direction:column;gap:4px;box-sizing:border-box;opacity:0.45;">'
            f'<div style="font-size:0.62rem;letter-spacing:0.10em;text-transform:uppercase;'
            f'color:#888;font-weight:700;line-height:1.45;min-height:2.5em;">{label}</div>'
            f'<div style="font-size:1.60rem;color:#aaa;font-family:\'Times New Roman\',Georgia,serif;'
            f'font-weight:600;line-height:1.1;">—</div>'
            f'<div style="font-size:0.70rem;color:#aaa;font-style:italic;line-height:1.35;'
            f'min-height:1.9em;">{formula}</div>'
            f'<div style="font-size:0.70rem;color:#aaa;font-style:italic;line-height:1.4;'
            f'min-height:2.0em;">Insufficient data for a reliable estimate</div>'
            f'</div>'
        )

    if low_data:
        cards_html = (
            '<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:10px;'
            'margin-bottom:16px;align-items:stretch;">'
            + _card("Gross Margin %", f"{avg_margin:.1f}%", "Gross Profit / Sales (aggregate)",
                    f"Total Profit: ${total_pft:,.0f}", "#1D9E75", margin_badge, margin_badge_color)
            + _card("Profit per Unit", f"${ppu:.2f}", "Gross Profit / Units",
                    f"Total Units: {total_units:,}", "#378ADD")
            + _card("Revenue Contribution", f"{top_rev_pct:.1f}%", "Selected Sales / Total Portfolio Sales",
                    f"Top: {trim(top_rev_prd)}", "#E8963A")
            + _card("Profit Contribution", f"{top_pft_pct:.1f}%", "Selected Profit / Total Portfolio Profit",
                    f"Top: {trim(top_pft_prd)}", "#7F77DD")
            + _faded_card("Margin Volatility", "", "Monthly margin range (max - min)", "", "#D85A30")
            + _faded_card("Critical Zone", "", "Margin threshold", "", "#E24B4A")
            + '</div>'
        )
    else:
        cards_html = (
            '<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:10px;'
            'margin-bottom:16px;align-items:stretch;">'
            + _card("Gross Margin %", f"{avg_margin:.1f}%", "Gross Profit / Sales (aggregate)",
                    f"Total Profit: ${total_pft:,.0f}", "#1D9E75", margin_badge, margin_badge_color)
            + _card("Profit per Unit", f"${ppu:.2f}", "Gross Profit / Units",
                    f"Total Units: {total_units:,}", "#378ADD")
            + _card("Revenue Contribution", f"{top_rev_pct:.1f}%", "Selected Sales / Total Portfolio Sales",
                    f"Top: {trim(top_rev_prd)}", "#E8963A")
            + _card("Profit Contribution", f"{top_pft_pct:.1f}%", "Selected Profit / Total Portfolio Profit",
                    f"Top: {trim(top_pft_prd)}", "#7F77DD")
            + _card("Margin Volatility", f"{margin_vol:.1f}%", "Monthly margin range (max - min)",
                    vol_sub, "#D85A30", vol_badge, vol_color)
            + (_faded_card("Critical Zone", "", "Margin threshold", "", "#E24B4A")
               if sel_div in ('Chocolate', 'Sugar')
               else _card("Critical Zone", str(critical_count), f"Margin < {risk_threshold:.1f}%",
                          crit_sub, "#E24B4A", crit_badge, crit_color))
            + '</div>'
        )
    st.markdown(cards_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Shared division-level data ─────────────────────────────────────────────
    div_data = (
        df.groupby('Division')[['Sales', 'Gross Profit']]
        .sum().reset_index()
        .sort_values('Sales', ascending=False)
    )
    div_data['Margin_Pct'] = (div_data['Gross Profit'] / div_data['Sales'] * 100).round(1)
    div_data['Cost']       = div_data['Sales'] - div_data['Gross Profit']
    div_data['Cost_Pct']   = (div_data['Cost']         / div_data['Sales'] * 100).round(1)
    div_data['Profit_Pct'] = (div_data['Gross Profit'] / div_data['Sales'] * 100).round(1)

    # ═══════════════════════════════════════════════════════════════════════════
    # CHART 1 — Sales Distribution (moved here, just below KPI cards)
    # ═══════════════════════════════════════════════════════════════════════════
    mean_s, median_s = df['Sales'].mean(), df['Sales'].median()
    chart("Sales Distribution — Mean vs Median",
          "Distribution of transaction values illustrating mean-median divergence")

    fig_dist = go.Figure()
    fig_dist.add_trace(go.Histogram(
        x=df['Sales'], nbinsx=40,
        marker_color='#6c63ff', opacity=0.75, name='Orders',
    ))
    fig_dist.add_vline(x=mean_s, line_dash='dash', line_color='#c0221c', line_width=2,
                       annotation_text=f"Mean ${mean_s:.2f}",
                       annotation_position='top right',
                       annotation_font_color='#8b1a1a')
    fig_dist.add_vline(x=median_s, line_dash='dash', line_color='#0f7a3e', line_width=2,
                       annotation_text=f"Median ${median_s:.2f}",
                       annotation_position='top left',
                       annotation_font_color='#145a28')
    fig_dist.update_layout(
        **_BASE, height=280,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
    )
    fig_dist.update_xaxes(tickprefix='$', gridcolor=_GRID, tickfont=_TF,
                          title=dict(text='Sales ($)', font=_LF))
    fig_dist.update_yaxes(gridcolor=_GRID, tickfont=_TF,
                          title=dict(text='Frequency', font=_LF))
    st.plotly_chart(fig_dist, use_container_width=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # CHART 2 — User-selectable comparison view
    # ═══════════════════════════════════════════════════════════════════════════
    chart("Division Performance — Select View")
    chart_choice = st.radio(
        "chart_choice_radio",
        options=[
            "Revenue, Profit & Margin",
            "Revenue vs Gross Profit",
            "Cost vs Profit Split",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

    if chart_choice == "Revenue, Profit & Margin":
        chart("Revenue, Profit & Margin % by Division",
              "Side-by-side Revenue and Gross Profit with Gross Margin % line overlay")

        figA = go.Figure()
        figA.add_trace(go.Bar(
            name='Total Revenue',
            x=div_data['Division'],
            y=div_data['Sales'],
            marker_color=[DIV.get(d, '#888') for d in div_data['Division']],
            opacity=0.92,
            text=[money_label(v) for v in div_data['Sales']],
            textposition='outside',
            textfont=dict(size=12, color='#1a1a2e', family='DM Sans, sans-serif'),
            cliponaxis=False,
            offsetgroup='sales',
            showlegend=False,
        ))
        figA.add_trace(go.Bar(
            name='Gross Profit',
            x=div_data['Division'],
            y=div_data['Gross Profit'],
            marker_color=[DIV.get(d, '#888') for d in div_data['Division']],
            opacity=0.42,
            cliponaxis=False,
            offsetgroup='profit',
            showlegend=False,
        ))
        # Profit bar labels — use text on a separate invisible bar trace
        # to get exact centering over the profit bar without xshift guessing
        figA.add_trace(go.Bar(
            name='_profit_labels',
            x=div_data['Division'],
            y=div_data['Gross Profit'],
            marker_color='rgba(0,0,0,0)',
            text=[money_label(v) for v in div_data['Gross Profit']],
            textposition='outside',
            textfont=dict(size=11, color='#1a1a2e', family='DM Sans, sans-serif'),
            cliponaxis=False,
            offsetgroup='profit',
            showlegend=False,
        ))
        # Dummy legend traces added AFTER bars so categorical x-axis is set first
        figA.add_trace(go.Scatter(
            name='Total Revenue (dark shade)', x=[None], y=[None], mode='markers',
            marker=dict(symbol='square', size=12, color='#555555'),
            showlegend=True, legendrank=1,
        ))
        figA.add_trace(go.Scatter(
            name='Gross Profit (light shade)', x=[None], y=[None], mode='markers',
            marker=dict(symbol='square', size=12, color='#aaaaaa'),
            showlegend=True, legendrank=2,
        ))
        figA.add_trace(go.Scatter(
            name='Gross Margin %',
            x=div_data['Division'],
            y=div_data['Margin_Pct'],
            mode='lines+markers+text',
            yaxis='y2',
            line=dict(color='#E24B4A', width=2.5, dash='dot'),
            marker=dict(size=9, color='#E24B4A', symbol='diamond',
                        line=dict(width=1.5, color='white')),
            text=[f"{m:.1f}%" for m in div_data['Margin_Pct']],
            textposition='top center',
            textfont=dict(size=11, color='#E24B4A', family='DM Sans, sans-serif'),
            cliponaxis=False,
        ))
        for _, row in div_data.iterrows():
            figA.add_annotation(
                x=row['Division'], y=-0.20, yref='paper',
                text=f"Margin Captured: {row['Margin_Pct']:.1f}%",
                showarrow=False,
                font=dict(size=10, color='#12122a', family='DM Sans, sans-serif'),
                xanchor='center',
            )
        figA.update_layout(
            **_BASE, barmode='group', bargroupgap=0.18, bargap=0.30,
            height=400, margin=dict(l=10, r=70, t=30, b=85),
            legend=dict(orientation='h', y=1.12, x=0,
                        font=dict(size=11, color='#1a1a2e')),
            yaxis=dict(
                tickprefix='$', gridcolor=_GRID,
                tickfont=dict(color='#1a1a2e', size=11),
                title=dict(text='Amount ($)', font=dict(color='#333333', size=12)),
                rangemode='tozero',
            ),
            yaxis2=dict(
                title=dict(text='Gross Margin %', font=dict(color='#E24B4A', size=11)),
                overlaying='y', side='right', ticksuffix='%', showgrid=False,
                tickfont=dict(color='#E24B4A', size=11),
                range=[0, div_data['Margin_Pct'].max() * 1.55],
            ),
        )
        figA.update_xaxes(tickfont=dict(color='#1a1a2e', size=13), showgrid=False)
        st.plotly_chart(figA, use_container_width=True)

    elif chart_choice == "Revenue vs Gross Profit":
        # ── EDA-matched: grouped bars, division colours, shade legend, margin captured ──
        chart("Revenue vs Gross Profit by Division",
              "Division-level view of revenue earned vs gross profit captured")

        div_sorted = div_data.sort_values('Sales', ascending=False).reset_index(drop=True)

        figB = go.Figure()

        # Sales bars — showlegend=False (dummy scatter handles legend)
        figB.add_trace(go.Bar(
            name='Total Sales',
            x=div_sorted['Division'],
            y=div_sorted['Sales'],
            marker_color=[DIV.get(d, '#888') for d in div_sorted['Division']],
            opacity=0.90,
            text=[f"${v:,.0f}" for v in div_sorted['Sales']],
            textposition='outside',
            textfont=dict(size=11, color='#1a1a2e', family='DM Sans, sans-serif'),
            cliponaxis=False,
            width=0.35,
            offsetgroup='sales',
            showlegend=False,
        ))

        # Profit bars — showlegend=False (dummy scatter handles legend)
        figB.add_trace(go.Bar(
            name='Total Profit',
            x=div_sorted['Division'],
            y=div_sorted['Gross Profit'],
            marker_color=[DIV.get(d, '#888') for d in div_sorted['Division']],
            opacity=0.45,
            text=[f"${v:,.0f}" for v in div_sorted['Gross Profit']],
            textposition='outside',
            textfont=dict(size=11, color='#1a1a2e', family='DM Sans, sans-serif'),
            cliponaxis=False,
            width=0.35,
            offsetgroup='profit',
            showlegend=False,
        ))

        # Legend line 1: division colour patches (Chocolate, Other, Sugar)
        for div, color in DIV.items():
            if div in div_sorted['Division'].values:
                figB.add_trace(go.Scatter(
                    name=div, x=[None], y=[None], mode='markers',
                    marker=dict(symbol='square', size=10, color=color),
                    showlegend=True,
                    legendrank=1,
                ))

        # Legend line 2: shade explanation
        figB.add_trace(go.Scatter(
            name='Total Sales (dark shade)', x=[None], y=[None], mode='markers',
            marker=dict(symbol='square', size=10, color='#555555'),
            showlegend=True,
            legendrank=2,
        ))
        figB.add_trace(go.Scatter(
            name='Total Profit (light shade)', x=[None], y=[None], mode='markers',
            marker=dict(symbol='square', size=10, color='#aaaaaa'),
            showlegend=True,
            legendrank=2,
        ))

        # Bottom annotation: Margin Captured per division
        for _, row in div_sorted.iterrows():
            mc = row['Gross Profit'] / row['Sales'] * 100
            figB.add_annotation(
                x=row['Division'], y=-0.14, yref='paper',
                text=f"Margin Captured: {mc:.1f}%",
                showarrow=False,
                font=dict(size=10, color='#444455', family='DM Sans, sans-serif'),
                xanchor='center',
            )

        figB.update_layout(
            **_BASE,
            barmode='group',
            bargroupgap=0.20,
            bargap=0.35,
            height=400,
            margin=dict(l=10, r=20, t=30, b=70),
            legend=dict(
                orientation='h', y=1.13, x=0,
                font=dict(size=11, color='#1a1a2e'),
                itemsizing='constant',
            ),
            yaxis=dict(
                tickprefix='$', tickformat=',.0f', gridcolor=_GRID,
                tickfont=dict(color='#1a1a2e', size=11),
                title=dict(text='Amount ($)', font=dict(color='#333333', size=12)),
                range=[0, div_sorted['Sales'].max() * 1.28],
            ),
        )
        figB.update_xaxes(
            tickfont=dict(color='#1a1a2e', size=13, family='DM Sans, sans-serif'),
            showgrid=False, type='category',
        )
        st.plotly_chart(figB, use_container_width=True)

    else:  # 100% Revenue Mix
        chart("Cost vs Profit % by Division",
              "Proportion of each revenue dollar captured as profit vs absorbed as cost")

        figC = go.Figure()
        figC.add_trace(go.Bar(
            name='Cost %',
            x=div_data['Division'],
            y=div_data['Cost_Pct'],
            marker_color='#c0bfd0',
            text=[f"{v:.1f}%" for v in div_data['Cost_Pct']],
            textposition='inside',
            textfont=dict(size=13, color='#333344'),
        ))
        figC.add_trace(go.Bar(
            name='Gross Profit %',
            x=div_data['Division'],
            y=div_data['Profit_Pct'],
            marker_color='#6c63ff',
            opacity=0.88,
            text=[f"{v:.1f}%" for v in div_data['Profit_Pct']],
            textposition='inside',
            textfont=dict(size=13, color='white'),
        ))
        figC.update_layout(
            **_BASE, barmode='stack',
            height=320, margin=dict(l=10, r=30, t=30, b=20),
            legend=dict(orientation='h', y=1.12, x=0,
                        font=dict(size=11, color='#1a1a2e')),
            yaxis=dict(
                ticksuffix='%', gridcolor=_GRID,
                tickfont=dict(color='#1a1a2e', size=11),
                title=dict(text='% of Revenue', font=dict(color='#333333', size=12)),
                range=[0, 105],
            ),
        )
        figC.update_xaxes(tickfont=dict(color='#1a1a2e', size=13), showgrid=False)
        st.plotly_chart(figC, use_container_width=True)

    # ── Revenue & Profit Contribution by Product ───────────────────────────────
    chart("Revenue & Profit Contribution by Product",
          "Proportional revenue and profit contribution per product line")

    contrib = df.groupby('Product Name').agg(
        Total_Sales  =('Sales',        'sum'),
        Total_Profit =('Gross Profit', 'sum'),
    ).reset_index()
    contrib['Rev_Pct'] = (contrib['Total_Sales']  / total_rev * 100).round(2)
    contrib['Pft_Pct'] = (contrib['Total_Profit'] / total_pft * 100).round(2)

    # ── Pareto: Revenue & Profit Contribution ────────────────────────────────
    col_p1, col_p2 = st.columns(2)

    # Revenue Pareto — y-axis = Total Sales ($), matching EDA
    with col_p1:
        st.markdown(
            '<p style="font-size:0.82rem;color:#44445a;font-weight:500;'
            'margin:0 0 4px 2px">Revenue Contribution % — Pareto View</p>',
            unsafe_allow_html=True,
        )
        par_r = (contrib.sort_values('Rev_Pct', ascending=False)
                        .reset_index(drop=True))
        par_r['Cumulative'] = par_r['Rev_Pct'].cumsum().round(1)

        fig_r = go.Figure()

        # Bars — Total Sales ($) on left y-axis, matching EDA
        fig_r.add_trace(go.Bar(
            name='Sales',
            x=par_r['Product Name'],
            y=par_r['Total_Sales'],
            marker_color='#6c63ff',
            opacity=0.85,
            yaxis='y',
            showlegend=True,
        ))

        # Cumulative % line — no text labels on dots, matching EDA
        fig_r.add_trace(go.Scatter(
            name='Cumulative %',
            x=par_r['Product Name'],
            y=par_r['Cumulative'],
            mode='lines+markers',
            line=dict(color='#E8963A', width=2),
            marker=dict(size=5, color='#E8963A'),
            yaxis='y2',
            showlegend=True,
        ))

        # Single red dashed 80% threshold line — matching EDA style
        fig_r.add_hline(
            y=80, line_dash='dash', line_color='#c0221c',
            line_width=1.8, yref='y2',
        )
        # Legend entry for threshold
        fig_r.add_trace(go.Scatter(
            name='80% threshold',
            x=[None], y=[None], mode='lines',
            line=dict(color='#c0221c', width=1.8, dash='dash'),
            showlegend=True,
        ))

        fig_r.update_layout(
            **_BASE,
            height=420,
            margin=dict(l=10, r=60, t=50, b=110),
            legend=dict(orientation='h', y=1.02, x=-0.05, xanchor='left', yanchor='bottom',
                        font=dict(size=10, color='#1a1a2e'),
                        itemsizing='constant', tracegroupgap=0,
                        traceorder='normal'),
            bargap=0.25,
            yaxis=dict(
                title=dict(text='Total Sales ($)', font=_LF),
                tickprefix='$', tickformat=',.0f',
                gridcolor=_GRID, tickfont=dict(color='#0d0d0d', size=11, family='DM Sans, sans-serif'),
                rangemode='tozero',
            ),
            yaxis2=dict(
                title=dict(text='Cumulative Revenue %',
                           font=dict(color='#c47000', size=11)),
                overlaying='y', side='right',
                ticksuffix='%', range=[0, 110],
                showgrid=False,
                tickfont=dict(color='#c47000', size=10),
            ),
        )
        fig_r.update_xaxes(
            tickfont=dict(size=10, color='#1a1a2e'),
            tickangle=-45, showgrid=False,
        )
        st.plotly_chart(fig_r, use_container_width=True)

    # Profit Pareto — y-axis = Total Profit ($)
    with col_p2:
        st.markdown(
            '<p style="font-size:0.82rem;color:#44445a;font-weight:500;'
            'margin:0 0 4px 2px">Profit Contribution % — Pareto View</p>',
            unsafe_allow_html=True,
        )
        par_p = (contrib.sort_values('Pft_Pct', ascending=False)
                        .reset_index(drop=True))
        par_p['Cumulative'] = par_p['Pft_Pct'].cumsum().round(1)

        fig_p = go.Figure()

        fig_p.add_trace(go.Bar(
            name='Profit',
            x=par_p['Product Name'],
            y=par_p['Total_Profit'],
            marker_color='#1a7a4a',
            opacity=0.85,
            yaxis='y',
            showlegend=True,
        ))

        fig_p.add_trace(go.Scatter(
            name='Cumulative %',
            x=par_p['Product Name'],
            y=par_p['Cumulative'],
            mode='lines+markers',
            line=dict(color='#E8963A', width=2),
            marker=dict(size=5, color='#E8963A'),
            yaxis='y2',
            showlegend=True,
        ))

        fig_p.add_hline(
            y=80, line_dash='dash', line_color='#c0221c',
            line_width=1.8, yref='y2',
        )
        fig_p.add_trace(go.Scatter(
            name='80% threshold',
            x=[None], y=[None], mode='lines',
            line=dict(color='#c0221c', width=1.8, dash='dash'),
            showlegend=True,
        ))

        fig_p.update_layout(
            **_BASE,
            height=420,
            margin=dict(l=10, r=60, t=50, b=110),
            legend=dict(orientation='h', y=1.02, x=-0.05, xanchor='left', yanchor='bottom',
                        font=dict(size=10, color='#1a1a2e'),
                        itemsizing='constant', tracegroupgap=0,
                        traceorder='normal'),
            bargap=0.25,
            yaxis=dict(
                title=dict(text='Total Profit ($)', font=_LF),
                tickprefix='$', tickformat=',.0f',
                gridcolor=_GRID, tickfont=dict(color='#0d0d0d', size=11, family='DM Sans, sans-serif'),
                rangemode='tozero',
            ),
            yaxis2=dict(
                title=dict(text='Cumulative Profit %',
                           font=dict(color='#c47000', size=11)),
                overlaying='y', side='right',
                ticksuffix='%', range=[0, 110],
                showgrid=False,
                tickfont=dict(color='#c47000', size=10),
            ),
        )
        fig_p.update_xaxes(
            tickfont=dict(size=10, color='#1a1a2e'),
            tickangle=-45, showgrid=False,
        )
        st.plotly_chart(fig_p, use_container_width=True)

    # ── Gross Margin KDE by Division ──────────────────────────────────────────
    chart("Gross Margin % Distribution by Division",
          "Kernel density estimate showing margin clustering and outliers per division")

    if _product_filtered:
        st.markdown(
            '<p style="font-size:0.72rem;color:#5a5a7a;font-style:italic;margin:-6px 0 10px 2px;">'
            '📌 Showing full portfolio — unaffected by filter selection</p>',
            unsafe_allow_html=True,
        )

    # KDE always uses full data filtered by division only — product filter has no effect here
    df_kde = df_full if sel_div == 'All' else df_full[df_full['Division'] == sel_div]

    if low_data:
        st.markdown(
            '<div style="opacity:0.35;pointer-events:none;">',
            unsafe_allow_html=True
        )

    x_range = np.linspace(df_kde['Gross_Margin_Pct'].min() - 2,
                          df_kde['Gross_Margin_Pct'].max() + 2, 300)
    fig_kde = go.Figure()
    for div, color in DIV.items():
        data = df_kde[df_kde['Division'] == div]['Gross_Margin_Pct'].dropna()
        if len(data) < 2 or data.nunique() < 2:
            continue
        try:
            kde = gaussian_kde(data, bw_method=0.3)
        except np.linalg.LinAlgError:
            continue
        fig_kde.add_trace(go.Scatter(
            x=x_range, y=kde(x_range),
            mode='lines', name=div,
            line=dict(color=color, width=2.5),
            fill='tozeroy', fillcolor=hex_to_rgba(color, 0.15),
        ))
    for x_val, lc, label, fc in [
        (healthy_threshold, '#0f7a3e', f"Healthy {healthy_threshold}%", '#145a28'),
        (warning_threshold, '#c87000', f"Warning {warning_threshold}%", '#7a5800'),
        (risk_threshold,    '#c0221c', f"Risk {risk_threshold}%",       '#8b1a1a'),
    ]:
        if not _pd.isna(x_val):
            fig_kde.add_vline(x=x_val, line_dash='dash', line_color=lc, line_width=1.5,
                              annotation_text=label, annotation_position='top right',
                              annotation_font_color=fc)
    fig_kde.update_layout(
        **_BASE, height=300, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation='h', y=1.12, title='', font=dict(color=_DARK)),
    )
    fig_kde.update_xaxes(ticksuffix='%', gridcolor=_GRID, tickfont=_TF,
                         title=dict(text='Gross Margin (%)', font=_LF))
    fig_kde.update_yaxes(gridcolor=_GRID, tickfont=_TF,
                         title=dict(text='Density', font=_LF))
    st.plotly_chart(fig_kde, use_container_width=True)

    if low_data:
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Product Margin Summary Table ──────────────────────────────────────────
    chart("Product Margin Summary Table",
          "Margin, revenue and profit metrics per product with strategic action recommendations")

    vol_stats = df.groupby('Product Name').agg(
        Avg_Margin    =('Gross_Margin_Pct', 'mean'),
        Total_Orders  =('Gross_Margin_Pct', 'count'),
        Total_Revenue =('Sales',            'sum'),
        Total_Profit  =('Gross Profit',     'sum'),
    ).round(2).reset_index()

    vol_stats = vol_stats.merge(
        ps[['Product Name', 'Division', 'Recommended_Action', 'Product_Category']],
        on='Product Name', how='left',
    ).sort_values('Avg_Margin', ascending=True)

    _action_emoji = {
        'Maintain':         '✅ Maintain',
        'Promote':          '⭐ Promote',
        'Monitor':          '🟡 Monitor',
        'Reprice':          '🔴 Reprice',
        'Renegotiate Cost': '🔷 Renegotiate Cost',
        'Discontinue':      '⛔ Discontinue',
    }

    vol_display = vol_stats.rename(columns={
        'Avg_Margin':         'Avg Margin %',
        'Total_Orders':       'Orders',
        'Total_Revenue':      'Revenue',
        'Total_Profit':       'Profit',
        'Recommended_Action': 'Action',
        'Product_Category':   'Category',
    })
    vol_display['Action'] = vol_display['Action'].map(_action_emoji).fillna(vol_display['Action'])

    def hl_margin(row):
        a = row['Action']
        if   a == '✅ Maintain':         return ['background-color:#f0faf4'] * len(row)
        elif a == '⭐ Promote':          return ['background-color:#e8f4f8'] * len(row)
        elif a == '🟡 Monitor':          return ['background-color:#fffbea'] * len(row)
        elif a == '🔴 Reprice':          return ['background-color:#fdf2f2'] * len(row)
        elif a == '🔷 Renegotiate Cost': return ['background-color:#f5eeff'] * len(row)
        elif a == '⛔ Discontinue':      return ['background-color:#fce8e8'] * len(row)
        else:                            return [''] * len(row)

    # Compute full-portfolio margin range for stable gradient colours
    _margin_min = df_full.groupby('Product Name')['Gross_Margin_Pct'].mean().min()
    _margin_max = df_full.groupby('Product Name')['Gross_Margin_Pct'].mean().max()

    # Truncated RdYlGn — avoids dark red/green ends that force white text
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    _cmap_full = plt.get_cmap('RdYlGn')
    _cmap_light = mcolors.LinearSegmentedColormap.from_list(
        'RdYlGn_light', _cmap_full(np.linspace(0.15, 0.85, 256))
    )

    st.dataframe(
        vol_display[['Division', 'Product Name', 'Avg Margin %',
                     'Orders', 'Revenue', 'Profit', 'Category', 'Action']]
        .style.apply(hl_margin, axis=1)
        .format({'Avg Margin %': '{:.1f}%', 'Revenue': '${:,.0f}', 'Profit': '${:,.0f}'})
        .set_properties(**{'text-align': 'center'})
        .set_table_styles([{'selector': 'th', 'props': [
            ('text-align', 'center'), ('font-weight', '600'),
            ('background-color', '#f0f0f8'), ('color', '#1a1a2e'),
            ('font-size', '0.82rem'), ('letter-spacing', '0.03em'),
        ]}])
        .background_gradient(subset=['Avg Margin %'], cmap=_cmap_light,
                             vmin=_margin_min, vmax=_margin_max)
        .set_properties(subset=['Avg Margin %'], **{'color': '#2a2a2a'}),
        use_container_width=True, height=490,
    )

    # ── Strategic Assessment Cards ────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    chart("Strategic Assessment",
          "Key portfolio insights and action priorities derived from the Executive Overview")

    if _product_filtered or sel_div != 'All':
        st.markdown(
            '<p style="font-size:0.72rem;color:#5a5a7a;font-style:italic;margin:-6px 0 10px 2px;">'
            '📌 Assessment reflects full portfolio — unaffected by filter selection</p>',
            unsafe_allow_html=True,
        )
        st.markdown('<div style="margin-bottom:16px;"></div>', unsafe_allow_html=True)

    def _assessment_card(border_color, bg_color, icon, title, title_color, body, bullets):
        bullet_html = "".join(
            f'<div style="font-size:13.5px;color:#2a2a3a;margin-top:5px;line-height:1.5;">{b}</div>'
            for b in bullets
        )
        return f"""
        <div style="border-left:5px solid {border_color};background:{bg_color};
                    border-radius:10px;padding:22px 28px;margin-bottom:20px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.06);width:100%;">
          <div style="font-size:15.5px;font-weight:700;color:{title_color};margin-bottom:10px;
                      display:flex;align-items:center;gap:8px;">
            {icon}&nbsp;{title}
          </div>
          <div style="font-size:13.5px;color:#3a3a4a;line-height:1.7;margin-bottom:8px;">{body}</div>
          {bullet_html}
        </div>"""

    # ── Derive card data ──────────────────────────────────────────────────────
    # Top division by revenue
    top_div       = div_data.iloc[0]['Division'] if not div_data.empty else '—'
    top_div_rev   = div_data.iloc[0]['Sales'] if not div_data.empty else 0
    top_div_pct   = top_div_rev / total_rev * 100 if total_rev else 0
    top_div_margin= div_data.iloc[0]['Margin_Pct'] if not div_data.empty else 0

    # Lowest margin division
    low_div       = div_data.loc[div_data['Margin_Pct'].idxmin(), 'Division'] if not div_data.empty else '—'
    low_div_margin= div_data['Margin_Pct'].min() if not div_data.empty else 0

    # Products at risk
    maintain_count   = (ps_full['Recommended_Action'] == 'Maintain').sum()
    promote_count    = (ps_full['Recommended_Action'] == 'Promote').sum()
    monitor_products = ps_full[ps_full['Recommended_Action'] == 'Monitor']['Product Name'].tolist()
    disc_products    = ps_full[ps_full['Recommended_Action'] == 'Discontinue']['Product Name'].tolist()
    reprice_products = ps_full[ps_full['Recommended_Action'] == 'Reprice']['Product Name'].tolist()
    reneg_products   = ps_full[ps_full['Recommended_Action'] == 'Renegotiate Cost']['Product Name'].tolist()

    # Mean vs median skew
    skew_ratio = mean_s / median_s if median_s else 1
    skew_label = "heavily right-skewed" if skew_ratio > 1.5 else "moderately right-skewed" if skew_ratio > 1.1 else "balanced"

    # ── Card 1: Portfolio Health ───────────────────────────────────────────────
    st.markdown(_assessment_card(
        border_color = '#1D9E75',
        bg_color     = '#f0faf6',
        icon         = '⚠️',
        title        = 'Portfolio Health',
        title_color  = '#0d6e42',
        body         = f'The portfolio reports a {margin_badge.lower()} overall margin, but the headline stability is misleading — '
                       f'the narrow {margin_worst:.1f}%–{margin_best:.1f}% band is anchored by Chocolate\'s volume dominance, which suppresses the portfolio average '
                       f'while Sugar and Other divisions exhibit significant month-to-month swings. '
                       f'This is a product-mix signal, not evidence of pricing discipline.',
        bullets      = [
            f'Revenue is heavily concentrated — two Chocolate products alone exceed 40% of total portfolio revenue, creating an over-dependency risk where a single product underperforming would materially impact overall performance.',
            f'Profit per unit of ${ppu:.2f} reflects Chocolate\'s outsized contribution — Sugar and Other divisions together add marginally to per-unit returns, leaving the portfolio\'s profitability structurally exposed to one division.',
            f'{"<strong>" + " and ".join(monitor_products) + "</strong> are" if monitor_products else "No products are"} trending below the portfolio margin average — not yet in decline, but warranting monthly tracking before {"they cross" if len(monitor_products) > 1 else "it crosses"} into the risk zone.',
        ]
    ), unsafe_allow_html=True)

    # ── Card 2: Division Concentration ────────────────────────────────────────
    st.markdown(_assessment_card(
        border_color = '#7B4F2E',
        bg_color     = '#fdf6f0',
        icon         = '📊',
        title        = 'Division Concentration Risk',
        title_color  = '#5a3218',
        body         = f'<strong>{top_div}</strong> dominates the portfolio with <strong>{top_div_pct:.1f}%</strong> of total revenue '
                       f'at a <strong>{top_div_margin:.1f}%</strong> gross margin. '
                       f'Heavy reliance on a single division creates structural concentration risk — a downturn in {top_div} would materially impact total portfolio performance.',
        bullets      = [f'<strong>{row["Division"]}</strong> — Revenue: ${row["Sales"]:,.0f} | Margin: {row["Margin_Pct"]:.1f}% | Cost ratio: {row["Cost_Pct"]:.1f}%'
                        for _, row in div_data.iterrows()]
    ), unsafe_allow_html=True)

    # ── Card 3: Sales Distribution Insight ────────────────────────────────────
    st.markdown(_assessment_card(
        border_color = '#6C63FF',
        bg_color     = '#f4f3ff',
        icon         = '📈',
        title        = 'Sales Distribution',
        title_color  = '#3b34cc',
        body         = f'Transaction values show a mild skew — mean <strong>${mean_s:.2f}</strong> vs median <strong>${median_s:.2f}</strong> '
                       f'(ratio: <strong>{skew_ratio:.2f}x</strong>). This is a modest gap and not a cause for concern, but it does indicate that '
                       f'a minority of high-value bulk Chocolate orders pull the average above the typical transaction size.',
        bullets      = [
            f'<strong>Median order of ${median_s:.2f}</strong> is the more representative benchmark — most transactions cluster around this value.',
            f'<strong>Mean of ${mean_s:.2f}</strong> is elevated by high-value Chocolate bulk orders — a handful of large orders are doing most of the lifting.',
            f'The gap between mean and median is modest at <strong>{skew_ratio:.2f}x</strong> — this is not a concentration risk at the transaction level, but a shift in Chocolate order patterns could move it materially.',
        ]
    ), unsafe_allow_html=True)

    # ── Card 4: Maintain Products ─────────────────────────────────────────────
    maintain_products = ps_full[ps_full['Recommended_Action'] == 'Maintain']['Product Name'].tolist()
    if maintain_products:
        st.markdown(_assessment_card(
            border_color = '#1D9E75',
            bg_color     = '#f0faf6',
            icon         = '✅',
            title        = f'Core Portfolio — {maintain_count} Products Performing Well',
            title_color  = '#0d6e42',
            body         = (
                f'<strong>{maintain_count} products are operating in the healthy zone</strong>, all within Chocolate — '
                f'strong margins, steady demand, no action required. However, their concentration within a single division '
                f'means portfolio resilience is largely a function of Chocolate\'s stability. '
                f'Diversifying the Maintain tier over time would reduce structural dependency.'
            ),
            bullets      = []
        ), unsafe_allow_html=True)