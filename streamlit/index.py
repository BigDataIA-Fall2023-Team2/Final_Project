import streamlit as st
import requests, pathlib, os
from dotenv import load_dotenv
from request_utils import get_request, post_request
from streamlit_mic_recorder import mic_recorder, speech_to_text
from gtts import gTTS
from io import BytesIO



env_path = pathlib.Path('.') / '.env.streamlit'
load_dotenv(dotenv_path=env_path)

FASTAPI_HOST = os.getenv('FASTAPI_HOST')
def login_page():
    st.title('Login to NewsSphere')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    if st.button('Login'):
        data = {'username': username, 'password': password}
        response, error = post_request(url=FASTAPI_HOST+'/login', data=data, headers=None)
        if error:
            st.error("Invalid credentials")
        elif response.status_code == 200:
            token = response.json()['token']
            st.session_state['token'] = token
            st.session_state['user_preferences'] = response.json()['user_preferences']
            st.session_state['page'] = 'landing' 
            st.rerun()
        else:
            st.error("Something went wrong!!!")
        
    if st.button('New here? Sign up!!'):
        st.session_state['page'] = 'register'
        st.rerun()
       
            
def register_page():
    st.title('Sign Up')
    email = st.text_input('Email')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')
    response, error = get_request(url=FASTAPI_HOST+'/categories')
    
    categories = response.json()['categories']
    preferred_categories = st.multiselect('Preferences', categories, key='preferred_categories')
    
    if st.button('REGISTER', key='reg_button'):
        if not username or not password or not email:
            st.error('Please provide both username and password for registration.')
        else:
            request_body = {
                "email": email,
                "username": username,
                "password": password,
                "preferred_categories": preferred_categories
            }
        response, error = post_request(url=FASTAPI_HOST+'/register', data=request_body)
        if error:
            st.error("Unable to Register")
        elif response.status_code == 201:
            st.session_state['page'] = 'login'
            st.rerun()
        elif response.status_code == 400:
            st.error("Username already exists")
        else:
            st.error("Something went wrong!!!")
          

def landing_page():

    st.set_page_config(layout="wide")
    if 'token' not in st.session_state:
        st.session_state['page'] = 'login' 
        st.rerun()
    st.title('Welcome to NewsSpear')

    c1, c2, c3 = st.columns([2, 1,0.5])
    
    st.session_state['search_query'] = None 
    with c1:
        text_search_query = st.text_input("Whats on your mind!!",value=st.session_state.search_query)
        if text_search_query is not None:
            st.session_state['text_search_query'] = text_search_query

    with c2:
        st.write("\n")
        st.write("\n")
        audio_search_query = speech_to_text(language='en', use_container_width=True, just_once=True, key='STT')
        if audio_search_query is not None:
            st.session_state['audio_search_query'] = audio_search_query
            st.write("Did you mean this: ", st.session_state['audio_search_query'])

    with c3:
        st.write("\n")
        st.write("\n")
        get_news = st.button("Get News")

    if get_news:
        st.write(st.session_state['text_search_query'])
        st.write(st.session_state['audio_search_query'])
        if 'text_search_query' in st.session_state and st.session_state.text_search_query is not None:
            st.session_state['search_query'] = st.session_state['text_search_query']
        elif 'audio_search_query' in st.session_state and st.session_state.audio_search_query is not None:
            st.session_state['search_query'] = st.session_state['audio_search_query']
        else:
            st.error("Please Enter the search query!!")
        auth_token =  "Bearer "+ st.session_state['token']
        headers = {
            "accept": "application/json",
            "Authorization": auth_token,
            "Content-Type": "application/json" 
        }
        search_result, error = get_request(FASTAPI_HOST+'/gnews_search?query='+st.session_state['search_query'],headers=headers,params=None)
        st.write(search_result.json()['summary'])
        tts = gTTS(text=search_result.json()['summary'], lang='en', slow=False)
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        st.audio(mp3_fp, format='audio/mp3')
        st.subheader(f'Based in your search')
        result = search_result.json()['result']
        cols1 = st.columns(5)
        cols2 = st.columns(5)
        cols3 = st.columns(5)
        for i, result in enumerate(result[:5]):
            with cols1[i]:
                st.markdown(f"**[{result['title']}]({result['url']})**")
            with cols2[i]:
                st.write(f"**Description:** {result['description']}")
            with cols3[i]:
                st.write(f"**Published Date:** {result['published date']}")
        
        st.subheader(f'Recommended Suggestion')
        top_news = search_result.json()['recommendation']
        cols1 = st.columns(5)
        cols2 = st.columns(5)
        cols3 = st.columns(5)
        cols4 = st.columns(5)
        merged_summary = ""
        for index, news in enumerate(top_news):
            with cols1[index]:
                st.markdown(f"**[{news[0]}]({news[1]})**")
            with cols2[index]:
                if news[6]:
                    st.image(f"{news[6]}", use_column_width=True)
            with cols3[index]:
                st.write(f"**Summary:** {news[3]}")
            with cols4[index]:
                tts = gTTS(text=news[3], lang='en', slow=False)
                mp3_fp = BytesIO()
                tts.write_to_fp(mp3_fp)
                st.audio(mp3_fp, format='audio/mp3')
            merged_summary = merged_summary + news[3]
            if index == 4:  
                break
            
        
    user_preferences = st.session_state['user_preferences'].split(',')
    auth_token =  "Bearer "+ st.session_state['token']
    headers = {
        "accept": "application/json",
        "Authorization": auth_token,
        "Content-Type": "application/json" 
    }
    data = {'categories': user_preferences}
    response, error = post_request(url=FASTAPI_HOST+'/latest_preferred_news', data=data, headers=headers)
    preferred_news = response.json()['latest_preferred_news']
    if "queue" not in st.session_state:
        st.session_state["queue"] = []
    st.session_state["checkbox_key"] = []
    for category in user_preferences:
        st.subheader(f'Top News in {category}')
        top_news = preferred_news[category]
        cols1 = st.columns(5)
        cols2 = st.columns(5)
        cols3 = st.columns(5)
        cols4 = st.columns(5)
        cols5 = st.columns(5)        
        for index, news in enumerate(top_news):
            with cols1[index]:
                st.markdown(f"**[{news[0]}]({news[1]})**")
            with cols2[index]:
                if news[6]:
                    st.image(f"{news[6]}", use_column_width=True)
            with cols3[index]:
                st.write(f"**Summary:** {news[3]}")
            with cols4[index]:
                tts = gTTS(text=news[3], lang='en', slow=False)
                mp3_fp = BytesIO()
                tts.write_to_fp(mp3_fp)
                st.audio(mp3_fp, format='audio/mp3')
            with cols5[index]:
                if st.button("Add to queue", key=category+"-"+str(index)):
                    st.session_state["queue"].append(category+"-"+str(index))
                if category+"-"+str(index) in st.session_state["queue"]:
                    if st.button("Remove from queue", key="remove"+category+"-"+str(index)):
                        st.session_state["queue"].remove(category+"-"+str(index))
                news_checkbox_key = f"{news[7]}"
                if st.checkbox("Add to Playlist", key=news_checkbox_key):
                    st.session_state["checkbox_key"].append(news_checkbox_key)

            if index == 4:  
                break
        st.write("---")
    play_text = "hello this is your queue"+"\n\n\n\n\n\n\n\n\n\n\n\n\n"
    for i in st.session_state["queue"]:
        j = i.split("-")
        play_text+=preferred_news[j[0]][int(j[1])][3] + "The next article is "
    play_text=play_text[:-20]
    tts = gTTS(text=play_text, lang='en', slow=False)
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    st.audio(mp3_fp, format='audio/mp3')
    c1, c2, c3 = st.columns([2, 1,0.5])
    with c1:
        playlist_name = st.text_input("Enter new playlist name!")
    with c2:
        st.write("\n")
        st.write("\n")
        if st.button("Create Playlist"):
            if st.session_state["checkbox_key"] is None or playlist_name is None:
                st.error("Seelct news to add to playlsit")
            else:
                headers = {
                    "accept": "application/json",
                    "Authorization": auth_token,
                    "Content-Type": "application/json" 
                }
                data = {'playlist_name': playlist_name, 'news_id_list': st.session_state["checkbox_key"]}
                response, error = post_request(url=FASTAPI_HOST+'/create_playlist', data=data, headers=headers)
                if error is None:
                    st.write("Playlist Created")
    with c3:
        st.write("\n")
        st.write("\n")
        if st.button("Show Playlist"):
            st.session_state['page'] = 'playlist'
            st.rerun()
    
    headers = {
        "accept": "application/json",
        "Authorization": auth_token,
        "Content-Type": "application/json" 
    }
    search_result, error = get_request(FASTAPI_HOST+'/get_user_playlists' ,headers=headers,params=None)
    if error is None:
        playlists = search_result.json()['playlists']
        c1, c2, c3 = st.columns([2, 1,0.5])
        with c1:
            playlist = st.selectbox('Update Existing Playlist', playlists, key='playlist')
        with c2:
            st.write("\n")
            st.write("\n")
            if st.button("Update Playlist"):
                if st.session_state["checkbox_key"] is None or playlist is None:
                    st.error("Select news to add to playlsit")
                else:
                    headers = {
                        "accept": "application/json",
                        "Authorization": auth_token,
                        "Content-Type": "application/json" 
                    }
                    data = {'playlist_name': playlist, 'news_id_list': st.session_state["checkbox_key"]}
                    response, error = post_request(url=FASTAPI_HOST+'/update_playlist', data=data, headers=headers)
                    if error is None:
                        st.write("Playlist Updated")
    if st.button('LogOut'):
        del st.session_state['token']
        st.session_state['page'] = 'login' 
        st.rerun()  
        
def playlist_page():
    st.set_page_config(layout="wide")
    if 'token' not in st.session_state:
        st.session_state['page'] = 'login' 
        st.rerun()
    st.title('Your Playlist')
    auth_token =  "Bearer "+ st.session_state['token']
    headers = {
                "accept": "application/json",
                "Authorization": auth_token,
                "Content-Type": "application/json" 
            }
    response, error = get_request(url=FASTAPI_HOST+'/get_user_playlists', headers=headers)
    playlists = response.json()['playlists']
    for key, value in playlists.items():
        headers = {
                "accept": "application/json",
                "Authorization": auth_token,
                "Content-Type": "application/json" 
            }
        data = { "news_id_list": value }
        response, error = post_request(url=FASTAPI_HOST+'/get_news_articles', data=data, headers=headers)
        st.subheader(key)
        top_news1 = response.json()['news_result']
        merged_summary = ""

        for k in range(0, len(top_news1), 5):
            top_news = top_news1[k:k+5]
            cols1 = st.columns(5)
            cols2 = st.columns(5)
            cols3 = st.columns(5)
            cols4 = st.columns(5)
            for index, news in enumerate(top_news):
                with cols1[index]:
                    st.markdown(f"**[{news[0]}]({news[1]})**")
                with cols2[index]:
                    if news[6]:
                        st.image(f"{news[6]}", use_column_width=True)
                with cols3[index]:
                    st.write(f"**Summary:** {news[3]}")
                with cols4[index]:
                    tts = gTTS(text=news[3], lang='en', slow=False)
                    mp3_fp = BytesIO()
                    tts.write_to_fp(mp3_fp)
                    st.audio(mp3_fp, format='audio/mp3')
                merged_summary = merged_summary + news[3]
                if index == 4:  
                    break
        tts = gTTS(text=merged_summary, lang='en', slow=False)
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        st.audio(mp3_fp, format='audio/mp3')
        if st.button("Delete Playlist", key=key):
            headers = {
                "accept": "application/json",
                "Authorization": auth_token,
                "Content-Type": "application/json" 
            }
            data = {'playlist_name': key}
            response, error = post_request(url=FASTAPI_HOST+'/delete_playlist', data=data, headers=headers)
            if error is None:
                st.write("Playlist Deleted")
                st.rerun()
        
    st.write("---")
    
    c1, c2, c3 = st.columns([2, 1,0.5])
    with c1:
        if st.button('Return to Home'):
            st.session_state['page'] = 'landing' 
            st.rerun() 
        
    with c2:
        if st.button('LogOut'):
            del st.session_state['token']
            st.session_state['page'] = 'login' 
            st.rerun()  
        
        

    

def main():
    # st.session_state['page'] = 'landing'    
    if 'page' not in st.session_state:
        st.session_state['page'] = 'login'    
    if st.session_state['page'] == 'login':
        login_page()
    elif st.session_state['page'] == 'register':
        register_page()
    elif st.session_state['page'] == 'landing':
        landing_page()
    elif st.session_state['page'] == 'playlist':
        playlist_page()
    # elif st.session_state['page'] == 'chat':
    #     chat_page()
    else:
        st.error('Unknown page: %s' % st.session_state['page'])

if __name__ == '__main__':
    main()