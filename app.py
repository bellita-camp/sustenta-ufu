import hashlib
from datetime import date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from supabase import Client, create_client

st.set_page_config(
    page_title="Sustenta UFU | Gestão & Impacto", page_icon="🌱", layout="wide"
)

st.markdown(
    """
<style>
    div[data-testid="stMetric"] {
        background-color: #132119;
        border: 1px solid #1F3A2B;
        padding: 18px;
        border-radius: 14px;
    }
    div[data-testid="stForm"] {
        background-color: #132119;
        border: 1px solid #1F3A2B;
        border-radius: 14px;
        padding: 20px;
    }
    .card-item {
        background-color: #132119;
        border-left: 5px solid #10B981;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 12px;
        border: 1px solid #1F3A2B;
    }
    .badge {
        background-color: #064E3B;
        color: #6EE7B7;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


supabase = init_connection()


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_nome = ""


def tela_autenticacao():
    _, col2, _ = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("## 🌱 Sustenta — Empresa Júnior UFU")
        st.caption("Faça login com a credencial oficial da diretoria.")

        with st.form("form_login"):
            email = st.text_input("E-mail", value="isabella.felipe@ufu.br")
            senha = st.text_input("Senha", type="password")
            
            if st.form_submit_button("Acessar Dashboard", use_container_width=True):
                if email.strip().lower() == "isabella.felipe@ufu.br" and senha == "Sustenta2026!":
                    st.session_state.logado = True
                    st.session_state.usuario_nome = "Isabella Felipe"
                    st.rerun()
                else:
                    try:
                        res = (
                            supabase.table("usuarios")
                            .select("*")
                            .eq("email", email.strip().lower())
                            .eq("senha_hash", hash_senha(senha))
                            .execute()
                        )
                        if res.data:
                            st.session_state.logado = True
                            st.session_state.usuario_nome = res.data[0]["nome"]
                            st.rerun()
                        else:
                            st.error("E-mail ou senha incorretos.")
                    except Exception:
                        st.error("E-mail ou senha incorretos.")


def dashboard_principal():
    with st.sidebar:
        st.markdown("## 🌿 Sustenta UFU")
        st.caption(f"Olá, **{st.session_state.usuario_nome}**")
        st.divider()
        menu = st.radio(
            "Navegação",
            [
                "📊 Visão Geral & Metas",
                "⏳ Demandas Pendentes",
                "✅ Demandas Concluídas",
                "🤝 Ideias & Parcerias",
                "💰 Gestão Financeira",
            ],
        )
        st.divider()
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logado = False
            st.rerun()

    try:
        demandas_data = (
            supabase.table("demandas").select("*").order("prazo").execute().data
        )
        fin_data = (
            supabase.table("financeiro")
            .select("*")
            .order("data_registro")
            .execute()
            .data
        )
    except Exception:
        demandas_data, fin_data = [], []

    df_demandas = pd.DataFrame(demandas_data) if demandas_data else pd.DataFrame()
    df_fin = pd.DataFrame(fin_data) if fin_data else pd.DataFrame()

    if menu == "📊 Visão Geral & Metas":
        st.title("Painel de Controle — Sustenta UFU")
        pendentes = (
            len(df_demandas[df_demandas["categoria"] == "Pendente"])
            if not df_demandas.empty and "categoria" in df_demandas.columns
            else 0
        )
        concluidas = (
            len(df_demandas[df_demandas["categoria"] == "Concluída"])
            if not df_demandas.empty and "categoria" in df_demandas.columns
            else 0
        )
        parcerias = (
            len(df_demandas[df_demandas["categoria"] == "Ideia/Parceria"])
            if not df_demandas.empty and "categoria" in df_demandas.columns
            else 0
        )

        total_caixa = df_fin["valor"].sum() if not df_fin.empty and "valor" in df_fin.columns else 0.0
        media_valores = df_fin["valor"].mean() if not df_fin.empty and "valor" in df_fin.columns else 0.0
        meta_atual = (
            df_fin["meta_mensal"].iloc[-1] if not df_fin.empty and "meta_mensal" in df_fin.columns else 5000.0
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("⏳ Pendentes", pendentes)
        c2.metric("✅ Concluídos", concluidas)
        c3.metric("🤝 Ideias & Parcerias", parcerias)
        c4.metric(
            "💵 Caixa Total",
            f"R$ {total_caixa:,.2f}",
            f"Média: R$ {media_valores:,.2f}",
        )

        st.markdown("### 📈 Desempenho Financeiro & Progresso da Meta")
        col_g1, col_g2 = st.columns([1.6, 1])

        with col_g1:
            if not df_fin.empty and "descricao" in df_fin.columns and "valor" in df_fin.columns:
                fig_bar = px.bar(
                    df_fin,
                    x="descricao",
                    y="valor",
                    title="Entradas vs. Média dos Valores",
                    color_discrete_sequence=["#10B981"],
                )
                fig_bar.add_hline(
                    y=media_valores,
                    line_dash="dash",
                    line_color="#A7F3D0",
                    annotation_text=f"Média: R$ {media_valores:,.2f}",
                )
                fig_bar.update_layout(
                    paper_bgcolor="#132119",
                    plot_bgcolor="#132119",
                    font_color="#ECFDF5",
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Adicione valores em 'Gestão Financeira' para ver o gráfico.")

        with col_g2:
            percentual = (
                min((total_caixa / meta_atual) * 100, 100)
                if meta_atual > 0
                else 0
            )
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=percentual,
                    number={"suffix": "%"},
                    title={
                        "text": f"Meta: R$ {meta_atual:,.2f}",
                        "font": {"size": 16},
                    },
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "#10B981"},
                        "bgcolor": "#0B130E",
                    },
                )
            )
            fig_gauge.update_layout(
                paper_bgcolor="#132119", font_color="#ECFDF5", height=350
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

    elif menu in [
        "⏳ Demandas Pendentes",
        "✅ Demandas Concluídas",
        "🤝 Ideias & Parcerias",
    ]:
        mapa = {
            "⏳ Demandas Pendentes": "Pendente",
            "✅ Demandas Concluídas": "Concluída",
            "🤝 Ideias & Parcerias": "Ideia/Parceria",
        }
        cat = mapa[menu]
        st.title(menu)

        with st.form(f"form_{cat}"):
            col_a, col_b = st.columns([2, 1])
            titulo = col_a.text_input("Título / Empresa Parceira *")
            responsavel = col_b.text_input(
                "Nome do Usuário *", value=st.session_state.usuario_nome
            )
            col_c, col_d = st.columns([2, 1])
            descricao = col_c.text_input("Detalhes")
            prazo = col_d.date_input("Prazo *", min_value=date(2025, 1, 1))

            if st.form_submit_button("Salvar"):
                if not titulo.strip() or not responsavel.strip():
                    st.error("Preencha Título, Nome do Usuário e Prazo.")
                else:
                    try:
                        supabase.table("demandas").insert({
                            "categoria": cat,
                            "titulo": titulo.strip(),
                            "descricao": descricao.strip(),
                            "responsavel": responsavel.strip(),
                            "prazo": str(prazo),
                        }).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

        if not df_demandas.empty and "categoria" in df_demandas.columns:
            itens = df_demandas[df_demandas["categoria"] == cat]
            for _, row in itens.iterrows():
                c_card, c_btn = st.columns([4, 1.2])
                with c_card:
                    st.markdown(
                        f"""
                    <div class="card-item">
                        <span class="badge">{row.get('categoria', '')}</span>
                        <h4 style="margin: 8px 0 4px 0;">{row.get('titulo', '')}</h4>
                        <p style="margin: 0 0 8px 0; color: #A7F3D0;">{row.get('descricao', '') or ''}</p>
                        <small style="color: #6EE7B7;">👤 <b>{row.get('responsavel', '')}</b> | 📅 Prazo: <b>{row.get('prazo', '')}</b></small>
                    </div>""",
                        unsafe_allow_html=True,
                    )
                with c_btn:
                    if cat != "Concluída" and st.button(
                        "✔ Concluir", key=f"ok_{row['id']}"
                    ):
                        supabase.table("demandas").update(
                            {"categoria": "Concluída"}
                        ).eq("id", row["id"]).execute()
                        st.rerun()
                    if st.button("🗑️ Excluir", key=f"del_{row['id']}"):
                        supabase.table("demandas").delete().eq(
                            "id", row["id"]
                        ).execute()
                        st.rerun()

    elif menu == "💰 Gestão Financeira":
        st.title("💰 Metas e Lançamentos Financeiros")
        with st.form("form_fin"):
            c1, c2, c3 = st.columns(3)
            desc = c1.text_input("Origem / Projeto *")
            val = c2.number_input("Valor (R$) *", min_value=0.0, step=100.0)
            meta = c3.number_input(
                "Meta Mensal (R$) *", min_value=1.0, value=5000.0, step=500.0
            )
            if st.form_submit_button("Registrar"):
                if not desc.strip() or val <= 0:
                    st.error("Preencha a descrição e um valor maior que zero.")
                else:
                    try:
                        supabase.table("financeiro").insert({
                            "descricao": desc.strip(),
                            "valor": val,
                            "meta_mensal": meta,
                        }).execute()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao registrar: {e}")

        if not df_fin.empty:
            st.markdown("### 📋 Histórico de Lançamentos")
            for _, row in df_fin.iterrows():
                c_card, c_btn = st.columns([4, 1.2])
                with c_card:
                    st.markdown(
                        f"""
                    <div class="card-item">
                        <span class="badge">📅 {row.get('data_registro', '')}</span>
                        <h4 style="margin: 8px 0 4px 0;">{row.get('descricao', '')}</h4>
                        <p style="margin: 0; color: #A7F3D0;">
                            💵 Valor: <b>R$ {float(row.get('valor', 0)):,.2f}</b> | 
                            🎯 Meta do Período: <b>R$ {float(row.get('meta_mensal', 0)):,.2f}</b>
                        </p>
                    </div>""",
                        unsafe_allow_html=True,
                    )
                with c_btn:
                    st.write("")
                    if st.button("🗑️ Excluir", key=f"del_fin_{row['id']}"):
                        supabase.table("financeiro").delete().eq(
                            "id", row["id"]
                        ).execute()
                        st.rerun()


if st.session_state.logado:
    dashboard_principal()
else:
    tela_autenticacao()