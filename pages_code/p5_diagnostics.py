import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pages_code.utils import load_data, sidebar_filters, build_product_summary, kpi_card, section, chart

DIV = {'Chocolate':'#7B4F2E','Sugar':'#E8963A','Other':'#6C63FF'}

def render():
    df_full = load_data()                        # full dataset — for stable thresholds
    df, sel_div = sidebar_filters(df_full)       # filtered dataset — for display
    ps_full = build_product_summary(df_full)     # full product summary — thresholds only

    # Division-only filtered df (ignores product filter) — for stable comparisons
    df_div = df_full if sel_div == 'All' else df_full[df_full['Division'] == sel_div]

    ps      = build_product_summary(df).copy()   # filtered product summary — counts & display (.copy avoids SettingWithCopyWarning)

    section("Cost vs Margin Diagnostics",
            "A diagnostic view of cost structure health, margin erosion risks, and products requiring strategic intervention.")

    if df.empty or ps.empty:
        st.warning("No records found for the selected criteria. Consider revising the filter selections.", icon="⚠️")
        return

    # ── Thresholds derived from FULL dataset — never change with division filter ──
    _avg_mg  = ps_full['Avg_Gross_Margin'].mean()
    _std_mg  = ps_full['Avg_Gross_Margin'].std(ddof=0) or 0   # ddof=0 avoids NaN on single row
    _healthy = round(_avg_mg, 1)
    _warning = round(_avg_mg - _std_mg, 1)
    _risk    = round(_avg_mg - 2 * _std_mg, 1)
    _s_med   = ps_full['Total_Sales'].median()
    _o_med   = ps_full['Order_Count'].median()

    # ── Product filter detection — before everything so all charts can use it ──
    # Compare name sets not counts: division filter alone shrinks rows but keeps
    # the same product names — only a product filter makes this a strict subset.
    _all_product_names = set(ps_full['Product Name'].unique())
    _sel_product_names = set(ps['Product Name'].unique())
    _product_filtered  = len(df) != len(df_div)   # True only when product filter is active
    selected_products  = _sel_product_names

    def _assign_action(row):
        hi_s = row['Total_Sales']  >= _s_med
        hi_o = row['Order_Count']  >= _o_med
        mg   = row['Avg_Gross_Margin']
        if   mg >= _healthy: return 'Maintain'         if (hi_s or hi_o)  else 'Promote'
        elif mg >= _warning: return 'Monitor'          if (hi_s and hi_o) else 'Discontinue'
        elif mg >= _risk:    return 'Reprice'          if (hi_s or hi_o)  else 'Discontinue'
        else:                return 'Renegotiate Cost' if (hi_s or hi_o)  else 'Discontinue'

    # Apply actions to filtered ps using full-dataset thresholds
    # (overrides the unstable thresholds set by build_product_summary on small ps)
    ps['Recommended_Action'] = ps.apply(_assign_action, axis=1)

    # ── Action flag KPIs ──────────────────────────────────────────────────────
    ra = ps['Recommended_Action'].value_counts()

    def _div_breakdown(action):
        grp = ps[ps['Recommended_Action'] == action]
        if grp.empty:
            return '—'
        if _product_filtered:
            return str(len(grp))
        else:
            # Default: division-level counts (same as division filter behaviour)
            parts = []
            for div in ['Chocolate', 'Sugar', 'Other']:
                n = (grp['Division'] == div).sum()
                if n > 0:
                    parts.append(f"{div}: {n}")
            return ' · '.join(parts) if parts else '—'

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        kpi_card("Maintain",         str(ra.get('Maintain',         0)), f"Margin >= {_healthy}%", _div_breakdown('Maintain'),         "#1fa66a", badge="Protect & grow",      badge_color="green")
    with k2:
        kpi_card("Promote",          str(ra.get('Promote',          0)), f"Margin >= {_healthy}%", _div_breakdown('Promote'),          "#2196a6", badge="Healthy, low volume",  badge_color="green")
    with k3:
        kpi_card("Monitor",          str(ra.get('Monitor',          0)), f"{_warning}-{_healthy}%", _div_breakdown('Monitor'),         "#e8963a", badge="Watch margin trend",   badge_color="amber")
    with k4:
        kpi_card("Reprice",          str(ra.get('Reprice',          0)), f"{_risk}-{_warning}%",    _div_breakdown('Reprice'),         "#e05252", badge="Raise prices",         badge_color="red")
    with k5:
        kpi_card("Renegotiate Cost", str(ra.get('Renegotiate Cost', 0)), f"Margin < {_risk}%",      _div_breakdown('Renegotiate Cost'),"#9c27b0", badge="Fix cost structure",   badge_color="amber")
    with k6:
        kpi_card("Discontinue",      str(ra.get('Discontinue',      0)), "Low margin & demand",     _div_breakdown('Discontinue'),     "#6c0d0d", badge="Phase out",            badge_color="red")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Cost vs Sales Scatter — Two-panel (EDA 8.1) ───────────────────────────
    chart("Cost vs Sales — Margin Positioning",
          "Cost-to-sales relationship by division — left panel zooms into the $0–$1,400 range (Sugar & Other); right panel shows the full range across all divisions")

    # Use full dataset as base so chart never collapses on product filter
    max_v   = max(ps_full['Total_Sales'].max(), ps_full['Total_Cost'].max())
    ref_x   = [0, max_v]
    u_min, u_max = ps_full['Total_Units'].min(), ps_full['Total_Units'].max()

    def _scale_size(units):
        if u_max == u_min:
            return [14] * len(units)
        return [10 + 22 * (u - u_min) / (u_max - u_min) for u in units]

    def _scatter_traces(fig, panel_col):
        for div, clr in DIV.items():
            if sel_div != 'All' and div != sel_div:
                continue
            sub = ps_full[ps_full['Division'] == div]
            if sub.empty:
                continue
            if _product_filtered:
                # ── Faded layer: unselected products ──
                faded = sub[~sub['Product Name'].isin(selected_products)]
                if not faded.empty:
                    fig.add_trace(go.Scatter(
                        x=faded['Total_Sales'], y=faded['Total_Cost'],
                        mode='markers',
                        marker=dict(size=_scale_size(faded['Total_Units']),
                                    color=clr, opacity=0.12,
                                    line=dict(color='white', width=0.5)),
                        name=div, legendgroup=div, showlegend=False,
                        hoverinfo='skip',
                    ), row=1, col=panel_col)
                # ── Highlighted layer: selected products ──
                hi = sub[sub['Product Name'].isin(selected_products)]
                if not hi.empty:
                    fig.add_trace(go.Scatter(
                        x=hi['Total_Sales'], y=hi['Total_Cost'],
                        mode='markers',
                        marker=dict(size=_scale_size(hi['Total_Units']),
                                    color=clr, opacity=1.0,
                                    line=dict(color='white', width=1.5)),
                        name=div, legendgroup=div,
                        showlegend=(panel_col == 2),
                        hovertemplate=(
                            '<b>%{customdata[0]}</b><br>'
                            'Sales: $%{x:,.0f}<br>Cost: $%{y:,.0f}<br>'
                            'Margin: %{customdata[1]:.1f}%<extra></extra>'
                        ),
                        customdata=list(zip(hi['Product Name'], hi['Avg_Gross_Margin'])),
                    ), row=1, col=panel_col)
            else:
                # ── No filter: render all at full opacity ──
                fig.add_trace(go.Scatter(
                    x=sub['Total_Sales'], y=sub['Total_Cost'],
                    mode='markers',
                    marker=dict(size=_scale_size(sub['Total_Units']),
                                color=clr, opacity=1.0,
                                line=dict(color='white', width=1.2)),
                    name=div, legendgroup=div,
                    showlegend=(panel_col == 2),
                    hovertemplate=(
                        '<b>%{customdata[0]}</b><br>'
                        'Sales: $%{x:,.0f}<br>Cost: $%{y:,.0f}<br>'
                        'Margin: %{customdata[1]:.1f}%<extra></extra>'
                    ),
                    customdata=list(zip(sub['Product Name'], sub['Avg_Gross_Margin'])),
                ), row=1, col=panel_col)

    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.35, 0.65],
        shared_yaxes=False,
        subplot_titles=['Zoom: $0 – $1,400 (Sugar & Other)',
                        'Full Range — All Divisions'],
        horizontal_spacing=0.06,
    )

    # Reference lines — both panels
    for col in (1, 2):
        fig.add_trace(go.Scatter(x=ref_x, y=[0, max_v],
                                 mode='lines', line=dict(dash='dash', color='gray', width=1.2),
                                 name='Break-even (0% margin)',
                                 legendgroup='ref_be', showlegend=(col == 1)), row=1, col=col)
        fig.add_trace(go.Scatter(x=ref_x, y=[0, max_v * 0.6],
                                 mode='lines', line=dict(dash='dash', color='orange', width=1.2),
                                 name='40% margin line',
                                 legendgroup='ref_40', showlegend=(col == 1)), row=1, col=col)
        fig.add_trace(go.Scatter(x=ref_x, y=[0, max_v * 0.4],
                                 mode='lines', line=dict(dash='dash', color='green', width=1.2),
                                 name='60% margin line',
                                 legendgroup='ref_60', showlegend=(col == 1)), row=1, col=col)

    # Division scatter points — highlight/fade based on selection
    _scatter_traces(fig, panel_col=1)
    _scatter_traces(fig, panel_col=2)

    fig.update_xaxes(tickprefix='$', gridcolor='#f0f0f0', tickfont=dict(color='#1a1a2e'),
                     range=[-20, 1400],  title_text='Total Sales ($)', title_font=dict(color='#1a1a2e'), row=1, col=1)
    fig.update_yaxes(tickprefix='$', gridcolor='#f0f0f0', tickfont=dict(color='#1a1a2e'),
                     range=[-20, 1200], title_text='Total Cost ($)', title_font=dict(color='#1a1a2e'), row=1, col=1)
    fig.update_xaxes(tickprefix='$', gridcolor='#f0f0f0', tickfont=dict(color='#1a1a2e'),
                     range=[-500, 31000], title_text='Total Sales ($)', title_font=dict(color='#1a1a2e'), row=1, col=2)
    fig.update_yaxes(tickprefix='$', gridcolor='#f0f0f0', tickfont=dict(color='#1a1a2e'),
                     range=[-500, 14000], showticklabels=False, row=1, col=2)

    fig.update_layout(height=440, margin=dict(l=60, r=10, t=40, b=50),
                      plot_bgcolor='white', paper_bgcolor='white',
                      legend=dict(orientation='v', x=1.01, y=0,
                                  xanchor='left', yanchor='bottom',
                                  bgcolor='rgba(255,255,255,0.9)',
                                  bordercolor='#e0e0e0', borderwidth=1))
    fig.update_annotations(font_size=12, font_color='#666')
    st.plotly_chart(fig, use_container_width=True)

    # ── Margin Zone Classification Table ─────────────────────────────────────
    def _margin_zone(cost_ratio):
        if cost_ratio >= 90:   return '🔴 Near Break-even (>90% cost)'
        elif cost_ratio >= 60: return '🟠 Below 40% margin (60–90% cost)'
        elif cost_ratio >= 40: return '🟡 40–60% margin (40–60% cost)'
        else:                  return '🟢 Above 60% margin (<40% cost)'

    zone_bg = {
        '🔴 Near Break-even (>90% cost)':    '#ffe5e5',
        '🟠 Below 40% margin (60–90% cost)': '#fff0e0',
        '🟡 40–60% margin (40–60% cost)':    '#fffbe0',
        '🟢 Above 60% margin (<40% cost)':   '#e8f5e9',
    }

    # Use ps_full filtered to selected products — ensures all columns present
    _tbl_source = ps_full[ps_full['Product Name'].isin(_sel_product_names)] if _product_filtered else ps_full if sel_div == 'All' else ps_full[ps_full['Division'] == sel_div]
    tbl = _tbl_source[['Division', 'Product Name', 'Total_Sales',
              'Avg_Gross_Margin', 'Cost_Ratio']].copy()
    tbl['Margin Zone'] = tbl['Cost_Ratio'].apply(_margin_zone)
    tbl = tbl.sort_values(['Margin Zone', 'Cost_Ratio'], ascending=[True, False])
    tbl['Product Name'] = tbl['Product Name'].str.replace('Wonka Bar - ', '', regex=False) \
                                              .str.replace('Wonka Bar -',  '', regex=False)
    tbl = tbl.rename(columns={
        'Total_Sales':      'Sales',
        'Avg_Gross_Margin': 'Gross Margin %',
        'Cost_Ratio':       'Cost Ratio %',
        'Product Name':     'Product',
    })[['Margin Zone', 'Division', 'Product', 'Sales', 'Gross Margin %', 'Cost Ratio %']]

    def _hl_zone(row):
        bg = zone_bg.get(row['Margin Zone'], '#ffffff')
        return [f'background-color: {bg}'] * len(row)

    st.markdown("**Product Margin Zone Classification**")
    st.dataframe(
        tbl.style.apply(_hl_zone, axis=1).format({
            'Sales':          '${:,.0f}',
            'Gross Margin %': '{:.1f}%',
            'Cost Ratio %':   '{:.1f}%',
        }),
        use_container_width=True, height=420
    )
    # ── Cost vs Profit Stacked + Cost Ratio ──────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        chart("Cost vs Gross Profit",
              "Margin efficiency by product — products with rightward green dots retain more revenue as profit after cost")
        # Filter by division if selected, keep full for product filter stability
        _ps_base = ps_full if sel_div == 'All' else ps_full[ps_full['Division'] == sel_div]
        ps_s = _ps_base.sort_values('Cost_Ratio', ascending=False).copy()
        ps_s['Cost_Pct']   = ps_s['Total_Cost']   / ps_s['Total_Sales'] * 100
        ps_s['Profit_Pct'] = ps_s['Total_Profit'] / ps_s['Total_Sales'] * 100
        fig2 = go.Figure()
        for _, row in ps_s.iterrows():
            is_sel   = (not _product_filtered) or (row['Product Name'] in selected_products)
            line_a   = 0.4 if is_sel else 0.08
            fig2.add_shape(type='line',
                           x0=row['Cost_Pct'], x1=row['Profit_Pct'],
                           y0=row['Product Name'], y1=row['Product Name'],
                           line=dict(color=f'rgba(150,150,150,{line_a})', width=2))
        # Per-point colours with opacity baked in as rgba strings
        def _dot_color(base_rgb, alpha):
            return f'rgba({base_rgb},{alpha})'
        cost_colors   = [_dot_color('224,82,82',  '1.0' if (not _product_filtered) or (n in selected_products) else '0.1')
                         for n in ps_s['Product Name']]
        profit_colors = [_dot_color('31,166,106', '1.0' if (not _product_filtered) or (n in selected_products) else '0.1')
                         for n in ps_s['Product Name']]
        fig2.add_trace(go.Scatter(
            x=ps_s['Cost_Pct'], y=ps_s['Product Name'],
            mode='markers', name='Cost %',
            marker=dict(color=cost_colors, size=10),
            customdata=ps_s['Profit_Pct'],
            hovertemplate='<b>%{y}</b><br>Cost: %{x:.1f}%<br>Gross Profit: %{customdata:.1f}%<extra></extra>'
        ))
        fig2.add_trace(go.Scatter(
            x=ps_s['Profit_Pct'], y=ps_s['Product Name'],
            mode='markers', name='Gross Profit %',
            marker=dict(color=profit_colors, size=10),
            customdata=ps_s['Cost_Pct'],
            hovertemplate='<b>%{y}</b><br>Gross Profit: %{x:.1f}%<br>Cost: %{customdata:.1f}%<extra></extra>'
        ))
        fig2.update_layout(height=400, margin=dict(l=0,r=0,t=10,b=0),
                           plot_bgcolor='white', paper_bgcolor='white',
                           legend=dict(orientation='h', y=1.1))
        fig2.update_xaxes(ticksuffix='%', gridcolor='#f0f0f0', range=[0, 105], tickvals=[0, 25, 50, 75, 100], tickfont=dict(color='#1a1a2e'))
        fig2.update_yaxes(gridcolor='#f0f0f0', tickfont=dict(color='#1a1a2e'))
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        chart("Cost Ratio by Product",
              "Products exceeding a 60% cost ratio are margin-critical and require immediate intervention; those between 40–60% signal close monitoring")
        # Filter by division if selected, keep full for product filter stability
        ps_cr  = _ps_base.sort_values('Cost_Ratio', ascending=True)
        bar_c  = []
        for _, r in ps_cr.iterrows():
            is_sel = (not _product_filtered) or (r['Product Name'] in selected_products)
            if not is_sel:
                bar_c.append('rgba(200,200,200,0.2)')   # faded grey for unselected
            elif r['Cost_Ratio'] > 60:
                bar_c.append('#e05252')
            elif r['Cost_Ratio'] > 40:
                bar_c.append('#e8963a')
            else:
                bar_c.append('#1fa66a')
        text_colors = [
            'rgba(255,255,255,0.4)' if c == 'rgba(200,200,200,0.2)' else 'white'
            for c in bar_c
        ]
        max_cr = ps_cr['Cost_Ratio'].max()
        x_max  = max(105, round(max_cr + 10))
        fig3   = go.Figure()
        fig3.add_bar(x=ps_cr['Cost_Ratio'], y=ps_cr['Product Name'],
                     orientation='h', marker_color=bar_c, showlegend=False,
                     text=[f"{v:.1f}%" for v in ps_cr['Cost_Ratio']],
                     textposition='inside',
                     textfont=dict(color=text_colors, size=13))
        y_vals = ps_cr['Product Name'].tolist()
        for xv, clr, label in [
            (40, '#e8963a', '40% cost threshold (60% margin)'),
            (60, '#e05252', '60% cost threshold (40% margin)'),
        ]:
            fig3.add_scatter(x=[xv, xv], y=[y_vals[0], y_vals[-1]],
                             mode='lines', name=label,
                             line=dict(dash='dash', color=clr, width=1.5))
        fig3.update_layout(height=400, margin=dict(l=0, r=10, t=40, b=0),
                           plot_bgcolor='white', paper_bgcolor='white',
                           xaxis=dict(ticksuffix='%', gridcolor='#f0f0f0', range=[0, x_max],
                                      tickvals=[0,20,40,60,80,100], tickfont=dict(color='#1a1a2e')),
                           yaxis=dict(tickfont=dict(color='#1a1a2e')),
                           legend=dict(orientation='h', x=0, y=1.2,
                                       xanchor='left', yanchor='top',
                                       bgcolor='rgba(255,255,255,0.9)',
                                       bordercolor='#e0e0e0', borderwidth=1))
        st.plotly_chart(fig3, use_container_width=True)

    # ── Margin Volatility ─────────────────────────────────────────────────────
    chart("Margin Volatility Over Time — by Division",
          "Monthly average gross margin % per division — flat lines indicate consistent pricing; swings reveal product-mix driven instability")

    # Use df_div (division-filtered) so division filter applies;
    # unaffected by product filter — uses df_full when product filter is active
    _volatility_src = df_full if _product_filtered else df_div
    monthly_div = (
        _volatility_src.groupby(['Month', 'Division'])['Gross_Margin_Pct']
        .agg(Avg_Margin='mean', Std_Margin='std')
        .reset_index()
        .fillna(0)
    )
    monthly_div = monthly_div.sort_values('Month')
    monthly_div['Month_Label'] = pd.to_datetime(monthly_div['Month']).dt.strftime('%b-%Y')
    month_order = monthly_div['Month_Label'].unique().tolist()

    col_avg, col_std = st.columns(2)

    with col_avg:
        fig_avg = go.Figure()
        for div, clr in DIV.items():
            sub = monthly_div[monthly_div['Division'] == div]
            fig_avg.add_trace(go.Scatter(
                x=sub['Month_Label'], y=sub['Avg_Margin'],
                mode='lines+markers',
                name=div,
                line=dict(color=clr, width=2),
                marker=dict(size=5),
                hovertemplate='<b>%{x}</b><br>Avg Margin: %{y:.1f}%<extra>' + div + '</extra>',
            ))
        fig_avg.update_layout(
            height=320, margin=dict(l=0, r=0, t=10, b=80),
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(categoryorder='array', categoryarray=month_order,
                       tickangle=45, tickfont=dict(size=9, color='#1a1a2e'), gridcolor='#f0f0f0'),
            yaxis=dict(ticksuffix='%', gridcolor='#f0f0f0', tickfont=dict(color='#1a1a2e')),
            legend=dict(orientation='h', y=-0.35, x=0.5, xanchor='center', title_text=''),
        )
        st.markdown("**Avg Gross Margin % by Month**")
        st.plotly_chart(fig_avg, use_container_width=True)

    with col_std:
        fig_std = go.Figure()
        for div, clr in DIV.items():
            sub = monthly_div[monthly_div['Division'] == div]
            fig_std.add_trace(go.Scatter(
                x=sub['Month_Label'], y=sub['Std_Margin'],
                mode='lines+markers',
                name=div,
                line=dict(color=clr, width=2),
                marker=dict(size=5),
                hovertemplate='<b>%{x}</b><br>Std Dev: %{y:.2f}%<extra>' + div + '</extra>',
            ))
        fig_std.update_layout(
            height=320, margin=dict(l=0, r=0, t=10, b=80),
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(categoryorder='array', categoryarray=month_order,
                       tickangle=45, tickfont=dict(size=9, color='#1a1a2e'), gridcolor='#f0f0f0'),
            yaxis=dict(ticksuffix='%', gridcolor='#f0f0f0', tickfont=dict(color='#1a1a2e')),
            legend=dict(orientation='h', y=-0.35, x=0.5, xanchor='center', title_text=''),
        )
        st.markdown("**Margin Volatility (Std Dev) by Month**")
        st.plotly_chart(fig_std, use_container_width=True)

    if _product_filtered:
        st.markdown(
            "<div style='text-align:center;font-size:0.78rem;color:#888;margin-top:-8px;margin-bottom:16px;'>"
            "📌 Showing full portfolio — unaffected by filter selection"
            "</div>",
            unsafe_allow_html=True,
        )

    # ── Action Recommendations Table ──────────────────────────────────────────
    chart("Action Recommendations",
          "Products evaluated by margin risk and demand viability to determine the right strategic intervention.")

    _action_emoji = {
        'Maintain':         '✅ Maintain',
        'Promote':          '⭐ Promote',
        'Monitor':          '🟡 Monitor',
        'Reprice':          '🔴 Reprice',
        'Renegotiate Cost': '🔷 Renegotiate Cost',
        'Discontinue':      '⛔ Discontinue',
    }

    _action_bg = {
        '✅ Maintain':         '#f0faf4',
        '⭐ Promote':          '#e8f4f8',
        '🟡 Monitor':          '#fffbea',
        '🔴 Reprice':          '#fdf2f2',
        '🔷 Renegotiate Cost': '#f5eeff',
        '⛔ Discontinue':      '#fce8e8',
    }

    _action_order_map = {
        'Discontinue': 0, 'Reprice': 1, 'Monitor': 2,
        'Renegotiate Cost': 3, 'Promote': 4, 'Maintain': 5
    }
    _action_source = ps_full[ps_full['Product Name'].isin(_sel_product_names)].copy() if _product_filtered else ps_full.copy() if sel_div == 'All' else ps_full[ps_full['Division'] == sel_div].copy()
    _action_source['Recommended_Action'] = _action_source.apply(_assign_action, axis=1)
    action = _action_source[['Division', 'Product Name', 'Avg_Gross_Margin', 'Total_Sales',
                 'Total_Profit', 'Cost_Ratio', 'Order_Count',
                 'Product_Category', 'Recommended_Action']].copy()
    # Sort BEFORE renaming so raw action names are still available for ordering
    action['_order'] = action['Recommended_Action'].map(_action_order_map).fillna(99)
    action = action.sort_values('_order').drop(columns='_order')
    action = action.rename(columns={
        'Avg_Gross_Margin':   'Margin %',
        'Total_Sales':        'Sales',
        'Total_Profit':       'Profit',
        'Cost_Ratio':         'Cost Ratio %',
        'Order_Count':        'Orders',
        'Product_Category':   'Category',
        'Recommended_Action': 'Action',
    })
    action['Action'] = action['Action'].map(_action_emoji).fillna(action['Action'])

    _cols = list(action.columns)
    _col_w = {
        'Division': 100, 'Product Name': 200,
        'Margin %': 85, 'Sales': 95, 'Profit': 95,
        'Cost Ratio %': 100, 'Orders': 70,
        'Category': 160, 'Action': 140,
    }

    def _fmt_action(col, val):
        if col == 'Margin %':     return f"{val:.1f}%"
        if col == 'Sales':        return f"${val:,.0f}"
        if col == 'Profit':       return f"${val:,.0f}"
        if col == 'Cost Ratio %': return f"{val:.1f}%"
        if col == 'Orders':       return f"{int(val):,}"
        return str(val)

    th_base = (
        "position:sticky;top:0;z-index:2;"
        "background:#f0f0f8;color:#1a1a2e;font-size:0.72rem;"
        "font-weight:700;letter-spacing:0.04em;text-transform:uppercase;"
        "padding:8px 10px;border-bottom:2px solid #d0d0e0;white-space:nowrap;"
        "text-align:center;"
    )
    td_base = "padding:7px 10px;font-size:0.78rem;color:#0a0a1a;white-space:nowrap;text-align:center;border-bottom:1px solid #ebebf4;"

    header = "<tr>"
    for i, c in enumerate(_cols):
        w = _col_w.get(c, 100)
        sticky = ""
        z_idx = ""
        if i == 0:   sticky = "left:0px;border-right:1px solid #d0d0e0;";   z_idx = "z-index:4;"
        elif i == 1: sticky = "left:100px;border-right:2px solid #b0b0cc;";  z_idx = "z-index:4;"
        header += f'<th style="{th_base}{sticky}{z_idx}min-width:{w}px;max-width:{w}px;">{c}</th>'
    header += "</tr>"

    rows_html = ""
    for _, row in action.iterrows():
        bg = _action_bg.get(row['Action'], '#ffffff')
        rows_html += "<tr>"
        for i, c in enumerate(_cols):
            val = _fmt_action(c, row[c])
            sticky = ""
            z_idx = ""
            if i == 0:   sticky = f"position:sticky;left:0px;background:{bg};border-right:1px solid #d0d0e0;";   z_idx = "z-index:1;"
            elif i == 1: sticky = f"position:sticky;left:100px;background:{bg};border-right:2px solid #b0b0cc;";  z_idx = "z-index:1;"
            else:        sticky = f"background:{bg};"
            align = "text-align:left;" if c == 'Product Name' else ""
            rows_html += f'<td style="{td_base}{sticky}{z_idx}{align}">{val}</td>'
        rows_html += "</tr>"

    import base64
    csv_data = action.to_csv(index=False)
    b64 = base64.b64encode(csv_data.encode()).decode()
    download_link = (
        f'<a href="data:text/csv;base64,{b64}" download="action_recommendations.csv" '
        f'style="display:block;text-align:right;font-size:0.75rem;color:#aaa;text-decoration:none;'
        f'opacity:0.35;transition:opacity 0.2s;margin-bottom:2px;" '
        f'onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.35">⬇️</a>'
    )

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

    # ── Assessment Cards (EDA Step 10 recommendations) ───────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    chart("Strategic Assessment")
    if _product_filtered or sel_div != 'All':
        st.markdown(
            '<p style="font-size:0.78rem;color:#6b6b8a;margin:4px 0 8px;">📌 Assessment reflects full portfolio — unaffected by filter selection</p>',
            unsafe_allow_html=True
        )
    st.markdown("<br>", unsafe_allow_html=True)

    _card_cfg = {
        'Maintain':         ('#f0faf4', '#1a7a50', '✅', 'Margins healthy. Expand volume and protect pricing.'),
        'Promote':          ('#e8f4f8', '#156a7a', '⭐', 'Margin strong but low volume. Bundle, trial discounts, or push to underpenetrated accounts.'),
        'Monitor':          ('#fffbea', '#a06010', '🟡', 'Margin below portfolio average. Demand intact — track monthly and escalate if declining.'),
        'Reprice':          ('#fdf2f2', '#a03030', '🔴', 'Margin in risk zone. Demand exists — raise prices to restore margin.'),
        'Renegotiate Cost': ('#f5eeff', '#6a30a0', '🔷', 'Active demand confirms viability. Fix cost structure — do not discontinue.'),
        'Discontinue':      ('#fce8e8', '#8b1a1a', '⛔', 'Low margin and insufficient demand. Phase out.'),
    }

    # ── Margin Volatility — Product Mix Analysis card ─────────────────────────
    # Compute per-division std dev from full-portfolio monthly_div
    _vol_src = (
        df_full.groupby(['Month', 'Division'])['Gross_Margin_Pct']
        .agg(Avg_Margin='mean', Std_Margin='std')
        .reset_index()
        .fillna(0)
    )
    _div_volatility = (
        _vol_src.groupby('Division')['Std_Margin']
        .mean()
        .reindex(['Chocolate', 'Sugar', 'Other'])
        .fillna(0)
    )
    _choc_std  = _div_volatility.get('Chocolate', 0)
    _sugar_std = _div_volatility.get('Sugar', 0)
    _other_std = _div_volatility.get('Other', 0)
    _most_volatile = _div_volatility.idxmax()

    _mix_bullets = []
    _mix_bullets.append(
        f"<b>Chocolate</b> — avg monthly std dev {_choc_std:.1f}% — flat and consistent, "
        f"anchored by high-volume recurring orders. Pricing discipline is strong and the division "
        f"acts as the portfolio's margin stabiliser."
    )
    _mix_bullets.append(
        f"<b>Sugar</b> — avg monthly std dev {_sugar_std:.1f}% — elevated volatility driven by "
        f"irregular order patterns across a small product set. A single month with or without a "
        f"high-margin product order materially shifts the divisional average."
    )
    _mix_bullets.append(
        f"<b>Other</b> — avg monthly std dev {_other_std:.1f}% — most volatile division. "
        f"Contains products at margin extremes; whichever gets ordered in a given month "
        f"disproportionately determines the division's reported average."
    )

    _mix_body = (
        f"Portfolio-level margin stability masks a deeper structural imbalance — it is anchored "
        f"by Chocolate's volume dominance, which suppresses the headline figure while Sugar and Other "
        f"divisions exhibit significant month-to-month swings. This is not a pricing issue; it is a "
        f"product-mix issue driven by low order frequency in smaller divisions."
    )

    st.markdown(
        f"""<div style="background:#eef3fb;border-left:5px solid #2c5f9e;
            border-radius:6px;padding:14px 18px;margin-bottom:12px;">
        <div style="font-size:15px;font-weight:700;color:#2c5f9e;margin-bottom:6px;">
            📊 Margin Volatility — Product Mix Analysis
        </div>
        <div style="font-size:13px;color:#111;margin-bottom:10px;line-height:1.7;">{_mix_body}</div>
        {''.join(f'<div style="font-size:13px;color:#333;line-height:1.7;margin-bottom:6px;">• {b}</div>' for b in _mix_bullets)}
        </div>""",
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Assessment cards always use full portfolio — unaffected by product filter ──
    ps_full['Recommended_Action'] = ps_full.apply(_assign_action, axis=1)
    action_groups = ps_full.groupby('Recommended_Action')

    for action_label, (bg, text_color, icon, guidance) in _card_cfg.items():
        if action_label not in action_groups.groups:
            continue
        grp = action_groups.get_group(action_label).sort_values('Avg_Gross_Margin')

        if action_label == 'Maintain':
            lines  = [f"<b>{r['Product Name']}</b> ({r['Division']}) — {r['Avg_Gross_Margin']:.1f}% margin, "
                      f"{int(r['Order_Count'])} orders, ${r['Total_Sales']:,.0f} sales"
                      for _, r in grp.iterrows()]
            detail = '<br>'.join(lines)
            body   = f"All 5 products are operating at healthy margins (≥{_healthy}%) with strong demand. Focus on volume expansion and pricing discipline."
        elif action_label == 'Promote':
            lines  = [f"<b>{r['Product Name']}</b> ({r['Division']}) — {r['Avg_Gross_Margin']:.1f}% margin, "
                      f"{int(r['Order_Count'])} orders, ${r['Total_Sales']:,.0f} sales"
                      for _, r in grp.iterrows()]
            detail = '<br>'.join(lines)
            body   = f"Margin ≥ {_healthy}%, strong margins but untapped potential. These products need a demand push — bundle deals, trial discounts or targeted outreach to underpenetrated accounts."
        elif action_label == 'Monitor':
            lines  = [f"<b>{r['Product Name']}</b> ({r['Division']}) — {r['Avg_Gross_Margin']:.1f}% margin, "
                      f"{int(r['Order_Count'])} orders, ${r['Total_Sales']:,.0f} sales"
                      for _, r in grp.iterrows()]
            detail = '<br>'.join(lines)
            body   = f"Margin {_warning}–{_healthy}% — below portfolio average but demand intact. Track monthly; escalate to Reprice if declining."
        elif action_label == 'Reprice':
            lines  = [f"<b>{r['Product Name']}</b> ({r['Division']}) — {r['Avg_Gross_Margin']:.1f}% margin"
                      for _, r in grp.iterrows()]
            detail = '<br>'.join(lines)
            body   = f"Margin {_risk}–{_warning}% risk zone. Demand exists — raise prices to restore margin."
        elif action_label == 'Renegotiate Cost':
            lines  = [f"<b>{r['Product Name']}</b> ({r['Division']}) — {r['Avg_Gross_Margin']:.1f}% margin, "
                      f"{r['Cost_Ratio']:.1f}% cost ratio, {int(r['Order_Count'])} orders"
                      for _, r in grp.iterrows()]
            detail = '<br>'.join(lines)
            body   = f"Despite margins falling below {_risk}%, sustained demand signals product viability. Immediate action required: renegotiate supplier terms before profitability deteriorates further."
        else:  # Discontinue
            lines  = [f"<b>{r['Product Name']}</b> ({r['Division']}) — {r['Avg_Gross_Margin']:.1f}% margin, "
                      f"{int(r['Order_Count'])} orders, ${r['Total_Sales']:,.0f} sales"
                      for _, r in grp.iterrows()]
            detail = '<br>'.join(lines)
            body   = "Margins are unsustainable and demand signals are too weak to justify continued investment. Initiate a structured phase-out and reallocate resources to higher-performing products."

        st.markdown(
            f"""<div style="background:{bg};border-left:4px solid {text_color};
                border-radius:6px;padding:14px 18px;margin-bottom:12px;">
            <div style="font-size:15px;font-weight:600;color:{text_color};margin-bottom:6px;">
                {icon} {action_label}
            </div>
            <div style="font-size:13px;color:#111;margin-bottom:8px;">{body}</div>
            <div style="font-size:13px;color:#333;line-height:1.7;">{detail}</div>
            </div>""",
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)