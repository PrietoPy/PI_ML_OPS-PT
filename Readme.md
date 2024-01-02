# Proyecto Individual MLops - Sistema de Recomendación de Steam

<img src="src/Steam.png" alt="Steam" width="200" height="120"><img src="src/FastAPI.png" alt="FastAPI" width="220" height="120"><img src="src/Render.png" alt="Render" width="220" height="150">

## Descripción

Este proyecto consiste en la implementación de una API utilizando el framework FastAPI para ofrecer servicios mediante la plataforma de despliegue Render. Ofrece funcionalidades con datos de videojuegos de la plataforma Steam sobre análisis de sentimiento de reseñas de usuarios y sistemas de recomendación.

Video presentación del proyecto y funciones: [link](https://drive.google.com/file/d/1BIPP_FYSZLwllkK2CkZSULbMETgV_OXw/view?usp=drive_link).

### Características Principales

1. **Transformaciones y Feature Engineering:**
   
   - Lectura y manipulación de datos.
   
   - Eliminación de columnas no necesarias para consultas o modelos.
   
   - Transformación de generos a Formato Binario.
   
   - Análisis de sentimiento a las reseñas de usuarios.
   
   - Encontramos Juegos Similares mediante la similitud del coseno.
   
   - Diccionario de datos (MVP):
     
     - `gamesoh.parquet`: contiene 62 columnas: 'item_id' del tipo entero corresponde al identificador unico de los juegos, 61 columnas categoricas (géneros) en binario.
     
     | Columna   | Tipo  | Descripción                  |
     | --------- | ----- | ---------------------------- |
     | item_id   | int32 | Identificador unico de juego |
     | 2D        | int8  | Género                       |
     | ACTION    | int8  | Género                       |
     | ADENTURE  | int8  | Género                       |
     | ANIME     | int8  | Género                       |
     | ...       | int8  | Género                       |
     | VIOLENT   | int8  | Género                       |
     | VISUAL N. | int8  | Género                       |
     | ZOMBIES   | int8  | Género                       |
     
     - `reviews.parquet`: contiene 5 columnas.
     
     | Columna            | Tipo  | Descripción                                                |
     | ------------------ | ----- | ---------------------------------------------------------- |
     | posted             | int32 | Año de publicación de reseña                               |
     | item_id            | int32 | Identificador unico de juego                               |
     | recommend          | bool  | Indicador de recomendacion                                 |
     | user_id            | int32 | Identificador unico de usuario                             |
     | sentiment_analysis | int8  | Analisis de sentimientos 0=Negativo, 1=Neutral, 2=Positivo |
     
     - `itemso.parquet`: contiene 3 columnas.
     
     | Columna          | Tipo  | Descripción                              |
     | ---------------- | ----- | ---------------------------------------- |
     | item_id          | int32 | Identificador unico de juego             |
     | playtime_forever | int32 | Cantidad de Horas acumuladas por usuario |
     | user_id          | int32 | Identificador unico de usuario           |
     
     - `games.parquet`: contiene 3 columnas, con los nombres de los juegos.
     
     | Columna      | Tipo   | Descripción                    |
     | ------------ | ------ | ------------------------------ |
     | title        | object | Identificador unico de juego   |
     | release_date | int32  | Fecha de lanzamiento del Juego |
     | item_id      | int32  | Identificador unico de juego   |
     
     - `fnames.parquet`: contiene 2 columnas, con los nombres de los juegos obtenidos de la API oficial de Steam
     
     | Columna   | Tipo   | Descripción                  |
     | --------- | ------ | ---------------------------- |
     | item_id   | int32  | Identificador unico de juego |
     | item_name | object | Nombre del juego             |
     
     - `unames.parquet`: contiene 2 columnas, con los nombres de los usuarios.
     
     | Columna   | Tipo   | Descripción                    |
     | --------- | ------ | ------------------------------ |
     | user_id   | int32  | Identificador unico de usuario |
     | user_name | object | Nombre del usuario             |

2. **Desarrollo de la API:**
   
   - Implementación de endpoints para realizar consultas específicas.
   - Consultas disponibles:
     - `PlayTimeGenre`: Toma como parametro un valor del tipo String y devuelve el año con más horas jugadas para un género específico.
     - `UserForGenre`: Toma como parametro un valor del tipo String y devuelve el usuario que acumula más horas jugadas para un género y una lista de la acumulación de horas jugadas por año.
     - `UsersRecommend`: Toma como parametro un valor del tipo int y devuelve el top 3 de juegos MÁS recomendados por usuarios para un año dado.
     - `UsersNotRecommend`: Toma como parametro un valor del tipo int y devuelve el top 3 de juegos MENOS recomendados por usuarios para un año dado.
     - `sentiment_analysis`: Toma como parametro un valor del tipo int y devuelve la cantidad de registros de reseñas de usuarios categorizados con un análisis de sentimiento para un año dado.

3. **Deployment:**
   
   - Utilización de Render para desplegar la API y hacerla accesible desde la web.

4. **Análisis Exploratorio de Datos (EDA):**
   
   - Explorando el sentimiento de las reseñas de los usuarios encontramos este top generos aceptados por la comunidad:
   
   <img src="src/EDA1.PNG">
- Explorando la cantidad de comentarios positivos por año, vemos que hay un pico en el año 2014 y un considerable descenso para el siguente año:
  
  <img src="src/EDA2.PNG">

- Explorando el tiempo de juego por genero nos encontramos un ligero cambio en el top. 
  
  <img src="src/EDA3.PNG">
  
  - Podemos concluir que el genero Action junto con Multiplayer y CO-OP, encontramos buenas reseñas de usuarios sumados a la popularidad en horas de juego, por lo que si consideramos el desarrollo de un juego con estos géneros, podriamos encontrarnos con una gran audiencia y aceptación, no obstante debido a la caida de reseñas en el ultimo año 2015, tendriamos que realizar el mismo analisis con datos actualizados para confirmar los generos más demandados.

- Como resultado tendiramos el siguiente top de juegos que se encuentran dentro de los generos Action, Multiplayer y CO-OP.
  
  <img src="src/EDA4.PNG">
5. **Modelo de Aprendizaje Automático:**
   
   - Implementación de al menos uno de los sistemas de recomendación propuestos:
     - `recomendacion_juego`: Toma como parametro un valor del tipo int y devuelve un top 5 de juegos recomendados (similares).

### Uso

1. **Uso de la API:**
   
   Puede utilizar cualquiera de las endpoints definidas mas arriba, así también el modelo de recomendación.
   
   - Ejemplo de consulta `PlayTimeGenre`:
     
     ```python
     import requests  
     response = requests.get('https://pi-ml-ops-pt.onrender.com/PlayTimeGenre/action') 
     print(response.json())
     ```
     
     Ejemplo de resultado:
     `{'Año de lanzamiento con más horas jugadas para Género ACTION': 2012}`

2. **Uso de Documentacion FastAPI**
   
   - Link del deploy: [Render](https://pi-ml-ops-pt.onrender.com/docs)
   
   - Ejemplo de consulta `PlayTimeGenre`:
     
     - Haga click en la funcionalidad deseada, en este caso `PlayTimeGenre`.
       
       <img src="src/FastAPIu.PNG">
     
     - Haga click `Try it out` y luego ingrese el genero deseado.
       
       <img src="src/FastAPId.PNG">
     
     - Haga click en `Execute`.
       
       <img src="src/FastAPIt.PNG">
     
     - El resultado de la consulta estara en el recuadro debajo de `Response body`.
       
       <img src="src/FastAPIc.PNG">

### Soporte

Para obtener ayuda o realizar preguntas, puedes abrir un problema mediante la plataforma [Slido](https://app.sli.do/event/91QKwt3an5ty6VyKnxUQYp).

o al correo electronico [gmail](angelprieto92@gmail.com).

## ¡Gracias por usar nuestra API! ¡Esperamos que sea de utilidad! 🚀
