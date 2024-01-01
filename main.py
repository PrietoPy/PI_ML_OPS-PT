#importamos librerias necesarias
from fastapi import FastAPI
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
from sklearn.metrics.pairwise import cosine_similarity

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Obtiene la variable de entorno MI_SECRETO (version de python para render)
mi_secreto = os.getenv("MI_SECRETO")

# Crea una instancia de FastAPI
app = FastAPI(swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"})

# Lee los DataFrames desde archivos parquet
games = pd.read_parquet('./Datasets/gamesoh.parquet') # DF de juegos con generos en formato binario o 'one hot encode'
reviews = pd.read_parquet('./Datasets/reviews.parquet') # DF con reseña de usuarios sobre videojuegos con la columna de sentimiento
items = pd.read_parquet('./Datasets/itemso.parquet') # DF de horas jugadas por juego por usuario
gnames = pd.read_parquet('./Datasets/games.parquet') # DF con el id y nombre de los juegos
fnames = pd.read_parquet('./Datasets/fnames.parquet') # DF con el id y nombre de los juegos que se tiene el id y se obtuvo el nombre de fuente externa (api oficial de Steam)
unames = pd.read_parquet('./Datasets/unames.parquet') # DF con el id y nombre de usuarios

# generamos listas para verificar contenido del Dataset
generos = list(games.drop(columns=['item_id']).columns) # lista de generos disponibles en el Dataset
lid=list(set(gnames['item_id'])) # lista de juegos
lfid=list(set(fnames['item_id'])) # lista de juegos 2
lanio=list(set(reviews['posted'].to_list())) # lista de años

# Define la ruta principal del API
@app.get('/')
async def root():
    '''
    Esta funcion no realiza ninguna tarea, es la pagina principal
    '''
    return {'hello': 'world'}

# Define la ruta para la función PlayTimeGenre
@app.get('/PlayTimeGenre/{genero}')
async def PlayTimeGenre(genero:str):
    '''
    Esta funcion toma como parametro el género, un valor del tipo String, 
    y devuelve el año de lanzamiento con más horas jugadas para el género ingresado.
    '''
    genero=genero.upper() # la variable obtenida se dispone en mayuscula para evitar errores de tipeo
    if genero in generos: # consultamos si la variable ingresada se encuentra en la base de datos 
        lgames = games.loc[games[genero] == 1, ['item_id']] # filtramos el DF de juegos con el genero que nos interesa
        lhoras = items.groupby('item_id')['playtime_forever'].sum().reset_index() # Agrupamos el DF obtenido por el id de los juegos sumando las horas de juego
        dfplay = pd.merge(lgames, lhoras, on='item_id', how='inner') # juntamos el DF de generos y DF de horas 
        dfplay = pd.merge(dfplay, gnames, on='item_id', how='inner') # volvemos a juntar el resultado con gnames para obtener el año de lanzamiento
        df_horas = dfplay.groupby('release_date')['playtime_forever'].sum().reset_index() # agrupamos por año sumando las horas de juego
        df_horas_ordenado = df_horas.sort_values(by='playtime_forever', ascending=False) # ordenamos de mayor a menor la columna de horas de juego
        resultado=df_horas_ordenado.head(1) # obtenemos el primer registro ya que luego de ordenar seria el mayor
        prin = "Año de lanzamiento con más horas jugadas para Género " + genero # anidamos la cadena del resultado con el genero ingresado
        anio = int(resultado['release_date'].iloc[0]) # nos centramos en el valor de la columna de año de lanzamiento de juego
        return {prin : anio} # retornamos el string y el valor obtenido
    else:
        return {"El Genero indicado no se encuentra en la base de datos":genero} # en el caso de que el genero solicitado no se encuentre en nuestro Dataset

# Define la ruta para la función UserForGenre
@app.get('/UserForGenre/{genero}')
async def UserForGenre(genero:str):
    '''
    Esta funcion toma como parametro el género, un valor del tipo String, 
    devuelve el usuario que acumula más horas jugadas para el género ingresado
    y una lista de la acumulación de horas jugadas por año de lanzamiento.
    '''
    genero=genero.upper() # la variable obtenida se dispone en mayuscula para evitar errores de tipeo
    if genero in generos:  # consultamos si la variable ingresada se encuentra en la base de datos
        dfgames = games[['item_id',genero]] # filtramos el DF de juegos con el genero que nos interesa
        dfgames = dfgames[games[genero]==1] # filtramos el DF de juegos con el genero que nos interesa
        dfuserg = pd.merge(dfgames,items,on='item_id',how='inner') # juntamos el DF de juegos con el de items para obtener las horas jugadas
        uhoras = dfuserg.groupby('user_id')['playtime_forever'].sum().reset_index() # Agrupamos por usuario y sumamos las horas jugadas
        uhoras = uhoras.sort_values(by='playtime_forever', ascending=False) #Ordenamos de mayor a menor por horas jugadas
        uhoras = uhoras.head(1) # Como hemos ordenado la primera fila es el de mayor cantidad de horas
        uhoras = uhoras['user_id'].iloc[0] # obtenemos el usuario con mayor cantidad de horas
        dfuserg = dfuserg[dfuserg['user_id']==uhoras] # filtramos el df de juegos por el usuario
        dfuserg = pd.merge(dfuserg,gnames,on='item_id',how='inner') # juntamos con gnames para obtener el año de lanzamiento
        dfuserg = dfuserg.groupby('release_date')['playtime_forever'].sum().reset_index() # agrupamos por año y sumamos las horas jugadas
        dfuserg = dfuserg.sort_values(by='release_date', ascending=False) # ordenamos por año de mayor a menor
        dfuserg = dfuserg[dfuserg['playtime_forever']>0] # descartamos los años en los que no tuvo horas jugadas
        dfuserg['playtime_forever'] = dfuserg['playtime_forever'].astype(int) # convertimos a entero la columna de horas
        dfuserg = dfuserg[['playtime_forever', 'release_date']] # obtenemos el DF con las columnas relevantes para este caso
        dfuserg.rename(columns={'release_date': 'Año', 'playtime_forever':'Horas'}, inplace=True) #cambiamos el nombre de las columnas
        di=dfuserg.to_dict(orient='records') # convertimos el DF en un diccionario
        uhoras = unames[unames['user_id']==uhoras] # filtramos el df para obtener el usuario
        uhoras = uhoras['user_name'].iloc[0] # obtenemos el nombre del usuario
        prin="Usuario con más horas jugadas para Género " + genero # anidamos el string de la respuesta con el genero ingresado
        return {prin:uhoras,"Horas Jugadas":di} # retorna el string y el diccionario de valores obtenido
    else:
        return {"El Genero indicado no se encuentra en la base de datos ":genero} # en el caso de que el genero solicitado no se encuentre en nuestro Dataset

# Define la ruta para la función UsersRecommend
@app.get('/UsersRecommend/{anio}')
async def UsersRecommend(anio:int):
    '''
    Esta funcion toma como parametro el año, un valor del tipo int, 
    y devuelve el top 3 de juegos MÁS recomendados por usuarios para el año ingresado.
    '''
    if anio in lanio: # consultamos si el valor ingresado se encuentra dentro del Dataset
        dfa = reviews[(reviews['posted'] == anio) & (reviews['recommend'] == True) & (reviews['sentiment_analysis'] >0)].copy() # Filtramos el DF mediante el año ingresado, el juego es recomendado y el sentimiento es nulo o positivo (1 o 2)
        dfa = dfa.groupby('item_id')['sentiment_analysis'].sum().reset_index() # agrupamos por el juego y sumamos el sentimiento
        dfa = dfa.sort_values('sentiment_analysis', ascending=False) # ordenamos por cantidad de sentimiento
        dfa['item_id'] = dfa['item_id'].astype(int) # converimos a entero la columna 
        top_games = dfa.head(3)['item_id'].to_list() # obtenemos los 3 id de mayor sentimiento (mas recomendados)
        for i,g in enumerate(top_games): # recorreoms la lista de id de juegos recomendados
            if g in lid: # para el caso de que el id este en el Dataset normal, obtenemos el nombre del Dataset normal
                top_games[i]=gnames[gnames['item_id'] == top_games[i]].head(1)['title'].iloc[0]
            else: #para aquellos id que no se encontraban en el Dataset, sacamos el nombre de los datos de la API oficial de Steam
                top_games[i]=fnames[fnames['item_id'] == top_games[i]].head(1)['item_name'].iloc[0]
        return{'Puesto 1':top_games[0],'Puesto 2':top_games[1],'Puesto 3':top_games[2]} # retornamos los nombres obtenidos
    else:
        return {f'El año indicado no se encuentra en la base de datos: ':anio} # en el caso de que el año ingresado no se encuentre en el Dataset

# Define la ruta para la función UsersNotRecommend
@app.get('/UsersNotRecommend/{anio}')
async def UsersNotRecommend(anio:int):
    '''
    Esta funcion toma como parametro el año, un valor del tipo int, 
    y devuelve el top 3 de juegos menos recomendados por usuarios para el año ingresado.
    '''
    if anio in lanio: # consultamos si el valor ingresado se encuentra dentro del Dataset
        dfa = reviews[(reviews['posted'] == anio) & (reviews['recommend'] == False) & (reviews['sentiment_analysis'] ==0)].copy() # Filtramos el DF mediante el año ingresado, el juego NO es recomendado y el sentimiento es negativo (igual a 0)
        dfa['sentiment_analysis']=1 # insertamos 1 en todas las filas
        dfa = dfa.groupby('item_id')['sentiment_analysis'].sum().reset_index() #agrupamos por id de juego y sumamos el sentimiento
        dfa['item_id'] = dfa['item_id'].astype(int) # convertimos a entero la columna
        dfa = dfa.sort_values('sentiment_analysis', ascending=False) # ordenamos el DF mediante el sentimiento
        top_games = dfa.head(3)['item_id'].to_list() #obtenemos el top 3 id de juegos con mayor sentimiento negativo
        for i,g in enumerate(top_games): #recorremos la lista de juegos menos recomendados
            if g in lid: # para el caso de que el id este en el Dataset normal, obtenemos el nombre del Dataset normal
                top_games[i]=gnames[gnames['item_id'] == top_games[i]].head(1)['title'].iloc[0]
            else: # para aquellos id que no se encontraban en el Dataset, sacamos el nombre de los datos de la API oficial de Steam
                top_games[i]=fnames[fnames['item_id'] == top_games[i]].head(1)['item_name'].iloc[0]
        if len(top_games)<2: # hubo ocaciones en las que se obtenia solo 1 valor por lo que intentar recorrer salia error
            return{'Puesto 1':top_games[0],'Puesto 2':'','Puesto 3':''}
        elif len(top_games)<3:# hubo ocaciones en las que se obtenia solo 2 valores por lo que intentar recorrer salia erro
            return{'Puesto 1':top_games[0],'Puesto 2':top_games[1],'Puesto 3':''}
        else:
            return{'Puesto 1':top_games[0],'Puesto 2':top_games[1],'Puesto 3':top_games[2]} # se retorna la lista de juegos menos recomendados
    else:
        return {f'El año indicado no se encuentra en la base de datos: ':anio} # en el caso de que el año ingresado no se encuentre en el Dataset

# Define la ruta para la función sentiment_analysis
@app.get('/sentiment_analysis/{anio}')
async def sentiment_analysis(anio:int):
    '''
    Esta funcion toma como parametro el año, un valor del tipo int, 
    y del año ingresado devuelve la cantidad de registros de reseñas de usuarios, evaluados con un análisis de sentimiento.
    '''
    if anio in lanio: # consultamos si el valor ingresado se encuentra dentro del Dataset
        dfs = pd.merge(reviews[['item_id','sentiment_analysis']],gnames[['item_id','release_date']],on='item_id',how='inner') #obtenemos el DF con el sentimiento y el año de lanzamiento
        dfs = dfs[dfs['release_date']==anio] # filtramos el DF por el año
        dfs = dfs[['sentiment_analysis']] # obtenemos solo la columna de interes
        dfs = dfs.value_counts().reset_index() # obtenemos la cantidad de elementos y recuperamos la columna ya que con este metodo se agrupa en el indice
        dfs = dfs.sort_values('sentiment_analysis', ascending=True) # ordenamos la columna sentimientos
        dfs = dfs['count'].to_list() # convertimos la columna a lista
        return{'Negative':dfs[0],'Neutral':dfs[1],'Positive':dfs[2]} # retornamos los valores obtenidos
    else:
        return {f'El año indicado no se encuentra en la base de datos: ':anio} # en el caso de que el año ingresado no se encuentre en el Dataset

# Define la ruta para la función
@app.get('/recomendacion_juego/{idg}')
async def recomendacion_juego(idg:int):
    '''
    Esta funcion toma como parametro el identificador de un Juego de la plataforma Steam, un valor del tipo int, 
    y devuelve un top 5 de juegos recomendados (similares).
    '''
    if (idg in lid) or (idg in lfid): #consultamos si el id se encuentra en el Dataset
        gx=pd.DataFrame(games.loc[idg]) obtenemos el DF del juego ingresado
        gx=pd.pivot_table(gx,columns=['item_id', '2D', 'ACTION', 'ADVENTURE', 'ANIME', 'ARCADE',
       'ATMOSPHERIC', 'CASUAL', 'CLASSIC', 'CO-OP', 'COMEDY', 'CUTE',
       'DESIGN & ILLUSTRATION', 'DIFFICULT', 'EARLY ACCESS', 'EXPLORATION',
       'FPS', 'FAMILY FRIENDLY', 'FANTASY', 'FEMALE PROTAGONIST',
       'FIRST-PERSON', 'FREE TO PLAY', 'FUNNY', 'GORE', 'GREAT SOUNDTRACK',
       'HIDDEN OBJECT', 'HORROR', 'INDIE', 'LOCAL CO-OP', 'LOCAL MULTIPLAYER',
       'MASSIVELY MULTIPLAYER', 'MOVIE', 'MULTIPLAYER', 'ONLINE CO-OP',
       'OPEN WORLD', 'PIXEL GRAPHICS', 'PLATFORMER', 'POINT & CLICK', 'PUZZLE',
       'RPG', 'RPGMAKER', 'RACING', 'RETRO', 'ROGUE-LIKE', 'SANDBOX', 'SCI-FI',
       "SHOOT 'EM UP", 'SHOOTER', 'SIMULATION', 'SINGLEPLAYER', 'SPACE',
       'SPORTS', 'STORY RICH', 'STRATEGY', 'SURVIVAL', 'TACTICAL',
       'THIRD PERSON', 'TURN-BASED', 'UTILITIES', 'VIOLENT', 'VISUAL NOVEL',
       'ZOMBIES']) # invertimos filas a columnas del DF del juego inngresado
        gx.drop(columns=['item_id'], inplace=True) # eliminamos la columna id
        xgames=games[games['item_id']!=idg].copy() # eliminamos el juego ingresado del DF de juegos 
        xgames=xgames.reset_index() # reseteamos indice para tener las filas correlativas
        xgames.drop(columns=['index'],inplace=True) # eliminamos el indice anterior
        ygames=xgames.copy() # hacemos una copia del df obtenido
        xgames.drop(columns=['item_id'],inplace=True) # eliminamos la columna id para que no nos afecte al realizar la similitud
        matriz = cosine_similarity(gx,xgames) # obtenemos la matriz de similitud del coseno
        matrix = pd.DataFrame(matriz) #convertimos la matriz en DF
        matriz=matriz[0] #obtenemos la serie de valores que nos interesa (puntajes de similitud)
        reco=[] # para ingestar la lista de ubicaciones
        for i in range(5): #repetimos 5 veces
            imax=np.argmax(matriz) # del array obtenemos la ubicacion del mayor valor
            reco.append(imax) # ingestamos la lsita con la ubicacion del mayor valor
            matriz[imax]=0 # reemplazamos el mayor valor con 0
        top_games = [] #para obtener lista de recomendados
        for i in reco: #recorremos la lista de recomendados
            top_games.append(ygames.iloc[i]['item_id']) #de la copia que hicimos donde aun esta el id lo obtenemos mediante la ubicacion
        for i,g in enumerate(top_games): # recorremos la lista de id recomendados
            if g in lid: # para el caso de que el id este en el Dataset normal, obtenemos el nombre del Dataset normal
                top_games[i]=gnames[gnames['item_id'] == top_games[i]]['title'].iloc[0]
            else: #para aquellos id que no se encontraban en el Dataset, sacamos el nombre de los datos de la API oficial de Steam
                top_games[i]=fnames[fnames['item_id'] == top_games[i]]['item_name'].iloc[0]
        return {"juegos recomendados":
                 [{"Puesto 1":top_games[0]},
                  {"Puesto 2":top_games[1]},
                  {"Puesto 3":top_games[2]},
                  {"Puesto 4":top_games[3]},
                  {"Puesto 5":top_games[4]}]} # retornamos la lista de recomendados mediante el indice de la lista creada
    else:
        return {"id de juego no se encuentra en la base de datos ":idg} # en el caso de que el id no se encuentre en el dataset