import sqlite3
import pandas as pd
import altair as alt
import networkx as nx

### Handlong SQLite Database

def createDB():
    # código para criar as tabelas 
    structure = '''
    DROP TABLE IF EXISTS "author";
    DROP TABLE IF EXISTS "paper";
    DROP TABLE IF EXISTS "author_paper";
    CREATE TABLE "author" (
        "id" INTEGER PRIMARY KEY  NOT NULL ,
        "name" VARCHAR NOT NULL UNIQUE
    );
    CREATE TABLE "paper" (
        "id" INTEGER PRIMARY KEY  NOT NULL ,
        "title" VARCHAR NOT NULL UNIQUE
    );
    CREATE TABLE "author_paper" (
        id_paper VARCHAR,
        id_author VARCHAR,
        FOREIGN KEY(id_paper) REFERENCES paper(id)
        FOREIGN KEY(id_author) REFERENCES author(id)
    );
    '''
    
    # criando o arquivo .db
    connect = sqlite3.connect('hw1.sqlite',timeout=10)
    cursor = connect.cursor()
    cursor.executescript(structure)
    connect.commit()
    connect.close()
    

# Atualiza a base de dados    
def updateDB(titulos,autores, flat_df):
    # adicionando autores
    add_autor = '''
    INSERT OR IGNORE INTO author (name) VALUES (?);
    '''

    connect = sqlite3.connect('hw1.sqlite',timeout=10)
    for autor in autores:
        connect.execute(add_autor, [autor])
    connect.commit()
    connect.close()
    
    # adicionando artigos
    add_titulo = '''
    INSERT OR IGNORE INTO paper (title) VALUES (?);
    '''

    connect = sqlite3.connect('hw1.sqlite',timeout=10)
    for titulo in titulos:
        connect.execute(add_titulo,[titulo])
    connect.commit()
    connect.close()
    
    
    # coletando os IDs: Autores
    connect = sqlite3.connect('hw1.sqlite',timeout=10)

    autores = []
    autores_table = connect.execute('SELECT * from author')

    for autor in autores_table:
        autores.append(autor)

    connect.close()

    autores = pd.DataFrame(autores, columns=['ID_author','author'])
    
    # coletando os IDs: Artigos
    connect = sqlite3.connect('hw1.sqlite',timeout=10)

    artigos = []
    artigos_table = connect.execute('SELECT * from paper')

    for artigo in artigos_table:
        artigos.append(artigo)

    connect.close()

    artigos = pd.DataFrame(artigos, columns=['ID_paper','paper'])
    artigos.head(2)
    

    autores_e_artigos = pd.merge(flat_df,artigos,on='paper')  # adicionando coluna de ID_Artigo
    autores_e_artigos = pd.merge(autores_e_artigos,autores,on='author') # adicionando coluna ID_Autor
    
    # adicionando IDs dos autores e dos artigos
    add_autor_e_artigo ='''
    INSERT INTO author_paper (id_paper, id_author) VALUES (?,?);
    '''

    connect = sqlite3.connect('hw1.sqlite',timeout=10)
    for ID,obs in autores_e_artigos.iterrows():
        connect.execute(add_autor_e_artigo,[obs['ID_paper'],obs['ID_author']])
    connect.commit()
    connect.close()
    
    
# query all info in a table
def queryDB(table, columns):
    query = 'SELECT * FROM {}'
    
    connect = sqlite3.connect('hw1.sqlite', timeout=10)
    row = []
    for obs in connect.execute(query.format(table)):
        row.append(obs)
    connect.close()
    
    return pd.DataFrame(row, columns=columns)




### Funções para os gráficos

## Preparando os dataframes para visualização
# OBS: essas funções foram retiradas do pacote nx_altair (https://github.com/Zsailer/nx_altair) e todo crédito vai para 
# Zachary Sailer. 
#
# Do seu projeto, vamos usar apenas as funções to_pandas_edges e to_pandas_nodes para facilitar a criação dos
# dataframes para visualização com o Altair.


# Função retirada do pacote nx_altair (https://github.com/Zsailer/nx_altair)
def to_pandas_edges(G, pos, **kwargs):
    """Convert Graph edges to pandas DataFrame that's readable to Altair.
    """
    # Get all attributes in nodes
    attributes = ['source', 'target', 'x', 'y', 'edge', 'pair']
    for e in G.edges():
        attributes += list(G.edges[e].keys())
    attributes = list(set(attributes))


    # Build a dataframe for all edges and their attributes
    df = pd.DataFrame(
        index=range(G.size()*2),
        columns=attributes
    )


    # Add node data to dataframe.
    for i, e in enumerate(G.edges):
        idx = i*2

        data1 = dict(
            edge=i,
            source=e[0],
            target=e[1],
            pair=e,
            x=pos[e[0]][0],
            y=pos[e[0]][1],
            **G.edges[e]
        )

        data2 = dict(
            edge=i,
            source=e[0],
            target=e[1],
            pair=e,
            x=pos[e[1]][0],
            y=pos[e[1]][1],
            **G.edges[e]
        )

        df.loc[idx] = data1
        df.loc[idx+1] = data2

    return df


# Função retirada do pacote nx_altair (https://github.com/Zsailer/nx_altair)
def to_pandas_nodes(G, pos):
    """Convert Graph nodes to pandas DataFrame that's readable to Altair.
    """
    # Get all attributes in nodes
    attributes = ['x', 'y']
    for n in G.nodes():
        attributes += list(G.nodes[n].keys())
    attributes = list(set(attributes))

    # Build a dataframe for all nodes and their attributes
    df = pd.DataFrame(
        index=G.nodes(),
        columns=attributes
    )

    # Add node data to dataframe.
    for n in G.nodes:
        data = dict(
            x=pos[n][0],
            y=pos[n][1],
            **G.nodes[n]
        )
        df.loc[n] = data

    return df
    

   
    
    
    