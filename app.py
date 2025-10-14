import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard Operacional", layout="wide")

# --- CSS para layout e abas customizadas + cards Diárias ---
st.markdown("""
<style>
body {background-color: #f4f9ff;}
div[data-testid="stHorizontalBlock"] > div {margin-bottom: -8px;}
.stButton>button {
  border-radius: 12px 12px 0 0 !important;
  padding: 7px 25px 5px 25px !important;
  margin: 0 6px 0 0 !important;
  border: none !important;
  font-size: 1em !important;
  font-weight: 700 !important;
  color: #2266ee !important;
  background: #e7eefb !important;
  transition: background .18s, color .18s;
}
.stButton>button.selected-tab {
  background: #2266ee !important;
  color: #fff !important;
  box-shadow: 0 4px 14px #2266ee47;
}
.stButton>button:focus {outline: 2px solid #205491;}
.kpi-row {display:flex;gap:12px;margin-bottom:8px;}
.kpi-card {flex:1;background:#fff;padding:10px 0 8px 12px;border-radius:10px;color:#fff;display:flex;flex-direction:column;align-items:flex-start;box-shadow:0 2px 8px #0003;font-size:0.85em;}
.kpi-blue {background:#2266ee;}
.kpi-green {background:#23b26d;}
.kpi-purple {background:#9b1de9;}
.kpi-orange {background:#ff7927;}
.kpi-val {font-size:1.5em;font-weight:800;}
.kpi-title {font-size:0.85em;font-weight:600;}
.graph-row {display:flex;gap:12px;margin-bottom:3px;align-items:stretch;}
.graph-container {flex:1;background:#f6faff;border-radius:8px;box-shadow:0 2px 6px #0001;overflow:hidden;display:flex;flex-direction:column;}
.graph-title {background:#e8f0fa;padding:6px 12px;font-weight:bold;font-size:0.9em;color:#2a2a2a;text-align:center;border-bottom:1px solid #d0dfe8;}
.graph-content {padding:4px;flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;}
.goal-box {background:#eaffef;border-left:5px solid #19bb62;padding:5px 12px 4px 12px; border-radius:6px; font-weight:600;font-size:0.8em;color:#137749;box-shadow:0 1px 5px #19bb6222;margin:4px 0;}
.obs-box {background:#fff9e6;border-left:5px solid #ffe066;margin-top:15px;font-size:0.82em;padding:8px 12px 6px 12px;border-radius:6px;color:#a16100;}
.dashboard-header {background:#ffffff;padding:10px 20px;margin:-60px -60px 10px -60px;border-bottom:3px solid #2266ee;display:flex;justify-content:space-between;align-items:center;}
.header-left h1 {font-size:1.25em;font-weight:800;color:#1a4d9e;margin:0;padding:0;line-height:1.2;}
.header-left p {font-size:0.8em;color:#5a5a5a;margin:2px 0 0 0;padding:0;}
.header-right {text-align:right;}
.header-right .periodo-label {font-size:0.7em;color:#5a5a5a;margin:0;}
.header-right .periodo-value {font-size:1.05em;font-weight:700;color:#1a4d9e;margin:0;}
@media (max-width: 1000px) {.graph-row{flex-direction:column;gap:0px;}}

/* KPIs apenas para a aba Diárias */
.diarias-kpi-row {display: flex; gap: 18px; margin-bottom: 14px;}
.diarias-kpi-card {flex: 1; padding: 18px 0 10px 0; border-radius: 10px; display: flex; flex-direction: column; align-items: center; box-shadow: 0 2px 8px #0001;}
.diarias-kpi-blue {background: #e8f0fe; color: #205891;}
.diarias-kpi-green {background: #e6f8ef; color: #178655;}
.diarias-kpi-purple {background: #f3e9fd; color: #781bc4;}
.diarias-kpi-title {font-size: 1.01em; font-weight: 600; margin-bottom:2px;}
.diarias-kpi-val {font-size: 2.3em; font-weight:900; line-height:1;}
.diarias-card-sucesso {background:#eaffee; border-left:6px solid #19bb62; border-radius:8px; padding:13px 18px 12px 18px; margin-bottom:16px; margin-top:2px; font-weight:500; color:#178655;}
.diarias-card-sucesso b {font-size:1.03em;}
.diarias-motivos {background:#fff7e4; border-left:6px solid #ffba4f; border-radius:8px; padding:13px 19px 12px 19px; margin-bottom:18px; margin-top:1px; color:#b67804;}
.diarias-motivos-title {margin-bottom:7px; font-weight: 700; font-size:1.05em;}
@media (max-width:1000px){.diarias-kpi-row{flex-direction:column;gap:9px;}}
</style>
""", unsafe_allow_html=True)

# ------------ Cabeçalho do Dashboard --------------
st.markdown("""
<div class="dashboard-header">
  <div class="header-left">
    <h1>Dashboard Semanal Outubro 2025</h1>
    <p>Relatório de Contratação de Temporários - Mendes RH</p>
  </div>
  <div class="header-right">
    <p class="periodo-label">Período</p>
    <p class="periodo-value">Semana 01/10 a 12/10</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ------------ Tabs horizontais --------------
tab_names = ["Visão Geral", "Análise SLA", "Diárias", "Histórico"]
if "current_tab" not in st.session_state:
    st.session_state.current_tab = tab_names[0]

def set_tab(tab):
    st.session_state.current_tab = tab

tab_cols = st.columns(len(tab_names))
for i, tab in enumerate(tab_names):
    btn_class = "selected-tab" if st.session_state.current_tab == tab else ""
    tab_cols[i].button(tab, key=tab, on_click=set_tab, args=(tab,), help=None, type="secondary")
    tab_cols[i].markdown(
        f"""<style>
        [data-testid="stButton"] button#{tab} {{ {'background:#2266ee !important;color:#fff !important;box-shadow:0 4px 14px #2266ee47;' if st.session_state.current_tab == tab else ''} }}
        </style>""",
        unsafe_allow_html=True,
    )

# =========== VISÃO GERAL ============
if st.session_state.current_tab == "Visão Geral":
    sla = pd.read_csv('dados/SLA.csv', sep=';', decimal=',', encoding='latin1')
    pedidos = pd.read_csv('dados/ANALISE_PEDIDO.csv', sep=';', decimal=',', encoding='latin1')

    sla_percent = sla['taxa'].iloc[0] * 100
    diaria_val = pedidos['Taxa'].iloc[0]
    diaria_percent = float(str(diaria_val).replace(",", ".").replace("%", "")) if "%" in str(diaria_val) else float(diaria_val) * 100

    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card kpi-blue"><span class="kpi-title">Total de Pedidos</span><span class="kpi-val">{sla['Solicitado'].iloc[0]}</span></div>
      <div class="kpi-card kpi-green"><span class="kpi-title">Taxa SLA</span><span class="kpi-val">{sla_percent:.1f}%</span></div>
      <div class="kpi-card kpi-purple"><span class="kpi-title">Diárias Entregues</span><span class="kpi-val">{pedidos['Entregue'].iloc[0]}</span></div>
      <div class="kpi-card kpi-orange"><span class="kpi-title">Taxa Diárias</span><span class="kpi-val">{diaria_percent:.2f}%</span></div>
    </div>
    """, unsafe_allow_html=True)

    col_pie, col_bar = st.columns(2, gap="medium")
    with col_pie:
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        st.markdown('<div class="graph-title">Desempenho SLA - 01/10 a 12/10</div>', unsafe_allow_html=True)
        st.markdown('<div class="graph-content">', unsafe_allow_html=True)

        no_prazo = sla["No_prazo"].iloc[0]
        fora_prazo = sla["Fora_prazo"].iloc[0]
        pie_labels = ["No Prazo", "Fora do Prazo"]
        pie_vals = [no_prazo, fora_prazo]
        pie_colors = ['#2266ee', '#f65054']

        fig_pie = px.pie(
            values=pie_vals,
            names=pie_labels,
            hole=0.40,
            color_discrete_sequence=pie_colors
        )
        fig_pie.update_traces(
            textinfo="percent",
            textposition="inside",
            textfont=dict(size=14, color="#ffffff"),
            marker=dict(line=dict(color='#ffffff', width=2)),
            pull=[0.02, 0.02]
        )
        fig_pie.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(size=10, color="#1a1a1a")
            ),
            margin=dict(l=5, r=5, t=5, b=5),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=180
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_bar:
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        st.markdown('<div class="graph-title">Diárias - 01/10 a 12/10</div>', unsafe_allow_html=True)
        st.markdown('<div class="graph-content">', unsafe_allow_html=True)
        solicitadas = pedidos.Solicitado.iloc[0]
        entregues = pedidos.Entregue.iloc[0]
        saldo = entregues - solicitadas

        comp_df = pd.DataFrame({"Tipo": ["Solicitadas", "Entregues"], "Qtd": [solicitadas, entregues]})
        fig_bar = px.bar(
            comp_df, x="Tipo", y="Qtd", text_auto='.0f',
            color="Tipo", color_discrete_map={"Solicitadas":"#FFA500","Entregues":"#23B26D"}
        )
        fig_bar.update_traces(
    texttemplate='<b>%{y}</b>',
    textposition='inside',  # <- Aqui está a mudança!
    textfont=dict(size=14, color="#fff")   # Recomendo cor clara para melhor contraste dentro da barra!
)
        fig_bar.update_layout(
            showlegend=False,
            xaxis=dict(
                title="",
                tickfont=dict(size=11, color="#1a1a1a")
            ),
            yaxis=dict(
                title="",
                showticklabels=True,
                tickfont=dict(size=9, color="#1a1a1a"),
                range=[0, max(solicitadas, entregues) * 1.15]
            ),
            margin=dict(l=12, r=12, t=8, b=8),
            height=150,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar":False})

        st.markdown(
            f"""<div class='goal-box'>✅ Superamos a meta! Entregamos {saldo} diárias a mais que o solicitado ({diaria_percent:.2f}%)</div>""",
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="obs-box">
    <b>Observações Importantes - 01/10 a 12/10</b>
    <ul>
      <li><b>SLA:</b> A redução na diária de eventos (de R$ 80,00 para R$ 57,37) impactou diretamente a performance, gerando dificuldades nas entregas do VO. O restabelecimento da diária para R$ 80,00 foi a chave para a recuperação imediata, elevando a performance de entrega para acima de 97%, comprovando a eficácia do incentivo financeiro.).</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# =========== ANÁLISE SLA ============
elif st.session_state.current_tab == "Análise SLA":
    sla = pd.read_csv('dados/SLA.csv', sep=';', decimal=',', encoding='latin1')
    total = int(sla['Solicitado'].iloc[0])
    dentro = int(sla['No_prazo'].iloc[0])
    fora = int(sla['Fora_prazo'].iloc[0])
    perc_dentro = dentro / total * 100
    perc_fora = fora / total * 100

    # KPIs Análise SLA
    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card kpi-blue">
        <span class="kpi-title">Total de Solicitações</span>
        <span class="kpi-val">{total}</span>
      </div>
      <div class="kpi-card kpi-green">
        <span class="kpi-title">Dentro do Prazo</span>
        <span class="kpi-val">{dentro}</span>
        <span style="font-size:0.92em;color:#e9ffe1;margin-left:2px;">{perc_dentro:.2f}% do total</span>
      </div>
      <div class="kpi-card kpi-orange">
        <span class="kpi-title">Fora do Prazo</span>
        <span class="kpi-val">{fora}</span>
        <span style="font-size:0.92em;color:#fffbe5;margin-left:2px;">{perc_fora:.2f}% do total</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Indicador Circular (Gauge)
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = perc_dentro,
        delta = {'reference': 100, 'increasing': {'color': "#ff7927"}, 'decreasing': {'color': "#23B26D"}},
        number = {'suffix': " %", 'font': {'size': 32}},
        title = {'text': "SLA Cumprido (%)", 'font': {'size': 17}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 2},
            'bar': {'color': "#23B26D"},
            'bgcolor': "#eaeaee",
            'steps': [
                {'range': [0, perc_dentro], 'color': "#23B26D"},
                {'range': [perc_dentro, 100], 'color': "#ffebdf"},
            ],
            'threshold': {
                'line': {'color': "#FF7927", 'width': 4},
                'thickness': 0.7,
                'value': perc_dentro
            }
        }
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=22, r=22, t=22, b=20),
        paper_bgcolor="#f6f9fd",
        font=dict(size=15)
    )
    st.markdown('<div class="graph-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    # Bloco azul - Contexto Evento VO
    st.markdown("""
    <div class="obs-box" style="background:#e8f1fd;border-left:5px solid #5aa7db;color:#164976;font-size:1.04em;margin-top:10px;font-weight:500;">
    <b>Contexto do Evento VO (18/09)</b><br>
    O evento de encerramento do VO ocorreu em <b>18/09/2025</b>, porém as solicitações chegaram apenas em <b>15/09/2025</b>, deixando apenas <b>3 dias</b> para contratação, muito abaixo do SLA de 10 dias.<br>
    Apesar dos esforços da equipe, não foi possível entregar 13 temporários dentro desse prazo extremamente curto. Excluindo esse evento excepcional, a taxa de cumprimento do SLA seria de <b style="color:#205891;">81.98%</b>.
    </div>
    """, unsafe_allow_html=True)

# =========== DIÁRIAS ============
elif st.session_state.current_tab == "Diárias":
    pedidos = pd.read_csv('dados/ANALISE_PEDIDO.csv', sep=';', decimal=',', encoding='latin1')
    solicitadas = int(pedidos.Solicitado.iloc[0])
    entregues = int(pedidos.Entregue.iloc[0])
    saldo = entregues - solicitadas
    taxa = float(str(pedidos['Taxa'].iloc[0]).replace(",", ".").replace("%", "")) if "%" in str(pedidos['Taxa'].iloc[0]) else float(pedidos['Taxa'].iloc[0]) * 100

    # Cards superiores
    st.markdown(f"""
    <div class="diarias-kpi-row">
        <div class="diarias-kpi-card diarias-kpi-blue">
            <span class="diarias-kpi-title">Solicitadas</span>
            <span class="diarias-kpi-val">{solicitadas}</span>
        </div>
        <div class="diarias-kpi-card diarias-kpi-green">
            <span class="diarias-kpi-title">Entregues</span>
            <span class="diarias-kpi-val">{entregues}</span>
        </div>
        <div class="diarias-kpi-card diarias-kpi-purple">
            <span class="diarias-kpi-title">Taxa de Atendimento</span>
            <span class="diarias-kpi-val">{taxa:.2f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Gráfico de barras
    fig_barras = go.Figure()
    fig_barras.add_trace(go.Bar(
        x=["01/10 a 12/10"],
        y=[solicitadas],
        name="Solicitadas",
        marker=dict(color="#FFA500"),
        text=[solicitadas],
        textposition="outside"
    ))
    fig_barras.add_trace(go.Bar(
        x=["01/10 a 12/10"],
        y=[entregues],
        name="Entregues",
        marker=dict(color="#23B26D"),
        text=[entregues],
        textposition="outside"
    ))
    fig_barras.update_layout(
        barmode='group',
        xaxis=dict(title="", tickfont=dict(size=13, color="#212121")),
        yaxis=dict(title="", showticklabels=True, tickfont=dict(size=13, color="#666"), range=[0, max(solicitadas, entregues) * 1.15]),
        height=310,
        margin=dict(t=30, b=30, l=28, r=28),
        legend=dict(orientation='h', x=0.5, y=-0.20, xanchor='center', font=dict(size=13)),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff"
    )
    st.plotly_chart(fig_barras, use_container_width=True, config={"displayModeBar": False})

    # Bloco verde sucesso
    st.markdown(f"""
    <div class="diarias-card-sucesso">
      <b>Desempenho Excepcional</b><br>
      Em setembro, superamos as expectativas ao entregar <b>{entregues} diárias</b>, quando foram solicitadas <b>{solicitadas}</b>, resultando em uma diferença positiva de <b style="color:#12bb26;">+{saldo} diárias</b>.<br>
      Taxa de atendimento: <b>{taxa:.2f}%</b>.
    </div>
    """, unsafe_allow_html=True)

    # Bloco laranja motivos
    st.markdown("""
    <div class="diarias-motivos">
      <div class="diarias-motivos-title">Motivos para Diárias Acima do Solicitado</div>
      <ol style="margin-top:0.1em;margin-bottom:0.1em;">
        <li>Alguns temporários foram enviados para área sem STH (Solicitação de Trabalho em Horário especial).</li>
        <li>Algumas STHs estavam vencidas, mas os temporários continuaram trabalhando.</li>
        <li>Nos eventos de segunda no VO, entregamos temporários acima das solicitações para compensar o período em que estávamos com diária mais baixa.</li>
      </ol>
    </div>
    """, unsafe_allow_html=True)

# =========== HISTÓRICO ============
if st.session_state.current_tab == "Histórico":
    # ----------- Histórico de Prazo de Entregas (SLA) -----------
    sla_hist = pd.read_csv('dados/HISTORICO_SLA.csv', sep=';', encoding='latin1')
    sla_hist.columns = ['Mes', 'Taxa']
    sla_hist['Taxa'] = sla_hist['Taxa'].map(lambda x: float(str(x).replace(",", ".").strip()))
    sla_hist['Fora'] = 1 - sla_hist['Taxa']
    sla_hist['No Prazo (%)'] = sla_hist['Taxa'] * 100
    sla_hist['Fora do Prazo (%)'] = sla_hist['Fora'] * 100

    st.markdown("""
<div style="background:#fff;border-radius:16px;padding:28px 35px 26px 35px;margin-bottom:28px;box-shadow:0 1px 8px #0001;">
    <div style="font-weight:800;font-size:1.20em;margin-bottom:12px;">Histórico de Prazos de Entregas (Março - Setembro)</div>
</div>
""", unsafe_allow_html=True)

    # gráfico empilhado SLA
    meses = sla_hist['Mes']
    fig1 = go.Figure(data=[
        go.Bar(
            name='No Prazo',
            x=meses, y=sla_hist['No Prazo (%)'],
            marker_color='#2266ee',
            text=[f"{v:.1f}%" for v in sla_hist['No Prazo (%)']],
            textposition='inside',
            insidetextanchor='middle',
            textfont=dict(color="#fff", size=12)
        ),
        go.Bar(
            name='Fora do Prazo',
            x=meses, y=sla_hist['Fora do Prazo (%)'],
            marker_color='#f65054',
            text=[f"{v:.1f}%" for v in sla_hist['Fora do Prazo (%)']],
            textposition='inside',
            insidetextanchor='middle',
            textfont=dict(color="#fff", size=12)
        )
    ])
    fig1.update_layout(
        barmode='stack',
        xaxis=dict(tickfont=dict(size=15)),
        yaxis=dict(title='', range=[0, 100], tickfont=dict(size=14)),
        legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center', font=dict(size=13)),
        height=350,
        margin=dict(l=20, r=20, t=80, b=38),
        plot_bgcolor='#fff', paper_bgcolor='#fff'
    )
    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

    
    # ----------- Histórico de Diárias Entregues -----------
    ent_hist = pd.read_csv('dados/HISTORICO_ENTREGA.csv', sep=';', encoding='latin1')
    ent_hist.columns = ['Mês', 'Solicitadas', 'Entregues', 'Taxa']
    ent_hist['Solicitadas'] = ent_hist['Solicitadas'].astype(int)
    ent_hist['Entregues'] = ent_hist['Entregues'].astype(int)
    ent_hist['Taxa_float'] = ent_hist['Taxa'].map(lambda x: float(str(x).replace(',', '.')))
    ent_hist['Taxa_%'] = ent_hist['Taxa_float'] * 100

    st.markdown("""
<div style="background:#fff;border-radius:16px;padding:28px 35px 26px 35px;margin-bottom:28px;box-shadow:0 1px 8px #0001;">
    <div style="font-weight:800;font-size:1.20em;margin-bottom:12px;">Histórico de Diárias Entregues (Janeiro - Setembro)</div>
</div>
""", unsafe_allow_html=True)

    meses = ent_hist['Mês']
    fig2 = go.Figure()
    # Barras - Solicitadas
    fig2.add_trace(go.Bar(
        x=meses,
        y=ent_hist['Solicitadas'],
        name='Solicitadas',
        marker_color='#FFA500',
        text=ent_hist['Solicitadas'],
        textposition='outside',
        textfont=dict(size=11, color="#222")
    ))
    # Barras - Entregues
    fig2.add_trace(go.Bar(
        x=meses,
        y=ent_hist['Entregues'],
        name='Entregues',
        marker_color='#23B26D',
        text=ent_hist['Entregues'],
        textposition='outside',
        textfont=dict(size=11, color="#222")
    ))
    # Linha - Taxa (%) - rótulo branco e maior espaço superior para não cortar o label
    fig2.add_trace(go.Scatter(
        x=meses,
        y=ent_hist['Taxa_%'],
        mode='lines+markers+text',
        name='Taxa (%)',
        line=dict(color='#2266ee', width=2, shape='spline'),
        marker=dict(size=8, color='#2266ee'),
        text=[f"{tx:.2f}%" for tx in ent_hist['Taxa_%']],
        textposition="top center",
        textfont=dict(size=14, color="#fff")
    ))
    fig2.update_layout(
        barmode='group',
        xaxis=dict(tickfont=dict(size=13)),
        yaxis=dict(title='', tickfont=dict(size=12), showgrid=True),
        legend=dict(
            orientation='h', y=-0.22, x=0.5, xanchor='center', font=dict(size=13)
        ),
        height=540,         # Mais espaço para label!
        margin=dict(l=20, r=20, t=120, b=38),  # Top bem grande!
        plot_bgcolor='#fff',
        paper_bgcolor='#fff'
    )
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

    # ----------- Análise de Tendências -----------
    st.markdown("""
<div style="background:#f5faf9;border-radius:16px;padding:18px 35px 24px 35px;margin-bottom:8px;box-shadow:0 1px 6px #0001;">
    <div style="font-weight:800;font-size:1.13em;margin-bottom:12px;">Análise de Tendências</div>
    <div style="display:flex;gap:32px;flex-wrap:wrap;">
        <div style="flex:1;min-width:260px;background:#fff;border-radius:9px;padding:18px 18px 15px 18px;margin-bottom:8px;box-shadow:0 1px 5px #0001;">
            <div style="color:#16c06b;font-weight:700;margin-bottom:3px;">
                <span style="font-size:1.08em;">&#8593; Pontos Positivos</span>
            </div>
            <ul style="font-size:1em;margin-left:6px;margin-bottom:0;">
                <li>Melhoria consistente na taxa de diárias desde março</li>
                <li>Taxa de SLA de setembro (73,39%) mantém-se acima da média histórica considerando o evento excepcional</li>
                <li>Superação das diárias solicitadas demonstra comprometimento</li>
            </ul>
        </div>
        <div style="flex:1;min-width:260px;background:#fff;border-radius:9px;padding:18px 18px 15px 18px;margin-bottom:8px;box-shadow:0 1px 5px #0001;">
            <div style="color:#FFA500;font-weight:700;margin-bottom:3px;">
                <span style="font-size:1.08em;">&#9888; Pontos de Atenção</span>
            </div>
            <ul style="font-size:1em;margin-left:6px;margin-bottom:0;">
                <li>Necessidade de antecedência mínima para eventos especiais</li>
                <li>Controle mais rigoroso de STHs vencidas</li>
                <li>Padronização do envio de temporários conforme solicitações</li>
            </ul>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

