import streamlit as st

import streamlit as st
import pandas as pd
import pymssql

# Azure SQL Server details
server = 'bdia.database.windows.net'
database = 'assignment1'
admin_username = 'dhawal'
admin_password = 'Bigdata@2023'


# Function to fetch top news from SQL server based on selected categories
def fetch_top_news(selected_categories):

    # Create a connection string
    #conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'

    # Create a connection and a cursor
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
        with conn.cursor(as_dict=True) as cursor:
            top_news = []
            for category in selected_categories:
                # Fetch top 3 news for each selected category
                cursor.execute(
                    f"SELECT TOP 3 id, title, link, published, summary, source, category, image_link FROM all_news WHERE category = '{category}' AND summary IS NOT NULL AND published_datetime IS NOT NULL ORDER BY published_datetime DESC"
                )
                top_news.extend(cursor.fetchall())

    return pd.DataFrame(top_news)

# Function to fetch user preferences from SQL server
def fetch_user_preferences(logged_username):
    # Create a connection string
    #conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'

    # Create a connection and a cursor
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
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
    #conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'

    # Create a connection and a cursor
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
        with conn.cursor() as cursor:
            # Fetch the user record from the user_details table
            cursor.execute(
                f"SELECT * FROM user_details WHERE username = '{login_username}' AND password = '{login_password}'"
            )
            user_data = cursor.fetchone()

    return user_data is not None

def get_user_id(login_username):
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT id FROM user_details WHERE username = '{login_username}'"
            )
            user_data = cursor.fetchone()
    return user_data[0] if user_data else None

def add_to_playlist(playlist_name, news_id):
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO playlists (playlist_name, News_id) OUTPUT INSERTED.id VALUES (%s, %s)",
                           (playlist_name, news_id))
            inserted_id = cursor.fetchone()[0]
            conn.commit()
    return inserted_id
     
def create_user_playlist(user_id, playlist_id, news_title):
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
        with conn.cursor() as cursor:  
            cursor.execute("INSERT INTO user_playlist (user_id, playlist_id) VALUES (%s, %s)",
                           (user_id, playlist_id))
            conn.commit()
    return f"Added to Playlist - {news_title}"

# Function to register a new user
def register_user(register_username, register_password, register_preferences):
    # Create a connection string
    #conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'

    # Create a connection and a cursor
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
        with conn.cursor() as cursor:
            # Insert a new user record into the user_details table
            cursor.execute(
                "INSERT INTO user_details (username, password, preferences) VALUES (%s, %s, %s)",
                (register_username, register_password, ','.join(register_preferences))
            )
            conn.commit()

def button_click(new_playlist_name, news_id_new):
    playlist_id = add_to_playlist(new_playlist_name, news_id_new)
    user_id_new = get_user_id(st.session_state.user)
    done_or_not_done = create_user_playlist(user_id_new, playlist_id)
    #st.write(done_or_not_done)


def fetch_playlists_for_user(username):
    user_id = get_user_id(username)
    playlists_query = f"""
    SELECT DISTINCT playlist_name FROM playlists WHERE id IN (
        SELECT playlist_id FROM user_playlist WHERE user_id = {user_id}
    )
    """
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
        with conn.cursor(as_dict=True) as cursor:  # Ensure that as_dict=True is properly set
            cursor.execute(playlists_query)
            playlist_names = cursor.fetchall()
    # Extract just the playlist names into a list
    return [row['playlist_name'] for row in playlist_names]

def fetch_playlist_ids_for_name(username, playlist_name):
    user_id = get_user_id(username)
    # Fetch IDs for all playlists with the given name associated with the user
    playlist_ids_query = f"""
    SELECT id FROM playlists WHERE playlist_name = '{playlist_name}' AND id IN (
        SELECT playlist_id FROM user_playlist WHERE user_id = {user_id}
    )
    """
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
        with conn.cursor() as cursor:
            cursor.execute(playlist_ids_query)
            playlist_ids = cursor.fetchall()
    # Extract just the playlist IDs into a list
    return [row[0] for row in playlist_ids]  # Use index 0 to access the id from the tuple

def insert_into_existing_playlist(playlist_id, news_id):
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
        with conn.cursor() as cursor:
            # Insert a new user record into the user_details table
            cursor.execute(
                "INSERT INTO playlists (playlist_name, News_id) OUTPUT INSERTED.id VALUES (%s, %s)",
                (playlist_id, news_id)
            )
            inserted_id = cursor.fetchone()[0]
            conn.commit()
    return inserted_id

def add_user_playlist_association(user_id, playlist_id):
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
        with conn.cursor() as cursor:
            # Insert a new user record into the user_details table
            cursor.execute(
                "INSERT INTO user_playlist (user_id, playlist_id) VALUES (%s, %s)",
                (user_id, playlist_id)
            ) 
            conn.commit()
    return True

# Streamlit app
# def main():
#     st.title('Add to Playlist')

#     # Check if the user is logged in
#     if 'user' not in st.session_state:
#         st.session_state.user = None
#         st.write("Please login or register by goin to home page")
#         st.stop()

#         # Registration section
#         st.session_state.user = None 
#         conn_str = f'SERVER={server};DATABASE={database};USER={username};PASSWORD={password}'
#         st.subheader('Registration')
#         register_username = st.text_input('Registration Username')
#         register_password = st.text_input('Registration Password', type='password')
#         with pymssql.connect(server, username, password, database) as conn:
#             with conn.cursor() as cursor:
#                 cursor.execute("SELECT DISTINCT category FROM all_news")
#                 categories = [row[0] for row in cursor.fetchall()]
#         register_preferences = st.multiselect('Preferences', categories)
#         register_button = st.button('Register')

#         if register_button:
#             if not register_username or not register_password:
#                 st.error('Please provide both username and password for registration.')
#             else:
#                 register_user(register_username, register_password, register_preferences)
#                 st.success(f"Successfully registered as {register_username}. Please log in.")

#     if st.session_state.user:
#         user_preferences = fetch_user_preferences(st.session_state.user)
#         selected_news = []
#         new_playlist_name = st.text_input("Enter the name of the new playlist:")

#         # Display news with checkboxes
#         for category in user_preferences:
#             st.subheader(f'Top 3 News in {category}')
#             top_news_df = fetch_top_news([category])

#             for _, news in top_news_df.iterrows():
#                 # Create a unique key for each checkbox
#                 checkbox_key = f"select_{news['id']}"
#                 if checkbox_key not in st.session_state:
#                     st.session_state[checkbox_key] = False

#                 # Display checkbox for each news item
#                 if st.checkbox(news['title'], key=checkbox_key):
#                     selected_news.append(news)

#         # Button to display selected news
#         if st.button("Add news to playlist"):
#             st.subheader("News added")
#             for news in selected_news:
#                 playlist_id = add_to_playlist(new_playlist_name, news['id'])
#                 user_id_new = get_user_id(st.session_state.user)
#                 done_or_not_done = create_user_playlist(user_id_new, playlist_id, news['title'])
#                 st.write(done_or_not_done)

def main():
    st.title('Add to Playlist')

    # Check if the user is logged in
    if 'user' not in st.session_state:
        st.session_state.user = None
        st.write("Please login or register by goin to home page")
        st.stop()

    if st.session_state.user:
        user_preferences = fetch_user_preferences(st.session_state.user)
        selected_news = []
        user_id_new = get_user_id(st.session_state.user)
        # Display news with checkboxes
        for category in user_preferences:
            st.subheader(f'Top 3 News in {category}')
            top_news_df = fetch_top_news([category])

            for _, news in top_news_df.iterrows():
                # Create a unique key for each checkbox
                checkbox_key = f"select_{news['id']}"
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = False

                # Display checkbox for each news item
                if st.checkbox(news['title'], key=checkbox_key):
                    selected_news.append(news)
        
        playlist_option = st.radio("Do you want to add to a new playlist or an existing one?",
                               ('New Playlist', 'Existing Playlist'))
        if playlist_option == 'New Playlist':
            new_playlist_name = st.text_input("Enter the name of the new playlist:")
            if st.button("Add news to new playlist"):
                st.subheader("News added")
                for news in selected_news:
                    playlist_id = add_to_playlist(new_playlist_name, news['id'])
                    done_or_not_done = create_user_playlist(user_id_new, playlist_id, news['title'])
                    st.write(done_or_not_done)
        elif playlist_option == 'Existing Playlist':
            existing_playlists = fetch_playlists_for_user(st.session_state.user)
            st.write("Existing Playlists:", existing_playlists)
            selected_playlist_name = st.selectbox("Select a playlist", options=existing_playlists)
            if st.button("Add news to selected playlist"):
                #playlist_ids = fetch_playlist_ids_for_name(st.session_state.user , selected_playlist_name)
                for news in selected_news:
                    inserted_id = insert_into_existing_playlist(selected_playlist_name, news["id"])
                    status = add_user_playlist_association(user_id_new, inserted_id)
                    if status:
                        st.write(f"Added to existing playlist - {news['title']}")
                    else:
                        st.write(f"Not added to existing playlist - {news['title']}")

        # Fetch and display top news for each user preference
if __name__ == '__main__':
    main()
