import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pages_code.utils import load_data, sidebar_filters, build_product_summary, section, chart

DIV = {'Chocolate':'#7B4F2E','Sugar':'#E8963A','Other':'#6C63FF'}
ZONE_COLORS = {
    '🟢 Healthy Zone':   '#1fa66a',
    '🌟 Growth Zone':    '#378ADD',
    '🟡 Watch Zone':     '#e8963a',
    '🔧 Cost Risk Zone': '#c97200',
    '⛔ Critical Zone':  '#6c0d0d',
}

def render():
    df_all = load_data()                   # full unfiltered dataset — source of truth
    df, sel_div = sidebar_filters(df_all)  # filtered — used for charts/tables only

    # ── Build product summaries ───────────────────────────────────────────────
    ps_all = build_product_summary(df_all) # full portfolio — stable thresholds & zones
    ps     = build_product_summary(df)     # filtered — used for charts/tables only

    # Division-only filtered data (ignores product filter)
    df_div = df_all if sel_div == 'All' else df_all[df_all['Division'] == sel_div]
    ps_div = build_product_summary(df_div)

    # Product filter detection
    _product_filtered = set(df['Product Name'].unique()) != set(df_div['Product Name'].unique())
    _sel_products     = set(ps['Product Name'].unique())

    section("Product Profitability",
            "Product-level gross margin ranking to support portfolio rationalisation and pricing decisions")

    if df.empty or ps.empty:
        st.warning("No records found for the selected criteria. Consider revising the filter selections.", icon="⚠️")
        return

    # ── Thresholds derived ONCE from full data — never shift with filters ─────
    _avg_z     = ps_all['Avg_Gross_Margin'].mean()
    _std_z     = ps_all['Avg_Gross_Margin'].std()
    _healthy_t = _avg_z
    _warning_t = _avg_z - _std_z
    _risk_t    = _avg_z - 2 * _std_z

    # ── Zone assignment — same logic as original, applied to full data ────────
    def assign_zone(row):
        action = row['Recommended_Action']
        if action == 'Maintain':          return '🟢 Healthy Zone'
        elif action == 'Promote':         return '🌟 Growth Zone'
        elif action == 'Monitor':         return '🟡 Watch Zone'
        elif action == 'Renegotiate Cost':return '🔧 Cost Risk Zone'
        else:                             return '⛔ Critical Zone'

    ps_all['Zone'] = ps_all.apply(assign_zone, axis=1)

    # Merge stable Zone + Product_Category from ps_all into ps (filtered)
    # so every product always carries its full-data classification
    stable = ps_all[['Product Name', 'Zone', 'Product_Category']].copy()
    ps = ps.drop(columns=[c for c in ['Zone', 'Product_Category'] if c in ps.columns])
    ps = ps.merge(stable, on='Product Name', how='left')

    # ── KPI row ───────────────────────────────────────────────────────────────
    # Cards 1 & 2: best/worst within current filter selection (updates with filter)
    best  = ps.loc[ps['Avg_Gross_Margin'].idxmax()]
    worst = ps.loc[ps['Avg_Gross_Margin'].idxmin()]

    # Cards 3 & 4: count zones within FILTERED ps, but using STABLE zone labels
    # (zones came from ps_all merge, so classifications never shift — only counts update)
    healthy_count  = ps['Zone'].isin(['🟢 Healthy Zone', '🌟 Growth Zone']).sum()
    growth_count   = (ps['Zone'] == '🌟 Growth Zone').sum()
    watch_count    = (ps['Zone'] == '🟡 Watch Zone').sum()
    costrisk_count = (ps['Zone'] == '🔧 Cost Risk Zone').sum()
    critical_count = (ps['Zone'] == '⛔ Critical Zone').sum()
    total_count    = len(ps)
    at_risk_count  = watch_count + costrisk_count + critical_count

    # Card 1 badge: based on the best product's stable zone classification
    _zone_badge_map = {
        '🟢 Healthy Zone':    ("Top performer",   "green"),
        '🌟 Growth Zone':     ("Scale up",        "amber"),
        '🟡 Watch Zone':      ("Watch zone",       "amber"),
        '🔧 Cost Risk Zone':  ("Cost risk",        "amber"),
        '⛔ Critical Zone':   ("Critical — review","red"),
    }
    c1_badge, c1_color = _zone_badge_map.get(best['Zone'], ("Top performer", "green"))

    # Card 2 badge: compare worst product's margin against full-data healthy threshold
    worst_mg = worst['Avg_Gross_Margin']
    if worst_mg >= _healthy_t:
        c2_badge, c2_color = "Stable", "green"
    else:
        c2_badge, c2_color = "Needs review", "red" 

    def _badge(text, color):
        bg = {'green': '#c8f0d4', 'amber': '#fdefc0', 'red': '#fcd8d8'}.get(color, '#c8f0d4')
        fg = {'green': '#145a28', 'amber': '#7a5800', 'red': '#8b1a1a'}.get(color, '#145a28')
        return (
            f'<div style="margin-top:auto;padding-top:6px;">'
            f'<span style="background:{bg};color:{fg};padding:3px 10px;'
            f'border-radius:20px;font-size:0.68rem;font-weight:600;">'
            f'{text}</span></div>'
        )

    def _card(label, value, sub, accent, badge_text=None, badge_color=None, faded=False):
        b = _badge(badge_text, badge_color) if (badge_text and not faded) else ''
        card_value = '—' if faded else value
        card_sub   = '—' if faded else sub
        fade_style = 'opacity:0.45;' if faded else ''
        return (
            f'<div style="background:#fff;border:1px solid #d8d8e8;border-radius:12px;'
            f'padding:14px 14px 12px;border-top:3px solid {accent};position:relative;'
            f'display:flex;flex-direction:column;justify-content:space-between;min-height:150px;box-sizing:border-box;{fade_style}">'
            f'<div style="font-size:0.62rem;letter-spacing:0.10em;text-transform:uppercase;'
            f'color:#1a1a2e;font-weight:700;line-height:1.3;margin-bottom:10px;">{label}</div>'
            f'<div style="font-size:1.55rem;color:#12122a;'
            f'font-family:\'Times New Roman\',Georgia,serif;font-weight:600;letter-spacing:0.01em;'
            f'line-height:1.2;min-height:4.2rem;word-break:break-word;">{card_value}</div>'
            f'<div style="font-size:0.68rem;color:#0a0a1a;line-height:1.3;margin-top:6px;font-weight:600;'
            f'word-break:break-word;">{card_sub}</div>'
            f'{b}</div>'
        )

    single_product = len(ps) == 1
    best_name  = best['Product Name'].split(' - ')[-1]
    worst_name = worst['Product Name'].split(' - ')[-1]

    cards_html = (
        '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;'
        'margin-bottom:16px;align-items:stretch;">'
        + _card("Highest Margin Product", best_name,
                f"Avg Margin: {best['Avg_Gross_Margin']:.1f}%", "#1D9E75", c1_badge, c1_color,
                faded=single_product)
        + _card("Lowest Margin Product", worst_name,
                f"Avg Margin: {worst_mg:.1f}%", "#E24B4A", c2_badge, c2_color,
                faded=single_product)
        + _card("Healthy · Growth Zone", f"{healthy_count} / {total_count}",
                f'🟢 Maintain: {healthy_count - growth_count}  •  🌟 Promote: {growth_count}', "#1D9E75",
                "Strong margin", "green")
        + _card("Watch · Cost Risk · Critical", str(at_risk_count),
                f'🟡 Watch: {watch_count}  •  🔧 Cost Risk: {costrisk_count}<br>⛔ Critical: {critical_count}', "#E8963A",
                "Intervention needed" if at_risk_count > 0 else "All clear",
                "red" if at_risk_count > 0 else "green")
        + '</div>'
    )
    st.markdown(cards_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gross Margin Ranked ───────────────────────────────────────────────────
    chart("Gross Margin % — All Products Ranked",
          "Products ranked by average gross margin; threshold lines indicate performance zones")

    # ── Stable thresholds from full data (never shift with filters) ─────────
    healthy_threshold = round(_healthy_t, 1)
    warning_threshold = round(_warning_t, 1)
    risk_threshold    = round(_risk_t,    1)

    EDA_DIV_COLORS = {'Chocolate': '#7B4F2E', 'Sugar': '#CC5500', 'Other': '#6C63FF'}
    ps_m = ps.sort_values('Avg_Gross_Margin', ascending=True)
    bar_colors = [EDA_DIV_COLORS.get(d, '#999') for d in ps_m['Division']]
    fig = go.Figure(go.Bar(
        x=ps_m['Avg_Gross_Margin'],
        y=ps_m['Product Name'],
        orientation='h',
        marker_color=bar_colors,
        text=ps_m['Avg_Gross_Margin'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside',
        textfont=dict(color='#0d0d0d', size=12),
        showlegend=False,
    ))
    fig.add_vline(x=healthy_threshold, line_dash='dash', line_color='#1a7a4f', line_width=2)
    fig.add_vline(x=warning_threshold, line_dash='dash', line_color='#c97200', line_width=2)
    fig.add_vline(x=risk_threshold, line_dash='dash', line_color='#b52a2a', line_width=2)
    # EDA-matched legend (bottom-right box)
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='lines',
        name=f'✓  Healthy   ≥{healthy_threshold}%',
        line=dict(color='#1a7a4f', width=2, dash='dash'), showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='lines',
        name=f'⚠  Warning  {warning_threshold}%–{healthy_threshold}%',
        line=dict(color='#c97200', width=2, dash='dash'), showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='lines',
        name=f'✗  Risk       <{risk_threshold}%',
        line=dict(color='#b52a2a', width=2, dash='dash'), showlegend=True,
    ))
    fig.update_layout(
        height=480,
        margin=dict(l=0, r=120, t=30, b=0),
        plot_bgcolor='white', paper_bgcolor='white',
        showlegend=True,
        legend=dict(
            orientation='v',
            x=1.0, y=0.0,
            xanchor='right', yanchor='bottom',
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#cccccc', borderwidth=1,
            font=dict(size=13, color='#0d0d0d'),
        ),
        xaxis=dict(
            range=[0, ps_m['Avg_Gross_Margin'].max() * 1.18],
            dtick=10, gridcolor='#e0e0e0',
            tickfont=dict(color='#0d0d0d', size=12),
            title=dict(text='Average Gross Margin (%)', font=dict(color='#0d0d0d', size=13)),
        ),
        yaxis=dict(
            categoryorder='array',
            categoryarray=ps_m['Product Name'].tolist(),
            tickfont=dict(color='#0d0d0d', size=12),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Profit per Unit + Profit Contribution ─────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        chart("Profit per Unit",
              "Gross profit per unit sold — ranked by product")
        # Always use full portfolio values; division filter shows only that division
        _ppu_src = ps_all if sel_div == 'All' else ps_all[ps_all['Division'] == sel_div]
        ppu = _ppu_src.sort_values('Profit_Per_Unit', ascending=True)
        fig2 = go.Figure()
        for _, row in ppu.iterrows():
            is_sel = (not _product_filtered) or (row['Product Name'] in _sel_products)
            alpha  = 1.0 if is_sel else 0.12
            color  = DIV.get(row['Division'], '#999')
            fig2.add_trace(go.Scatter(
                x=[0, row['Profit_Per_Unit']],
                y=[row['Product Name'], row['Product Name']],
                mode='lines',
                line=dict(color=color, width=2 if is_sel else 1,
                          dash='solid' if is_sel else 'dot'),
                opacity=alpha,
                showlegend=False,
                hoverinfo='skip',
            ))
        for div, grp in ppu.groupby('Division'):
            colors = [
                DIV.get(div, '#999') if (not _product_filtered) or (n in _sel_products)
                else 'rgba(200,200,200,0.2)'
                for n in grp['Product Name']
            ]
            opacities = [
                1.0 if (not _product_filtered) or (n in _sel_products) else 0.2
                for n in grp['Product Name']
            ]
            fig2.add_trace(go.Scatter(
                x=grp['Profit_Per_Unit'],
                y=grp['Product Name'],
                mode='markers+text',
                name=div,
                marker=dict(color=colors, size=12, line=dict(width=1.5, color='white'),
                            opacity=opacities),
                text=grp['Profit_Per_Unit'].apply(lambda v: f'${v:.2f}'),
                textposition='middle right',
                textfont=dict(color='#0d0d0d', size=11),
                hovertemplate='%{y}<br>$%{x:.2f}/unit<extra></extra>',
            ))
        fig2.update_layout(
            height=460, margin=dict(l=0, r=100, t=10, b=80),
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(tickprefix='$', gridcolor='#f0f0f0',
                       title=dict(text='Profit per Unit ($)', font=dict(color='#0d0d0d', size=13)),
                       tickfont=dict(color='#0d0d0d', size=12), rangemode='tozero',
                       range=[0, ppu['Profit_Per_Unit'].max() * 1.30]),
            yaxis=dict(tickfont=dict(color='#0d0d0d', size=11), gridcolor='#f0f0f0'),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        chart("Total Profit Contribution",
              "Portfolio profit breakdown — ranked by individual product contribution")
        # Always use full portfolio values; division filter shows only that division
        _pc_src  = ps_all if sel_div == 'All' else ps_all[ps_all['Division'] == sel_div]
        total_p  = ps_all['Total_Profit'].sum()  # always full portfolio denominator
        pc_df    = _pc_src[['Product Name','Division','Total_Profit']].copy()
        pc_df['Profit_%'] = (pc_df['Total_Profit'] / total_p * 100).round(1)
        pc_df = pc_df.sort_values('Profit_%', ascending=True)

        bar_colors = [
            DIV.get(row['Division'], '#999') if (not _product_filtered) or (row['Product Name'] in _sel_products)
            else 'rgba(200,200,200,0.2)'
            for _, row in pc_df.iterrows()
        ]
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=pc_df['Profit_%'], y=pc_df['Product Name'],
            orientation='h',
            marker_color=bar_colors,
            text=pc_df['Profit_%'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            textfont=dict(color='#0d0d0d', size=11),
        ))
        fig3.update_layout(
            height=460, margin=dict(l=0, r=80, t=10, b=40),
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(
                ticksuffix='%', gridcolor='#f0f0f0',
                tickfont=dict(color='#0d0d0d', size=12),
                title=dict(text='Profit Contribution (%)', font=dict(color='#0d0d0d', size=13)),
                range=[0, pc_df['Profit_%'].max() * 1.40],
            ),
            yaxis=dict(tickfont=dict(color='#0d0d0d', size=11)),
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Shared legend for both charts above
    DIV_LABELS = {'Chocolate': '#7B4F2E', 'Sugar': '#E8963A', 'Other': '#6C63FF'}
    legend_html = '<div style="display:flex;justify-content:center;gap:28px;margin-top:4px;margin-bottom:16px;">'
    for label, color in DIV_LABELS.items():
        legend_html += (
            f'<span style="display:flex;align-items:center;gap:7px;font-size:13px;color:#0d0d0d;font-weight:500;">'
            f'<span style="width:13px;height:13px;border-radius:3px;background:{color};display:inline-block;"></span>'
            f'{label}</span>'
        )
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)

    # ── Product Quadrant ──────────────────────────────────────────────────────
    chart("Product Quadrant Analysis — Sales vs Margin",
          "Products positioned by total sales, gross margin and unit volume across all divisions")

    # Always use full portfolio — medians and positions never shift with filters
    import numpy as np
    ps_q = ps_all.copy()
    ps_q['_bubble_size'] = np.sqrt(ps_q['Total_Units'])
    # Match px.scatter size_max=28: sizeref = 2 * max / (size_max^2)
    _sizeref = 2. * ps_q['_bubble_size'].max() / (28 ** 2)
    sm = ps_all['Total_Sales'].median()
    mm = ps_all['Avg_Gross_Margin'].median()

    # Use px.scatter exactly as original — preserves size_max=28 bubble sizing
    fig_q = px.scatter(ps_q, x='Total_Sales', y='Avg_Gross_Margin',
                       size='_bubble_size', color='Division',
                       hover_name='Product Name',
                       color_discrete_map=DIV, size_max=28, opacity=0.85,
                       labels={'Total_Sales':'Total Sales ($)',
                               'Avg_Gross_Margin':'Avg Gross Margin (%)','Division':''})

    # Apply per-bubble highlight/fade by patching marker colors to rgba
    # (px.scatter sets uniform opacity; we override per-point via color strings)
    for trace in fig_q.data:
        div = trace.name
        clr = DIV.get(div, '#999')
        hex_c = clr.lstrip('#')
        r, g, b = int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)
        # Reconstruct per-point colors with correct opacity
        names = ps_q[ps_q['Division'] == div]['Product Name'].tolist()
        colors = []
        for name in names:
            if _product_filtered or sel_div != 'All':
                op = 0.85 if name in _sel_products else 0.08
            elif sel_div != 'All':
                op = 0.85 if (ps_q.loc[ps_q['Product Name']==name, 'Division'].iloc[0] == sel_div) else 0.08
            else:
                op = 0.85
            colors.append(f'rgba({r},{g},{b},{op})')
        trace.marker.color = colors
        trace.marker.line  = dict(width=1.5, color='white')

    fig_q.add_vline(x=sm, line_dash='dot', line_color='#555555', line_width=1.5)
    fig_q.add_hline(y=mm, line_dash='dot', line_color='#555555', line_width=1.5)
    fig_q.add_annotation(x=ps_all['Total_Sales'].max()*0.85, y=ps_all['Avg_Gross_Margin'].max()*0.97,
                          text="High Sales / High Margin", showarrow=False,
                          font=dict(color='#0d6e42', size=11, family='DM Sans'))
    fig_q.add_annotation(x=ps_all['Total_Sales'].max()*0.85, y=mm*0.5,
                          text="High Sales / Low Margin", showarrow=False,
                          font=dict(color='#b86200', size=11, family='DM Sans'))
    fig_q.add_annotation(x=sm*0.1, y=ps_all['Avg_Gross_Margin'].max()*0.97,
                          text="Low Sales / High Margin", showarrow=False,
                          font=dict(color='#3b34cc', size=11, family='DM Sans'))
    fig_q.add_annotation(x=sm*0.1, y=mm*0.5,
                          text="Low Sales / Low Margin", showarrow=False,
                          font=dict(color='#b52020', size=11, family='DM Sans'))
    fig_q.update_layout(height=400, margin=dict(l=0,r=0,t=10,b=0),
                        plot_bgcolor='white', paper_bgcolor='white',
                        legend=dict(orientation='h', y=1.08, title='',
                                    font=dict(color='#0d0d0d', size=12)))
    fig_q.update_xaxes(tickprefix='$', gridcolor='#f0f0f0',
                       tickfont=dict(color='#0d0d0d', size=12),
                       title=dict(text='Total Sales ($)', font=dict(color='#0d0d0d', size=13)))
    fig_q.update_yaxes(ticksuffix='%', gridcolor='#f0f0f0',
                       tickfont=dict(color='#0d0d0d', size=12),
                       title=dict(text='Avg Gross Margin (%)', font=dict(color='#0d0d0d', size=13)))
    st.plotly_chart(fig_q, use_container_width=True)
    # ── Leaderboard Table ─────────────────────────────────────────────────────
    chart("Product Margin Leaderboard",
          "Comprehensive product-level profitability metrics ranked by gross margin")

    _zone_order = ['🟢 Healthy Zone','🌟 Growth Zone','🟡 Watch Zone','🔧 Cost Risk Zone','⛔ Critical Zone']
    ps['_zone_rank'] = ps['Zone'].map({z: i for i, z in enumerate(_zone_order)})
    display = ps.sort_values(['_zone_rank', 'Avg_Gross_Margin'], ascending=[True, False]).drop(columns='_zone_rank')[[
        'Division','Product Name','Avg_Gross_Margin','Order_Count',
        'Total_Units','Profit_Per_Unit','Total_Sales','Total_Profit',
        'Product_Category','Zone'
    ]].rename(columns={
        'Avg_Gross_Margin':'Margin %','Total_Sales':'Total Sales',
        'Total_Profit':'Total Profit','Profit_Per_Unit':'Profit/Unit',
        'Total_Units':'Units','Order_Count':'Orders',
        'Product_Category':'Category','Zone':'Zone'
    })

    ZONE_BG = {
        '🟢 Healthy Zone':    '#f0faf4',
        '🌟 Growth Zone':     '#eaf4ff',
        '🟡 Watch Zone':      '#fffbea',
        '🔧 Cost Risk Zone':  '#fff4e0',
        '⛔ Critical Zone':   '#fce8e8',
    }

    def _fmt(col, val):
        if col == 'Margin %':    return f"{val:.1f}%"
        if col == 'Total Sales': return f"${val:,.0f}"
        if col == 'Total Profit':return f"${val:,.0f}"
        if col == 'Profit/Unit': return f"${val:.2f}"
        return str(val)

    cols = list(display.columns)
    col_w = {
        'Division': 100, 'Product Name': 200,
        'Margin %': 80, 'Total Sales': 90, 'Total Profit': 95,
        'Profit/Unit': 95, 'Units': 65, 'Orders': 65,
        'Category': 160, 'Zone': 145,
    }

    th_base = (
        "position:sticky;top:0;z-index:2;"
        "background:#f0f0f8;color:#1a1a2e;font-size:0.72rem;"
        "font-weight:700;letter-spacing:0.04em;text-transform:uppercase;"
        "padding:8px 10px;border-bottom:2px solid #d0d0e0;white-space:nowrap;"
        "text-align:center;"
    )
    td_base = "padding:7px 10px;font-size:0.78rem;color:#0a0a1a;white-space:nowrap;text-align:center;border-bottom:1px solid #ebebf4;"

    header = "<tr>"
    for i, c in enumerate(cols):
        w = col_w.get(c, 100)
        sticky = ""
        z_idx = ""
        if i == 0:   sticky = "left:0px;border-right:1px solid #d0d0e0;";  z_idx = "z-index:4;"
        elif i == 1: sticky = "left:100px;border-right:2px solid #b0b0cc;"; z_idx = "z-index:4;"
        header += f'<th style="{th_base}{sticky}{z_idx}min-width:{w}px;max-width:{w}px;">{c}</th>'
    header += "</tr>"

    rows_html = ""
    for _, row in display.iterrows():
        zone = row['Zone']
        bg = ZONE_BG.get(zone, '#ffffff')
        rows_html += "<tr>"
        for i, c in enumerate(cols):
            val = _fmt(c, row[c])
            sticky = ""
            z_idx = ""
            if i == 0:   sticky = f"position:sticky;left:0px;background:{bg};border-right:1px solid #d0d0e0;";   z_idx = "z-index:1;"
            elif i == 1: sticky = f"position:sticky;left:100px;background:{bg};border-right:2px solid #b0b0cc;";  z_idx = "z-index:1;"
            else:        sticky = f"background:{bg};"
            align = "text-align:left;" if c == 'Product Name' else ""
            rows_html += f'<td style="{td_base}{sticky}{z_idx}{align}">{val}</td>'
        rows_html += "</tr>"

    import base64
    csv_data = display.to_csv(index=False)
    b64 = base64.b64encode(csv_data.encode()).decode()
    download_link = f'<a href="data:text/csv;base64,{b64}" download="product_margin_leaderboard.csv" style="display:block;text-align:right;font-size:0.75rem;color:#aaa;text-decoration:none;opacity:0.35;transition:opacity 0.2s;margin-bottom:2px;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.35">⬇️</a>'

    table_html = f"""
    <div>
      {download_link}
      <div style="overflow-x:auto;overflow-y:auto;max-height:460px;
                  border:1px solid #d0d0e0;border-radius:8px;">
        <table style="border-collapse:collapse;width:max-content;min-width:100%;">
          <thead>{header}</thead>
          <tbody>{rows_html}</tbody>
        </table>
      </div>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)

    # ── Product Portfolio Assessment — 3 Insight Cards ───────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    chart("Product Portfolio Assessment",
          "Key signals from margin ranking, profit efficiency and quadrant positioning")
    if _product_filtered or sel_div != 'All':
        st.markdown(
            "<p style='font-size:0.75rem;color:#888;margin:-6px 0 8px;'>"
            "📌 Assessment reflects full portfolio — unaffected by filter selection"
            "</p>",
            unsafe_allow_html=True,
        )
        st.markdown('<div style="margin-bottom:16px;"></div>', unsafe_allow_html=True)

    # ── All derived from ps_all — stable, unaffected by filter ───────────────
    _total_profit = ps_all['Total_Profit'].sum()
    _total_sales  = ps_all['Total_Sales'].sum()
    _bench        = ps_all['Avg_Gross_Margin'].mean()

    # Card 1 — Margin Leadership
    _top    = ps_all.loc[ps_all['Avg_Gross_Margin'].idxmax()]
    _bottom = ps_all.loc[ps_all['Avg_Gross_Margin'].idxmin()]
    _top_name    = _top['Product Name'].split(' - ')[-1]
    _bot_name    = _bottom['Product Name'].split(' - ')[-1]
    _spread      = _top['Avg_Gross_Margin'] - _bottom['Avg_Gross_Margin']
    _above_bench = (ps_all['Avg_Gross_Margin'] >= _bench).sum()
    _below_bench = len(ps_all) - _above_bench

    # Card 2 — Profit Engine
    ps_all_s = ps_all.copy()
    ps_all_s['_profit_share'] = ps_all_s['Total_Profit'] / _total_profit * 100
    ps_all_s = ps_all_s.sort_values('_profit_share', ascending=False)
    _top2      = ps_all_s.iloc[:2]
    _top2_share = _top2['_profit_share'].sum()
    _top2_names = ' & '.join(_top2['Product Name'].str.split(' - ').str[-1].tolist())
    _top1_ppu   = ps_all_s.iloc[0]['Profit_Per_Unit']
    _bot_ppu    = ps_all.loc[ps_all['Profit_Per_Unit'].idxmin()]
    _bot_ppu_name = _bot_ppu['Product Name'].split(' - ')[-1]
    _ppu_gap    = ps_all_s.iloc[0]['Profit_Per_Unit'] - _bot_ppu['Profit_Per_Unit']

    # Card 3 — Quadrant Tension
    _sm = ps_all['Total_Sales'].median()
    _mm = ps_all['Avg_Gross_Margin'].median()
    _hi_s_lo_m = ps_all[(ps_all['Total_Sales'] >= _sm) & (ps_all['Avg_Gross_Margin'] < _mm)]
    _lo_s_hi_m = ps_all[(ps_all['Total_Sales'] <  _sm) & (ps_all['Avg_Gross_Margin'] >= _mm)]
    _hi_s_hi_m = ps_all[(ps_all['Total_Sales'] >= _sm) & (ps_all['Avg_Gross_Margin'] >= _mm)]
    _leakage   = _hi_s_lo_m['Total_Sales'].sum() / _total_sales * 100
    _hs_hm_names = ', '.join(_hi_s_hi_m['Product Name'].str.split(' - ').str[-1].tolist()) or '—'
    _hs_lm_names = ', '.join(_hi_s_lo_m['Product Name'].str.split(' - ').str[-1].tolist()) or 'None'
    _lo_hi_names = ', '.join(_lo_s_hi_m['Product Name'].str.split(' - ').str[-1].tolist()) or 'None'

    def _insight_card(title, icon, accent, badge_text, badge_bg, badge_fg,
                      stat_pairs, narrative, action_text, action_color, bg_color='#fff'):
        # Inline metrics bar — same style as p3 division cards
        metrics_html = ' &nbsp;|&nbsp; '.join(
            f'<span style="color:#666;font-size:0.75rem;">{l}: </span>'
            f'<span style="font-size:0.75rem;font-weight:700;color:#12122a;">{v}</span>'
            for l, v in stat_pairs
        )
        return f"""
<div style="background:{bg_color};border:1px solid #e4e4ee;border-left:4px solid {accent};
            border-radius:10px;padding:18px 22px 16px 20px;margin-bottom:14px;
            box-shadow:0 1px 4px rgba(0,0,0,0.05);">
  <div style="display:flex;align-items:center;justify-content:space-between;
              flex-wrap:wrap;gap:8px;margin-bottom:10px;">
    <div style="display:flex;align-items:center;gap:10px;">
      <span style="font-size:1.0rem;">{icon}</span>
      <span style="font-size:0.95rem;font-weight:600;color:#12122a;">{title}</span>
      <span style="background:{badge_bg};color:{badge_fg};padding:3px 11px;border-radius:20px;
                   font-size:0.68rem;font-weight:700;">{badge_text}</span>
    </div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">
      {metrics_html}
    </div>
  </div>
  <div style="font-size:0.82rem;color:#2a2a3a;line-height:1.65;margin-bottom:10px;">
    {narrative}
  </div>
  <div style="font-size:0.72rem;font-weight:700;color:{action_color};
              letter-spacing:0.02em;text-align:right;">→ {action_text}</div>
</div>"""

    # ── Card 1: Margin Leadership ─────────────────────────────────────────────
    c1 = _insight_card(
        title   = "Margin Leadership",
        icon    = "📊",
        accent  = "#1fa66a",
        badge_text = f"{_above_bench} above benchmark",
        badge_bg   = "#d1f5e0", badge_fg = "#0e5c2a",
        stat_pairs = [
            ("Top Margin",    f"{_top['Avg_Gross_Margin']:.1f}%"),
            ("Bottom Margin", f"{_bottom['Avg_Gross_Margin']:.1f}%"),
            ("Spread",        f"{_spread:.1f}pp"),
            ("Benchmark",     f"{_bench:.1f}%"),
        ],
        narrative = (
            f"<strong>{_top_name}</strong> leads the portfolio at <strong>{_top['Avg_Gross_Margin']:.1f}%</strong> gross margin, "
            f"while <strong>{_bot_name}</strong> sits at the bottom at {_bottom['Avg_Gross_Margin']:.1f}% — "
            f"a <strong>{_spread:.1f}pp spread</strong> across the range. "
            f"{_above_bench} of {len(ps_all)} products clear the portfolio benchmark of {_bench:.1f}%, "
            f"with {_below_bench} requiring margin attention."
        ),
        action_text  = f"Protect {_top_name} pricing · address {_bot_name} margin gap",
        action_color = "#1fa66a",
        bg_color     = "#f0faf6",
    )

    # ── Card 2: Profit Engine ─────────────────────────────────────────────────
    _engine_badge_color = "#d1f5e0" if _top2_share >= 70 else "#fdefc0"
    _engine_badge_fg    = "#0e5c2a" if _top2_share >= 70 else "#7a5800"
    c2 = _insight_card(
        title   = "Profit Engine",
        icon    = "⚡",
        accent  = "#378ADD",
        badge_text = f"Top 2 drive {_top2_share:.0f}% of profit",
        badge_bg   = _engine_badge_color, badge_fg = _engine_badge_fg,
        stat_pairs = [
            ("Top Profit/Unit",  f"${ps_all_s.iloc[0]['Profit_Per_Unit']:.2f}"),
            ("Lowest Profit/Unit", f"${_bot_ppu['Profit_Per_Unit']:.2f}"),
            ("Efficiency Gap",   f"${_ppu_gap:.2f}"),
            ("Top 2 Share",      f"{_top2_share:.1f}%"),
        ],
        narrative = (
            f"<strong>{_top2_names}</strong> together account for "
            f"<strong>{_top2_share:.1f}%</strong> of total portfolio profit — "
            f"a highly concentrated profit base. "
            f"Profit per unit ranges from <strong>${ps_all_s.iloc[0]['Profit_Per_Unit']:.2f}</strong> "
            f"down to <strong>${_bot_ppu['Profit_Per_Unit']:.2f}</strong> ({_bot_ppu_name}), "
            f"a <strong>${_ppu_gap:.2f} efficiency gap</strong> that signals uneven unit economics across the range."
        ),
        action_text  = f"Prioritise volume on top earners · review {_bot_ppu_name} unit economics",
        action_color = "#378ADD",
        bg_color     = "#f0f5ff",
    )

    # ── Card 3: Quadrant Tension ──────────────────────────────────────────────
    _tension_badge = "Leakage risk" if len(_hi_s_lo_m) > 0 else "Well positioned"
    _tension_bg    = "#fcd8d8" if len(_hi_s_lo_m) > 0 else "#d1f5e0"
    _tension_fg    = "#8b1a1a" if len(_hi_s_lo_m) > 0 else "#0e5c2a"
    # Split high-sales/low-margin by actual zone action
    _reprice_prods   = _hi_s_lo_m[_hi_s_lo_m['Recommended_Action'].isin(['Reprice','Discontinue','Renegotiate Cost'])]
    _monitor_prods   = _hi_s_lo_m[_hi_s_lo_m['Recommended_Action'].isin(['Monitor','Promote','Maintain'])]
    _reprice_names   = ', '.join(_reprice_prods['Product Name'].str.split(' - ').str[-1].tolist())
    _monitor_names   = ', '.join(_monitor_prods['Product Name'].str.split(' - ').str[-1].tolist())
    _lo_hi_names_all = ', '.join(_lo_s_hi_m['Product Name'].str.split(' - ').str[-1].tolist()) or 'None'
    _action_parts = []
    if _reprice_names:          _action_parts.append(f"Reprice {_reprice_names}")
    if _monitor_names:          _action_parts.append(f"Monitor {_monitor_names}")
    if _lo_hi_names_all != 'None': _action_parts.append(f"Promote {_lo_hi_names_all}")
    _qt_action = ' · '.join(_action_parts) if _action_parts else f"Expand volume on {_lo_hi_names_all}"

    c3 = _insight_card(
        title   = "Quadrant Tension",
        icon    = "🎯",
        accent  = "#e8963a" if len(_hi_s_lo_m) > 0 else "#1fa66a",
        badge_text = _tension_badge,
        badge_bg   = _tension_bg, badge_fg = _tension_fg,
        stat_pairs = [
            ("High Sales · High Margin", str(len(_hi_s_hi_m))),
            ("High Sales · Low Margin",  str(len(_hi_s_lo_m))),
            ("Low Sales · High Margin",  str(len(_lo_s_hi_m))),
            ("Revenue at Risk",          f"{_leakage:.1f}%"),
        ],
        narrative = (
            f"<strong>{len(_hi_s_hi_m)} product{'s' if len(_hi_s_hi_m)!=1 else ''}</strong> "
            f"({_hs_hm_names}) sit in the ideal quadrant — high sales and high margin. "
            + (f"However, <strong>{len(_hi_s_lo_m)} product{'s' if len(_hi_s_lo_m)!=1 else ''}</strong> "
               f"({_hs_lm_names}) generate strong revenue but weak margin, "
               f"representing <strong>{_leakage:.1f}% of total revenue at risk</strong> of profit leakage"
               + (f" — {_reprice_names} require repricing" if _reprice_names else "")
               + (f"; {_monitor_names} flagged for monitoring" if _monitor_names else "")
               + ". "
               if len(_hi_s_lo_m) > 0 else "") +
            (f"{len(_lo_s_hi_m)} high-margin product{'s' if len(_lo_s_hi_m)!=1 else ''} "
             f"({_lo_hi_names_all}) have volume upside — these are the primary promote candidates."
             if len(_lo_s_hi_m) > 0 else "")
        ),
        action_text  = _qt_action,
        action_color = "#e8963a" if len(_hi_s_lo_m) > 0 else "#1fa66a",
        bg_color     = "#fff8f0" if len(_hi_s_lo_m) > 0 else "#f0faf6",
    )

    st.markdown(c1 + c2 + c3, unsafe_allow_html=True)