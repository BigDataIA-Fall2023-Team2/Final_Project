from fastapi import FastAPI, HTTPException, status, Body, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from db_utils import load_sql_db_config, get_sql_db_connection, close_sql_db_connection, execute_sql_query, query_piencone_vectors
from auth_utils import hash_password, create_jwt_token, decode_jwt_token
from openai_utils import ask_openai_model, build_prompt, generate_embeddings
from pydantic import BaseModel
from dotenv import load_dotenv
from gnews import GNews

import pathlib, os

env_path = pathlib.Path('.') / '.env.fastapi'
load_dotenv(dotenv_path=env_path)

# Define the global variable
DB_CONFIG = load_sql_db_config()
# SECRET_KEY = os.getenv("PRIVATE_KEY")

app = FastAPI()

class RegisterRequestModel(BaseModel):
    username: str
    email: str
    password: str
    preferred_categories: list
    
class LoginRequestModel(BaseModel):
    username: str
    password: str
    
class NewsRequestModel(BaseModel):
    categories: list
    
class CreatePlaylistRequestModel(BaseModel):
    playlist_name: str
    news_id_list: list

class DeletePlaylistRequestModel(BaseModel):
    playlist_name: str

    
class GetNewsRequestModel(BaseModel):
    news_id_list: tuple

    
security = HTTPBearer()

def get_current_user(authorization: HTTPAuthorizationCredentials = Depends(security)):
    schema = DB_CONFIG['schema']
    token = authorization.credentials
    conn = get_sql_db_connection(DB_CONFIG)
    try:
        payload = decode_jwt_token(token)
        username = payload.get("username")
        sql_fetch_user = f"SELECT username, email, userid FROM [{schema}].[Users] WHERE username = %s"
        user = execute_sql_query(conn, sql_fetch_user, (username,), fetch="ONE")
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
    
@app.post("/login", status_code=status.HTTP_200_OK)
async def login(data: LoginRequestModel = Body(...)):
    conn = get_sql_db_connection(DB_CONFIG)
    schema = DB_CONFIG['schema']
    sql_fetch_password = f"SELECT passwordhash FROM [{schema}].[Users] WHERE username = %s"
    stored_password_hash = execute_sql_query(conn, sql_fetch_password, (data.username,), fetch="ONE")
    provided_password_hash = hash_password(data.password)
    if stored_password_hash is None or provided_password_hash != stored_password_hash[0]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sql_get_user_preferences = f"SELECT userpreferences FROM [{schema}].[Users] WHERE username = %s"
    user_preferences_category = execute_sql_query(conn, sql_get_user_preferences, (data.username,), fetch="ALL")
    print(user_preferences_category)
    close_sql_db_connection(conn=conn)
    token, expiration= create_jwt_token({"username":data.username})
    return {
        "token" : token,
        "validity" : expiration,
        "user_preferences" : user_preferences_category[0][0]
    }
    
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(data: RegisterRequestModel = Body(...)):
    conn = get_sql_db_connection(DB_CONFIG)
    schema = DB_CONFIG['schema']
    sql_check_username = f"SELECT 1 FROM [{schema}].[Users] WHERE username = %s"
    username_check_result = execute_sql_query(conn, sql_check_username, (data.username,), fetch="ONE")
    if username_check_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    hashed_password = hash_password(data.password)
    sql_insert = (
        f"INSERT INTO [{schema}].[Users] "
        f"(Username, PasswordHash, Email, userpreferences) VALUES (%s, %s, %s, %s)"
    )
    execute_sql_query(conn, sql_insert, (data.username, hashed_password, data.email, ','.join(data.preferred_categories)))
    close_sql_db_connection(conn=conn)
    return {"success": True}

@app.get("/categories", status_code=status.HTTP_200_OK)
async def get_categories():
    conn = get_sql_db_connection(DB_CONFIG)
    schema = DB_CONFIG['schema']
    sql_get_categories = f"SELECT distinct category FROM [{schema}].[all_news]"
    categories = execute_sql_query(conn, sql_get_categories, None, fetch="ALL")
    close_sql_db_connection(conn=conn)
    news_categories = []
    for i in categories:
        news_categories.append(i[0])
    return {
        "categories" : news_categories
    }
    
@app.get("/gnews_search", status_code=status.HTTP_200_OK)
async def get_gnews(query : str):
    google_news = GNews( max_results=5)
    google_news.period = '1d'
    search_result = google_news.get_news(query)
    for i in range(0,5):
        article = google_news.get_full_article(search_result[i]['url'])
        if article is not None:
            search_result[i]['text']=article.text
        else:
            search_result[i]['text']=""
    search_result = sorted(search_result, key=lambda x: len(x['text']), reverse=True)
    content_for_chatgpt = "title 1 : " + search_result[0]['title'] + "\n" + "description: " + search_result[0]['description'] + "\n" + "text: " + search_result[0]['text'] + "\n"
    content_for_chatgpt += content_for_chatgpt + "title 2 : " + search_result[1]['title'] + "\n" + "description: " + search_result[1]['description'] + "\n" + "text: " + search_result[1]['text'] + "\n"
    content_for_chatgpt_chuck = [content_for_chatgpt[i:i+3000] for i in range(0, len(content_for_chatgpt), 3000)]
    prompt = build_prompt(context=content_for_chatgpt[:3000], user_query=query)
    # summary = ""
    # for chunk in content_for_chatgpt_chuck:
    #     prompt = build_prompt(chunk, query)
    #     summary += ask_openai_model(prompt)
    # prompt = build_prompt(summary, query)
    merged_summary = ask_openai_model(prompt)
    search_result = sorted(search_result, key=lambda x: x['published date'], reverse=True)

    
    query_embeddings = generate_embeddings(query)
    query_vector = [float(value) for value in query_embeddings]
    query_response = query_piencone_vectors(query_vector, 5)
    print(query_response["matches"])
    news_id=[]
    for i in query_response["matches"]:
        news_id.append(i['id'])
    conn = get_sql_db_connection(DB_CONFIG)
    schema = DB_CONFIG['schema']
    a = '%s'
    for i in range(len(news_id)-1):
        a+=',%s'
    sql_get_news = f"SELECT title, link, published, summary, source, category, image_link, id FROM [{schema}].[all_news] WHERE id in ({a}) AND summary IS NOT NULL AND published_datetime IS NOT NULL ORDER BY published_datetime DESC"
    news_result = execute_sql_query(conn, sql_get_news, tuple(news_id), fetch="ALL")
    close_sql_db_connection(conn=conn)

    return{
        "summary" : merged_summary,
        "result" : search_result,
        "recommendation" : news_result
    }
    
    
@app.post("/latest_preferred_news", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
async def latest_preferred_news(data: NewsRequestModel = Body(...)):
    conn = get_sql_db_connection(DB_CONFIG)
    schema = DB_CONFIG['schema']
    all_news={}
    for category in data.categories:
        sql_get_category_news = f"SELECT TOP 5 title, link, published, summary, source, category, image_link, id FROM [{schema}].[all_news] WHERE category = '{category}' AND summary IS NOT NULL AND published_datetime IS NOT NULL ORDER BY published_datetime DESC"
        category_news_result = execute_sql_query(conn, sql_get_category_news, category, fetch="ALL")
        all_news[category] = category_news_result
    close_sql_db_connection(conn=conn)

    return {
        "latest_preferred_news" : all_news
    }


@app.post("/create_playlist", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
async def create_playlist(data: CreatePlaylistRequestModel = Body(...), user = Depends(get_current_user)):
    print(data.news_id_list)
    conn = get_sql_db_connection(DB_CONFIG)
    schema = DB_CONFIG['schema']
    sql_insert_playlist = (
        f"INSERT INTO [{schema}].[user_playlists] "
        f"(user_id, playlist_name) VALUES (%s, %s)"
    )
    execute_sql_query(conn, sql_insert_playlist, (user[2], data.playlist_name))
    sql_fetch_playlistid = f"select playlist_id from [{schema}].[user_playlists] where user_id = %s and playlist_name = %s"
    playlist_id = execute_sql_query(conn, sql_fetch_playlistid, (user[2], data.playlist_name), fetch="ONE")
    print(playlist_id)
    for newsid in data.news_id_list:
        sql_insert_news = (
            f"INSERT INTO [{schema}].[playlist_news] "
            f"(playlist_id, news_id) VALUES (%s, %s)"
        )
        execute_sql_query(conn, sql_insert_news, (playlist_id, newsid))
    close_sql_db_connection(conn=conn)

    return {
        "success"
    }
    
@app.get("/get_user_playlists", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
async def get_user_playlists(user = Depends(get_current_user)):
    conn = get_sql_db_connection(DB_CONFIG)
    schema = DB_CONFIG['schema']
    sql_fetch_playlist = f"select playlist_id, playlist_name FROM [{schema}].[user_playlists] where user_id = %s"
    user_playlist = execute_sql_query(conn, sql_fetch_playlist, (user[2],), fetch="ALL")
    playlists ={}
    for i in user_playlist:
        sql_fetch_news_playlist = f"select news_id from [{schema}].[playlist_news] where playlist_id = %s"
        playlist_news = execute_sql_query(conn, sql_fetch_news_playlist, (i[0]), fetch="ALL")
        p_n=[]
        for j in playlist_news:
            p_n.append(j[0])
        playlists[i[1]] = p_n
    close_sql_db_connection(conn=conn)
    print(playlists)
    return{
        "playlists" : playlists
    }
    
@app.post("/get_news_articles", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
async def get_news_article(data : GetNewsRequestModel = Body(...)):
    conn = get_sql_db_connection(DB_CONFIG)
    schema = DB_CONFIG['schema']
    a = '%s'
    for i in range(len(data.news_id_list)-1):
        a+=',%s'
    print(a)
    sql_get_news = f"SELECT title, link, published, summary, source, category, image_link, id FROM [{schema}].[all_news] WHERE id in ({a}) AND summary IS NOT NULL AND published_datetime IS NOT NULL ORDER BY published_datetime DESC"
    news_result = execute_sql_query(conn, sql_get_news, data.news_id_list, fetch="ALL")
    close_sql_db_connection(conn=conn)
    return {
            "news_result": news_result
    }
    

@app.post("/update_playlist", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
async def update_playlist(data: CreatePlaylistRequestModel = Body(...), user = Depends(get_current_user)):
    print(data.news_id_list)
    conn = get_sql_db_connection(DB_CONFIG)
    schema = DB_CONFIG['schema']
    print(user[2])
    print(data.playlist_name)
    sql_fetch_playlistid = f"select playlist_id from [{schema}].[user_playlists] where user_id = %s and playlist_name = %s"
    playlist_id = execute_sql_query(conn, sql_fetch_playlistid, (user[2], data.playlist_name), fetch="ONE")
    print(playlist_id)
    for newsid in data.news_id_list:
        sql_insert_news = (
            f"INSERT INTO [{schema}].[playlist_news] "
            f"(playlist_id, news_id) VALUES (%s, %s)"
        )
        execute_sql_query(conn, sql_insert_news, (playlist_id, newsid))
    close_sql_db_connection(conn=conn)

    return {
        "success"
    }
    
@app.post("/delete_playlist", status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_user)])
async def delete_playlist(data: DeletePlaylistRequestModel = Body(...), user = Depends(get_current_user)):
    conn = get_sql_db_connection(DB_CONFIG)
    schema = DB_CONFIG['schema']

    sql_fetch_playlistid = f"select playlist_id from [{schema}].[user_playlists] where user_id = %s and playlist_name = %s"
    playlist_id = execute_sql_query(conn, sql_fetch_playlistid, (user[2], data.playlist_name), fetch="ONE")
    print(playlist_id)
    sql_delete_news = (
        f"DELETE FROM [{schema}].[playlist_news] "
        f" WHERE playlist_id = %s"
    )
    execute_sql_query(conn, sql_delete_news, (playlist_id))    
    sql_delete_playlist = (
        f"DELETE FROM [{schema}].[user_playlists] "
        f" WHERE playlist_id = %s"
    )
    execute_sql_query(conn, sql_delete_playlist, (playlist_id))
    close_sql_db_connection(conn=conn)

    return {
        "success"
    }
    
    