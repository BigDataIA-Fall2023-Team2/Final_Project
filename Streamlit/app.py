import streamlit as st
import openai
from gnews import GNews
import requests
from bs4 import BeautifulSoup
from gtts import gTTS
import os
import tempfile
from streamlit_mic_recorder import mic_recorder, speech_to_text
import requests, pathlib, os
from dotenv import load_dotenv
import pandas as pd
import pymssql



env_path = pathlib.Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

server = os.getenv('server')
database = os.getenv('database')
username = os.getenv('username')
password = os.getenv('password')
api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = api_key

conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'



def perform_authentication(login_username, login_password):
    conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'
    with pymssql.connect(server, username, password, database) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM user_details WHERE username = '{login_username}' AND password = '{login_password}'"
            )
            user_data = cursor.fetchone()
 
    return user_data is not None

def authenticate_user():
    st.title('LOGIN')
    login_username = st.text_input('Username')
    login_password = st.text_input('Password', type='password')
    login_button = st.button('Login')
    if login_button:
        if not login_username or not login_password:
            st.error('Please provide both username and password for login.')
        else:
            user_authenticated = perform_authentication(login_username, login_password)
            if user_authenticated:
                st.session_state['user'] = login_username
                st.session_state['token'] = 'user_token_here'  # Set your user's token here
                st.success(f"Successfully logged in as {login_username}.")
                st.session_state['page'] = 'landing'  
                st.experimental_rerun()
            else:
                st.error('Invalid username or password.')
    
    if st.button('New here? Sign up!!'):
        st.session_state['page'] = 'register'
        st.experimental_rerun()


def register_user(register_username, register_password, register_preferences):
    try:
        conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'
        with pymssql.connect(server, username, password, database) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO user_details (username, password, preferences) VALUES (%s, %s, %s)",
                    (register_username, register_password, ','.join(register_preferences))
                )
                conn.commit()
        return True
    except pymssql.Error as db_err:
        st.error("Could not register user. The username may already exist or another error occurred.")
        print("Database error:", db_err)
        return False

def registration_section():
    st.subheader('Registration')
    register_username = st.text_input('Registration Username', key='reg_username')
    register_password = st.text_input('Registration Password', type='password', key='reg_password')
    categories = fetch_categories()  
    register_preferences = st.multiselect('Preferences', categories, key='reg_preferences')
    
    if st.button('Register', key='reg_button'):
        if not register_username or not register_password:
            st.error('Please provide both username and password for registration.')
        else:
            success = register_user(register_username, register_password, register_preferences)
            if success:
                st.success(f"Successfully registered as {register_username}. Please log in.")

                st.session_state['page'] = 'login' 
    if st.button('Return to Home'):
        return_to_home()

def fetch_categories():
    conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'
    with pymssql.connect(server, username, password, database) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT category FROM all_news")
            return [row[0] for row in cursor.fetchall()]

def fetch_top_news(selected_categories): 
    conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'
    with pymssql.connect(server, username, password, database) as conn:
        with conn.cursor(as_dict=True) as cursor:
            top_news = []
            for category in selected_categories:
                # Fetch top 5 news for each selected category
                cursor.execute(
                    f"SELECT TOP 5 title, link, published, summary, source, category, image_link FROM all_news WHERE category = '{category}' AND summary IS NOT NULL AND published_datetime IS NOT NULL ORDER BY published_datetime DESC"
                )
                top_news.extend(cursor.fetchall())
 
    return pd.DataFrame(top_news)
 
# Fetch user preferences from SQL server for logged person
def fetch_user_preferences(logged_username): 
    conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'
    with pymssql.connect(server, username, password, database) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT preferences FROM user_details WHERE username = '{logged_username}'"
            )
            preferences_str = cursor.fetchone()[0]
 
    return preferences_str.split(',') if preferences_str else []

def get_questions(context):
    prompt = (
        "On the below information, Just identify what is the important information related to news."
        " It is related to some news but the below information contains some useless information also in some HTML tags."
        " Don't give me any useless links or images. Just give me the summary and I don't want to have any other information."
        f"\n\nText: {context}\n\nSummary:"
    )
    response = openai.Completion.create(
        engine="text-davinci-003", 
        prompt=prompt,
        max_tokens=100,
    )
    questions = response['choices'][0]['text'].strip()
    return questions

def scrape_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.text.strip() if soup.title else "Title not available."
    meta_content_tags = soup.find_all('meta', {'content': True})
    meta_content = [tag['content'] for tag in meta_content_tags]
    return {'title': title, 'content': meta_content}

def fetch_and_sort_news(search_query):
    # Fetch news using GNews and sort them
    st.write(f"Processing input: {search_query}")
    google_news = GNews()
    google_news.period = '1d'
    boston_news = google_news.get_news(search_query)
    return sorted(boston_news, key=lambda x: x['published date'], reverse=True)

def display_news_in_columns(news_items):
    cols = st.columns(5)

    for i, result in enumerate(news_items[:5]):
        scraped_data = scrape_url(result['url'])
        st.session_state.summary = get_questions(scraped_data['content'])

        if scraped_data['title'] != "Title not available." and \
           scraped_data['title'] != " Access to this page has been denied" and \
           scraped_data['content'] and \
           st.session_state.summary != "The given text does not provide any useful information. It appears to be HTML tags related to website design.":

            with cols[i]:
                st.subheader(f"Result {i + 1}")
                st.write(f"**Title:** {result['title']}")
                st.write(f"**Description:** {result['description']}")
                # st.write(f"**Published Date:** {result['published date']}")
                # st.write(f"**Publisher:** {result['publisher']['title']}")
                st.write(f"**URL:** {result['url']}")
                st.subheader("GPT Summarized")
                st.write(f"**Summary:** {st.session_state.summary}") 

def return_to_home():
    st.session_state['page'] = 'login'  
    st.experimental_rerun()


if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

if 'summary' not in st.session_state:
    st.session_state.summary = ""

def landing_page():
    st.set_page_config(layout="wide")
    st.title('Welcome to the Landing Page')
    def handle_speech_to_text():
        text = speech_to_text(language='en', use_container_width=False, just_once=True, key='STT')

        if text:
            st.session_state.search_query = text

    # Layout with columns
    c1, c2, c3 = st.columns([2, 1,0.5])

    with c1:
        search_query = st.text_input("Enter a search query for news:",value=st.session_state.search_query ,key='')

    with c2:
        st.write("\n")
        st.write("\n")
        handle_speech_to_text()
        if st.session_state.search_query:
            st.write("Did you mean this: ", st.session_state.search_query)
            # st.rerun()

    with c3:
        # Button to trigger news retrieval
        st.write("\n")
        st.write("\n")
        get_news = st.button("Get News")

    if get_news:
        sorted_boston_news = fetch_and_sort_news(search_query)
        display_news_in_columns(sorted_boston_news)

    user_preferences = fetch_user_preferences(st.session_state.user)

    # Fetch and display top news for each user preference
    for category in user_preferences:
        st.subheader(f'Top 5 News in {category}')
        top_news_df = fetch_top_news([category])

        # Create 5 columns for 5 news items
        cols = st.columns(5)

        for index, news in enumerate(top_news_df.iterrows()):
            _, news = news  # unpack the tuple returned by iterrows()
            with cols[index]:
                st.markdown(f"**[{news['title']}]({news['link']})**")
                # st.write(f"**Link:** {news['link']}")
                # st.write(f"**Published:** {news['published']}")
                if news['image_link']:
                    st.image(f"{news['image_link']}", use_column_width=True)
                st.write(f"**Summary:** {news['summary']}")
                # source_prefix = news['source'].split('_')[0]
                # st.write(f"**Source:** {source_prefix}")

            if index == 4:  # Break after filling 5 columns
                break
        st.write("---")















    if st.button('Return to Home'):
        return_to_home()

def main():
    if 'page' not in st.session_state:
        st.session_state['page'] = 'login'  # Set the default page to 'login'

    if st.session_state['page'] == 'login':
        authenticate_user()
    elif st.session_state['page'] == 'register':
        registration_section()
    elif st.session_state['page'] == 'landing':
        landing_page()
    else:
        st.error(f'Unknown page: {st.session_state["page"]}')

if __name__ == "__main__":
    main()
