import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="HP Soluções - Orçamentos", layout="wide", initial_sidebar_state="expanded")

# --- CONEXÃO COM O BANCO DE DADOS (SQLite) ---
def conectar_db():
    conn = sqlite3.connect('hp_solucoes_db.sqlite')
    cursor = conn.cursor()
    # Tabela de Catálogo de Preços
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS catalogo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            servico TEXT NOT NULL,
            descricao TEXT NOT NULL,
            preco_base REAL NOT NULL
        )
    ''')
    conn.commit()
    return conn

conn = conectar_db()

# --- ESTILIZAÇÃO CUSTOMIZADA (CSS) ---
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #0B43A1 !important; 
        color: white !important;
    }
    .proposta-container {
        background-color: white;
        padding: 40px;
        border: 1px solid #ddd;
        font-family: Arial, sans-serif;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# --- CORPO DO APLICATIVO ---
st.title("💼 Sistema de Gestão de Orçamentos — HP Soluções")

aba1, aba2, aba3 = st.tabs(["📋 1. Banco de Dados / Preços", "🧮 2. Montar Orçamento", "📄 3. Proposta Comercial Gerada"])

# ==========================================
# ABA 1: BANCO DE DADOS
# ==========================================
with aba1:
    st.header("Cadastro de Serviços e Preços Base")
    
    with st.form("form_cadastro"):
        col1, col2 = st.columns([1, 2])
        with col1:
            novo_servico = st.text_input("Nome do Serviço / Insumo:", placeholder="Ex: Pintura Predial Externo")
            novo_preco = st.number_input("Preço de Custo / Base (R$):", min_value=0.0, step=10.0)
        with col2:
            nova_descricao = st.text_area("Descrição Detalhada (coloque um item por linha):", placeholder="1. Preparação da superfície\n2. Aplicação de selador\n3. Duas demãos de tinta")
        
        botao_salvar = st.form_submit_button("💾 Salvar no Banco de Dados")
        
        if botao_salvar and novo_servico:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO catalogo (servico, descricao, preco_base) VALUES (?, ?, ?)", 
                           (novo_servico, nova_descricao, novo_preco))
            conn.commit()
            st.success(f"'{novo_servico}' adicionado com sucesso!")

    # Exibir itens cadastrados
    st.subheader("Itens Cadastrados no Sistema")
    df_itens = pd.read_sql_query("SELECT id as ID, servico as 'Serviço/Material', descricao as 'Descrição', preco_base as 'Preço Base (R$)' FROM catalogo", conn)
    
    if df_itens.empty:
        st.info("Nenhum item cadastrado. Use o formulário acima para adicionar os primeiros serviços.")
    else:
        st.dataframe(df_itens, use_container_width=True, hide_index=True)
        
        # Botão para deletar itens se necessário
        item_deletar = st.selectbox("Selecione um ID para remover se cadastrou errado:", [""] + df_itens["ID"].tolist())
        if st.button("❌ Excluir Item Selecionado") and item_deletar != "":
            cursor = conn.cursor()
            cursor.execute("DELETE FROM catalogo WHERE id = ?", (item_deletar,))
            conn.commit()
            st.rerun()

# ==========================================
# ABA 2: MONTAR ORÇAMENTO
# ==========================================
with aba2:
    st.header("Configuração do Orçamento Ativo")
    
    if df_itens.empty:
        st.warning("👉 Cadastre pelo menos um item na Aba 1 antes de montar o orçamento.")
    else:
        st.subheader("Dados do Cliente")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            cliente_nome = st.text_input("Nome do Cliente / Razão Social:", "EEB MONSENHOR VENDELINO HOBOLD")
            cliente_cnpj = st.text_input("CNPJ:", "35.175.408/0001-89")
            cliente_endereco = st.text_input("Endereço:", "Rua Alexandre Moser, s/n, Itaipava, Itajaí/SC")
        with col_c2:
            cliente_contato = st.text_input("Contato / Telefone:", "(47) 99152-5220")
            cliente_resp = st.text_input("Responsável:", "Dannyelle da Mota Rosário Menezes")
            cliente_email = st.text_input("E-mail:", "eebmonsenhorvendelinohobold17@sed.sc.gov.br")

        st.write("---")
        st.subheader("Precificação & Margem")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            # MARGEM DE LUCRO SOLICITADA
            margem_lucro = st.slider("Margem de Lucro Desejada (%)", min_value=0, max_value=200, value=30, step=5)
        with col_m2:
            forma_pagamento = st.text_input("Forma de Pagamento:", "Cartão (1x) ou Pix")

        st.write("---")
        st.subheader("Seleção de Itens da Proposta")
        
        # Selecionar múltiplos itens do banco de dados
        lista_servicos = df_itens['Serviço/Material'].tolist()
        itens_selecionados = st.multiselect("Selecione os serviços/produtos que entram neste orçamento:", lista_servicos)
        
        dados_orcamento_atual = []
        custo_total_itens = 0.0
        
        if itens_selecionados:
            for item in itens_selecionados:
                # Puxa os dados originais do banco de dados
                row = df_itens[df_itens['Serviço/Material'] == item].iloc[0]
                preco_original = row['Preço Base (R$)']
                desc_original = row['Descrição']
                
                # Aplica a margem de lucro calculada: Preço final = Preço Base * (1 + Margem/100)
                preco_com_margem = float(preco_original) * (1 + (margem_lucro / 100))
                
                st.markdown(f"**🔹 {item}** | Preço Base: R$ {preco_original:.2f} ➔ **Com Margem ({margem_lucro}%): R$ {preco_com_margem:.2f}**")
                dados_orcamento_atual.append({
                    "servico": item,
                    "descricao": desc_original,
                    "valor": preco_com_margem
                })
                custo_total_itens += preco_com_margem
                
        st.write("---")
        st.subheader("⏱️ Mão de Obra Técnica Opcional")
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            horas_estimadas = st.number_input("Horas Técnicas Estimadas:", min_value=0.0, value=0.0, step=1.0)
        with col_h2:
            valor_hora = st.number_input("Preço da Hora Técnica (R$):", min_value=0.0, value=50.0, step=5.0)
            
        custo_mao_de_obra = horas_estimadas * valor_hora
        valor_final_calculado = custo_total_itens + custo_mao_de_obra
        
        # Salva o estado para a Aba 3 ler
        st.session_state['dados_proposta'] = {
            "cliente": {"nome": cliente_nome, "cnpj": cliente_cnpj, "endereco": cliente_endereco, "contato": cliente_contato, "responsavel": cliente_resp, "email": cliente_email},
            "itens": dados_orcamento_atual,
            "mao_de_obra": custo_mao_de_obra,
            "total": valor_final_calculado,
            "pagamento": forma_pagamento
        }
        
        st.success(f"🎉 Tudo pronto! O valor calculado deu R$ {valor_final_calculado:.2f}. Vá para a Aba 3 para ver o resultado.")

# ==========================================
# ABA 3: PROPOSTA COMERCIAL (Fiel ao image_dfff4d.png)
# ==========================================
with aba3:
    if 'dados_proposta' not in st.session_state:
        st.info("Aguardando dados da configuração. Monte o orçamento na Aba 2 primeiro.")
    else:
        dp = st.session_state['dados_proposta']
        
        st.warning("💡 Dica: Para salvar como PDF, clique com o botão direito na página e selecione 'Imprimir' ou use Ctrl+P.")
        
        # DESIGN DA PÁGINA EM HTML SIMULANDO A FOLHA DA IMAGEM
        linhas_tabela_html = ""
        for it in dp['itens']:
            # Quebra as linhas da descrição para gerar a lista numérica
            desc_formatada = "".join([f"<div>{linha.strip()}</div>" for linha in it['descricao'].split('\n') if linha.strip()])
            linhas_tabela_html += f"""
            <tr>
                <td style="border: 1px solid #e0e0e0; padding: 12px; font-weight: bold; width: 30%; color: #333;">{it['servico']}</td>
                <td style="border: 1px solid #e0e0e0; padding: 12px; font-size: 13px; color: #555; width: 50%;">{desc_formatada}</td>
                <td style="border: 1px solid #e0e0e0; padding: 12px; text-align: center; font-weight: bold; width: 20%; color: #333;">R$ {it['valor']:.2f}</td>
            </tr>
            """
            
        if dp['mao_de_obra'] > 0:
            linhas_tabela_html += f"""
            <tr>
                <td style="border: 1px solid #e0e0e0; padding: 12px; font-weight: bold; color: #333;">Mão de Obra Técnica</td>
                <td style="border: 1px solid #e0e0e0; padding: 12px; font-size: 13px; color: #555;">Execução, montagem e horas de engenharia aplicadas ao projeto.</td>
                <td style="border: 1px solid #e0e0e0; padding: 12px; text-align: center; font-weight: bold; color: #333;">R$ {dp['mao_de_obra']:.2f}</td>
            </tr>
            """

        html_folha = f"""
        <div class="proposta-container" style="position: relative; border-top: 15px solid #0B43A1; border-left: 5px solid #0B43A1; min-height: 1000px;">
            <!-- CABEÇALHO -->
            <table style="width: 100%; border: none; margin-bottom: 30px;">
                <tr>
                    <td style="width: 45%;">
                        <!-- LOGO CIRCULAR -->
                        <div style="width: 140px; height: 140px; border-radius: 50%; background: #222; border: 4px solid #B58A3D; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: white; padding: 10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.2);">
                            <div style="font-weight: bold; font-size: 14px; letter-spacing: 1px; color: #B58A3D;">HP</div>
                            <div style="font-size: 9px; font-weight: bold; margin-bottom: 4px;">SOLUÇÕES</div>
                            <div style="font-size: 6px; color: #ccc; border-top: 1px solid #44px; padding-top: 3px; line-height: 1.2;">PINTURA | ELÉTRICA<br>HIDRÁULICA<br>RESIDENCIAL E PREDIAL</div>
                        </div>
                    </td>
                    <td style="text-align: right; font-family: sans-serif; line-height: 1.4;">
                        <h2 style="color: #000; margin: 0; font-size: 24px; letter-spacing: 1px;">HP SOLUÇÕES</h2>
                        <div style="font-size: 12px; font-weight: bold; color: #444; margin-bottom: 5px;">CNPJ: 66.799.072/0001-59</div>
                        <div style="font-size: 12px; color: #555;">hpsolucoes@gmail.com ✉️</div>
                        <div style="font-size: 12px; color: #555; font-weight: bold; color: #0B43A1;">(47) 99637-2330 📞</div>
                        <div style="font-size: 12px; color: #555; font-weight: bold; color: #0B43A1;">(47) 99188-1921 📞</div>
                    </td>
                </tr>
            </table>

            <h1 style="color: #0B43A1; text-align: center; font-size: 26px; margin-bottom: 25px; border-bottom: 2px solid #0B43A1; padding-bottom: 10px;">PROPOSTA COMERCIAL / ORÇAMENTO</h1>
            
            <div style="text-align: right; margin-bottom: 20px; font-size: 14px; font-weight: bold; color: #333;">
                Data: {datetime.now().strftime('%d/%m/%Y')} <br>
                Nº do Orçamento: 0001
            </div>

            <!-- DADOS DO CLIENTE -->
            <div style="margin-bottom: 30px; line-height: 1.6; font-size: 14px;">
                <strong style="color: #0B43A1; font-size: 16px;">CLIENTE:</strong><br>
                <strong>{dp['cliente']['nome']}</strong><br>
                CGC/CNPJ: {dp['cliente']['cnpj']}<br>
                Endereço: {dp['cliente']['endereco']}<br>
                Contato: {dp['cliente']['contato']}<br>
                Responsável: {dp['cliente']['responsavel']}<br>
                E-mail: {dp['cliente']['email']}
            </div>

            <!-- TABELA DE PREÇOS -->
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                <thead>
                    <tr style="background-color: #0B43A1; color: white; text-align: left;">
                        <th style="padding: 12px; border: 1px solid #0B43A1;">SERVIÇO</th>
                        <th style="padding: 12px; border: 1px solid #0B43A1;">DESCRIÇÃO</th>
                        <th style="padding: 12px; border: 1px solid #0B43A1; text-align: center;">VALOR</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas_tabela_html}
                </tbody>
            </table>

            <!-- TOTALIZADOR -->
            <div style="text-align: right; margin-bottom: 40px;">
                <span style="background-color: #0B43A1; color: white; padding: 12px 35px; font-size: 18px; font-weight: bold; border-radius: 4px;">
                    TOTAL: R$ {dp['total']:.2f}
                </span>
            </div>

            <!-- TERMOS -->
            <div style="margin-bottom: 40px; font-size: 14px; line-height: 1.5;">
                <h4 style="color: #0B43A1; margin-bottom: 5px;">FORMA DE PAGAMENTO</h4>
                <p style="margin: 0 0 15px 0;">{dp['pagamento']}</p>
                
                <h4 style="color: #0B43A1; margin-bottom: 5px;">TERMOS E CONDIÇÕES</h4>
                <p style="margin: 0;">Este orçamento é válido por 30 dias.</p>
            </div>

            <div style="margin-top: 20px; font-weight: bold; color: #0B43A1; font-size: 14px;">ASSINATURA</div>
            <div style="width: 250px; border-bottom: 1px solid #333; margin-top: 40px;"></div>
            
            <!-- MARCA D'ÁGUA DE CANTO INFERIOR (ÍCONES SIMULADOS) -->
            <div style="position: absolute; bottom: 15px; right: 20px; text-align: right; color: #eaeaea; font-size: 70px; font-weight: bold; user-select: none; z-index: 0; pointer-events: none; line-height: 0.8;">
                🏠⚡🛠️
            </div>
        </div>
        """
        st.markdown(html_folha, unsafe_allow_html=True)
