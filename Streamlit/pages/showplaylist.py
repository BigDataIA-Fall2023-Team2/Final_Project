import streamlit as st

import streamlit as st
import pandas as pd
import pymssql

# Azure SQL Server details
server = 'bdia.database.windows.net'
database = 'assignment1'
admin_username = 'dhawal'
admin_password = 'Bigdata@2023'

def get_user_id(login_username):
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT id FROM user_details WHERE username = '{login_username}'"
            )
            user_data = cursor.fetchone()
    return user_data[0] if user_data else None

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

def fetch_news_for_playlist(playlist_id):
    # Fetch all news articles associated with a playlist ID
    news_query = f"""
    SELECT an.* FROM all_news an
    INNER JOIN playlists p ON an.id = p.News_id
    WHERE p.id = {playlist_id}
    """
    with pymssql.connect(server, admin_username, admin_password, database) as conn:
        with conn.cursor(as_dict=True) as cursor:
            cursor.execute(news_query)
            news_articles = cursor.fetchall()
    return news_articles

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


def display_playlists_and_articles(username):
    playlist_names = fetch_playlists_for_user(username)
    
    if not playlist_names:
        st.write("No playlists available.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Playlists")
        selected_playlist_name = st.selectbox("Select a playlist", options=playlist_names)
    
    with col2:
        st.subheader("Articles")
        if selected_playlist_name:
            playlist_ids = fetch_playlist_ids_for_name(username, selected_playlist_name)
            for playlist_id in playlist_ids:
                news_articles = fetch_news_for_playlist(playlist_id)
                if news_articles:
                    for article in news_articles:
                        st.image(article['image_link'], use_column_width=True)  # Assuming image_link is the 4th column
                        st.write(f"**Title:** {article['Title']}")  # Assuming title is the 2nd column
                        st.write(f"**Summary:** {article['Summary']}")  # Assuming summary is the 3rd column
                        st.markdown(f"[Read More]({article['Link']})", unsafe_allow_html=True)  # Assuming link is the 5th column
                        st.markdown("---")  # Add a separator line
                else:
                    st.write("No articles available for this playlist.")

def main():
    st.title('Show Playlists')

    # Check if the user is logged in
    if 'user' not in st.session_state:
        st.session_state.user = None
        st.write("Please login or register by goin to home page")
        st.stop()

    if st.session_state.user:
        st.write("Show Playlist")
        display_playlists_and_articles(st.session_state.user)


if __name__ == '__main__':
    main()