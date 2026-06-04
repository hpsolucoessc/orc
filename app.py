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

    st.subheader("Itens Cadastrados no Sistema")
    df_itens = pd.read_sql_query("SELECT id as ID, servico as 'Serviço/Material', descricao as 'Descrição', preco_base as 'Preço Base (R$)' FROM catalogo", conn)
    
    if df_itens.empty:
        st.info("Nenhum item cadastrado. Use o formulário acima para adicionar os primeiros serviços.")
    else:
        st.dataframe(df_itens, use_container_width=True, hide_index=True)
        
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
            margem_lucro = st.slider("Margem de Lucro Desejada (%)", min_value=0, max_value=200, value=30, step=5)
        with col_m2:
            forma_pagamento = st.text_input("Forma de Pagamento:", "Cartão (1x) ou Pix")

        st.write("---")
        st.subheader("Seleção de Itens da Proposta")
        
        lista_servicos = df_itens['Serviço/Material'].tolist()
        itens_selecionados = st.multiselect("Selecione os serviços/produtos que entram neste orçamento:", lista_servicos)
        
        dados_orcamento_atual = []
        custo_total_itens = 0.0
        
        if itens_selecionados:
            for item in itens_selecionados:
                row = df_itens[df_itens['Serviço/Material'] == item].iloc[0]
                preco_original = row['Preço Base (R$)']
                desc_original = row['Descrição']
                
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
        
        st.session_state['dados_proposta'] = {
            "cliente": {"nome": cliente_nome, "cnpj": cliente_cnpj, "endereco": cliente_endereco, "contato": cliente_contato, "responsavel": cliente_resp, "email": cliente_email},
            "itens": dados_orcamento_atual,
            "mao_de_obra": custo_mao_de_obra,
            "total": valor_final_calculado,
            "pagamento": forma_pagamento
        }
        
        st.success(f"🎉 Calculado com sucesso! Valor total: R$ {valor_final_calculado:.2f}. Vá para a Aba 3.")

# ==========================================
# ABA 3: PROPOSTA COMERCIAL (CORRIGIDA)
# ==========================================
with aba3:
    if 'dados_proposta' not in st.session_state:
        st.info("Aguardando dados. Monte o orçamento na Aba 2 primeiro.")
    else:
        dp = st.session_state['dados_proposta']
        
        st.warning("💡 Para salvar como PDF: Pressione Ctrl+P (ou Cmd+P no Mac) e selecione 'Salvar como PDF'.")
        
        # Gerando as linhas da tabela dinamicamente de forma segura
        linhas_html = ""
        for it in dp['itens']:
            linhas_desc = "".join([f"<div>• {l.strip()}</div>" for l in it['descricao'].split('\n') if l.strip()])
            linhas_html += f"""
            <tr>
                <td style="border: 1px solid #e0e0e0; padding: 12px; font-weight: bold; width: 30%; color: #333;">{it['servico']}</td>
                <td style="border: 1px solid #e0e0e0; padding: 12px; font-size: 13px; color: #555; width: 50%; text-align: left;">{linhas_desc}</td>
                <td style="border: 1px solid #e0e0e0; padding: 12px; text-align: center; font-weight: bold; width: 20%; color: #333;">R$ {it['valor']:.2f}</td>
            </tr>
            """
            
        if dp['mao_de_obra'] > 0:
            linhas_html += f"""
            <tr>
                <td style="border: 1px solid #e0e0e0; padding: 12px; font-weight: bold; color: #333;">Mão de Obra / Execução</td>
                <td style="border: 1px solid #e0e0e0; padding: 12px; font-size: 13px; color: #555; text-align: left;">Tempo técnico dedicado à execução dos serviços solicitados.</td>
                <td style="border: 1px solid #e0e0e0; padding: 12px; text-align: center; font-weight: bold; color: #333;">R$ {dp['mao_de_obra']:.2f}</td>
            </tr>
            """

        # O segredo da correção está aqui: Injetando a folha limpa sem travar strings
        st.components.v1.html(f"""
        <div style="background-color: white; padding: 30px; border: 1px solid #ddd; font-family: Arial, sans-serif; color: #333; border-top: 15px solid #0B43A1; min-height: 900px; box-sizing: border-box;">
            
            <!-- CABEÇALHO DA FOTO -->
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr>
                    <td style="width: 40%; vertical-align: middle;">
                        <div style="width: 130px; height: 130px; border-radius: 50%; background: #222; border: 4px solid #B58A3D; text-align: center; color: white; display: inline-block; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);">
                            <div style="font-weight: bold; font-size: 15px; margin-top: 25px; color: #B58A3D; letter-spacing: 1px;">HP</div>
                            <div style="font-size: 10px; font-weight: bold; margin-bottom: 5px;">SOLUÇÕES</div>
                            <div style="font-size: 6px; color: #ccc; border-top: 1px solid #444; padding-top: 3px; line-height: 1.2;">PINTURA | ELÉTRICA<br>HIDRÁULICA</div>
                        </div>
                    </td>
                    <td style="text-align: right; vertical-align: middle; line-height: 1.4;">
                        <h2 style="color: #0B43A1; margin: 0; font-size: 24px; font-weight: bold;">HP SOLUÇÕES</h2>
                        <div style="font-size: 12px; font-weight: bold; color: #444;">CNPJ: 66.799.072/0001-59</div>
                        <div style="font-size: 12px; color: #555;">hpsolucoes@gmail.com</div>
                        <div style="font-size: 12px; color: #0B43A1; font-weight: bold;">(47) 99637-2330 | (47) 99188-1921</div>
                    </td>
                </tr>
            </table>

            <h1 style="color: #0B43A1; text-align: center; font-size: 22px; margin: 20px 0; border-bottom: 2px solid #0B43A1; padding-bottom: 8px; font-weight: bold; letter-spacing: 0.5px;">PROPOSTA COMERCIAL / ORÇAMENTO</h1>
            
            <table style="width: 100%; margin-bottom: 20px; font-size: 13px;">
                <tr>
                    <td style="line-height: 1.6;">
                        <span style="color: #0B43A1; font-weight: bold; font-size: 14px;">CLIENTE:</span><br>
                        <strong>{dp['cliente']['nome']}</strong><br>
                        CNPJ: {dp['cliente']['cnpj']}<br>
                        Endereço: {dp['cliente']['endereco']}<br>
                        Contato: {dp['cliente']['contato']}<br>
                        Responsável: {dp['cliente']['responsavel']}<br>
                        E-mail: {dp['cliente']['email']}
                    </td>
                    <td style="text-align: right; vertical-align: top; font-weight: bold; line-height: 1.5;">
                        Data: {datetime.now().strftime('%d/%m/%Y')}<br>
                        Nº do Orçamento: 0001
                    </td>
                </tr>
            </table>

            <!-- TABELA DE ITENS -->
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 13px;">
                <thead>
                    <tr style="background-color: #0B43A1; color: white;">
                        <th style="padding: 10px; border: 1px solid #0B43A1; text-align: left;">SERVIÇO</th>
                        <th style="padding: 10px; border: 1px solid #0B43A1; text-align: left;">DESCRIÇÃO</th>
                        <th style="padding: 10px; border: 1px solid #0B43A1; text-align: center;">VALOR</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas_html}
                </tbody>
            </table>

            <!-- TOTAL -->
            <div style="text-align: right; margin-bottom: 30px;">
                <span style="background-color: #0B43A1; color: white; padding: 10px 30px; font-size: 16px; font-weight: bold; display: inline-block;">
                    TOTAL: R$ {dp['total']:.2f}
                </span>
            </div>

            <!-- TERMOS -->
            <div style="font-size: 13px; line-height: 1.5; margin-bottom: 40px;">
                <strong style="color: #0B43A1;">FORMA DE PAGAMENTO</strong><br>
                {dp['pagamento']}<br><br>
                <strong style="color: #0B43A1;">TERMOS E CONDIÇÕES</strong><br>
                Este orçamento é válido por 30 dias.
            </div>

            <!-- ASSINATURA -->
            <div style="margin-top: 50px; font-size: 13px;">
                <div style="font-weight: bold; color: #0B43A1;">ASSINATURA</div>
                <div style="width: 200px; border-bottom: 1px solid #666; margin-top: 35px;"></div>
            </div>
        </div>
        """, height=1000, scrolling=True)
