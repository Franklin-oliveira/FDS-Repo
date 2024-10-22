import os
import sys
import zipfile
import pandas as pd
import networkx as nx
import altair as alt
import urllib.parse
import urllib.request as request

import matplotlib.pyplot as plt

from flask import Flask, render_template, request, Markup
from scrape_scholar import scrape, find_papers_and_authors, get_chrome_version, download_chrome_driver
from database_and_graphics import createDB, updateDB, queryDB, to_pandas_edges, to_pandas_nodes

# checking chromedriver
path = os.getcwd()
file_names = os.listdir(path)

# getting driver_name
if sys.platform.lower().startswith('win'):
    driver_name = 'chromedriver.exe'
else:
    driver_name = 'chromedriver'


# checking if there's already a version of chromedriver on the current directory
if driver_name not in file_names:
    # trying to get chromedriver automatically
    try:
        chromeVersion = get_chrome_version()
        download_chrome_driver(sys.platform,chromeVersion[1])
    except:
        print('Could not download chromedriver automatically.') 
        print('\nPlease access \
                https://sites.google.com/a/chromium.org/chromedriver/downloads \
                to download it manually. ')
        print('\nDo not forget to unzip and place it at {}'.format(path))

else:
    print("There's already a version of chromedriver at {} \n".format(path))


# initializing flask
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# search_log
log = []

# Home  
@app.route('/')
def home():
    # limpar também a base de dados
    createDB()
    log = []

    return render_template('index.html')


# About 
@app.route('/about')
def about():
    return render_template('about.html')


# Scrape (collects data)
@app.route("/scrape", methods=["get", "post"])
def search():
    author = request.form['author'] # define o autor pesquisado
    
    # Se o autor já foi buscado, retorna uma mensagem e não repete a busca.
    if author.lower() in log:
        return render_template('result.html',
                               div_placeholder=Markup("This author has already been searched. Please try another one..."))
    
    else:
        log.append(author.lower()) # atualiza o log de busca

        # busca os dados
        source = scrape(str(author))[1]

        # encontra os coautores e artigos
        papers = find_papers_and_authors(source)
        
        # criando um dataframe flat (separando cada autor em uma linha diferente, para um mesmo artigo)
        flat = []
        for paper in papers:
            for author in paper['autores']:
                flat.append([paper['titulo'],author.strip()])

        flat_df = pd.DataFrame(flat, columns=['paper','author'])
        
        
        ### listas de títulos e autores
        
        # lista de artigos
        titulos = [paper['titulo'].strip() for paper in papers]

        # lista de autores
        autores = [autor.strip() for autores in 
                [paper['autores'] for paper in papers] for autor in autores]
        
        # atualiza a base de dados
        updateDB(titulos, autores, flat_df)
        

    return render_template('result.html')  # plot_url = plot_url



# Scrape (cria os gráficos)
@app.route("/scrape/graph")
def create_graph():
    # retira o número máximo de linhas para pot com Altair
    alt.data_transformers.disable_max_rows()
    
    # faz query no banco de dados
    autores = queryDB('author', ['ID_author','author'])
    artigos = queryDB('paper', ['ID_paper','paper'])
    author_paper = queryDB('author_paper', ['ID_paper','ID_author'])
    
    autores['ID_author'] = autores['ID_author'].astype(str)
    artigos['ID_paper'] = artigos['ID_paper'].astype(str)

    ### renderiza os gráficos
    
    ## Grafo 1 - Autores (authors)
    
    print('Preparando grafo dos autores...')
    graph = nx.Graph()
    
    # dataframe com colunas: paper e [lista_autores]
    group = pd.DataFrame(author_paper.groupby('ID_paper')['ID_author'].apply(list))
    
    
    # Adicionando "edges"
    for j,row in group.iterrows():
        i=len(row['ID_author'])
        for i in range(len(row['ID_author'])):
            for k in range(i,len(row['ID_author'])):
                graph.add_edge(row['ID_author'][i], row['ID_author'][k])
                
    pos = nx.spring_layout(graph,k=0.2, iterations=50, weight=0.1, center=(0.5,0.5)) # forces graph layout
    
    # coletando nodes
    nodes = to_pandas_nodes(graph,pos)
    nodes.reset_index(inplace=True)
    nodes.rename(columns={'index':'ID_author'}, inplace=True)
    nodes = pd.merge(nodes,autores,on='ID_author')  # coletando nome dos autores
    nodes = pd.merge(nodes,author_paper, on='ID_author')  # coletando ID_paper
    
    # coletando edges
    edges = to_pandas_edges(graph,pos)
    
    
    
    # Gráfico 1
    print('Criando interatividade com o Altair (autores) ...')
    
    selector = alt.selection_single(empty='all',fields=['ID_author']) # iniciando seletor
    
    points = alt.Chart(nodes).add_selection(selector).mark_point(filled=True,size=90).encode(
                alt.X('x', axis=alt.Axis(title='')),
                alt.Y('y', axis=alt.Axis(title='')),
                tooltip='author',
                opacity=alt.condition(selector,alt.value(0.95),alt.value(0.4),legend=None),
                color=alt.condition(selector, 'ID_author', alt.value('lightgray'), legend=None)
            ).properties( selection=selector ).transform_filter(selector)

    # cria um background para efeitos de transição do seletor
    bk = alt.Chart(nodes).mark_point(color='lightgray',filled=True,size=90).encode(
                alt.X('x', axis=alt.Axis(title='')),
                alt.Y('y', axis=alt.Axis(title='')),
                tooltip='author',
                opacity=alt.value(0.4),
    )

    lines = alt.Chart(edges).mark_line(color='salmon').encode(
                alt.X('x', axis=alt.Axis(title='')),
                alt.Y('y', axis=alt.Axis(title='')),
                detail='edge',
                opacity=alt.value(0.15)
            )

    chart = alt.LayerChart(layer=(lines,bk+points)).properties(
                height=350,
                width=450
                ).interactive()
    
    
    
    
    ## Grafo 2 - Artigos (papers)
    print('Preparando grafo dos artigos...')

    graph1 = nx.Graph()
    group1 = pd.DataFrame(author_paper.groupby('ID_author')['ID_paper'].apply(list))
    
    # Adicionando "edges"
    for j,row in group1.iterrows():
        i=len(row['ID_paper'])
        for i in range(len(row['ID_paper'])):
            for k in range(i,len(row['ID_paper'])):
                graph1.add_edge(row['ID_paper'][i], row['ID_paper'][k])
                
    pos1 = nx.spring_layout(graph1,k=0.2, iterations=50, weight=0.1, center=(0.5,0.5))  # forces graph layout
    
    # coletando nodes
    nodes1 = to_pandas_nodes(graph1, pos1)
    nodes1.reset_index(inplace=True)
    nodes1.rename(columns={'index':'ID_paper'}, inplace=True)
    nodes1 = pd.merge(nodes1,artigos,on='ID_paper')  # coletando nome dos papers
    nodes1 = pd.merge(nodes1,author_paper,on='ID_paper')  # coletando ID_author
    
    # coletando edges
    edges1 = to_pandas_edges(graph1,pos1)
    
    
    
    # Gráfico 2
    print('Criando interatividade com o Altair (artigos)...')

    points1 = alt.Chart(nodes1).add_selection(selector).mark_point(filled=True,size=90).encode(
                alt.X('x', axis=alt.Axis(title='')),
                alt.Y('y', axis=alt.Axis(title='')),
                tooltip='paper',
                opacity=alt.condition(selector,alt.value(0.95),alt.value(0.4),legend=None),
                color=alt.condition(selector, 'ID_author', alt.value('lightgray'), legend=None)
    ).transform_filter(selector)

    # cria um background para efeitos de transição do seletor
    bk1 = alt.Chart(nodes1).mark_point(color='lightgray',filled=True,size=90).encode(
                alt.X('x', axis=alt.Axis(title='')),
                alt.Y('y', axis=alt.Axis(title='')),
                tooltip='paper',
                opacity=alt.value(0.4),
    )

    lines1 = alt.Chart(edges1).mark_line(color='lightblue').encode(
                alt.X('x', axis=alt.Axis(title='')),
                alt.Y('y', axis=alt.Axis(title='')),
                detail='edge',
                opacity=alt.value(0.2)
    )

    chart1 = alt.LayerChart(layer=(lines1,bk1 + points1)).properties(
                height=350,
                width=450
                ).interactive()

    
    
    ### Concatenando horizontamnete os gráficos 1 e 2
    horiz_chart = alt.hconcat(chart, chart1 ).configure_axis( ticks=False,
                grid=False,
                domain=False,
                labels=False).configure_view(
                strokeWidth=0   
            )


    return horiz_chart.to_json()



    
if __name__ == '__main__':
    app.run(debug=True)
