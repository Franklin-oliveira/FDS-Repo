import urllib.parse
import pandas as pd
import networkx as nx
import altair as alt
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, Markup
from scrape_scholar import scrape, find_papers_and_authors
from database_and_graphics import createDB, updateDB, queryDB, to_pandas_edges, to_pandas_nodes

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

log = []
  
@app.route('/')
def home():
    # limpar também a base de dados
    createDB()
    return render_template('index.html')
  
@app.route('/about')
def about():
    return render_template('about.html')



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



# Cria os gráficos
@app.route("/scrape/graph")
def create_graph():

    # faz query no banco de dados
    autores = queryDB('author', ['ID_author','author'])
    author_paper = queryDB('author_paper', ['ID_paper','ID_author'])
    

    ### renderiza os gráficos
    
    ## Grafo 1
    graph = nx.Graph()
    
    # dataframe com colunas: paper e [lista_autores]
    group = pd.DataFrame(author_paper.groupby('ID_paper')['ID_author'].apply(list))
    
    # Adicionando "edges"
    for j,row in group.iterrows():
        i=len(row['ID_author'])
        for i in range(len(row['ID_author'])):
            for k in range(i,len(row['ID_author'])):
                graph.add_edge(row['ID_author'][i], row['ID_author'][k])
                
    # coletando labels
    autores['ID_author'] = autores['ID_author'].astype(str)
    labels = autores.set_index('ID_author').to_dict()['author']
    
    # Gráfico 1
    plt.figure(figsize=(8, 8))

    pos = nx.spring_layout(graph,k=0.2, iterations=50, weight=0.1, center=(0.5,0.5))
    nx.draw_networkx(graph,pos= pos,  labels=labels, node_color='lightseagreen', edge_color='salmon',
                    style="dotted", font_size=11)

    #plt.title('Authors',{'fontsize':14})
    plt.axis('off')
    plt.savefig('static/img/authors.png', format='png')

    plot_url = "static/img/authors.png"

    a = pd.DataFrame(pos.values(), columns=['edge_x','edge_y'])
    a['label'] = list(labels.values())

    chart = alt.Chart(a).mark_point(color='lightseagreen').encode(
             x='edge_x',
            y='edge_y',
            tooltip='label'
            ).interactive()

    return chart.to_json()



    
if __name__ == '__main__':
    app.run(debug=True)
