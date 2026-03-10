import streamlit as st
import pandas as pd
import datetime as dt
import re
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from pathlib import Path
import base64
import os
import glob

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard Operacional Mendes RH", layout="wide")

# --- CSS Customizado ---
st.markdown("""
<style>
body {background-color: #f4f9ff;}
div[data-testid="stHorizontalBlock"] > div {margin-bottom: -8px;}
.stButton>button {border-radius: 12px 12px 0 0 !important; padding: 7px 25px 5px 25px !important; margin: 0 6px 0 0 !important; border: none !important; font-size: 1em !important; font-weight: 700 !important; color: #2266ee !important; background: #e7eefb !important; transition: background .18s, color .18s;}
.stButton>button.selected-tab {background: #2266ee !important; color: #fff !important; box-shadow: 0 4px 14px #2266ee47;}
.kpi-row {display:flex;gap:12px;margin-bottom:8px;}
.kpi-card {flex:1;background:#fff;padding:10px 0 8px 12px;border-radius:10px;color:#fff;display:flex;flex-direction:column;align-items:flex-start;box-shadow:0 2px 8px #0003;font-size:0.85em;}
.kpi-blue {background:#2266ee;}
.kpi-green {background:#23b26d;}
.kpi-purple {background:#9b1de9;}
.kpi-orange {background:#ff7927;}
.kpi-val {font-size:1.5em;font-weight:800;}
.kpi-title {font-size:0.85em;font-weight:600;}
.diarias-kpi-row {display: flex; gap: 18px; margin-bottom: 14px;}
.diarias-kpi-card {flex: 1; padding: 18px 0 10px 0; border-radius: 10px; display: flex; flex-direction: column; align-items: center; box-shadow: 0 2px 8px #0001;}
.diarias-kpi-blue {background: #e8f0fe; color: #205891;}
.diarias-kpi-green {background: #e6f8ef; color: #178655;}
.diarias-kpi-purple {background: #f3e9fd; color: #781bc4;}
.diarias-kpi-title {font-size: 1.01em; font-weight: 600; margin-bottom:2px;}
.diarias-kpi-val {font-size: 2.3em; font-weight:900; line-height:1;}
.diarias-card-sucesso {background:#eaffee; border-left:6px solid #19bb62; border-radius:8px; padding:13px 18px 12px 18px; margin-bottom:16px; margin-top:2px; font-weight:500; color:#178655;}
.obs-box {background:#fff; border-left:5px solid #2266ee; border-radius:8px; padding:15px; margin-top:10px; font-size:0.95em; color:#333; box-shadow:0 1px 5px #0001;}
</style>
""", unsafe_allow_html=True)

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file: return base64.b64encode(img_file.read()).decode()
    except: return ""

base_dados = Path(__file__).resolve().parent / "dados"

def safe_read_csv(caminho):
    try: return pd.read_csv(caminho, sep=';', decimal=',', encoding='latin1')
    except:
        try: return pd.read_csv(caminho, sep=',', decimal='.', encoding='utf-8')
        except: return None

# --- INTELIGÊNCIA DE PASTAS ---
def obter_periodos():
    if not base_dados.exists(): return []
    pastas = []
    for item in base_dados.iterdir():
        if item.is_dir() and item.name.lower() != "solicitacoes" and not item.name.startswith('.'):
            pastas.append(item.name)
    if any(base_dados.glob("*.csv")) or any(base_dados.glob("*.xlsx")):
        if "." not in pastas: pastas.append(".")
    return sorted(pastas, reverse=True)

periodos_disponiveis = obter_periodos()

if not periodos_disponiveis:
    lista_opcoes = ["Nenhuma pasta de dados encontrada"]
else:
    lista_opcoes = ["Acumulado (Todas as Semanas)"] + [p for p in periodos_disponiveis if p != "."]
    if "." in periodos_disponiveis and len(periodos_disponiveis) == 1:
        lista_opcoes = ["Dados Atuais (Arquivos soltos na Raiz)"]

# --- CABEÇALHO E FILTRO ---
logo_html = f'<div style="text-align: center;"><img src="data:image/png;base64,{get_base64_image("images/Logo_Parceria.png")}" style="max-width:350px;"></div>'

col_title, col_logo, col_filter = st.columns([2.5, 3, 1.5])
with col_title: 
    st.markdown("<h2 style='margin-bottom:0; padding-top:20px;'>Dashboard Gestão de Temporários</h2>", unsafe_allow_html=True)
with col_logo: 
    st.markdown(logo_html, unsafe_allow_html=True)
with col_filter:
    st.markdown("<div style='padding-top:25px;'>", unsafe_allow_html=True)
    periodo_selecionado = st.selectbox("Filtro de Período:", lista_opcoes, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-top: 1px solid #ccc;'>", unsafe_allow_html=True)

def obter_caminhos_alvo():
    if periodo_selecionado == "Nenhuma pasta de dados encontrada": return []
    if periodo_selecionado == "Acumulado (Todas as Semanas)":
        pastas_reais = [p for p in periodos_disponiveis if p != "."]
        return pastas_reais if pastas_reais else ["."]
    if periodo_selecionado == "Dados Atuais (Arquivos soltos na Raiz)": 
        return ["."]
    return [periodo_selecionado]

alvos_ativos = obter_caminhos_alvo()

# --- NAVEGAÇÃO DE ABAS ---
tab_names = ["Visão Geral", "Análise SLA", "Diárias", "Histórico Mensal"]
if "current_tab" not in st.session_state: st.session_state.current_tab = tab_names[0]
def set_tab(tab): st.session_state.current_tab = tab

tab_cols = st.columns(len(tab_names))
for i, tab in enumerate(tab_names):
    tab_cols[i].button(tab, key=tab, on_click=set_tab, args=(tab,), type="secondary")
    tab_cols[i].markdown(f"""<style>[data-testid="stButton"] button#{tab.replace(' ', '')} {{ {'background:#2266ee !important;color:#fff !important;box-shadow:0 4px 14px #2266ee47;' if st.session_state.current_tab == tab else ''} }}</style>""", unsafe_allow_html=True)

# --- FUNÇÕES DE CARREGAMENTO AGREGADO ---
def load_sla_agregado(alvos):
    sol, no, fora = 0, 0, 0
    for p in alvos:
        caminho = base_dados / p / "SLA.csv" if p != "." else base_dados / "SLA.csv"
        if caminho.exists():
            df = safe_read_csv(caminho)
            if df is not None and not df.empty:
                sol += float(df['Solicitado'].iloc[0])
                no += float(df['No_prazo'].iloc[0])
                fora += float(df['Fora_prazo'].iloc[0])
    taxa = (no / sol) if sol > 0 else 0
    return pd.DataFrame({"Solicitado": [sol], "No_prazo": [no], "Fora_prazo": [fora], "taxa": [taxa]})

def load_analise_pedido_agregado(alvos):
    sol, ent = 0, 0
    for p in alvos:
        caminho = base_dados / p / "ANALISE_PEDIDO.csv" if p != "." else base_dados / "ANALISE_PEDIDO.csv"
        if caminho.exists():
            df = safe_read_csv(caminho)
            if df is not None and not df.empty:
                sol += float(df['Solicitado'].iloc[0])
                ent += float(df['Entregue'].iloc[0])
    taxa = (ent / sol) if sol > 0 else 0
    return pd.DataFrame({"Solicitado": [sol], "Entregue": [ent], "Taxa": [taxa]})

# --- RENDERIZAÇÃO DAS ABAS ---
def render_visao_geral(alvos):
    if not alvos:
        st.warning("Crie as pastas das semanas dentro de 'dados/' e insira seus arquivos.")
        return
        
    sla = load_sla_agregado(alvos)
    pedidos = load_analise_pedido_agregado(alvos)
    
    if sla['Solicitado'].iloc[0] == 0:
        st.warning("Não foram encontrados dados para o período selecionado.")
        return
        
    sla_percent = sla['taxa'].iloc[0] * 100
    diaria_percent = pedidos['Taxa'].iloc[0] * 100
    
    st.markdown(f"""<div class="kpi-row">
      <div class="kpi-card kpi-blue"><span class="kpi-title">Total de Pedidos</span><span class="kpi-val">{int(sla['Solicitado'].iloc[0])}</span></div>
      <div class="kpi-card kpi-green"><span class="kpi-title">Taxa SLA (No Prazo)</span><span class="kpi-val">{sla_percent:.1f}%</span></div>
      <div class="kpi-card kpi-purple"><span class="kpi-title">Diárias Entregues</span><span class="kpi-val">{int(pedidos['Entregue'].iloc[0])}</span></div>
      <div class="kpi-card kpi-orange"><span class="kpi-title">Taxa Diárias Global</span><span class="kpi-val">{diaria_percent:.2f}%</span></div>
    </div>""", unsafe_allow_html=True)
    
    col_pie, col_bar = st.columns(2, gap="medium")
    with col_pie:
        st.markdown('<div class="graph-container"><div class="graph-title">Eficiência de Entrega (SLA)</div><div class="graph-content">', unsafe_allow_html=True)
        fig_pie = px.pie(values=[sla['No_prazo'].iloc[0], sla['Fora_prazo'].iloc[0]], names=["Entregue no Prazo", "Fora do Prazo"], hole=0.40, color_discrete_sequence=['#2266ee','#f65054'])
        fig_pie.update_traces(textinfo="percent", textposition="inside", textfont=dict(size=14, color="#ffffff"), marker=dict(line=dict(color="#ffffff", width=2)), pull=[0.02,0.02])
        fig_pie.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=10,color="#1a1a1a")), margin=dict(l=5,r=5,t=5,b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=180)
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div></div>', unsafe_allow_html=True)
    with col_bar:
        st.markdown('<div class="graph-container"><div class="graph-title">Balanço de Diárias</div><div class="graph-content">', unsafe_allow_html=True)
        solicitadas, entregues = pedidos['Solicitado'].iloc[0], pedidos['Entregue'].iloc[0]
        saldo = entregues - solicitadas
        fig_bar = px.bar(pd.DataFrame({"Tipo":["Solicitadas","Entregues"],"Qtd":[solicitadas,entregues]}), x="Tipo", y="Qtd", text_auto='.0f', color="Tipo", color_discrete_map={"Solicitadas":"#FFA500","Entregues":"#23B26D"})
        fig_bar.update_traces(texttemplate='<b>%{y}</b>', textposition='inside', textfont=dict(size=14, color="#fff"))
        fig_bar.update_layout(showlegend=False, xaxis=dict(title="", tickfont=dict(size=11, color="#1a1a1a")), yaxis=dict(title="", showticklabels=True, range=[0,max(solicitadas,entregues)*1.15]), margin=dict(l=12,r=12,t=8,b=8), height=150, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar":False})
        if saldo >= 0: msg = f"✅ Superamos a meta em {int(saldo)} diárias!"
        else: msg = f"⚠️ Déficit de {int(abs(saldo))} diárias em relação à demanda."
        st.markdown(f"""<div class='diarias-card-sucesso' style='margin-top:8px;'>{msg}</div></div></div>""", unsafe_allow_html=True)

    info_saldo = f"superando o volume global em {int(saldo)} posições" if saldo >= 0 else f"deixando um déficit de {int(abs(saldo))} posições frente à demanda global"
    texto_resumo = f"""<div class="obs-box"><b>Resumo Executivo - Período Selecionado</b><br>
    <ul>
        <li><b>Eficiência de Entrega (SLA):</b> A operação atingiu <b>{sla_percent:.1f}%</b> de assertividade no prazo. Foram fechadas {int(sla['No_prazo'].iloc[0])} vagas rigorosamente no tempo acordado, enquanto {int(sla['Fora_prazo'].iloc[0])} vagas estouraram o limite contratual de SLA.</li>
        <li><b>Volume de Diárias:</b> A equipe apresentou uma taxa de entrega de <b>{diaria_percent:.1f}%</b>, {info_saldo}.</li>
    </ul></div>"""
    st.markdown(texto_resumo, unsafe_allow_html=True)

def render_analise_sla(alvos):
    if not alvos: return
    sla = load_sla_agregado(alvos)
    if sla['Solicitado'].iloc[0] == 0: return
    total, dentro, fora = int(sla['Solicitado'].iloc[0]), int(sla['No_prazo'].iloc[0]), int(sla['Fora_prazo'].iloc[0])
    perc_dentro, perc_fora = dentro/total*100, fora/total*100
    st.markdown(f"""<div class="kpi-row">
      <div class="kpi-card kpi-blue"><span class="kpi-title">Total de Solicitações</span><span class="kpi-val">{total}</span></div>
      <div class="kpi-card kpi-green"><span class="kpi-title">Entregues no Prazo</span><span class="kpi-val">{dentro}</span><span style="font-size:0.92em;color:#e9ffe1;">{perc_dentro:.2f}% do total</span></div>
      <div class="kpi-card kpi-orange"><span class="kpi-title">Fora do Prazo</span><span class="kpi-val">{fora}</span><span style="font-size:0.92em;color:#fffbe5;">{perc_fora:.2f}% do total</span></div>
    </div>""", unsafe_allow_html=True)
    fig = go.Figure(go.Indicator(mode="gauge+number", value=perc_dentro, number={'suffix':' %','font':{'size':32}}, title={'text':'SLA Cumprido (%)','font':{'size':17}}, gauge={'axis':{'range':[0,100],'tickwidth':2},'bar':{'color':'#23B26D'},'bgcolor':'#eaeaee','steps':[{'range':[0,perc_dentro],'color':'#23B26D'},{'range':[perc_dentro,100],'color':'#ffebdf'}],'threshold':{'line':{'color':'#FF7927','width':4},'thickness':0.7,'value':perc_dentro}}))
    fig.update_layout(height=220, margin=dict(l=22,r=22,t=22,b=20), paper_bgcolor="#f6f9fd", font=dict(size=15))
    st.markdown('<div class="graph-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    alerta_fora = f"Atenção: A equipe acumulou {fora} vagas fora da meta de entrega no período." if fora > 0 else "Nenhuma vaga estourou o prazo limite neste período."
    texto_sla = f"""<div class="obs-box" style="background:#e8f1fd;border-left:5px solid #5aa7db;color:#164976;font-size:1.04em;margin-top:10px;font-weight:500;">
    <b>Performance de Entrega ({periodo_selecionado})</b><br>
    <ul>
        <li><b>Assertividade:</b> {perc_dentro:.1f}% das posições solicitadas foram supridas respeitando o SLA de planejamento ideal.</li>
        <li><b>Impacto de Atrasos:</b> {alerta_fora}</li>
    </ul></div>"""
    st.markdown(texto_sla, unsafe_allow_html=True)

def render_diarias(alvos):
    if not alvos: return
    pedidos = load_analise_pedido_agregado(alvos)
    if pedidos['Solicitado'].iloc[0] == 0: return
    solicitadas, entregues = int(pedidos['Solicitado'].iloc[0]), int(pedidos['Entregue'].iloc[0])
    saldo = entregues - solicitadas
    taxa = pedidos['Taxa'].iloc[0] * 100
    st.markdown(f"""<div class="diarias-kpi-row"><div class="diarias-kpi-card diarias-kpi-blue"><span class="diarias-kpi-title">Solicitadas</span><span class="diarias-kpi-val">{solicitadas}</span></div><div class="diarias-kpi-card diarias-kpi-green"><span class="diarias-kpi-title">Entregues</span><span class="diarias-kpi-val">{entregues}</span></div><div class="diarias-kpi-card diarias-kpi-purple"><span class="diarias-kpi-title">Taxa de Atendimento</span><span class="diarias-kpi-val">{taxa:.2f}%</span></div></div>""", unsafe_allow_html=True)
    fig_barras = go.Figure()
    fig_barras.add_trace(go.Bar(x=["Volume Global Selecionado"], y=[solicitadas], name="Solicitadas", marker=dict(color="#FFA500"), text=[solicitadas], textposition="outside"))
    fig_barras.add_trace(go.Bar(x=["Volume Global Selecionado"], y=[entregues], name="Entregues", marker=dict(color="#23B26D"), text=[entregues], textposition="outside"))
    fig_barras.update_layout(barmode='group', yaxis=dict(range=[0,max(solicitadas,entregues)*1.15]), height=310, margin=dict(t=30,b=30,l=28,r=28), legend=dict(orientation='h', x=0.5, y=-0.20, xanchor='center'), plot_bgcolor="#fff", paper_bgcolor="#fff")
    st.plotly_chart(fig_barras, use_container_width=True, config={"displayModeBar": False})

    if saldo >= 0:
        texto_diarias = f"<b>Performance de Sucesso!</b><br> A operação entregou <b>{entregues} diárias</b> contra <b>{solicitadas} solicitadas</b>, mantendo um saldo positivo de suprimento de <b style='color:#12bb26;'>{saldo} diárias no pool</b>."
    else:
        texto_diarias = f"<b>Desempenho Abaixo da Meta</b><br> A operação processou <b>{entregues} diárias</b> sobre uma demanda de <b>{solicitadas} solicitadas</b>, restando um gap de entrega de <b style='color:#d93025;'>{abs(saldo)} posições no balanço</b>."
        
    st.markdown(f"""<div class="diarias-card-sucesso">{texto_diarias}<br> Taxa final de fechamento: <b>{taxa:.2f}%</b>.</div>""", unsafe_allow_html=True)

def render_historico(alvos):
    if not alvos: return
    p_alvo = alvos[0] 
    p_dir = base_dados / p_alvo if p_alvo != "." else base_dados
    try:
        sla_hist = safe_read_csv(p_dir / 'HISTORICO_SLA.csv')
        ent_hist = safe_read_csv(p_dir / 'HISTORICO_ENTREGA.csv')
        
        if sla_hist is None or ent_hist is None:
            st.warning(f"Planilhas de histórico não encontradas na pasta base.")
            return

        # Limpeza SLA
        sla_hist.columns = ['Mes','Taxa']
        sla_hist['Taxa'] = sla_hist['Taxa'].map(lambda x: float(str(x).replace(',', '.').strip()))
        sla_hist['No Prazo (%)'] = sla_hist['Taxa'] * 100
        sla_hist['Fora do Prazo (%)'] = (1 - sla_hist['Taxa']) * 100
        
        # Limpeza Entrega
        ent_hist.columns = ['Mês','Solicitadas','Entregues','Taxa']
        ent_hist['Solicitadas'] = pd.to_numeric(ent_hist['Solicitadas'], errors='coerce').fillna(0)
        ent_hist['Entregues'] = pd.to_numeric(ent_hist['Entregues'], errors='coerce').fillna(0)
        ent_hist['Taxa_%'] = ent_hist['Taxa'].map(lambda x: float(str(x).replace(',', '.'))) * 100

        # GRÁFICO 1: SLA
        st.markdown("""<div style="background:#fff;border-radius:16px;padding:28px 35px 26px 35px;margin-bottom:12px;box-shadow:0 1px 8px #0001;"><div style="font-weight:800;font-size:1.20em;margin-bottom:12px;">Histórico de Eficiência (SLA de Entrega)</div></div>""", unsafe_allow_html=True)
        
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(name='Entregue no Prazo', x=sla_hist['Mes'], y=sla_hist['No Prazo (%)'], marker_color='#2266ee', text=[f"<b>{v:.1f}%</b>" for v in sla_hist['No Prazo (%)']], textposition='inside', textfont=dict(color='white', size=13)))
        fig1.add_trace(go.Bar(name='Fora do Prazo (Atraso)', x=sla_hist['Mes'], y=sla_hist['Fora do Prazo (%)'], marker_color='#f65054', text=[f"<b>{v:.1f}%</b>" if v > 5 else "" for v in sla_hist['Fora do Prazo (%)']], textposition='inside', textfont=dict(color='white', size=13)))
        fig1.add_hline(y=100, line_dash="dash", line_color="#000", annotation_text="Meta (100%)", annotation_position="top left")
        
        fig1.update_layout(barmode='relative', height=400, margin=dict(l=20,r=20,t=40,b=38), legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center'), plot_bgcolor='#fff', yaxis=dict(title='SLA (%)'))
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar':False})
        
        # GRÁFICO 2: ENTREGAS
        st.markdown("""<div style="background:#fff;border-radius:16px;padding:28px 35px 26px 35px;margin-top:28px;margin-bottom:12px;box-shadow:0 1px 8px #0001;"><div style="font-weight:800;font-size:1.20em;margin-bottom:12px;">Histórico de Volume de Entregas</div></div>""", unsafe_allow_html=True)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=ent_hist['Mês'], y=ent_hist['Solicitadas'], name='Solicitadas', marker_color='#FFA500', text=[f"<b>{v}</b>" for v in ent_hist['Solicitadas']], textposition='auto'))
        fig2.add_trace(go.Bar(x=ent_hist['Mês'], y=ent_hist['Entregues'], name='Entregues', marker_color='#23B26D', text=[f"<b>{v}</b>" for v in ent_hist['Entregues']], textposition='auto'))
        fig2.add_trace(go.Scatter(x=ent_hist['Mês'], y=ent_hist['Taxa_%'], mode='lines+markers+text', name='Taxa (%)', line=dict(color='#9b1de9', width=2), marker=dict(size=8,color='#9b1de9'), text=[f"<b>{tx:.1f}%</b>" for tx in ent_hist['Taxa_%']], textposition="top center", yaxis="y2"))
        
        max_vol = max(ent_hist['Solicitadas'].max(), ent_hist['Entregues'].max())
        fig2.update_layout(barmode='group', height=400, margin=dict(l=20,r=20,t=40,b=38), legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center'), plot_bgcolor='#fff', yaxis=dict(range=[0, max_vol * 1.3]), yaxis2=dict(range=[0, max(110, ent_hist['Taxa_%'].max()*1.2)], overlaying='y', side='right', showgrid=False, visible=False))
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})

        # --- INTELIGÊNCIA DINÂMICA DO HISTÓRICO ---
        tot_solicitado = ent_hist['Solicitadas'].sum()
        tot_entregue = ent_hist['Entregues'].sum()
        tx_global = (tot_entregue / tot_solicitado * 100) if tot_solicitado > 0 else 0
        
        melhor_semana_ent = ent_hist.loc[ent_hist['Taxa_%'].idxmax()]
        pior_semana_ent = ent_hist.loc[ent_hist['Taxa_%'].idxmin()]
        melhor_semana_sla = sla_hist.loc[sla_hist['No Prazo (%)'].idxmax()]
        pior_semana_sla = sla_hist.loc[sla_hist['No Prazo (%)'].idxmin()]
        
        html_inteligencia = f"""
        <div style="display:flex; gap:20px; margin-top:20px;">
            <div style="flex:1; background:#eafff1; border-left:6px solid #23b26d; border-radius:8px; padding:20px;">
                <h4 style="color:#117b46; margin-top:0; margin-bottom:15px;">🚀 Retenção & Fechamento Ideal</h4>
                <ul style="color:#1a1a1a; font-size:0.95em; line-height:1.6;">
                    <li><b>Pico de Atendimento:</b> O maior volume de vagas fechadas ocorreu na medição de <b>{melhor_semana_ent['Mês']}</b>, registrando uma taxa de <b>{melhor_semana_ent['Taxa_%']:.1f}%</b>.</li>
                    <li><b>Pico de Eficiência (SLA):</b> O período de <b>{melhor_semana_sla['Mes']}</b> registrou a melhor performance da equipe, com <b>{melhor_semana_sla['No Prazo (%)']:.1f}%</b> das vagas entregues rigorosamente no prazo estipulado.</li>
                    <li><b>Volume Acumulado:</b> Considerando todo este histórico, entregamos <b>{int(tot_entregue)}</b> de <b>{int(tot_solicitado)}</b> posições (Média Global de {tx_global:.1f}%).</li>
                </ul>
            </div>
            <div style="flex:1; background:#fff2f2; border-left:6px solid #f65054; border-radius:8px; padding:20px;">
                <h4 style="color:#b32629; margin-top:0; margin-bottom:15px;">⚠️ Atrasos & Gargalos Operacionais</h4>
                <ul style="color:#1a1a1a; font-size:0.95em; line-height:1.6;">
                    <li><b>Queda de Fechamento:</b> O menor percentual de vagas preenchidas mapeado foi em <b>{pior_semana_ent['Mês']}</b>, atingindo <b>{pior_semana_ent['Taxa_%']:.1f}%</b> de atendimento global.</li>
                    <li><b>Volume de Atrasos:</b> Em <b>{pior_semana_sla['Mes']}</b>, a equipe enfrentou a maior dificuldade logística, com <b>{pior_semana_sla['Fora do Prazo (%)']:.1f}%</b> das entregas estourando a meta de tempo (SLA).</li>
                    <li><b>Status Atual:</b> A última linha de leitura ({ent_hist['Mês'].iloc[-1]}) aponta um fechamento de volume de <b>{ent_hist['Taxa_%'].iloc[-1]:.1f}%</b>, sendo que as entregas efetuadas no prazo (SLA) representam <b>{sla_hist['No Prazo (%)'].iloc[-1]:.1f}%</b>.</li>
                </ul>
            </div>
        </div>
        """
        st.markdown(html_inteligencia, unsafe_allow_html=True)

    except Exception as e: st.warning(f"Erro ao gerar a aba de Histórico. Detalhe: {e}")

# ---- ROTEAMENTO ----
aba_ativa = st.session_state.current_tab
alvos_ativos = obter_caminhos_alvo()

if aba_ativa == "Visão Geral": render_visao_geral(alvos_ativos)
elif aba_ativa == "Análise SLA": render_analise_sla(alvos_ativos)
elif aba_ativa == "Diárias": render_diarias(alvos_ativos)
elif aba_ativa == "Histórico Mensal": render_historico(alvos_ativos)