import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pages_code.utils import load_data, sidebar_filters, build_product_summary, kpi_card, section, chart

DIV = {'Chocolate':'#7B4F2E','Sugar':'#E8963A','Other':'#6C63FF'}

def render():
    df  = load_data()
    df, sel_div = sidebar_filters(df, show_product_filter=False)

    section("Division Performance",
            "Divisional revenue, profitability and margin efficiency benchmarking")

    if df.empty:
        st.warning("No records found for the selected criteria. Consider revising the filter selections.", icon="⚠️")
        return

    div_summary = df.groupby('Division').agg(
        Avg_Margin   =('Gross_Margin_Pct','mean'),
        Total_Sales  =('Sales','sum'),
        Total_Profit =('Gross Profit','sum'),
        Total_Cost   =('Cost','sum'),
        Total_Units  =('Units','sum'),
        Order_Count  =('Order ID','count'),
    ).round(2).reset_index()
    div_summary['Profit_Per_Unit'] = (div_summary['Total_Profit'] / div_summary['Total_Units']).round(2)
    div_summary['Revenue_Share']   = (div_summary['Total_Sales']  / div_summary['Total_Sales'].sum()  * 100).round(1)
    div_summary['Profit_Share']    = (div_summary['Total_Profit'] / div_summary['Total_Profit'].sum() * 100).round(1)

    # ── Full-portfolio summary — source of truth for all stable metrics ─────
    df_all = load_data()
    div_summary_all = df_all.groupby('Division').agg(
        Avg_Margin   =('Gross_Margin_Pct','mean'),
        Total_Sales  =('Sales','sum'),
        Total_Profit =('Gross Profit','sum'),
        Total_Cost   =('Cost','sum'),
        Total_Units  =('Units','sum'),
        Order_Count  =('Order ID','count'),
    ).round(2).reset_index()
    div_summary_all['Profit_Per_Unit'] = (div_summary_all['Total_Profit'] / div_summary_all['Total_Units']).round(2)
    div_summary_all['Revenue_Share']   = (div_summary_all['Total_Sales']  / div_summary_all['Total_Sales'].sum()  * 100).round(1)
    div_summary_all['Profit_Share']    = (div_summary_all['Total_Profit'] / div_summary_all['Total_Profit'].sum() * 100).round(1)

    # ── Division KPI cards ────────────────────────────────────────────────────
    cols = st.columns(3)
    for i, (_, row) in enumerate(div_summary.iterrows()):
        clr = list(DIV.values())[i]
        with cols[i]:
            st.markdown(f'''
<div style="background:#ffffff;border:1px solid #d8d8e8;border-radius:12px;
            padding:18px 14px 16px 14px;display:flex;flex-direction:column;gap:4px;
            box-sizing:border-box;margin-bottom:4px;border-top:3px solid {clr};
            min-height:175px;">
  <div style="font-size:0.62rem;letter-spacing:0.10em;text-transform:uppercase;
              color:#1a1a2e;font-weight:700;line-height:1.45;min-height:2.5em;
              margin-bottom:2px;">{row["Division"]}</div>
  <div style="font-size:1.60rem;color:#12122a;line-height:1.1;font-weight:600;
              font-family:'Times New Roman',Georgia,serif;white-space:nowrap;overflow:hidden;
              text-overflow:ellipsis;">{row["Avg_Margin"]:.1f}%</div>
  <div style="font-size:0.70rem;color:#4a4a68;font-style:italic;line-height:1.35;
              min-height:1.9em;">Avg Gross Margin</div>
  <div style="font-size:0.72rem;color:#0a0a1a;font-weight:600;line-height:1.4;
              min-height:2.0em;">Revenue: ${row["Total_Sales"]:,.0f}&nbsp;&nbsp;|&nbsp;&nbsp;Profit: ${row["Total_Profit"]:,.0f}</div>
</div>''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Revenue vs Profit grouped bar ─────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        chart("Revenue vs Gross Profit by Division",
              "Division-level view of revenue earned vs gross profit captured")

        div_sorted = div_summary.sort_values('Total_Sales', ascending=False).reset_index(drop=True)

        fig = go.Figure()

        # Sales bars — showlegend=False (dummy scatter handles legend)
        fig.add_trace(go.Bar(
            name='Total Sales',
            x=div_sorted['Division'],
            y=div_sorted['Total_Sales'],
            marker_color=[DIV.get(d, '#888') for d in div_sorted['Division']],
            opacity=1.0,
            text=[f"${v:,.0f}" for v in div_sorted['Total_Sales']],
            textposition='outside',
            textfont=dict(size=10, color='#000000', family='DM Sans, sans-serif'),
            cliponaxis=False,
            width=0.35,
            offsetgroup='sales',
            showlegend=False,
        ))

        fig.add_trace(go.Bar(
            name='Total Profit',
            x=div_sorted['Division'],
            y=div_sorted['Total_Profit'],
            marker=dict(
                color=[DIV.get(d, '#888888') for d in div_sorted['Division']],
                opacity=0.55,
            ),
            text=[f"${v:,.0f}" for v in div_sorted['Total_Profit']],
            textposition='outside',
            textfont=dict(size=9, color='#000000', family='DM Sans, sans-serif'),
            outsidetextfont=dict(size=9, color='#000000', family='DM Sans, sans-serif'),
            insidetextfont=dict(size=9, color='#000000', family='DM Sans, sans-serif'),
            cliponaxis=False,
            width=0.35,
            offsetgroup='profit',
            showlegend=False,
        ))

        # Row 1: division colour patches → legend (default)
        for div, color in DIV.items():
            if div in div_sorted['Division'].values:
                fig.add_trace(go.Scatter(
                    name=div, x=[None], y=[None], mode='markers',
                    marker=dict(symbol='square', size=10, color=color),
                    showlegend=True,
                    legend='legend',
                ))
        # Row 2: shade explanation → legend2
        fig.add_trace(go.Scatter(
            name='Total Sales (dark shade)', x=[None], y=[None], mode='markers',
            marker=dict(symbol='square', size=10, color='#555555'),
            showlegend=True,
            legend='legend2',
        ))
        fig.add_trace(go.Scatter(
            name='Total Profit (light shade)', x=[None], y=[None], mode='markers',
            marker=dict(symbol='square', size=10, color='#aaaaaa'),
            showlegend=True,
            legend='legend2',
        ))

        fig.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(color='#0a0a1a', family='DM Sans, sans-serif', size=11),
            barmode='group',
            bargroupgap=0.20,
            bargap=0.35,
            height=400,
            margin=dict(l=10, r=20, t=30, b=30),
            legend=dict(
                orientation='h', y=1.20, x=0,
                font=dict(size=11, color='#0a0a1a'),
                itemsizing='constant',
            ),
            legend2=dict(
                orientation='h', y=1.08, x=0,
                font=dict(size=11, color='#0a0a1a'),
                itemsizing='constant',
            ),
            yaxis=dict(
                tickprefix='$', tickformat=',.0f', gridcolor='#ebebf0',
                tickfont=dict(color='#0a0a1a', size=11),
                title=dict(text='Amount ($)', font=dict(color='#0a0a1a', size=12)),
                range=[0, div_sorted['Total_Sales'].max() * 1.28],
            ),
        )
        fig.update_xaxes(
            tickfont=dict(color='#0a0a1a', size=13, family='DM Sans, sans-serif'),
            showgrid=False, type='category',
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        chart("Gross Margin % Distribution",
              "Gross margin distribution by division — spread indicates consistency; outliers reflect structural pricing risk")
        fig2 = px.box(df, x='Division', y='Gross_Margin_Pct',
                      color='Division', points='outliers',
                      color_discrete_map=DIV,
                      labels={'Gross_Margin_Pct':'Gross Margin (%)','Division':''})
        fig2.update_layout(height=400, margin=dict(l=0,r=0,t=10,b=0),
                           plot_bgcolor='white', paper_bgcolor='white', showlegend=False,
                           xaxis=dict(tickfont=dict(color='#0a0a1a', size=12)),
                           yaxis=dict(tickfont=dict(color='#0a0a1a', size=12),
                                      title=dict(font=dict(color='#0a0a1a', size=12))))
        fig2.update_yaxes(ticksuffix='%', gridcolor='#f0f0f0', tickfont=dict(color='#0a0a1a', size=12))
        fig2.update_xaxes(tickfont=dict(color='#0a0a1a', size=12))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Revenue Share vs Profit Share ─────────────────────────────────────────
    chart("Revenue Share vs Profit Share",
          "Divisions where profit share trails revenue share exhibit structural margin inefficiency")

    # Pie charts always show the full portfolio; selected division is highlighted,
    # others are faded — so the share context is never lost when filtering.
    pie_note = "" if sel_div == 'All' else (
        f'<div style="font-size:0.72rem;color:#6c63ff;font-style:italic;margin-bottom:8px;">'
        f'📌 Showing full portfolio — <strong>{sel_div}</strong> highlighted</div>'
    )
    if pie_note:
        st.markdown(pie_note, unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    for col, field, title in [(col3,'Revenue_Share','Revenue Share'),(col4,'Profit_Share','Profit Share')]:
        with col:
            # Build per-slice colours: full colour for selected, greyed + faded for others
            slice_colors = []
            slice_opacities = []
            for d in div_summary_all['Division']:
                is_selected = (sel_div == 'All' or d == sel_div)
                slice_colors.append(DIV.get(d, '#888888') if is_selected else '#cccccc')
                slice_opacities.append(1.0 if is_selected else 0.25)

            fig_p = go.Figure(go.Pie(
                labels=div_summary_all['Division'],
                values=div_summary_all[field],
                hole=0.50,
                marker=dict(
                    colors=slice_colors,
                    line=dict(color='white', width=2),
                ),
                opacity=1.0,
                textinfo='label+percent',
                insidetextorientation='horizontal',
            ))

            # Apply per-slice opacity via customdata trick using individual trace colours with alpha
            # Plotly Pie doesn't support per-slice opacity natively, so we encode it into the color
            import re
            def hex_with_alpha(hex_color, alpha):
                hex_color = hex_color.lstrip('#')
                r, g, b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
                return f'rgba({r},{g},{b},{alpha})'

            slice_colors_rgba = [
                hex_with_alpha(DIV.get(d, '#888888'), 1.0) if (sel_div == 'All' or d == sel_div)
                else hex_with_alpha('#bbbbbb', 0.25)
                for d in div_summary_all['Division']
            ]
            fig_p.update_traces(marker=dict(colors=slice_colors_rgba, line=dict(color='white', width=2)))

            # Text colour: white inside highlighted slices, muted for faded ones
            text_colors = []
            for i, (d, v) in enumerate(zip(div_summary_all['Division'], div_summary_all[field])):
                is_selected = (sel_div == 'All' or d == sel_div)
                text_colors.append('white' if (is_selected and v >= 2) else '#999999')

            positions = ['outside' if v < 2 else 'inside' for v in div_summary_all[field]]
            fig_p.update_traces(
                textposition=positions,
                textfont=dict(size=12, color=text_colors),
            )
            fig_p.update_layout(
                height=340, margin=dict(l=30,r=30,t=30,b=20),
                title=dict(text=title, font_size=12),
                showlegend=True,
                legend=dict(font=dict(color='#0a0a1a')),
            )
            st.plotly_chart(fig_p, use_container_width=True)

    # ── Avg Margin bar ────────────────────────────────────────────────────────
    chart("Average Gross Margin % by Division",
          "Divisional gross margin performance measured against the cross-division average benchmark")
    fig3 = go.Figure()
    div_avg = div_summary['Avg_Margin'].mean()
    fig3.add_bar(x=div_summary['Division'], y=div_summary['Avg_Margin'],
                 marker_color=[DIV[d] for d in div_summary['Division']],
                 text=[f"{v:.1f}%" for v in div_summary['Avg_Margin']],
                 textposition='outside', opacity=0.9,
                 textfont=dict(size=12, color='#0a0a1a', family='DM Sans, sans-serif'))
    fig3.add_hline(y=div_avg, line_dash='dash', line_color='#0a6640', line_width=2,
                   annotation_text=f'Division avg ({div_avg:.1f}%)', annotation_font_color='#0a6640')
    fig3.update_layout(height=280, margin=dict(l=0,r=0,t=0,b=0),
                       plot_bgcolor='white', paper_bgcolor='white',
                       font=dict(color='#0a0a1a', family='DM Sans, sans-serif'),
                       yaxis=dict(ticksuffix='%', gridcolor='#f0f0f0', range=[0,75],
                                  tickfont=dict(color='#0a0a1a', size=12),
                                  title=dict(font=dict(color='#0a0a1a', size=12))),
                       xaxis=dict(tickfont=dict(color='#0a0a1a', size=12)),
                       showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

    # ── Summary Table ─────────────────────────────────────────────────────────
    chart("Division Summary Table",
          "Aggregated financial performance metrics by business division")

    # Pre-compute margin colours from full dataset so they never shift with filter
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    _cmap   = plt.get_cmap('RdYlGn')
    _vmin   = div_summary_all['Avg_Margin'].min()
    _vmax   = div_summary_all['Avg_Margin'].max()
    _norm   = mcolors.Normalize(vmin=_vmin, vmax=_vmax)
    _colors = {row['Division']: mcolors.to_hex(_cmap(_norm(row['Avg_Margin'])))
               for _, row in div_summary_all.iterrows()}

    def _margin_bg(val_series):
        # val_series is the 'Avg Margin %' column of the display df (already renamed)
        return [f'background-color: {_colors.get(div, "#ffffff")}; color: #0a0a1a'
                for div in div_summary_display["Division"]]

    div_summary_display = div_summary_all if sel_div == 'All' else div_summary_all[div_summary_all['Division'] == sel_div]
    _renamed = div_summary_display.rename(columns={
            'Avg_Margin':'Avg Margin %','Total_Sales':'Total Sales',
            'Total_Profit':'Total Profit','Total_Cost':'Total Cost',
            'Total_Units':'Units','Order_Count':'Orders',
            'Profit_Per_Unit':'Profit/Unit',
            'Revenue_Share':'Rev Share %','Profit_Share':'Profit Share %'
        })[['Division','Avg Margin %','Units','Orders','Total Sales','Total Cost','Total Profit','Profit/Unit','Rev Share %','Profit Share %']]
    st.dataframe(
        _renamed.style.format({
            'Avg Margin %':   '{:.1f}%',
            'Total Sales':    '${:,.0f}',
            'Total Profit':   '${:,.0f}',
            'Total Cost':     '${:,.0f}',
            'Profit/Unit':    '${:.2f}',
            'Rev Share %':    '{:.1f}%',
            'Profit Share %': '{:.1f}%',
        }).apply(_margin_bg, subset=['Avg Margin %']),
        use_container_width=True)

    # ── Financial Efficiency & Structural Margin Assessment ───────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    chart("Financial Efficiency & Structural Margin Assessment",
          "Identifies divisions with strong financial efficiency versus those with structural margin issues")

    DIV_COLORS_LOCAL = {'Chocolate':'#7B4F2E','Sugar':'#E8963A','Other':'#6C63FF'}

    div_avg = div_summary_all['Avg_Margin'].mean()

    div_summary_fe = div_summary_all if sel_div == 'All' else div_summary_all[div_summary_all['Division'] == sel_div]
    for _, row in div_summary_fe.iterrows():
        div   = row['Division']
        marg  = row['Avg_Margin']
        rev_s = row['Revenue_Share']
        pft_s = row['Profit_Share']
        gap   = rev_s - pft_s
        diff  = marg - div_avg

        if marg >= div_avg and gap <= 0 and rev_s >= 1:
            badge_color = "#d4f4dd"
            text_color  = "#1a6b30"
            badge_label = "Strong Financial Efficiency"
            badge_icon  = "✅"
            card_bg     = "#f0faf6"
            insight = (f"{div} division leads the portfolio with a {marg:.1f}% average gross margin — "
                       f"{abs(diff):.1f}% above the cross-division benchmark of {div_avg:.1f}%. "
                       f"Profit share ({pft_s:.1f}%) slightly exceeds revenue share ({rev_s:.1f}%). "
                       f"Cost structure is well controlled with no structural issues identified.")
        elif marg < div_avg and gap >= 2:
            badge_color = "#fde8e8"
            text_color  = "#922b21"
            badge_label = "Structural Margin Issues Detected"
            badge_icon  = "⚠️"
            card_bg     = "#fff5f5"
            insight = (f"{div} division falls {abs(diff):.1f}% below the cross-division benchmark of {div_avg:.1f}% "
                       f"— the weakest performing division. A revenue-to-profit gap of {gap:.1f}% further signals "
                       f"disproportionate cost absorption. Products in this division require immediate repricing "
                       f"or cost renegotiation.")
        else:
            badge_color = "#fff3cd"
            text_color  = "#856404"
            badge_label = "Moderate Efficiency — Monitor"
            badge_icon  = "🟡"
            card_bg     = "#fffbf0"
            insight = (f"{div} division leads the portfolio with a {marg:.1f}% average gross margin — "
                       f"{abs(diff):.1f}% above the cross-division benchmark of {div_avg:.1f}%. "
                       f"Profit share ({pft_s:.1f}%) slightly exceeds revenue share ({rev_s:.1f}%). "
                       f"Financial efficiency is acceptable but margin improvement is achievable through selective re-pricing.")

        clr = DIV_COLORS_LOCAL.get(div, '#888')

        st.markdown(f"""
<div style="background:{card_bg};border:1px solid #e8e8f0;border-radius:10px;padding:16px 20px;
            margin-bottom:12px;border-left:5px solid {clr};">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;flex-wrap:wrap;">
        <span style="font-size:1.05rem;color:#1a1a2e;font-weight:600;">{div} Division</span>
        <span style="background:{badge_color};color:{text_color};padding:3px 12px;
                     border-radius:20px;font-size:0.78rem;font-weight:500;">
            {badge_icon} {badge_label}
        </span>
        <span style="margin-left:auto;font-size:0.80rem;color:#444455;">
            Avg Margin: <strong style="color:{clr}">{marg:.1f}%</strong> &nbsp;|&nbsp;
            Rev Share: <strong style="color:#1a1a2e">{rev_s:.1f}%</strong> &nbsp;|&nbsp;
            Profit Share: <strong style="color:#1a1a2e">{pft_s:.1f}%</strong> &nbsp;|&nbsp;
            Gap: <strong style="color:#1a1a2e">{gap:.1f}%</strong>
        </span>
    </div>
    <p style="font-size:0.82rem;color:#1a1a2e;margin:0;line-height:1.6;">{insight}</p>
</div>""", unsafe_allow_html=True)