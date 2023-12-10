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

st.set_page_config(layout="wide")

 
# Set your OpenAI API key
openai.api_key = api_key

def fetch_top_news(selected_categories):
 
    # Create a connection string
    conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'
 
    # Create a connection and a cursor
    with pymssql.connect(server, username, password, database) as conn:
        with conn.cursor(as_dict=True) as cursor:
            top_news = []
            for category in selected_categories:
                # Fetch top 3 news for each selected category
                cursor.execute(
                    f"SELECT TOP 3 title, link, published, summary, source, category, image_link FROM all_news WHERE category = '{category}' AND summary IS NOT NULL AND published_datetime IS NOT NULL ORDER BY published_datetime DESC"
                )
                top_news.extend(cursor.fetchall())
 
    return pd.DataFrame(top_news)
 
# Function to fetch user preferences from SQL server
def fetch_user_preferences(logged_username):
    # Create a connection string
    conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'
 
    # Create a connection and a cursor
    with pymssql.connect(server, username, password, database) as conn:
        with conn.cursor() as cursor:
            # Fetch user preferences from the user_details table
            cursor.execute(
                f"SELECT preferences FROM user_details WHERE username = '{logged_username}'"
            )
            preferences_str = cursor.fetchone()[0]
 
    return preferences_str.split(',') if preferences_str else []
 
# Function to authenticate a user
def authenticate_user(login_username, login_password):
    # Create a connection string
    conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'
 
    # Create a connection and a cursor
    with pymssql.connect(server, username, password, database) as conn:
        with conn.cursor() as cursor:
            # Fetch the user record from the user_details table
            cursor.execute(
                f"SELECT * FROM user_details WHERE username = '{login_username}' AND password = '{login_password}'"
            )
            user_data = cursor.fetchone()
 
    return user_data is not None
 
# Function to register a new user
def register_user(register_username, register_password, register_preferences):
    # Create a connection string
    conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'
 
    # Create a connection and a cursor
    with pymssql.connect(server, username, password, database) as conn:
        with conn.cursor() as cursor:
            # Insert a new user record into the user_details table
            cursor.execute(
                "INSERT INTO user_details (username, password, preferences) VALUES (%s, %s, %s)",
                (register_username, register_password, ','.join(register_preferences))
            )
            conn.commit()


def text_to_speech(text, lang='en', slow=False):
    tts = gTTS(text=text, lang=lang, slow=slow)
    return tts

def scrape_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
 
    # Extract relevant details from the webpage
    # Customize this part based on the structure of the webpage you are scraping
    title = soup.title.text.strip() if soup.title else "Title not available."
    meta_content_tags = soup.find_all('meta', {'content': True})
    meta_content = [tag['content'] for tag in meta_content_tags]
    return {'title': title, 'content': meta_content}
 
def get_questions(context):
    prompt = (
        "On the below information, Just identify what is the important information related to news."
        " It is related to some news but the below information contains some useless information also in some HTML tags."
        " Don't give me any useless links or images. Just give me the summary and I don't want to have any other information."
        f"\n\nText: {context}\n\nSummary:"
    )
 
    response = openai.Completion.create(
        engine="text-davinci-003",  # Use the appropriate engine
        prompt=prompt,
        max_tokens=100,
    )
 
    questions = response['choices'][0]['text'].strip()
 
    return questions


if 'search_query' not in st.session_state:
    st.session_state.search_query = ""



def handle_speech_to_text():
    text = speech_to_text(language='en', use_container_width=False, just_once=True, key='STT')

    # Store the latest received text in the session state
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
        st.write("Did you mean this", st.session_state.search_query)
        # st.rerun()

with c3:
    # Button to trigger news retrieval
    st.write("\n")
    st.write("\n")
    if st.button("Get News"):
        st.write(f"Processing input: {search_query}")
        google_news = GNews()
        google_news.period = '1d'
        boston_news = google_news.get_news(search_query)
        sorted_boston_news = sorted(boston_news, key=lambda x: x['published date'], reverse=True)
    
        # Display details for the first 5 results in tile format
        for i, result in enumerate(sorted_boston_news[:1]):
            scraped_data = scrape_url(result['url'])
            st.session_state.summary = get_questions(scraped_data['content'])
            if scraped_data['title'] != "Title not available." and scraped_data['title'] != " Access to this page has been denied" and scraped_data['content'] and summary != "The given text does not provide any useful information. It appears to be HTML tags related to website design.":
                # Display details in tiles
                st.subheader(f"Result {i + 1}")
            
                col1, col2 = st.columns(2)
    
                with col1:
                    st.write(f"**Title:** {result['title']}")
                    st.write(f"**Description:** {result['description']}")
                    st.write(f"**Published Date:** {result['published date']}")
                    st.write(f"**Publisher:** {result['publisher']['title']}")
                    st.write(f"**URL:** {result['url']}")
            
                with col2:
                    # Scrape the content of the URL
                    # st.subheader("Scraped Content")
                    # st.write(f"**Title:** {scraped_data['title']}")
                    # st.write(f"**Content:** {scraped_data['content']}")
    
                    # Call get_questions function
                    #summary = get_questions(scraped_data['content'])
                    st.subheader("GPT Summarized")
                    st.write(f"**Summary:** {summary}")


    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Radio button for selecting login or registration
    auth_option = st.radio("Choose an option:", ["Login", "Register"])
 
    if auth_option == "Login":
        # Login section
        st.subheader('Login')
        login_username = st.text_input('Username')
        login_password = st.text_input('Password', type='password')
        login_button = st.button('Login')
 
        if login_button:
            if not login_username or not login_password:
                st.error('Please provide both username and password for login.')
            else:
                if authenticate_user(login_username, login_password):
                    st.session_state.user = login_username
                    st.success(f"Successfully logged in as {login_username}.")
                else:
                    st.error('Invalid username or password.')
    
    elif auth_option == "Register":
    # Registration section
        st.session_state.user = None
        conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'
        st.subheader('Registration')
        register_username = st.text_input('Registration Username')
        register_password = st.text_input('Registration Password', type='password')
        with pymssql.connect(server, username, password, database) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT DISTINCT category FROM all_news")
                categories = [row[0] for row in cursor.fetchall()]
        register_preferences = st.multiselect('Preferences', categories)
        register_button = st.button('Register')

        if register_button:
            if not register_username or not register_password:
                st.error('Please provide both username and password for registration.')
            else:
                register_user(register_username, register_password, register_preferences)
                st.success(f"Successfully registered as {register_username}. Please log in.")

    if st.session_state.user:
        # User is logged in, fetch user preferences
        user_preferences = fetch_user_preferences(st.session_state.user)

        # Fetch and display top news for each user preference
        for category in user_preferences:
            st.subheader(f'Top 3 News in {category}')
            top_news_df = fetch_top_news([category])

            for _, news in top_news_df.iterrows():
                st.write(f"**Title:** {news['title']}")
                st.write(f"**Link:** {news['link']}")
                st.write(f"**Published:** {news['published']}")
                st.write(f"**Summary:** {news['summary']}")
                source_prefix = news['source'].split('_')[0]
                st.write(f"**Source:** {source_prefix}")
                if news['image_link']:
                    st.image(f"{news['image_link']}", caption='Your Image Caption', use_column_width=True)
                st.write("---")

col1, col2, col3, col4, col5 = st.columns(5)

text1 = """ Rising Demand For Specialized HAZMAT Training
To achieve greenhouse gas emission goals, the rail industry is currently embarking on a transformative pursuit of alternative energy sources for railway
transportation. But the increase in lithium-ion battery and hydrogen railway vehicles underscores the need for specialized hazardous materials (HAZMAT) response training to ensure a 
safe and sustainable transportation future. The ARTC, located at the largest transportation testing and training facility in the world, is poised to utilize best practices from other 
modes of surface transportation and apply them for the railway industry through direct emergency response expertise and hands-on training to local HAZMAT responders.
Lessons From Past Accidents
Lithium-ion batteries have been used in commercial products for more than 25 years. 
They are used to power many modern devices we are all familiar with, such as power tools, laptops, appliances and automobiles. Due to their widespread use, 
we have a significant amount of information about incidents. More than 25,000 incidents of fire or overheating in lithium-ion batteries have occurred over a 
recent five-year period, according to the U.S. Consumer Product Safety Commission. Additionally, the United States Coast Guard (USCG) issued a Marine Safety Alert 
in March 2022 regarding the transportation of
lithium-ion batteries. Just like marine transportation, the freight railways will not only need to be capable of responding to emergencies involving 
railway vehicles powered by lithium-ion batteries, but also the increasing transportation of consumer goods that utilize the batteries, as well. """

with col1:
   st.header("A cat")
   st.image("https://static.streamlit.io/examples/cat.jpg")
   st.write(text1)

with col2:
   st.header("A dog")
   st.image("https://static.streamlit.io/examples/cat.jpg")
   st.write(text1)

with col3:
   st.header("An owl")
   st.image("https://static.streamlit.io/examples/cat.jpg")
   st.write(text1)

with col4:
   st.header("An owl")
   st.image("https://static01.nyt.com/images/2023/12/06/multimedia/06israel-hamas-flbk/06israel-hamas-flbk-mediumSquareAt3X.jpg")
   st.write(text1)

with col5:
   st.header("An owl")
   st.image("https://static.streamlit.io/examples/cat.jpg")
   st.write(text1)


if 'summary' not in st.session_state:
    st.session_state.summary = None

if st.session_state.summary:
    st.subheader("GPT Summarized")
    st.write(f"**Summary:** {st.session_state.summary}")

    # Option to save the summary as a text file
    if st.button("Save Summary"):
        print("Saved Summary:",st.session_state.summary)
        with open("summary.txt", "w") as file:
            file.write(summary)
        st.success("Summary saved as 'summary.txt'")

    # Option to convert summary to speech and download
    if st.button("Convert to Speech"):
        print("Speak Summary:",st.session_state.summary)
        tts = text_to_speech(text=text1, lang='en', slow=False)
        # tts = text_to_speech(text=st.session_state.summary, lang='en', slow=False)
        tts.save("summary_speech.mp3")
        st.audio("summary_speech.mp3", format='audio/mp3')
        with open("summary_speech.mp3", "rb") as file:
            btn = st.download_button(
                label="Download Speech",
                data=file,
                file_name="summary_speech.mp3",
                mime="audio/mp3"
            )

