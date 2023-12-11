from fastapi import FastAPI
import pandas as pd
from dotenv import load_dotenv
import os

# Carga las variables de entorno desde el archivo .env
load_dotenv()

mi_secreto = os.getenv("MI_SECRETO")

app=FastAPI()

games = pd.read_parquet('./Datasets/gamesv5.parquet')
reviews = pd.read_parquet('./Datasets/reviews.parquet')
items = pd.read_parquet('./Datasets/itemsv3.parquet')

generos = list(games.drop(columns=['item_id','release_date']).columns)
gnames = pd.read_csv('./Datasets/gnames.csv')
unames = pd.read_csv('./Datasets/unames.csv')
ids =pd.read_csv('./Datasets/idsnv2.csv')
iid=list(set(items['item_id']))
lanio=list(set(reviews['posted'].to_list()))

@app.get('/')
async def root():
    return {'hello': 'world'}

@app.get('/PlayTimeGenre/{genero}')
async def PlayTimeGenre(genero:str):
  genero=genero.upper()
  if genero in generos:
    lgames = games.loc[games[genero] == 1, ['release_date', 'item_id']]
    lhoras = items.groupby('item_id')['playtime_forever'].sum().reset_index()
    dfplay = pd.merge(lgames, lhoras, on='item_id', how='inner')
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
    dfgames = games[['item_id','release_date',genero]]
    dfgames = dfgames[games[genero]==1]
    dfuserg = pd.merge(dfgames,items,on='item_id',how='inner')
    uhoras = dfuserg.groupby('uid_user')['playtime_forever'].sum().reset_index()
    uhoras = uhoras.sort_values(by='playtime_forever', ascending=False)
    uhoras = uhoras.head(1)
    uhoras = uhoras['uid_user'].iloc[0]
    dfuserg = dfuserg[dfuserg['uid_user']==uhoras]
    dfuserg = dfuserg.groupby('release_date')['playtime_forever'].sum().reset_index()
    dfuserg = dfuserg.sort_values(by='release_date', ascending=False)
    dfuserg = dfuserg[dfuserg['playtime_forever']>0]
    dfuserg = dfuserg.astype(int)
    dfuserg.rename(columns={'release_date': 'Año', 'playtime_forever':'Horas'}, inplace=True)
    di = dfuserg.apply(lambda row: row.to_dict(), axis=1).tolist()
    uhoras = unames[unames['uid_user']==uhoras]
    uhoras = uhoras['user_id'].iloc[0]
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
    top_games = dfa.head(3)['item_id'].to_list()
    for i,g in enumerate(top_games):
      if g in iid:
        top_games[i]=gnames[gnames['item_id'] == top_games[i]].head(1)['item_name'].iloc[0]
      else:
        top_games[i]=ids[ids['item_id'] == top_games[i]].head(1)['item_name'].iloc[0]
    return{'Puesto 1':top_games[0],'Puesto 2':top_games[1],'Puesto 3':top_games[2]}
  else:
    return {f'El año indicado no se encuentra en la base de datos: ':anio}

@app.get('/UsersNotRecommend/{anio}')
async def UsersNotRecommend(anio:int):
  if anio in lanio:
    dfa = reviews[(reviews['posted'] == anio) & (reviews['recommend'] == False) & (reviews['sentiment_analysis'] ==0)].copy()
    dfa['sentiment_analysis']=1
    dfa = dfa.groupby('item_id')['sentiment_analysis'].sum().reset_index()
    dfa = dfa.sort_values('sentiment_analysis', ascending=False)
    top_games = dfa.head(3)['item_id'].to_list()
    for i,g in enumerate(top_games):
      if g in iid:
        top_games[i]=gnames[gnames['item_id'] == top_games[i]].head(1)['item_name'].iloc[0]
      else:
        top_games[i]=ids[ids['item_id'] == top_games[i]].head(1)['item_name'].iloc[0]
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
    dfs = pd.merge(reviews[['item_id','sentiment_analysis']],games[['item_id','release_date']].drop_duplicates(),on='item_id',how='inner')
    dfs = dfs[dfs['release_date']==anio]
    dfs = dfs.groupby('sentiment_analysis').size().reset_index(name='count')
    dfs = dfs.sort_values('sentiment_analysis', ascending=True)
    dfs = dfs['count'].to_list()
    return{'Negative':dfs[0],'Neutral':dfs[1],'Positive':dfs[2]}
  else:
    return {f'El año indicado no se encuentra en la base de datos: ':anio}