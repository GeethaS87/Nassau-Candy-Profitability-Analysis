import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from pages_code.utils import load_data, sidebar_filters, build_product_summary, section, chart, kpi_card

REGION = {'Interior':'#6c63ff','Atlantic':'#1fa66a','Gulf':'#e8963a','Pacific':'#e05252'}

def pareto_fig(data, val_col, name_col, prefix='$', color='#6c63ff', light='#c4bfff'):
    data = data.sort_values(val_col, ascending=False).reset_index(drop=True)
    data['cum_pct'] = data[val_col].cumsum() / data[val_col].sum() * 100
    idx80 = int(data[data['cum_pct'] >= 80].index[0])
    bar_colors = [color if i <= idx80 else light for i in data.index]

    fig = go.Figure()
    fig.add_bar(x=data[name_col], y=data[val_col],
                marker_color=bar_colors, name=val_col, yaxis='y1',
                text=[f"{prefix}{v:,.0f}" for v in data[val_col]],
                textposition='outside', textfont_size=9)
    fig.add_trace(go.Scatter(
        x=data[name_col], y=data['cum_pct'],
        mode='lines+markers',
        line=dict(color='#e8963a', width=2.5),
        marker=dict(size=6),
        name='Cumulative %', yaxis='y2'))
    fig.add_hline(y=80, line_dash='dash', line_color='#e05252',
                  line_width=1.5, yref='y2',
                  annotation_text='80% threshold',
                  annotation_position='right')
    fig.update_layout(
        height=380, margin=dict(l=0,r=70,t=10,b=80),
        plot_bgcolor='white', paper_bgcolor='white',
        legend=dict(orientation='h', y=1.1),
        xaxis=dict(tickangle=-35, tickfont_size=10, gridcolor='#f0f0f0'),
        yaxis=dict(tickprefix=prefix, gridcolor='#f0f0f0', title=''),
        yaxis2=dict(overlaying='y', side='right', range=[0,105],
                    ticksuffix='%', showgrid=False, title='Cumulative %'))
    return fig, idx80 + 1


def state_pareto_fig(data, val_col, title_suffix, color, light):
    data = data.sort_values(val_col, ascending=False).reset_index(drop=True)
    data['cum_pct'] = data[val_col].cumsum() / data[val_col].sum() * 100
    idx80 = int(data[data['cum_pct'] >= 80].index[0])

    bar_colors = [color if i <= idx80 else light for i in data.index]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data['State/Province'], y=data[val_col],
        marker_color=bar_colors, name=val_col, yaxis='y1', showlegend=True))
    fig.add_trace(go.Scatter(
        x=data['State/Province'], y=data['cum_pct'],
        mode='lines+markers',
        line=dict(color='#e8963a', width=2),
        marker=dict(size=5, color='#e8963a'),
        name='Cumulative %', yaxis='y2', showlegend=True))
    fig.add_hline(y=80, line_dash='dash', line_color='#c0221c',
                  line_width=1.8, yref='y2')
    fig.add_trace(go.Scatter(
        name='80% threshold', x=[None], y=[None], mode='lines',
        line=dict(color='#c0221c', width=1.8, dash='dash'),
        showlegend=True))
    fig.update_layout(
        height=420, margin=dict(l=0, r=70, t=50, b=100),
        plot_bgcolor='white', paper_bgcolor='white',
        font=dict(color='#1a1a2e', family='DM Sans, sans-serif', size=11),
        legend=dict(orientation='h', y=1.02, x=-0.05, xanchor='left', yanchor='bottom',
                    font=dict(size=10, color='#1a1a2e'),
                    itemsizing='constant', tracegroupgap=0, traceorder='normal'),
        xaxis=dict(tickangle=-55, gridcolor='#f0f0f0', showgrid=False,
                   tickfont=dict(size=10, color='#000000')),
        yaxis=dict(tickprefix='$', tickformat=',.0f', gridcolor='#ebebf0',
                   tickfont=dict(color='#1a1a2e', size=11),
                   title=dict(text='Total ($)', font=dict(color='#1a1a2e', size=12))),
        yaxis2=dict(overlaying='y', side='right', range=[0, 110],
                    ticksuffix='%', showgrid=False,
                    title=dict(text='Cumulative %', font=dict(color='#b36a00', size=11)),
                    tickfont=dict(color='#b36a00', size=10)))
    return fig, idx80 + 1


def render():
    df_full = load_data()
    df, sel_div = sidebar_filters(df_full)
    ps_full = build_product_summary(df_full)  # always full portfolio

    # Division-only filtered df (ignores product filter) — used for state/region charts
    df_div = df_full if sel_div == 'All' else df_full[df_full['Division'] == sel_div]

    # Ensure State/Province is clean on both
    df_full['State/Province'] = df_full['State/Province'].str.strip().str.title()
    df['State/Province']      = df['State/Province'].str.strip().str.title()

    # ps used for charts = filtered; ps for KPI denominators = full portfolio
    ps = build_product_summary(df)

    section("Profit Concentration Analysis",
            "Pareto-driven concentration analysis across products, regions and states — highlighting over-dependency and portfolio risk")

    if df.empty or ps.empty:
        st.warning("No records found for the selected criteria. Consider revising the filter selections.", icon="⚠️")
        return

    # ── Portfolio KPIs — always derived from full portfolio ───────────────────
    # Full-portfolio Pareto (denominator never changes)
    rev_full = ps_full.sort_values('Total_Sales',  ascending=False).reset_index(drop=True)
    pft_full = ps_full.sort_values('Total_Profit', ascending=False).reset_index(drop=True)
    rev_full['cum'] = rev_full['Total_Sales'].cumsum()  / rev_full['Total_Sales'].sum()  * 100
    pft_full['cum'] = pft_full['Total_Profit'].cumsum() / pft_full['Total_Profit'].sum() * 100

    total_portfolio = len(ps_full)  # always 15 (or whatever full count is)

    if sel_div == 'All':
        # "All" — show full Pareto counts as before
        n80r  = int((rev_full['cum'] < 80).sum()) + 1
        n80p  = int((pft_full['cum'] < 80).sum()) + 1
        n_div_products = total_portfolio
    else:
        # Filtered division: how many of THAT division's products are in the
        # full-portfolio 80% threshold, and how many products does that division have
        div_products_full = ps_full[ps_full['Division'] == sel_div]['Product Name'].tolist()
        n_div_products    = len(div_products_full)

        # Products in full-portfolio 80% revenue threshold that belong to this division
        idx80r = int((rev_full['cum'] < 80).sum()) + 1
        top80r_products = set(rev_full.iloc[:idx80r]['Product Name'])
        n80r = len(top80r_products & set(div_products_full))

        # Same for profit
        idx80p = int((pft_full['cum'] < 80).sum()) + 1
        top80p_products = set(pft_full.iloc[:idx80p]['Product Name'])
        n80p = len(top80p_products & set(div_products_full))

    # State KPIs — always from full dataset
    state_rev_full  = df_full.groupby('State/Province')['Sales'].sum().reset_index()
    state_rev_full.columns = ['State/Province','Total_Sales']
    state_rev_full  = state_rev_full.sort_values('Total_Sales', ascending=False).reset_index(drop=True)
    state_rev_full['cum'] = state_rev_full['Total_Sales'].cumsum() / state_rev_full['Total_Sales'].sum() * 100
    n80_state  = int((state_rev_full['cum'] < 80).sum()) + 1
    top_state  = state_rev_full.iloc[0]['State/Province']
    top_state_pct = (state_rev_full.iloc[0]['Total_Sales'] / state_rev_full['Total_Sales'].sum() * 100)
    n_states_full = df_full['State/Province'].nunique()

    # Division revenue/profit share of full portfolio — for badge on cards 1 & 2
    div_filtering = sel_div != 'All'
    if div_filtering:
        div_rev_share = (
            ps_full[ps_full['Division'] == sel_div]['Total_Sales'].sum()
            / ps_full['Total_Sales'].sum() * 100
        )
        div_pft_share = (
            ps_full[ps_full['Division'] == sel_div]['Total_Profit'].sum()
            / ps_full['Total_Profit'].sum() * 100
        )
        def _share_color(pct):
            if pct >= 50:   return 'green'
            elif pct >= 10: return 'amber'
            else:           return 'red'
        rev_badge       = f"↑ {div_rev_share:.1f}% of portfolio revenue"
        pft_badge       = f"↑ {div_pft_share:.1f}% of portfolio profit"
        rev_badge_color = _share_color(div_rev_share)
        pft_badge_color = _share_color(div_pft_share)
    else:
        rev_badge       = f"↑ {n80r/n_div_products*100:.0f}% of portfolio" if n_div_products else "—"
        pft_badge       = f"↑ {n80p/n_div_products*100:.0f}% of portfolio" if n_div_products else "—"
        rev_badge_color = 'green'
        pft_badge_color = 'green'

    k1,k2,k3,k4 = st.columns(4)
    with k1:
        kpi_card(
            label="Products → 80% Revenue",
            value=f"{n80r} of {n_div_products}",
            formula="Products driving 80% of total portfolio revenue",
            sub="",
            accent="#6c63ff",
            badge=rev_badge,
            badge_color=rev_badge_color,
        )
    with k2:
        kpi_card(
            label="Products → 80% Profit",
            value=f"{n80p} of {n_div_products}",
            formula="Products driving 80% of total gross profit",
            sub="",
            accent="#1fa66a",
            badge=pft_badge,
            badge_color=pft_badge_color,
        )
    with k3:
        kpi_card(
            label="States → 80% Revenue",
            value=f"{n80_state} of {n_states_full}",
            formula="States contributing 80% of total revenue",
            sub="",
            accent="#e8963a",
            badge="↑ Geographic concentration",
            badge_color="amber",
            grayed=div_filtering,
        )
    with k4:
        kpi_card(
            label="Top State",
            value=top_state,
            formula="Highest revenue-generating state",
            sub="",
            accent="#e05252",
            badge=f"↑ {top_state_pct:.1f}% of revenue",
            badge_color="amber",
            grayed=div_filtering,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SECTION 1: Product Pareto ─────────────────────────────────────────────
    st.markdown('<div class="chart-header">Product-Level Pareto Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Identifies which products drive 80% of portfolio revenue and profit</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # ── Revenue Pareto ────────────────────────────────────────────────────────
    with col1:
        chart("Revenue Pareto — by Product",
              "Products sorted by total sales with cumulative revenue percentage overlay")

        par_r = ps_full.sort_values('Total_Sales', ascending=False).reset_index(drop=True)
        par_r['Cumulative'] = (par_r['Total_Sales'] / par_r['Total_Sales'].sum() * 100).cumsum().round(1)

        # Determine selected products from product filter
        _sel_products = set(df['Product Name'].unique()) if len(df) != len(df_div) else set()
        # Highlight: division filter → division products; product filter → selected products; both → intersection
        _div_products = set(ps_full[ps_full['Division'] == sel_div]['Product Name']) if sel_div != 'All' else set()

        def _rev_color(p):
            if _sel_products:  # product filter active
                return '#6c63ff' if p in _sel_products else '#e0dfff'
            elif _div_products:  # division filter active
                return '#6c63ff' if p in _div_products else '#c4bfff'
            return '#6c63ff'  # all

        par_r_colors = [_rev_color(p) for p in par_r['Product Name']]

        fig_r = go.Figure()
        fig_r.add_trace(go.Bar(
            name='Sales',
            x=par_r['Product Name'],
            y=par_r['Total_Sales'],
            marker_color=par_r_colors,
            opacity=0.85,
            yaxis='y',
            showlegend=True,
        ))
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
        fig_r.add_hline(y=80, line_dash='dash', line_color='#c0221c',
                        line_width=1.8, yref='y2')
        fig_r.add_trace(go.Scatter(
            name='80% threshold', x=[None], y=[None], mode='lines',
            line=dict(color='#c0221c', width=1.8, dash='dash'),
            showlegend=True,
        ))
        fig_r.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(color='#1a1a2e', family='DM Sans, sans-serif', size=11),
            height=420, margin=dict(l=10, r=60, t=50, b=110),
            legend=dict(orientation='h', y=1.02, x=-0.05, xanchor='left', yanchor='bottom',
                        font=dict(size=10, color='#1a1a2e'),
                        itemsizing='constant', tracegroupgap=0, traceorder='normal'),
            bargap=0.25,
            yaxis=dict(
                title=dict(text='Total Sales ($)', font=dict(color='#333333', size=12)),
                tickprefix='$', tickformat=',.0f',
                gridcolor='#ebebf0', tickfont=dict(color='#1a1a2e', size=11),
                rangemode='tozero',
            ),
            yaxis2=dict(
                title=dict(text='Cumulative Revenue %', font=dict(color='#E8963A', size=11)),
                overlaying='y', side='right',
                ticksuffix='%', range=[0, 110],
                showgrid=False, tickfont=dict(color='#E8963A', size=10),
            ),
        )
        fig_r.update_xaxes(tickfont=dict(size=10, color='#0a0a1a', family='DM Sans, sans-serif'), tickangle=-45, showgrid=False)
        st.plotly_chart(fig_r, use_container_width=True)
        st.markdown(f'<div style="text-align:center;background:#EEF3FB;border-radius:8px;padding:10px;font-size:0.9rem;color:#1a1a2e;">📊 <strong>{n80r} product(s)</strong> drive 80% of total portfolio revenue</div>', unsafe_allow_html=True)

    # ── Profit Pareto ─────────────────────────────────────────────────────────
    with col2:
        chart("Profit Pareto — by Product",
              "Products sorted by gross profit with cumulative profit percentage overlay")

        par_p = ps_full.sort_values('Total_Profit', ascending=False).reset_index(drop=True)
        par_p['Cumulative'] = (par_p['Total_Profit'] / par_p['Total_Profit'].sum() * 100).cumsum().round(1)

        def _pft_color(p):
            if _sel_products:
                return '#1a7a4a' if p in _sel_products else '#c8e6d5'
            elif _div_products:
                return '#1a7a4a' if p in _div_products else '#a8d5be'
            return '#1a7a4a'

        par_p_colors = [_pft_color(p) for p in par_p['Product Name']]

        fig_p = go.Figure()
        fig_p.add_trace(go.Bar(
            name='Profit',
            x=par_p['Product Name'],
            y=par_p['Total_Profit'],
            marker_color=par_p_colors,
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
        fig_p.add_hline(y=80, line_dash='dash', line_color='#c0221c',
                        line_width=1.8, yref='y2')
        fig_p.add_trace(go.Scatter(
            name='80% threshold', x=[None], y=[None], mode='lines',
            line=dict(color='#c0221c', width=1.8, dash='dash'),
            showlegend=True,
        ))
        fig_p.update_layout(
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(color='#1a1a2e', family='DM Sans, sans-serif', size=11),
            height=420, margin=dict(l=10, r=60, t=50, b=110),
            legend=dict(orientation='h', y=1.02, x=-0.05, xanchor='left', yanchor='bottom',
                        font=dict(size=10, color='#1a1a2e'),
                        itemsizing='constant', tracegroupgap=0, traceorder='normal'),
            bargap=0.25,
            yaxis=dict(
                title=dict(text='Total Profit ($)', font=dict(color='#333333', size=12)),
                tickprefix='$', tickformat=',.0f',
                gridcolor='#ebebf0', tickfont=dict(color='#1a1a2e', size=11),
                rangemode='tozero',
            ),
            yaxis2=dict(
                title=dict(text='Cumulative Profit %', font=dict(color='#E8963A', size=11)),
                overlaying='y', side='right',
                ticksuffix='%', range=[0, 110],
                showgrid=False, tickfont=dict(color='#E8963A', size=10),
            ),
        )
        fig_p.update_xaxes(tickfont=dict(size=10, color='#0a0a1a', family='DM Sans, sans-serif'), tickangle=-45, showgrid=False)
        st.plotly_chart(fig_p, use_container_width=True)
        st.markdown(f'<div style="text-align:center;background:#EEF3FB;border-radius:8px;padding:10px;font-size:0.9rem;color:#1a1a2e;">💰 <strong>{n80p} product(s)</strong> drive 80% of total gross profit</div>', unsafe_allow_html=True)

    # ── SECTION 2: Region Pareto ──────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="chart-header">Regional Pareto Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Identifies which regions contribute disproportionately to revenue and profit — over-dependency risk</div>', unsafe_allow_html=True)

    reg_rev = df_full.groupby('Region').agg(
        Total_Sales  = ('Sales',        'sum'),
        Total_Profit = ('Gross Profit', 'sum'),
        Order_Count  = ('Order ID',     'count'),
    ).reset_index()

    col3, col4 = st.columns(2)

    with col3:
        chart("Revenue Pareto — by Region")
        reg_rev_s = reg_rev.sort_values('Total_Sales', ascending=False).reset_index(drop=True)
        reg_rev_s['cum_pct'] = reg_rev_s['Total_Sales'].cumsum() / reg_rev_s['Total_Sales'].sum() * 100
        idx80_r = int(reg_rev_s[reg_rev_s['cum_pct'] >= 80].index[0])

        fig_rr = go.Figure()
        bar_c = [REGION.get(r, '#888') for r in reg_rev_s['Region']]
        fig_rr.add_trace(go.Bar(
            name='Sales',
            x=reg_rev_s['Region'], y=reg_rev_s['Total_Sales'],
            marker_color=bar_c, yaxis='y1',
            text=[f"${v:,.0f}" for v in reg_rev_s['Total_Sales']],
            textposition='outside', showlegend=True))
        fig_rr.add_trace(go.Scatter(
            x=reg_rev_s['Region'], y=reg_rev_s['cum_pct'],
            mode='lines+markers',
            line=dict(color='#e8963a', width=2.5),
            marker=dict(size=6, color='#e8963a'),
            name='Cumulative %', yaxis='y2', showlegend=True))
        fig_rr.add_hline(y=80, line_dash='dash', line_color='#c0221c',
                         line_width=1.8, yref='y2')
        fig_rr.add_trace(go.Scatter(
            name='80% threshold', x=[None], y=[None], mode='lines',
            line=dict(color='#c0221c', width=1.8, dash='dash'),
            showlegend=True))
        fig_rr.update_layout(
            height=340, margin=dict(l=0, r=70, t=50, b=20),
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(color='#1a1a2e', family='DM Sans, sans-serif', size=11),
            legend=dict(orientation='h', y=1.02, x=-0.05, xanchor='left', yanchor='bottom',
                        font=dict(size=10, color='#1a1a2e'),
                        itemsizing='constant', tracegroupgap=0, traceorder='normal'),
            yaxis=dict(tickprefix='$', tickformat=',.0f', gridcolor='#ebebf0',
                       tickfont=dict(color='#1a1a2e', size=11),
                       title=dict(text='Total Sales ($)', font=dict(color='#1a1a2e', size=12))),
            yaxis2=dict(overlaying='y', side='right', range=[0, 110],
                        ticksuffix='%', showgrid=False,
                        title=dict(text='Cumulative Revenue %', font=dict(color='#b36a00', size=11)),
                        tickfont=dict(color='#b36a00', size=10)))
        fig_rr.update_xaxes(tickfont=dict(size=10, color='#1a1a2e'), showgrid=False)
        st.plotly_chart(fig_rr, use_container_width=True)

    with col4:
        chart("Profit Pareto — by Region")
        reg_pft_s = reg_rev.sort_values('Total_Profit', ascending=False).reset_index(drop=True)
        reg_pft_s['cum_pct'] = reg_pft_s['Total_Profit'].cumsum() / reg_pft_s['Total_Profit'].sum() * 100

        fig_rp = go.Figure()
        bar_c2 = [REGION.get(r, '#888') for r in reg_pft_s['Region']]
        fig_rp.add_trace(go.Bar(
            name='Profit',
            x=reg_pft_s['Region'], y=reg_pft_s['Total_Profit'],
            marker_color=bar_c2, yaxis='y1',
            text=[f"${v:,.0f}" for v in reg_pft_s['Total_Profit']],
            textposition='outside', showlegend=True))
        fig_rp.add_trace(go.Scatter(
            x=reg_pft_s['Region'], y=reg_pft_s['cum_pct'],
            mode='lines+markers',
            line=dict(color='#e8963a', width=2.5),
            marker=dict(size=6, color='#e8963a'),
            name='Cumulative %', yaxis='y2', showlegend=True))
        fig_rp.add_hline(y=80, line_dash='dash', line_color='#c0221c',
                         line_width=1.8, yref='y2')
        fig_rp.add_trace(go.Scatter(
            name='80% threshold', x=[None], y=[None], mode='lines',
            line=dict(color='#c0221c', width=1.8, dash='dash'),
            showlegend=True))
        fig_rp.update_layout(
            height=340, margin=dict(l=0, r=70, t=50, b=20),
            plot_bgcolor='white', paper_bgcolor='white',
            font=dict(color='#1a1a2e', family='DM Sans, sans-serif', size=11),
            legend=dict(orientation='h', y=1.02, x=-0.05, xanchor='left', yanchor='bottom',
                        font=dict(size=10, color='#1a1a2e'),
                        itemsizing='constant', tracegroupgap=0, traceorder='normal'),
            yaxis=dict(tickprefix='$', tickformat=',.0f', gridcolor='#ebebf0',
                       tickfont=dict(color='#1a1a2e', size=11),
                       title=dict(text='Total Profit ($)', font=dict(color='#1a1a2e', size=12))),
            yaxis2=dict(overlaying='y', side='right', range=[0, 110],
                        ticksuffix='%', showgrid=False,
                        title=dict(text='Cumulative Profit %', font=dict(color='#b36a00', size=11)),
                        tickfont=dict(color='#b36a00', size=10)))
        fig_rp.update_xaxes(tickfont=dict(size=10, color='#1a1a2e'), showgrid=False)
        st.plotly_chart(fig_rp, use_container_width=True)

    if len(df) != len(df_full):
        st.markdown(
            '<p style="font-size:0.78rem;color:#6b6b8a;margin:4px 0 8px;text-align:center;">📌 Showing full portfolio — unaffected by filter selection</p>',
            unsafe_allow_html=True
        )

    # ── SECTION 3: State-Level Pareto ─────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="chart-header">State-Level Pareto Analysis — Congestion & Over-Dependency Detection</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Identifies congestion-prone states driving disproportionate revenue concentration — geographic over-dependency risk</div>', unsafe_allow_html=True)

    state_pft = df_div.groupby(['State/Province','Region']).agg(
        Total_Sales   = ('Sales',        'sum'),
        Total_Profit  = ('Gross Profit', 'sum'),
        Order_Count   = ('Order ID',     'count'),
        Avg_Margin    = ('Gross_Margin_Pct', 'mean'),
    ).round(2).reset_index()

    col5, col6 = st.columns(2)

    with col5:
        chart("Revenue Pareto — by State",
              "Top 20 states sorted by revenue — states driving 80% of revenue signal geographic over-dependency")
        top20_rev = state_pft.sort_values('Total_Sales', ascending=False).head(20).reset_index(drop=True)
        fig_sr, n_sr = state_pareto_fig(top20_rev, 'Total_Sales',
                                        'Revenue', '#6c63ff', '#c4bfff')
        st.plotly_chart(fig_sr, use_container_width=True)

    with col6:
        chart("Profit Pareto — by State",
              "Top 20 states sorted by gross profit — over-dependency on key states")
        top20_pft = state_pft.sort_values('Total_Profit', ascending=False).head(20).reset_index(drop=True)
        fig_sp, n_sp = state_pareto_fig(top20_pft, 'Total_Profit',
                                        'Profit', '#1fa66a', '#a8e6c8')
        st.plotly_chart(fig_sp, use_container_width=True)

    lbl1, lbl2 = st.columns(2)
    with lbl1:
        st.markdown(f'<div style="text-align:center;background:#fff8e1;border-radius:8px;padding:12px 16px;font-size:0.82rem;color:#1a1a2e;">⚠️ <strong>{n_sr} state(s)</strong> account for 80% of total revenue — geographic concentration risk</div>', unsafe_allow_html=True)
    with lbl2:
        st.markdown(f'<div style="text-align:center;background:#fff8e1;border-radius:8px;padding:12px 16px;font-size:0.82rem;color:#1a1a2e;">⚠️ <strong>{n_sp} state(s)</strong> account for 80% of total gross profit — over-dependency risk</div>', unsafe_allow_html=True)

    if len(df) != len(df_div):
        st.markdown(
            '<p style="font-size:0.78rem;color:#6b6b8a;margin:8px 0 4px;text-align:center;">📌 Showing full portfolio — unaffected by filter selection</p>',
            unsafe_allow_html=True
        )

    # ── Order Concentration by State ──────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    chart("Order Concentration by State — All States",
          "Geographic distribution of order volume across all states — darker shading = higher order concentration")
    if len(df) != len(df_div):
        st.markdown(
            '<p style="font-size:0.78rem;color:#6b6b8a;margin:4px 0 8px;">📌 Showing full portfolio — unaffected by filter selection</p>',
            unsafe_allow_html=True
        )
    st.markdown('<style>div[data-testid="stMarkdownContainer"] p { color: #1a1a2e; }</style>', unsafe_allow_html=True)

    all_states_orders = state_pft[['State/Province','Order_Count']].sort_values('Order_Count', ascending=False)
    all_states_orders = all_states_orders[all_states_orders['Order_Count'] > 0]
    orders_dict = dict(zip(all_states_orders['State/Province'], all_states_orders['Order_Count']))
    orders_json = str(orders_dict).replace("'", '"')
    total_orders = int(all_states_orders['Order_Count'].sum())

    choropleth_html = f"""
    <div style="position:relative;">
      <p style="font-size:12px;color:#1a1a2e;margin:0 0 4px;">Hover over any state to see order count and share of total</p>
      <div id="tooltip_map" style="position:fixed;background:#1a1a2e;color:#fff;padding:6px 10px;border-radius:6px;font-size:12px;pointer-events:none;display:none;z-index:999;"></div>
      <div id="choro_map" style="width:100%;"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js"></script>
    <script>
    const orderData = {orders_json};
    const total = {total_orders};
    const maxVal = {int(all_states_orders['Order_Count'].max())};
    const ramp = ['#e8e6ff','#c4bfff','#9f98f7','#7a71ef','#5549d6','#3a30b0','#221a80'];
    const colorScale = (val) => {{
      if (val <= 0) return '#f0eeee';
      const logVal = Math.log(val + 1);
      const logMax = Math.log(maxVal + 1);
      const idx = Math.min(Math.floor((logVal / logMax) * ramp.length), ramp.length - 1);
      return ramp[idx];
    }};
    const mapW = 860, mapH = 420, legendW = 90;
    const totalW = mapW + legendW;
    const svg = d3.select('#choro_map').append('svg')
      .attr('viewBox', `0 0 ${{totalW}} ${{mapH}}`)
      .attr('width', '100%')
      .attr('height', mapH);
    // Bigger map — scale and translate updated
    const projection = d3.geoAlbersUsa().scale(920).translate([mapW/2, mapH/2 - 20]);
    const path = d3.geoPath(projection);
    const tooltip = document.getElementById('tooltip_map');
    d3.json('https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json').then(us => {{
      svg.selectAll('path')
        .data(topojson.feature(us, us.objects.states).features.filter(d => (orderData[d.properties.name] || 0) > 0))
        .join('path')
        .attr('d', path)
        .attr('fill', d => {{ const val = orderData[d.properties.name] || 0; return val > 0 ? colorScale(val) : '#f0eeee'; }})
        .attr('stroke', '#fff').attr('stroke-width', 0.8)
        .on('mousemove', (event, d) => {{
          const val = orderData[d.properties.name] || 0;
          const pct = val > 0 ? ((val/total)*100).toFixed(1) : '0.0';
          tooltip.style.display = 'block';
          tooltip.style.left = (event.clientX + 12) + 'px';
          tooltip.style.top  = (event.clientY - 28) + 'px';
          tooltip.innerHTML = `<strong>${{d.properties.name}}</strong><br>${{val.toLocaleString()}} orders &nbsp;|&nbsp; ${{pct}}% of total`;
        }})
        .on('mouseleave', () => {{ tooltip.style.display = 'none'; }});

      // ── Legend: vertical, top-right corner, always visible ──
      const lx = mapW + 14;
      const legendG = svg.append('g').attr('transform', `translate(${{lx}}, 8)`);
      legendG.append('text')
        .attr('x', 0).attr('y', 0)
        .attr('font-size', '10px').attr('fill', '#555')
        .attr('font-family', 'DM Sans, sans-serif').attr('font-weight', '600')
        .text('Orders');
      const swatchH = 18, gap = 3;
      const labels = ['High', '', '', '', '', '', 'Low'];
      [...ramp].reverse().forEach((c, i) => {{
        legendG.append('rect')
          .attr('x', 0).attr('y', 14 + i * (swatchH + gap))
          .attr('width', 14).attr('height', swatchH)
          .attr('rx', 2).attr('fill', c);
        if (labels[i]) {{
          legendG.append('text')
            .attr('x', 20).attr('y', 14 + i * (swatchH + gap) + 13)
            .attr('font-size', '10px').attr('fill', '#1a1a2e')
            .attr('font-family', 'DM Sans, sans-serif')
            .text(labels[i]);
        }}
      }});
    }});
    </script>
    """
    # Legend is in top-right corner inside SVG — always visible, map unchanged
    components.html(choropleth_html, height=450, scrolling=False)

    if not all_states_orders.empty:
        top_us = all_states_orders.iloc[0]
        top_us_pct = top_us['Order_Count'] / total_orders * 100
        st.markdown(
            f'<div style="text-align:center;background:#e6f1fb;border-radius:8px;padding:10px 16px;'
            f'font-size:0.82rem;color:#1a1a2e;">🗽 <strong>{top_us["State/Province"]}</strong> leads '
            f'US orders with <strong>{int(top_us["Order_Count"]):,}</strong> orders '
            f'({top_us_pct:.1f}% of total)</div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Canada Province Treemap ───────────────────────────────────────────────
    chart("Order Concentration by Province — Canada (CA)",
          "Treemap area = order volume per province — highlights concentration across 10 Canadian provinces")
    if len(df) != len(df_div):
        st.markdown(
            '<p style="font-size:0.78rem;color:#6b6b8a;margin:4px 0 8px;">📌 Showing full portfolio — unaffected by filter selection</p>',
            unsafe_allow_html=True
        )

    CA_PROVINCES = ['Alberta', 'British Columbia', 'Manitoba', 'New Brunswick',
                    'Newfoundland And Labrador', 'Nova Scotia', 'Ontario',
                    'Prince Edward Island', 'Quebec', 'Saskatchewan']

    ca_pft = df_div[df_div['State/Province'].isin(CA_PROVINCES)].groupby('State/Province').agg(
        Order_Count  = ('Order ID',     'count'),
        Total_Sales  = ('Sales',        'sum'),
        Total_Profit = ('Gross Profit', 'sum'),
    ).reset_index()

    if not ca_pft.empty:
        ca_pft['Share %'] = (ca_pft['Order_Count'] / ca_pft['Order_Count'].sum() * 100).round(1)
        ca_pft['label']   = ca_pft.apply(
            lambda r: f"{r['State/Province']}<br>{r['Order_Count']:,} orders ({r['Share %']}%)", axis=1
        )

        # Build colour list mapped to order count
        ca_ramp = ['#559e60','#3a8048','#277a35','#1a6b2a','#0d5518']
        max_ord = ca_pft['Order_Count'].max()
        def ca_color(val):
            import math
            i = min(int(math.pow(val/max_ord, 0.5) * len(ca_ramp)), len(ca_ramp)-1)
            return ca_ramp[i]

        clean_provinces = [p.split(' ', 1)[-1] if p.startswith('CA ') else p for p in ca_pft['State/Province'].tolist()]
        labels   = ['CA'] + clean_provinces
        parents  = ['']   + ['CA'] * len(ca_pft)
        values   = [0]       + ca_pft['Order_Count'].tolist()
        colors   = ['white'] + [ca_color(v) for v in ca_pft['Order_Count']]
        customs  = [dict(o=0, s=0, r=0, p=0)] + [
            dict(o=r['Order_Count'], s=r['Share %'],
                 r=r['Total_Sales'], p=r['Total_Profit'])
            for _, r in ca_pft.iterrows()
        ]

        fig_ca = go.Figure(go.Treemap(
            labels=labels,
            parents=parents,
            values=values,
            marker=dict(
                colors=colors,
                line=dict(width=2, color='white'),
                pad=dict(t=0, l=0, r=0, b=0),
            ),
            customdata=[[d['o'], d['s'], d['r'], d['p']] for d in customs],
            texttemplate='<b>%{label}</b><br>%{customdata[0]:,} orders<br>%{customdata[1]:.1f}% of CA total',
            hovertemplate=(
                '<b>%{label}</b><br>'
                'Orders: %{customdata[0]:,}<br>'
                'Share: %{customdata[1]:.1f}%<br>'
                'Revenue: $%{customdata[2]:,.0f}<br>'
                'Profit: $%{customdata[3]:,.0f}<extra></extra>'
            ),
            textfont=dict(size=12, color='white', family='DM Sans, sans-serif'),
            tiling=dict(pad=3),
            pathbar=dict(visible=False),
        ))
        fig_ca.update_layout(
            height=260,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='white',
            font=dict(family='DM Sans, sans-serif', color='#1a1a2e'),
        )
        fig_ca.update_traces(
            marker_depthfade=False,
            marker_line=dict(width=2, color='white'),
        )
        st.plotly_chart(fig_ca, use_container_width=True)
        ca_sorted = ca_pft.sort_values('Order_Count', ascending=False)
        top_ca = ca_sorted.iloc[0]
        top_count = top_ca['Order_Count']
        tied = ca_sorted[ca_sorted['Order_Count'] == top_count]
        def _clean(name):
            return str(name).split(" ", 1)[-1] if str(name).startswith("CA ") else str(name)
        if len(tied) >= 2:
            names = ' and '.join([f'<strong>{_clean(r["State/Province"])}</strong>' for _, r in tied.iterrows()])
            banner_text = (
                f'🍁 {names} share the lead with '
                f'<strong>{int(top_count):,}</strong> orders each '
                f'({top_ca["Share %"]:.1f}% of CA total)'
            )
        else:
            banner_text = (
                f'🍁 <strong>{_clean(top_ca["State/Province"])}</strong> leads '
                f'Canadian orders with <strong>{int(top_count):,}</strong> orders '
                f'({top_ca["Share %"]:.1f}% of CA total)'
            )
        st.markdown(
            f'<div style="text-align:center;background:#e6f1fb;border-radius:8px;padding:10px 16px;'
            f'font-size:0.82rem;color:#1a1a2e;">{banner_text}</div>',
            unsafe_allow_html=True
        )
    else:
        st.info("No Canadian province data found after applying current filters.")

    st.markdown("<br>", unsafe_allow_html=True)
    chart("Order Concentration by State — Top 20",
          "States driving the highest order volumes — concentration here signals distribution over-dependency")
    if len(df) != len(df_full):
        st.markdown(
            '<p style="font-size:0.78rem;color:#6b6b8a;margin:4px 0 8px;">📌 Showing full portfolio — unaffected by filter selection</p>',
            unsafe_allow_html=True
        )

    top20_ord = state_pft.sort_values('Order_Count', ascending=False).head(20)
    reg_color_map = [REGION.get(r, '#888') for r in top20_ord['Region']]

    fig_ord = go.Figure()
    fig_ord.add_bar(
        x=top20_ord['State/Province'],
        y=top20_ord['Order_Count'],
        marker_color=reg_color_map,
        text=top20_ord['Order_Count'].apply(lambda x: f"{x:,}"),
        textposition='outside'
    )
    fig_ord.update_layout(
        height=380, margin=dict(l=0,r=0,t=10,b=80),
        plot_bgcolor='white', paper_bgcolor='white',
        xaxis=dict(tickangle=-45, gridcolor='#f0f0f0',
                   tickfont=dict(size=10, color='#0a0a1a', family='DM Sans, sans-serif')),
        yaxis=dict(gridcolor='#f0f0f0',
                   title=dict(text='Order Count', font=dict(color='#0a0a1a', size=12, family='DM Sans, sans-serif')),
                   tickfont=dict(color='#0a0a1a', size=10, family='DM Sans, sans-serif')),
        uniformtext=dict(minsize=9, mode='hide'),
        showlegend=False
    )
    fig_ord.update_traces(textfont=dict(color='#0a0a1a', size=10, family='DM Sans, sans-serif'))

    # Add region colour legend as annotations
    for i, (reg, clr) in enumerate(REGION.items()):
        fig_ord.add_annotation(
            x=0.75 + i * 0.08, y=1.08, xref='paper', yref='paper',
            text=f"■ {reg}", font=dict(color=clr, size=10),
            showarrow=False
        )
    st.plotly_chart(fig_ord, use_container_width=True)

    # ── State Dependency Risk Table ────────────────────────────────────────────
    chart("State Over-Dependency Risk Table",
          "States ranked by revenue share — high concentration in few states represents supply chain and demand risk")
    if len(df) != len(df_full):
        st.markdown(
            '<p style="font-size:0.78rem;color:#6b6b8a;margin:4px 0 8px;">📌 Showing full portfolio — unaffected by filter selection</p>',
            unsafe_allow_html=True
        )

    total_rev = state_pft['Total_Sales'].sum()
    total_pft_val = state_pft['Total_Profit'].sum()

    state_table = state_pft.copy()
    state_table['Revenue Share %'] = (state_table['Total_Sales']  / total_rev      * 100).round(2)
    state_table['Profit Share %']  = (state_table['Total_Profit'] / total_pft_val  * 100).round(2)
    state_table['Cum Rev %']       = state_table.sort_values('Total_Sales', ascending=False)['Revenue Share %'].cumsum().round(1)

    def risk_flag(share):
        if share >= 15:  return '🔴 High Dependency'
        elif share >= 8: return '🟡 Moderate'
        else:            return '✅ Low'

    state_table['Dependency Risk'] = state_table['Revenue Share %'].apply(risk_flag)
    state_table = state_table.sort_values('Total_Sales', ascending=False).head(25)

    def hl_risk(row):
        r = row['Dependency Risk']
        if '🔴' in r:  return ['background-color:#fde8e8'] * len(row)
        elif '🟡' in r: return ['background-color:#fff3cd'] * len(row)
        else:           return ['background-color:#f0faf4'] * len(row)

    st.dataframe(
        state_table[['State/Province','Region','Order_Count',
                     'Total_Sales','Total_Profit','Avg_Margin',
                     'Revenue Share %','Profit Share %','Dependency Risk']]
        .rename(columns={
            'Order_Count':'Orders','Total_Sales':'Revenue',
            'Total_Profit':'Profit','Avg_Margin':'Avg Margin %',
            'Revenue Share %':'Rev Share %'
        })
        .style.apply(hl_risk, axis=1)
        .format({
            'Revenue':      '${:,.0f}',
            'Profit':       '${:,.0f}',
            'Avg Margin %': '{:.1f}%',
            'Rev Share %':  '{:.2f}%',
            'Profit Share %': '{:.2f}%',
        })
        .set_properties(**{'text-align':'center'})
        .set_table_styles([
            {'selector':'th', 'props':[('text-align','center'),('font-weight','600'),
                                       ('background-color','#f8f8fc'),('color','#1a1a2e')]},
            {'selector':'td', 'props':[('text-align','center !important')]},
        ])
        .background_gradient(subset=['Rev Share %'], cmap='YlOrRd'),
        use_container_width=True, height=500)

    # ── Division Concentration ────────────────────────────────────────────────
    chart("Division Profit Concentration",
          "Divisional share of total gross profit — elevated concentration denotes portfolio dependency risk")
    if len(df) != len(df_full):
        st.markdown(
            '<p style="font-size:0.78rem;color:#6b6b8a;margin:4px 0 8px;">📌 Showing full portfolio — unaffected by filter selection</p>',
            unsafe_allow_html=True
        )

    div_pft = df_full.groupby('Division')['Gross Profit'].sum().reset_index()
    div_pft = div_pft.sort_values('Gross Profit', ascending=False).reset_index(drop=True)
    total_div = div_pft['Gross Profit'].sum()
    div_pft['Share %'] = (div_pft['Gross Profit'] / total_div * 100).round(1)

    DIV_COLORS = {'Chocolate': '#7B4F2E', 'Sugar': '#E8963A', 'Other': '#6C63FF'}
    DIV_BG     = {'Chocolate': '#f3ede8', 'Sugar': '#fdf3e7', 'Other': '#eeeeff'}

    progress_html = """
    <style>
      .div-progress-wrap { padding: 8px 0; font-family: 'DM Sans', sans-serif; max-width: 70%; }
      .div-row { display: flex; align-items: center; gap: 14px; margin-bottom: 18px; }
      .div-icon { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center;
                  justify-content: center; font-size: 18px; flex-shrink: 0; }
      .div-info { flex: 1; }
      .div-header { display: flex; justify-content: space-between; align-items: baseline;
                    font-size: 13px; color: #1a1a2e; margin-bottom: 6px; }
      .div-name { font-weight: 500; }
      .div-val { font-size: 12px; color: #555; }
      .div-track { height: 10px; background: #f0f0f5; border-radius: 6px; overflow: hidden; }
      .div-fill { height: 100%; border-radius: 6px; transition: width 0.6s ease; }
      .div-pct { font-size: 15px; font-weight: 600; min-width: 48px; text-align: right; }
    </style>
    <div class="div-progress-wrap">
    """

    icons = {'Chocolate': '🍫', 'Sugar': '🍭', 'Other': '🍪'}
    for _, row in div_pft.iterrows():
        div    = row['Division']
        pct    = row['Share %']
        profit = row['Gross Profit']
        is_selected = (sel_div == 'All' or div == sel_div)
        color  = DIV_COLORS.get(div, '#888') if is_selected else '#cccccc'
        bg     = DIV_BG.get(div, '#f5f5f5') if is_selected else '#f5f5f5'
        icon   = icons.get(div, '●')
        opacity = '1.0' if is_selected else '0.3'
        progress_html += f"""
        <div class="div-row" style="opacity:{opacity};">
          <div class="div-icon" style="background:{bg};">{icon}</div>
          <div class="div-info">
            <div class="div-header">
              <span class="div-name">{div}</span>
              <span class="div-val">${profit:,.0f}</span>
            </div>
            <div class="div-track">
              <div class="div-fill" style="width:{pct}%;background:{color};"></div>
            </div>
          </div>
          <div class="div-pct" style="color:{color};">{pct}%</div>
        </div>"""

    progress_html += "</div>"
    components.html(progress_html, height=180, scrolling=False)

    # ── Product Revenue/Profit Share Table ────────────────────────────────────
    chart("Product Revenue & Profit Share — Dependency Indicators",
          "Dependency indicators ranked per product — disproportionate share in few products exposes the portfolio to concentration risk")

    dep_full = ps_full[['Division','Product Name','Total_Sales','Total_Profit',
              'Revenue_Share_Pct','Profit_Share_Pct']]\
        .sort_values('Profit_Share_Pct', ascending=False)\
        .rename(columns={
            'Total_Sales':'Total Sales','Total_Profit':'Total Profit',
            'Revenue_Share_Pct':'Rev Share %','Profit_Share_Pct':'Profit Share %'
        })

    # Get selected products from product filter
    _sel_products_table = set(df['Product Name'].unique()) if len(df) != len(df_div) else set()

    if _sel_products_table:
        # Product filter active — show only selected products with original values
        dep = dep_full[dep_full['Product Name'].isin(_sel_products_table)]
    elif sel_div != 'All':
        # Division filter only — show only that division's products
        dep = dep_full[dep_full['Division'] == sel_div]
    else:
        dep = dep_full

    # Apply gradient on full data to get consistent colours, then filter rows to display
    styled = dep_full.style.format({
        'Total Sales':    '${:,.0f}',
        'Total Profit':   '${:,.0f}',
        'Rev Share %':    '{:.2f}%',
        'Profit Share %': '{:.2f}%',
    }).background_gradient(subset=['Profit Share %'], cmap='YlOrRd')

    # Extract only the rows we want to show but keep original gradient colours
    import pandas as pd
    display_idx = dep.index
    styled_export = styled.data.loc[display_idx]
    styled_display = styled_export.style.format({
        'Total Sales':    '${:,.0f}',
        'Total Profit':   '${:,.0f}',
        'Rev Share %':    '{:.2f}%',
        'Profit Share %': '{:.2f}%',
    }).background_gradient(subset=['Profit Share %'], cmap='YlOrRd',
                           vmin=dep_full['Profit Share %'].min(),
                           vmax=dep_full['Profit Share %'].max())\
      .set_properties(**{'text-align':'center'})\
      .set_table_styles([{
          'selector':'th',
          'props':[('text-align','center'),('font-weight','600'),
                   ('background-color','#f8f8fc'),('color','#1a1a2e')]
      }])

    st.dataframe(styled_display, use_container_width=True)

    # ── Strategic Assessment Cards ────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<div class="chart-header">Strategic Assessment</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Concentration risks, margin signals and growth opportunities across the portfolio</div>', unsafe_allow_html=True)
    _p4_filter_active = (sel_div != 'All') or bool(st.session_state.get('selected_products', []))
    if _p4_filter_active:
        st.markdown(
            "<p style='font-size:0.75rem;color:#888;margin:-6px 0 8px;'>"
            "📌 Assessment reflects full portfolio — unaffected by filter selection"
            "</p>",
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Derived values for cards ──────────────────────────────────────────────
    # Card 1: Product concentration risk
    prod_conc_pct   = round(n80r / total_portfolio * 100)
    if prod_conc_pct <= 30:
        prod_risk_label = "High"
        prod_risk_color = "#A32D2D"
        prod_risk_bg    = "#FCEBEB"
        prod_risk_border= "#E24B4A"
        prod_badge_text = f"{n80r} of {total_portfolio} products drive 80% of revenue"
    elif prod_conc_pct <= 50:
        prod_risk_label = "Moderate"
        prod_risk_color = "#854F0B"
        prod_risk_bg    = "#FAEEDA"
        prod_risk_border= "#EF9F27"
        prod_badge_text = f"{n80r} of {total_portfolio} products drive 80% of revenue"
    else:
        prod_risk_label = "Low"
        prod_risk_color = "#3B6D11"
        prod_risk_bg    = "#EAF3DE"
        prod_risk_border= "#639922"
        prod_badge_text = f"{n80r} of {total_portfolio} products drive 80% of revenue"

    # Card 2: Geographic concentration risk
    geo_conc_pct = round(n80_state / n_states_full * 100)
    if geo_conc_pct <= 30:
        geo_risk_label  = "High"
        geo_risk_color  = "#A32D2D"
        geo_risk_bg     = "#FCEBEB"
        geo_risk_border = "#E24B4A"
    elif geo_conc_pct <= 50:
        geo_risk_label  = "Moderate"
        geo_risk_color  = "#854F0B"
        geo_risk_bg     = "#FAEEDA"
        geo_risk_border = "#EF9F27"
    else:
        geo_risk_label  = "Low"
        geo_risk_color  = "#3B6D11"
        geo_risk_bg     = "#EAF3DE"
        geo_risk_border = "#639922"

    # Card 3: Division balance — largest division profit share
    max_div_share = div_pft['Share %'].max()
    max_div_name  = div_pft.loc[div_pft['Share %'].idxmax(), 'Division']
    div_bal_label = "Skewed" if max_div_share >= 50 else "Balanced"
    div_bal_color = "#4B47C4"
    div_bal_bg    = "#EFEFFD"
    div_bal_border= "#C0BEF5"

    # Card 4: Margin quality — CV of top-5 Pareto products
    top5_products = rev_full.head(5)['Product Name'].tolist()
    top5_margins  = ps_full[ps_full['Product Name'].isin(top5_products)]['Gross_Margin_Pct'] \
                    if 'Gross_Margin_Pct' in ps_full.columns else pd.Series(dtype=float)
    if not top5_margins.empty and top5_margins.mean() != 0:
        margin_cv = top5_margins.std() / top5_margins.mean() * 100
    else:
        margin_cv = 0
    margin_label  = "Stable" if margin_cv < 15 else "Watch"
    margin_color  = "#3B6D11" if margin_cv < 15 else "#854F0B"
    margin_bg     = "#EAF3DE" if margin_cv < 15 else "#FAEEDA"
    margin_border = "#639922" if margin_cv < 15 else "#EF9F27"
    margin_sub    = "Consistent gross margin across top products — no margin compression detected." \
                    if margin_cv < 15 else \
                    "Margin variance detected across top products — monitor pricing."

    # Card 5: Tail product drag
    tail_count = total_portfolio - n80r

    # Card 6: Untapped regional coverage
    tail_states = n_states_full - n80_state

    # ── Render assessment cards — full-width stacked, reference style ────────
    def _assessment_card(border_color, bg_color, icon, title, title_color, body, bullets,
                         badge_text='', badge_bg='', badge_color='', badge_border=''):
        bullet_html = "".join(
            f'<div style="font-size:13.5px;color:#2a2a3a;margin-top:5px;line-height:1.5;">{b}</div>'
            for b in bullets
        )
        badge_html = (
            f'<span style="font-size:11.5px;font-weight:600;color:{badge_color};'
            f'background:{badge_bg};border:1.5px solid {badge_border};'
            f'border-radius:20px;padding:3px 11px;white-space:nowrap;">'
            f'{badge_text}</span>'
        ) if badge_text else ''
        return f"""
        <div style="border-left:5px solid {border_color};background:{bg_color};
                    border-radius:10px;padding:22px 28px;margin-bottom:20px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.06);width:100%;">
          <div style="font-size:15.5px;font-weight:700;color:{title_color};margin-bottom:10px;
                      display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            {icon}&nbsp;{title}{('&nbsp;' + badge_html) if badge_html else ''}
          </div>
          <div style="font-size:13.5px;color:#3a3a4a;line-height:1.7;margin-bottom:8px;">{body}</div>
          {bullet_html}
        </div>"""

    # ── Card 1: Product concentration risk ───────────────────────────────────
    top_n_products = rev_full.head(n80r)[['Product Name']].copy()
    _margin_cols = ['Product Name','Division','Total_Sales','Gross_Margin_Pct'] \
        if 'Gross_Margin_Pct' in ps_full.columns else ['Product Name','Division','Total_Sales']
    top_n_products = top_n_products.merge(
        ps_full[_margin_cols],
        on='Product Name', how='left'
    )
    prod_bullets = [
        f"<strong>{row['Product Name']}</strong> ({row['Division']}) — "
        f"{row['Gross_Margin_Pct']:.1f}% margin, ${row['Total_Sales']:,.0f} sales"
        for _, row in top_n_products.iterrows()
    ] if 'Gross_Margin_Pct' in ps_full.columns else [
        f"<strong>{row['Product Name']}</strong> ({row['Division']}) — "
        f"${row['Total_Sales']:,.0f} sales"
        for _, row in top_n_products.iterrows()
    ]

    st.markdown(_assessment_card(
        border_color = prod_risk_border,
        bg_color     = prod_risk_bg,
        icon         = "⚠️",
        title        = f"Product Concentration Risk — {prod_risk_label}",
        title_color  = prod_risk_color,
        body         = (
            f"{n80r} of {total_portfolio} products drive 80% of total revenue. "
            f"If a top product underperforms, the impact on overall revenue is outsized."
        ),
        bullets      = [],
        badge_text   = "Fragile top-5 dependency",
        badge_bg     = "#FEECEC",
        badge_color  = "#C0392B",
        badge_border = "#F1A9A9",
    ), unsafe_allow_html=True)

    # ── Card 2: Geographic concentration risk ────────────────────────────────
    top_states_list = state_rev_full.head(n80_state)[['State/Province','Total_Sales']].copy()
    top_states_list['pct'] = (top_states_list['Total_Sales'] / state_rev_full['Total_Sales'].sum() * 100).round(1)
    geo_bullets = [
        f"<strong>{row['State/Province']}</strong> — "
        f"${row['Total_Sales']:,.0f} revenue ({row['pct']:.1f}% of total)"
        for _, row in top_states_list.head(5).iterrows()
    ]
    if n80_state > 5:
        geo_bullets.append(f"<em style='color:#6b6b8a;font-size:12px;'>+ {n80_state - 5} more states in the 80% threshold</em>")

    st.markdown(_assessment_card(
        border_color = geo_risk_border,
        bg_color     = geo_risk_bg,
        icon         = "📍",
        title        = f"Geographic Concentration Risk — {geo_risk_label}",
        title_color  = geo_risk_color,
        body         = (
            f"{n80_state} of {n_states_full} states cover 80% of total revenue. "
            f"The top state drives {top_state_pct:.1f}% of revenue — track performance closely."
        ),
        bullets      = [],
        badge_text   = "Monitor dependency",
        badge_bg     = "#FEF6E4",
        badge_color  = "#9A6200",
        badge_border = "#F5D98B",
    ), unsafe_allow_html=True)

    # ── Card 3: Division balance ──────────────────────────────────────────────
    div_bullets = [
        f"<strong>{row['Division']}</strong> — {row['Share %']:.1f}% of total profit (${row['Gross Profit']:,.0f})"
        for _, row in div_pft.iterrows()
    ]

    st.markdown(_assessment_card(
        border_color = div_bal_border,
        bg_color     = div_bal_bg,
        icon         = "🏢",
        title        = f"Division Balance — {div_bal_label}",
        title_color  = div_bal_color,
        body         = (
            f"{max_div_name} holds {max_div_share:.1f}% of total profit share — "
            f"{'one division anchors the portfolio; review divisional mix.' if div_bal_label == 'Skewed' else 'divisions are reasonably balanced.'}"
        ),
        bullets      = [],
        badge_text   = "Review divisional mix",
        badge_bg     = "#EFEFFD",
        badge_color  = "#4B47C4",
        badge_border = "#C0BEF5",
    ), unsafe_allow_html=True)

    # ── Card 4: Margin quality signal ────────────────────────────────────────
    top5_detail = ps_full[ps_full['Product Name'].isin(top5_products)].copy() \
                  if 'Gross_Margin_Pct' in ps_full.columns else pd.DataFrame()
    if not top5_detail.empty:
        top5_detail = top5_detail.sort_values('Gross_Margin_Pct', ascending=False)
        margin_bullets = [
            f"<strong>{row['Product Name']}</strong> ({row['Division']}) — "
            f"{row['Gross_Margin_Pct']:.1f}% margin"
            for _, row in top5_detail.iterrows()
        ]
    else:
        margin_bullets = []

    st.markdown(_assessment_card(
        border_color = margin_border,
        bg_color     = margin_bg,
        icon         = "📈",
        title        = f"Margin Quality Signal — {margin_label}",
        title_color  = margin_color,
        body         = margin_sub,
        bullets      = margin_bullets,
        badge_text   = "No margin erosion detected",
        badge_bg     = "#EAFAF1",
        badge_color  = "#1E8449",
        badge_border = "#A9DFBF",
    ), unsafe_allow_html=True)

    # ── Card 5: Tail product drag ─────────────────────────────────────────────
    tail_products = rev_full.tail(tail_count)[['Product Name']].copy()
    tail_products = tail_products.merge(
        ps_full[['Product Name','Division','Total_Sales','Gross_Margin_Pct']],
        on='Product Name', how='left'
    ) if 'Gross_Margin_Pct' in ps_full.columns else tail_products.merge(
        ps_full[['Product Name','Division','Total_Sales']], on='Product Name', how='left'
    )
    tail_bullets = [
        f"<strong>{row['Product Name']}</strong> ({row['Division']}) — "
        f"{row['Gross_Margin_Pct']:.1f}% margin, ${row['Total_Sales']:,.0f} sales"
        for _, row in tail_products.iterrows()
    ] if 'Gross_Margin_Pct' in tail_products.columns else [
        f"<strong>{row['Product Name']}</strong> ({row['Division']}) — ${row['Total_Sales']:,.0f} sales"
        for _, row in tail_products.iterrows()
    ]

    st.markdown(_assessment_card(
        border_color = "#E24B4A",
        bg_color     = "#FCEBEB",
        icon         = "📦",
        title        = "Tail Product Drag",
        title_color  = "#A32D2D",
        body         = (
            f"The bottom {tail_count} products contribute only 20% of revenue. "
            f"Review each for Discontinue or Promote action."
        ),
        bullets      = [],
        badge_text   = "Product Rationalisation",
        badge_bg     = "#FEECEC",
        badge_color  = "#C0392B",
        badge_border = "#F1A9A9",
    ), unsafe_allow_html=True)

    # ── Card 6: Untapped regional coverage ───────────────────────────────────
    tail_states_list = state_rev_full.tail(tail_states)[['State/Province','Total_Sales']].copy()
    tail_states_list['pct'] = (tail_states_list['Total_Sales'] / state_rev_full['Total_Sales'].sum() * 100).round(2)
    tail_states_list = tail_states_list.sort_values('Total_Sales', ascending=False)
    expansion_bullets = [
        f"<strong>{row['State/Province']}</strong> — ${row['Total_Sales']:,.0f} revenue ({row['pct']:.2f}% of total)"
        for _, row in tail_states_list.head(8).iterrows()
    ]
    if tail_states > 8:
        expansion_bullets.append(
            f"<em style='color:#6b6b8a;font-size:12px;'>+ {tail_states - 8} more low-revenue states with growth potential</em>"
        )

    st.markdown(_assessment_card(
        border_color = "#EF9F27",
        bg_color     = "#FAEEDA",
        icon         = "🗺️",
        title        = "Untapped Regional Coverage",
        title_color  = "#854F0B",
        body         = (
            f"{tail_states} of {n_states_full} states account for only 20% of revenue. "
            f"Significant growth opportunity exists in underleveraged markets."
        ),
        bullets      = [],
        badge_text   = "Expansion headroom exists",
        badge_bg     = "#FEF6E4",
        badge_color  = "#9A6200",
        badge_border = "#F5D98B",
    ), unsafe_allow_html=True)