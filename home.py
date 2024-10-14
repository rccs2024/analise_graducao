import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import scipy.stats as stats
from datetime import datetime

# Configurar o Streamlit
st.set_page_config(page_title="Dashboard Interativo", layout="wide")

# Dicionário de credenciais simples (usuários e senhas)
credentials = {
    "usernames": {
        "usuario1": {
            "name": "jaiver",
            "password": "$2b$12$mdUYLj5hiYZ.S6fSGxwkK.2X93ad28IVLmAD5PVDAbpKTXYFLWFkS"  # Senha criptografada: senha123
        },
        "admin": {
            "name": "admin",
            "password": "$2b$12$mdUYLj5hiYZ.S6fSGxwkK.2X93ad28IVLmAD5PVDAbpKTXYFLWFkS"  # Senha criptografada: admin123
        }
    }
}

# Configuração do autenticador
authenticator = stauth.Authenticate(
    credentials,
    "login_cookie",  # Nome do cookie para persistência da sessão
    "random_key",    # Chave de segurança única
    cookie_expiry_days=30
)

# Implementação do login
name, authentication_status, username = authenticator.login("Login", "main")

# Se o usuário estiver autenticado
if authentication_status:
   
    ################################## Base ########################################################################################
    db_cc = pd.read_csv('base/amostra_alunos_completa_cc_10_2024.csv', encoding='ISO-8859-1', delimiter=';')
    db_enfermagem = pd.read_csv('base/amostra_alunos_completa_enfermagem_10_2024.csv', encoding='ISO-8859-1', delimiter=';')
    db_bict = pd.read_csv('base/amostra_alunos_completa_bict_10_2024.csv', encoding='ISO-8859-1', delimiter=';')
    df_descricao = pd.read_excel("base/descricao.xlsx")

    df_alunos = pd.concat([db_enfermagem,db_bict,db_cc], axis=0, ignore_index=True)
    df_alunos = df_alunos[df_alunos['Ano_Ingresso'] >= 2011]


    ############################ Criando colunas, conforme entendimento do negocio ####################################################

    ## Criando a coluna Novo_Status considerando todos os registros, e alterando os registro de status cancelado
    ## quando o tipo de saida for igual a CANCELAMENTO (RESOL 1175/CONSEPE Art.156)
    df_alunos['Novo_Status'] = df_alunos.apply(
        lambda row: 'DESLIGADO' if (row['Status'] == 'DESLIGADO') or 
        (row['Status'] == 'CANCELADO' and row['Tipo_Saida'] == 'CANCELAMENTO (RESOL 1175/CONSEPE Art.156)')
        else row['Status'], axis=1)



    ####### Criando as colunas (Prazo_Integralizacao_Ano e Prazo_Integralizacao_Semestre)  a partir da coluna Prazo_Integralizacao
    # separando o ano e o semestre

    # Criando a variável 'Prazo_Integralizacao_Ano' com os 4 primeiros dígitos
    df_alunos['Prazo_Integralizacao_Ano'] = df_alunos['Prazo_Integralizacao'].astype(str).str[:4].astype(int)
    # Criando a variável 'Prazo_Integralizacao_Semestre' com o último dígito
    df_alunos['Prazo_Integralizacao_Semestre'] = df_alunos['Prazo_Integralizacao'].astype(str).str[-1].astype(int)


    ##### Ajustando valores da variavel Novo_Status considerando se a variavel (Prazo_Integralizacao_Ano') 
    # for menor que o ano atual, altere o valor da variavel Novo_Status ('CANCELADO', 'ATIVO')  para (desligado2)  
    ano_atual = datetime.now().year
    df_alunos.loc[
        (df_alunos['Prazo_Integralizacao_Ano'] < ano_atual) & (df_alunos['Novo_Status'].isin(['CANCELADO', 'ATIVO'])),'Novo_Status'] = 'DESLIGADO2'


    ### Apagando alguns resgistros nulls (total 7)
    indices_para_remover = df_alunos[df_alunos['Novo_Status'].isnull()].index
    df_alunos = df_alunos.drop(indices_para_remover)
    indices_para_remover = df_alunos[df_alunos['Coeficiente_de_Rendimento'].isnull()].index
    df_alunos = df_alunos.drop(indices_para_remover)
    df_alunos = df_alunos.reset_index(drop=True)




    if not 'pagina_analise' in st.session_state:
        
        st.session_state.pagina_analise = 'home'

    def mudar_pagina(nome_pagina):
        st.session_state.pagina_analise = nome_pagina


    # ============== HOME ===================
    def home():
        #st.markdown('# Inicio - Dasboard Análise Exploratória')
        st.success(f"Olá, {name}!")
        st.markdown("""
        ### Bem-vindo ao Dashboard de Análise Acadêmica

        Este dashboard foi desenvolvido para fornecer uma visão abrangente e detalhada das taxas de conclusão, evasão e desempenho acadêmico dos alunos da Universidade Federal do Maranhão (UFMA), com foco inicial ns cursos de Ciência e Tecnologia, Ciência da Computação e Enfermagem. O objetivo principal é permitir uma análise exploratória e descritiva das principais métricas acadêmicas, facilitando o monitoramento contínuo de indicadores de sucesso e abandono dos estudantes.

        #### Regras e Considerações

        Para garantir a consistência e relevância das análises, algumas diretrizes foram aplicadas ao conjunto de dados:

        1. **Período de Ingresso**: Foram considerados apenas os registros de alunos que ingressaram a partir de 2011. Esse recorte temporal visa alinhar a análise com as políticas e diretrizes acadêmicas atuais da UFMA.
        
        2. **Novo Status dos Alunos**: Uma nova coluna chamada `Novo_Status` foi criada para refletir com mais precisão a situação acadêmica dos alunos. O status original de "cancelado" foi ajustado para "desligado" quando o tipo de saída era classificado como *CANCELAMENTO (RESOL 1175/CONSEPE Art.156)*.

        3. **Prazo de Integralização**: Foram criadas duas novas colunas, `Prazo_Integralizacao_Ano` e `Prazo_Integralizacao_Semestre`, a partir da coluna original de `Prazo_Integralizacao`. Essas colunas segmentam o prazo em componentes de ano e semestre, facilitando a análise da trajetória acadêmica dos alunos.

        4. **Ajuste de Status**: Para alunos cujo prazo de integralização tenha expirado (quando `Prazo_Integralizacao_Ano` é inferior ao ano atual), o valor da variável `Novo_Status` foi ajustado. Se o aluno estivesse com status de "CANCELADO" ou "ATIVO", foi alterado para "DESLIGADO2" como forma de indicar o desligamento por não conclusão dentro do prazo estabelecido.

        #### Atualização dos Dados

        O conjunto de dados utilizado para esta análise foi atualizado pela última vez em **Outubro de 2024**, garantindo que todas as informações estejam alinhadas com os registros acadêmicos mais recentes.
        """)

    # ============== DICIONARIO ===================
    def pag_dicionario():
        st.markdown('# Dicionário do Dados')
        st.dataframe(df_descricao, height=600, use_container_width=True)


    # ============== ESTATISITICA DESCRITIVA ===========================================================================
    def pag_Estatistica():
        st.markdown('# Estatística Descritiva')
        st.divider()
        st.markdown('## Medidas de Tendência Central')
        st.markdown("<br>", unsafe_allow_html=True)
    
        col1, col2, col3 = st.columns(3)
        with col1:
            curso = df_alunos['Curso'].unique()
            curso_selecionado = st.selectbox("Selecione o Curso", sorted(curso))
            
        with col2:
            tipo_estatistica = st.radio("Análise Descritiva - Selecione as Varíaveis:", ("Numéricas", "Categorias"))
        
        with col3:
            df_curso = df_alunos[df_alunos['Curso'] == curso_selecionado]
            df_curso['Ano_Ingresso_Ano'] = df_curso['Ano_Ingresso'].astype(int) # Criando nova coluna Ano_ingresso_ano a partir do ano ingresso
            data_inicial = df_curso['Ano_Ingresso_Ano'].min()
            data_final = df_curso['Ano_Ingresso_Ano'].max()
            intervalo_ano = st.slider("Selecione o período ingresso(ano)", min_value=data_inicial , max_value=data_final, value=(data_inicial, data_final))   
        
        # Filtro de status
        status_unicos = df_curso['Novo_Status'].unique().tolist()
        status_selecionados = st.multiselect("Selecione os Status", status_unicos, default=status_unicos)

        # Filtrar os dados com base no intervalo de anos e status selecionados
        df_curso = df_curso[
            (df_curso['Ano_Ingresso_Ano'] >= intervalo_ano[0]) & 
            (df_curso['Ano_Ingresso_Ano'] <= intervalo_ano[1]) & 
            (df_curso['Novo_Status'].isin(status_selecionados))]

        # Filtrar os dados com base no intervalo de anos selecionado no slider
        df_curso = df_curso[(df_curso['Ano_Ingresso_Ano'] >= intervalo_ano[0]) & (df_curso['Ano_Ingresso_Ano'] <= intervalo_ano[1])]

        st.markdown("<br>", unsafe_allow_html=True)
        
        if tipo_estatistica == "Categorias":
            col_object=['Cidade_Estado','Sexo','Tipo_Raca','Identidade_Genero','Forma_Ingresso','Tipo_Saida','Status','Tipo_Rede_Ensino','Estado_Civil']
            resumo_categoria = df_curso[col_object].describe(include=object).transpose().reset_index()
            st.dataframe(resumo_categoria)
            
        
        else:
            col_numericas = ['Coeficiente_de_Rendimento','Média_de_Conclusão','Média_de_Conclusão_Normalizada','Índice_de_Eficiência_em_Carga_Horária',
                    'Índice_de_Eficiência_em_Períodos_Letivos','Índice_de_Eficiência_Acadêmica']
            resumo_numerico = df_curso[col_numericas].describe().transpose().reset_index()
        
            col1, col2, col3 = st.columns([2,1,1])

            with col1:
                resumo_numerico[['index','count','std','max']]

            with col2:    
                for coluna in col_numericas:
                    media = df_curso[coluna].mean()
                    st.metric(label=f"Média: {coluna.replace('_', ' ')}", value=f"{media:.2f}")
            
            with col3: 
                for coluna in col_numericas:
                    mediana = df_curso[coluna].median()
                    st.metric(label=f"Mediana: {coluna.replace('_', ' ')}", value=f"{mediana:.2f}")

            st.divider()
            st.markdown('## Representações gráficas')
            st.markdown("<br>", unsafe_allow_html=True)
            
        
        # Controle para exibir duas métricas por vez
            metrica_selecionada = st.radio("Selecione a métrica para visualização:", col_numericas)

                # Histograma com Altair
            histograma = alt.Chart(df_curso).mark_bar().encode(
                    alt.X(f'{metrica_selecionada}:Q', bin=alt.Bin(maxbins=20), title=metrica_selecionada.replace('_', ' ')),
                    alt.Y('count()', title='Frequência')
                ).properties(
                    width=600,
                    height=400,
                    title=f'Distribuição {metrica_selecionada.replace("_", " ")}'
                )

                # Exibir o histograma
            st.altair_chart(histograma, use_container_width=True)

                # Box plot com Altair
            boxplot = alt.Chart(df_curso).mark_boxplot(size=70).encode(
                    x=alt.X(f'{metrica_selecionada}:Q', title=metrica_selecionada.replace('_', ' '))
                ).properties(
                    width=600,
                    height=300,
                    title=f'Box Plot do {metrica_selecionada.replace("_", " ")}'
                )

                # Exibir o boxplot
            st.altair_chart(boxplot, use_container_width=True)

            if st.button('Deseja visualizar os registros filtrados?'):   
                st.markdown('### Registros Filtrados: ')
                df = df_curso[['Matrícula','Nome','Novo_Status','Ano_Ingresso','Ano_Periodo_Saida','Tipo_Saida',
                            'Coeficiente_de_Rendimento','Média_de_Conclusão','Média_de_Conclusão_Normalizada',
                            'Índice_de_Eficiência_em_Carga_Horária','Índice_de_Eficiência_em_Períodos_Letivos','Índice_de_Eficiência_Acadêmica']]
                quantidade = len(df)
                st.markdown(f"#### {quantidade} Registros encontrados")
                df = df.sort_values(by='Ano_Ingresso', ascending=True)
                st.dataframe(df, use_container_width=True)


    # ============== DISTIBUIÇÃO DO STATUS ==========================================
    def pag_distibuicao():
        st.markdown('# Distribuição - Status do aluno')
        st.divider()
        
        # Listar os cursos disponíveis
        curso = df_alunos['Curso'].unique()

        # Espaço para layout     
        # Dividindo a interface em duas colunas
        col1, col2 = st.columns(2)
        
        # Seletor de curso
        with col1:
            # Seletor de status (multiselect)
            curso_selecionado = st.selectbox("Selecione o Curso", sorted(curso))
            
            # Filtrar os dados com base no curso selecionado
            df_curso = df_alunos[df_alunos['Curso'] == curso_selecionado]
            df_curso = df_curso.dropna(subset=['Novo_Status'])  # Remove registros(Null) sem status
            df_curso['Ano_Ingresso_Ano'] = df_curso['Ano_Ingresso'].astype(int) # Criando nova coluna Ano_ingresso_ano a partir do ano ingresso

        with col2:
            data_inicial = df_curso['Ano_Ingresso_Ano'].min()
            data_final = df_curso['Ano_Ingresso_Ano'].max()

            intervalo_ano = st.slider("Selecione o período", min_value=data_inicial , max_value=data_final, value=(data_inicial, data_final))

            status = df_curso['Novo_Status'].unique().tolist()
            lista_de_status = st.multiselect("Selecione os Status: ", status, default=[])  # Nenhum status selecionado por padrão


        # Verifica se o curso foi selecionado
        if curso_selecionado:
            st.markdown("<br>", unsafe_allow_html=True)
            # Verifica se há status selecionados no multiselect
            if lista_de_status:
                # Filtrar pelo status e pelo intervalo de anos
                df_filtrado = df_curso[(df_curso['Novo_Status'].isin(lista_de_status)) & 
                                    (df_curso['Ano_Ingresso_Ano'] >= intervalo_ano[0]) & 
                                    (df_curso['Ano_Ingresso_Ano'] <= intervalo_ano[1])]
            else:
                # Filtrar apenas pelo intervalo de anos
                df_filtrado = df_curso[(df_curso['Ano_Ingresso_Ano'] >= intervalo_ano[0]) & 
                                    (df_curso['Ano_Ingresso_Ano'] <= intervalo_ano[1])]

            # Criando o gráfico de barras com Altair para a distribuição de 'Novo_Status'
            chart = alt.Chart(df_filtrado).mark_bar().encode(
                x=alt.X('Novo_Status', title='Status'),
                y=alt.Y('count()', title='Contagem'),
                color=alt.Color('Novo_Status', scale=alt.Scale(scheme='viridis')),  # Aplicando a paleta 'viridis'
                tooltip=['Novo_Status', 'count()']  # Tooltip interativo para visualizar os valores
            ).properties(
                width=600,
                height=400,
                title='Distribuição de Status dos Alunos (Ajustado)'
            ).configure_axis(
                labelAngle=90  # Rotacionando os rótulos no eixo X
            ).configure_title(
                fontSize=20
            )

            # Exibindo o gráfico no Streamlit
            st.altair_chart(chart, use_container_width=True)
            
            if st.button('Deseja visualizar os registros filtrados?'):   
                st.markdown('### Registros Filtrados: ')
                df = df_filtrado[['Matrícula','Nome','Novo_Status','Coeficiente_de_Rendimento','Índice_de_Eficiência_Acadêmica','Índice_de_Eficiência_em_Carga_Horária','Ano_Ingresso','Ano_Periodo_Saida','Tipo_Saida']]
                quantidade = len(df)
                st.markdown(f"#### {quantidade} Registros encontrados")
                df = df.sort_values(by='Ano_Ingresso', ascending=True)
                st.dataframe(df, use_container_width=True)



    # ============== PAGINA TAXAS =====================================================
    def pag_taxas():
        st.markdown('# Taxas')
        st.divider()           
        
        col1, col2 = st.columns(2)

        with col1:
            curso = ['TODOS', 'CIÊNCIA DA COMPUTAÇÃO', 'ENFERMAGEM']
            curso_selecionado = st.selectbox("Selecione o Curso", sorted(curso))
            st.markdown("<br>", unsafe_allow_html=True)

            # Filtrar os dados com base no curso selecionado, exceto se for "TODOS"
            if curso_selecionado != 'TODOS':     
                df_filtrado = df_alunos[df_alunos['Curso'] == curso_selecionado]
            else:
                df_filtrado = df_alunos.copy()  # Usar todos os dados sem filtro

            df_filtrado['Ano_Ingresso_Ano'] = df_filtrado['Ano_Ingresso'].astype(int) # Criando nova coluna Ano_ingresso_ano a partir do ano ingresso
            data_inicial = df_filtrado['Ano_Ingresso_Ano'].min()
            data_final = df_filtrado['Ano_Ingresso_Ano'].max()

            intervalo_ano = st.slider("Selecione o período", min_value=data_inicial , max_value=data_final, value=(data_inicial, data_final))
            st.markdown("<br>", unsafe_allow_html=True)

            lista_de_Taxas = ['Taxa_Evasão','Taxa_Cancelados','Taxa_Conclusão','Taxa_Ativos']
            taxas = st.multiselect("Selecione os Status: ", lista_de_Taxas, default=lista_de_Taxas)  # Nenhum status selecionado por padrão
            st.markdown("<br>", unsafe_allow_html=True)
        #with col2:
        
        
        # Filtrar apenas pelo intervalo de anos
        df_filtrado = df_filtrado[(df_filtrado['Ano_Ingresso_Ano'] >= intervalo_ano[0]) & 
                                    (df_filtrado['Ano_Ingresso_Ano'] <= intervalo_ano[1])]
        
        # Calcular as métricas por ano de ingresso e status
        status_por_ano = df_filtrado.groupby(['Ano_Ingresso', 'Novo_Status']).size().unstack().fillna(0)
        ingressantes_por_ano = df_filtrado.groupby('Ano_Ingresso').size()

        # Atualizar a coluna 'Ingressantes' no dataframe status_por_ano com os valores corretos
        status_por_ano['Ingressantes'] = ingressantes_por_ano

        # Calcular as taxas
        status_por_ano['Taxa_Evasão'] = (status_por_ano['DESLIGADO'] / status_por_ano['Ingressantes']) * 100
        status_por_ano['Taxa_Cancelados'] = (status_por_ano['CANCELADO'] / status_por_ano['Ingressantes']) * 100
        status_por_ano['Taxa_Conclusão'] = ((status_por_ano['CONCLUÍDO'] + status_por_ano['FORMANDO']) / status_por_ano['Ingressantes']) * 100
        status_por_ano['Taxa_Ativos'] = (status_por_ano['ATIVO'] / status_por_ano['Ingressantes']) * 100
        

        with col2:
            total_ingressantes = status_por_ano['Ingressantes'].sum()
            conclusao = (status_por_ano['CONCLUÍDO'].sum() + status_por_ano['FORMANDO'].sum()) / total_ingressantes * 100
            cancelado = status_por_ano['CANCELADO'].sum() / total_ingressantes * 100
            evadido = status_por_ano['DESLIGADO'].sum() / total_ingressantes * 100
            ativo = status_por_ano['ATIVO'].sum() / total_ingressantes * 100
            trancado = status_por_ano['TRANCADO'].sum() / total_ingressantes * 100

            # Preparar os dados para o gráfico de pizza com Altair
            df_pizza = pd.DataFrame({
                'Status': ['Conclusão', 'Cancelado', 'Evadido', 'Ativo', 'Trancado'],
                'Percentual': [conclusao, cancelado, evadido, ativo, trancado]
            })
        # Cores degradê da UFMA
            cores_ufma = ['#11644d', '#f2c94e', '#f24e4e', '#8D0003', '#D4B277']

            # Ajustar o gráfico para parecer mais com um gráfico de pizza com espaçamento entre fatias
            grafico_pizza = alt.Chart(df_pizza).mark_arc(outerRadius=150, innerRadius=0).encode(
                theta=alt.Theta(field="Percentual", type="quantitative"),
                color=alt.Color(field="Status", scale=alt.Scale(range=cores_ufma)),
                tooltip=['Status', alt.Tooltip('Percentual', format='.1f')]
            ).properties(
                title={
                    "text": "Distribuição Percentual dos Status Acadêmicos dos Alunos",
                    "align": "right",  # Ajustar o título para a direita
                    "anchor": "end"
                },
                width=400,
                height=400
            ).configure_arc(
                stroke='white',  # Espaçamento entre as fatias com contorno branco
                strokeWidth=2
            )

            # Exibir o gráfico no Streamlit
            st.altair_chart(grafico_pizza, use_container_width=True)


    # Converter o dataframe para formato longo para usar no Altair
        status_long = status_por_ano.reset_index().melt(
            id_vars=['Ano_Ingresso'], 
            value_vars=taxas,
            var_name='Tipo_Taxa', 
            value_name='Taxa (%)'
        )

        # Criar o gráfico de linhas com Altair
        grafico_taxas = alt.Chart(status_long).mark_line(point=True).encode(
            x=alt.X('Ano_Ingresso:O', title='Ano de Ingresso'),
            y=alt.Y('Taxa (%):Q', title='Taxa (%)'),
            color='Tipo_Taxa:N',
            tooltip=['Ano_Ingresso', 'Tipo_Taxa', 'Taxa (%)']
        ).properties(
            title='Taxa de Alunos Cancelados, Concluintes, Ativos e Evadidos por Ano de Ingresso',
            width=800,
            height=400
        )

        # Exibir o gráfico no Streamlit
        st.altair_chart(grafico_taxas, use_container_width=True)
        
        if st.button('Deseja visualizar os registros filtrados?'): 
            df = df_filtrado[['Nome','Curso','Ano_Ingresso','Tipo_Saida','Novo_Status']]
            quantidade = len(df)
            st.markdown(f"#### {quantidade} Registros encontrados")
            df = df.sort_values(by='Ano_Ingresso', ascending=True)
            st.dataframe(df,use_container_width=True)
        
        # Exibir o dataframe atualizado
        #st.dataframe(status_por_ano, use_container_width=True) 


    # ============== INDICES ACADEMICO =================================================================
    def pag_acedemicos():
        st.markdown('# Índices Acadêmicos')
        st.divider()           
        
        col1, col2 = st.columns(2)

        with col1:
            curso = ['TODOS', 'CIÊNCIA E TECNOLOGIA', 'CIÊNCIA DA COMPUTAÇÃO', 'ENFERMAGEM']
            curso_selecionado = st.selectbox("Selecione o Curso", sorted(curso))
            st.markdown("<br>", unsafe_allow_html=True)

            # Filtrar os dados com base no curso selecionado, exceto se for "TODOS"
            if curso_selecionado != 'TODOS':     
                df_filtrado = df_alunos[df_alunos['Curso'] == curso_selecionado]
            else:
                df_filtrado = df_alunos.copy()  # Usar todos os dados sem filtro
            
            st.markdown("<br>", unsafe_allow_html=True)
            # Selecionar as colunas relevantes para a análise
            metricas_coluna = ['Coeficiente_de_Rendimento', 'Média_de_Conclusão', 
                            'Média_de_Conclusão_Normalizada', 'Índice_de_Eficiência_em_Carga_Horária', 
                            'Índice_de_Eficiência_em_Períodos_Letivos', 'Índice_de_Eficiência_Acadêmica']
            
            # Usar multiselect para selecionar múltiplas métricas ao mesmo tempo
            metricas_selecionadas = st.multiselect("Selecione as métricas para visualização:", 
                                                metricas_coluna, default=metricas_coluna)
            


        with col2:    
            df_filtrado['Ano_Ingresso_Ano'] = df_filtrado['Ano_Ingresso'].astype(int) # Criando nova coluna Ano_ingresso_ano a partir do ano ingresso
            data_inicial = df_filtrado['Ano_Ingresso_Ano'].min()
            data_final = df_filtrado['Ano_Ingresso_Ano'].max()

            intervalo_ano = st.slider("Selecione o período", min_value=data_inicial , max_value=data_final, value=(data_inicial, data_final))
            st.markdown("<br>", unsafe_allow_html=True)

            # Filtrar os dados com base no intervalo de anos selecionado
            df_filtrado = df_filtrado[
                (df_filtrado['Ano_Ingresso_Ano'] >= intervalo_ano[0]) & 
                (df_filtrado['Ano_Ingresso_Ano'] <= intervalo_ano[1])
            ]
            
            # Adicionar filtro por Status
            status_opcoes = df_filtrado['Novo_Status'].unique().tolist()
            status_selecionados = st.multiselect("Selecione os Status:", status_opcoes, default=status_opcoes)

            # Filtrar os dados com base nos status selecionados
            if status_selecionados:
                df_filtrado = df_filtrado[df_filtrado['Novo_Status'].isin(status_selecionados)]
        
        # Filtrar as métricas selecionadas para análise
        metricas_coluna = metricas_selecionadas

        # Calcular as médias, medianas e máximos gerais das métricas acadêmicas
        metricas_geral = df_filtrado[metricas_coluna].agg(['mean', 'median', 'max'])

        col1, col2, col3 = st.columns(3)
        
        with col1:
            for metrica in metricas_coluna:
                media = metricas_geral[metrica]['mean']
                st.metric(label=f"Média: {metrica.replace('_', ' ')}", value=f"{media:.2f}")
        
        with col2:
            for metrica in metricas_coluna:
                median = metricas_geral[metrica]['median']
                st.metric(label=f"Mediana: {metrica.replace('_', ' ')}", value=f"{median:.2f}")
        
        with col3:
            for metrica in metricas_coluna:
                maximo = metricas_geral[metrica]['max']
                st.metric(label=f"Máximo: {metrica.replace('_', ' ')}", value=f"{maximo:.2f}")


        # Transformar os dados para calcular a média por ano de ingresso e status
        df_agrupado = df_filtrado.groupby(['Ano_Ingresso_Ano', 'Novo_Status']).agg(
            Coeficiente_de_Rendimento=('Coeficiente_de_Rendimento', 'mean'),
            Média_de_Conclusão=('Média_de_Conclusão', 'mean'),
            Média_de_Conclusão_Normalizada=('Média_de_Conclusão_Normalizada', 'mean'),
            Índice_de_Eficiência_em_Carga_Horária=('Índice_de_Eficiência_em_Carga_Horária', 'mean'),
            Índice_de_Eficiência_em_Períodos_Letivos=('Índice_de_Eficiência_em_Períodos_Letivos', 'mean'),
            Índice_de_Eficiência_Acadêmica=('Índice_de_Eficiência_Acadêmica', 'mean')        
        ).reset_index()

        # Selecionar a métrica a ser visualizada
        metrica_selecionada = st.selectbox("Selecione a métrica para visualização:", metricas_selecionadas)

        # Criar gráfico de linhas com Altair para comparar as médias ao longo dos anos
        grafico = alt.Chart(df_agrupado).mark_line(point=True).encode(
            x=alt.X('Ano_Ingresso_Ano:O', title='Ano de Ingresso'),
            y=alt.Y(f'{metrica_selecionada}:Q', title=metrica_selecionada),
            color=alt.Color('Novo_Status:N', legend=alt.Legend(title='Status')),
            tooltip=['Ano_Ingresso_Ano', f'{metrica_selecionada}', 'Novo_Status']
        ).properties(
            width=700,
            height=400,
            title=f'Comparação de {metrica_selecionada} entre Concluintes, Desligados e Cancelados por Ano de Ingresso'
        ).interactive()

        # Exibir o gráfico no Streamlit
        st.altair_chart(grafico, use_container_width=True)
        # Exibir as tabelas para análise
        st.dataframe(metricas_geral, use_container_width=True)
    
    

    def main():
        st.sidebar.button('Inicio', use_container_width=True, on_click=mudar_pagina, args=('home',))
        st.sidebar.button('Dicionario', use_container_width=True, on_click=mudar_pagina, args=('dicionario',))
        st.sidebar.button('Estatística Descritiva', use_container_width=True, on_click=mudar_pagina, args=('estatistica',))
        st.sidebar.button('Distibuição - Satus do aluno', use_container_width=True, on_click=mudar_pagina, args=('distibuicao',))
        st.sidebar.button('Taxas', use_container_width=True, on_click=mudar_pagina, args=('taxas',))
        st.sidebar.button('Índices Acadêmicos', use_container_width=True, on_click=mudar_pagina, args=('indices',))
        

        if st.session_state.pagina_analise == 'home':
            home()
        elif st.session_state.pagina_analise == 'dicionario':
            pag_dicionario()
        elif st.session_state.pagina_analise == 'estatistica':
            pag_Estatistica()
        elif st.session_state.pagina_analise == 'distibuicao':
            pag_distibuicao()
        elif st.session_state.pagina_analise == 'taxas':
            pag_taxas()    
        elif st.session_state.pagina_analise == 'indices':
            pag_acedemicos()

    main()
    
# Caso a autenticação falhe
elif authentication_status == False:
    st.error('Usuário ou senha incorretos')

# Caso o usuário ainda não tenha tentado logar
elif authentication_status == None:
    st.warning('Por favor, insira seu nome de usuário e senha')

# Permitir logout
if authentication_status:
    authenticator.logout('Sair', 'sidebar')
