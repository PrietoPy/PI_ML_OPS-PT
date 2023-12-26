from fastapi import FastAPI
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
from sklearn.metrics.pairwise import cosine_similarity

# Carga las variables de entorno desde el archivo .env
load_dotenv()

mi_secreto = os.getenv("MI_SECRETO")

app = FastAPI(swagger_ui_parameters={"syntaxHighlight.theme": "obsidian"})

games = pd.read_parquet('./Datasets/gamesoh.parquet')
reviews = pd.read_parquet('./Datasets/reviews.parquet')
items = pd.read_parquet('./Datasets/itemso.parquet')

generos = list(games.drop(columns=['item_id']).columns)
gnames = pd.read_parquet('./Datasets/games.parquet')
fnames = pd.read_parquet('./Datasets/fnames.parquet')
unames = pd.read_parquet('./Datasets/unames.parquet')
items['item_id'] = items['item_id'].astype(int)
items['user_id'] = items['user_id'].astype(int)
unames['user_id'] = unames['user_id'].astype(int)
reviews.dropna(subset='item_id', inplace =True)
reviews['item_id'] = reviews['item_id'].astype(int)

lid=list(set(gnames['item_id']))
lfid=list(set(fnames['item_id']))
lanio=list(set(reviews['posted'].to_list()))

@app.get('/')
async def root():
    return {'hello': 'world'}

@app.get('/PlayTimeGenre/{genero}')
async def PlayTimeGenre(genero:str):
    genero=genero.upper()
    if genero in generos:
        lgames = games.loc[games[genero] == 1, ['item_id']]
        lhoras = items.groupby('item_id')['playtime_forever'].sum().reset_index()
        dfplay = pd.merge(lgames, lhoras, on='item_id', how='inner')
        dfplay = pd.merge(dfplay, gnames, on='item_id', how='inner')
        df_horas = dfplay.groupby('release_date')['playtime_forever'].sum().reset_index()
        df_horas_ordenado = df_horas.sort_values(by='playtime_forever', ascending=False)
        resultado=df_horas_ordenado.head(1)
        prin = "Año de lanzamiento con más horas jugadas para Género " + genero
        anio = int(resultado['release_date'].iloc[0])
        return {prin : anio}
    else:
        return {"El Genero indicado no se encuentra en la base de datos":genero}

@app.get('/UserForGenre/{genero}')
async def UserForGenre(genero:str):
    genero=genero.upper()
    if genero in generos:
        dfgames = games[['item_id',genero]]
        dfgames = dfgames[games[genero]==1]
        dfuserg = pd.merge(dfgames,items,on='item_id',how='inner')
        uhoras = dfuserg.groupby('user_id')['playtime_forever'].sum().reset_index()
        uhoras = uhoras.sort_values(by='playtime_forever', ascending=False)
        uhoras = uhoras.head(1)
        uhoras = uhoras['user_id'].iloc[0]
        dfuserg = dfuserg[dfuserg['user_id']==uhoras]
        dfuserg = pd.merge(dfuserg,gnames,on='item_id',how='inner')
        dfuserg = dfuserg.groupby('release_date')['playtime_forever'].sum().reset_index()
        dfuserg = dfuserg.sort_values(by='release_date', ascending=False)
        dfuserg = dfuserg[dfuserg['playtime_forever']>0]
        dfuserg['playtime_forever'] = dfuserg['playtime_forever'].astype(int)
        dfuserg = dfuserg[['playtime_forever', 'release_date']]
        dfuserg.rename(columns={'release_date': 'Año', 'playtime_forever':'Horas'}, inplace=True)
        #di = dfuserg.apply(lambda row: row.to_dict(), axis=1).tolist()
        di=dfuserg.to_dict(orient='records')
        uhoras = unames[unames['user_id']==uhoras]
        uhoras = uhoras['user_name'].iloc[0]
        prin="Usuario con más horas jugadas para Género " + genero
        return {prin:uhoras,"Horas Jugadas":di}
    else:
        return {"El Genero indicado no se encuentra en la base de datos ":genero}

@app.get('/UsersRecommend/{anio}')
async def UsersRecommend(anio:int):
    if anio in lanio:
        dfa = reviews[(reviews['posted'] == anio) & (reviews['recommend'] == True) & (reviews['sentiment_analysis'] >0)].copy()
        dfa = dfa.groupby('item_id')['sentiment_analysis'].sum().reset_index()
        dfa = dfa.sort_values('sentiment_analysis', ascending=False)
        dfa['item_id'] = dfa['item_id'].astype(int)
        top_games = dfa.head(3)['item_id'].to_list()
        for i,g in enumerate(top_games):
            if g in lid:
                top_games[i]=gnames[gnames['item_id'] == top_games[i]].head(1)['title'].iloc[0]
            else:
                top_games[i]=fnames[fnames['item_id'] == top_games[i]].head(1)['item_name'].iloc[0]
        return{'Puesto 1':top_games[0],'Puesto 2':top_games[1],'Puesto 3':top_games[2]}
    else:
        return {f'El año indicado no se encuentra en la base de datos: ':anio}

@app.get('/UsersNotRecommend/{anio}')
async def UsersNotRecommend(anio:int):
    if anio in lanio:
        dfa = reviews[(reviews['posted'] == anio) & (reviews['recommend'] == False) & (reviews['sentiment_analysis'] ==0)].copy()
        dfa['sentiment_analysis']=1
        dfa = dfa.groupby('item_id')['sentiment_analysis'].sum().reset_index()
        dfa['item_id'] = dfa['item_id'].astype(int)
        dfa = dfa.sort_values('sentiment_analysis', ascending=False)
        top_games = dfa.head(3)['item_id'].to_list()
        for i,g in enumerate(top_games):
            if g in lid:
                top_games[i]=gnames[gnames['item_id'] == top_games[i]].head(1)['title'].iloc[0]
            else:
                top_games[i]=fnames[fnames['item_id'] == top_games[i]].head(1)['item_name'].iloc[0]
        if len(top_games)<2:
            return{'Puesto 1':top_games[0],'Puesto 2':'','Puesto 3':''}
        elif len(top_games)<3:
            return{'Puesto 1':top_games[0],'Puesto 2':top_games[1],'Puesto 3':''}
        else:
            return{'Puesto 1':top_games[0],'Puesto 2':top_games[1],'Puesto 3':top_games[2]}
    else:
        return {f'El año indicado no se encuentra en la base de datos: ':anio}

@app.get('/sentiment_analysis/{anio}')
async def sentiment_analysis(anio:int):
    if anio in lanio:
        dfs = pd.merge(reviews[['item_id','sentiment_analysis']],gnames[['item_id','release_date']],on='item_id',how='inner')
        dfs = dfs[dfs['release_date']==anio]
        dfs = dfs.groupby('sentiment_analysis').size()
        dfs = dfs.reset_index(name='count')
        dfs = dfs.sort_values('sentiment_analysis', ascending=True)
        dfs = dfs['count'].to_list()
        return{'Negative':dfs[0],'Neutral':dfs[1],'Positive':dfs[2]}
    else:
        return {f'El año indicado no se encuentra en la base de datos: ':anio}

@app.get('/recomendacion_juego/{idg}')
async def recomendacion_juego(idg:int):
    if (idg in lid) or (idg in lfid):
        gx=pd.DataFrame(games.loc[idg])
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
       'ZOMBIES'])
        gx.drop(columns=['item_id'], inplace=True)
        xgames=games[games['item_id']!=idg].copy()
        xgames=xgames.reset_index()
        xgames.drop(columns=['index'],inplace=True)
        ygames=xgames.copy()
        xgames.drop(columns=['item_id'],inplace=True)
        matriz = cosine_similarity(gx,xgames)
        matrix = pd.DataFrame(matriz)
        matriz=matriz[0]
        reco=[]
        for i in range(5):
            imax=np.argmax(matriz)
            reco.append(imax)
            matriz[imax]=0
        top_games = []
        for i in reco:
            top_games.append(ygames.iloc[i]['item_id'])
        for i,g in enumerate(top_games):
            if g in lid:
                top_games[i]=gnames[gnames['item_id'] == top_games[i]]['title'].iloc[0]
            else:
                top_games[i]=fnames[fnames['item_id'] == top_games[i]]['item_name'].iloc[0]
        return {"juegos recomendados":
                 [{"Puesto 1":top_games[0]},
                  {"Puesto 2":top_games[1]},
                  {"Puesto 3":top_games[2]},
                  {"Puesto 4":top_games[3]},
                  {"Puesto 5":top_games[4]}]}
    else:
        return {"id de juego no se encuentra en la base de datos ":idg}