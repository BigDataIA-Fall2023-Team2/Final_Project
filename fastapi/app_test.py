import pytest
from fastapi.testclient import TestClient
from app import app

@pytest.fixture(scope="module")
def test_client():
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="module")
def user_token(test_client):
    # Login to get the token
    login_data = {"username": "chavan", "password": "chavan"}
    response = test_client.post("/login", json=login_data)
    token = response.json()["token"]
    assert response.status_code == 200
    assert token is not None
    return token

#################### TEST CASE 1: Succesful Registration ###################
def test_register_user(test_client):
    data = {
        "username": "chavan",
        "email": "chavan@example.com",
        "password": "chavan",
        "preferred_categories": ["America"]
    }
    response = test_client.post("/register", json=data)
    assert response.status_code == 201
    assert response.json() == {"success": True}


#################### TEST CASE 2: Succesful Login ###################

def test_login_user(test_client):
    data = {"username": "chavan", "password": "chavan"}
    response = test_client.post("/login", json=data)
    assert response.status_code == 200
    assert "token" in response.json()

#################### TEST CASE 3: Get distinct categories ###################
    
def test_get_categories(test_client):
    response = test_client.get("/categories")
    assert response.status_code == 200
    assert "categories" in response.json()


#################### TEST CASE 4: Get Latest News  ###################

def test_get_latest_news (test_client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    data = {"categories": ["Business"]}
    response = test_client.post("/latest_preferred_news", json=data, headers=headers)
    assert response.status_code == 200
    assert "latest_preferred_news" in response.json()


#################### TEST CASE 5: Create user playlist  ###################

def test_create_playlist(test_client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    data = {
        "playlist_name": "My New Playlist",
        "news_id_list": [3403, 3404]  # Replace with actual news IDs
    }
    response = test_client.post("/create_playlist", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json() == ['success'] 


#################### TEST CASE 6 : Get User Playlist ###################

def test_get_user_playlist (test_client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    response = test_client.get("/get_user_playlists", headers=headers)
    print("Response JSON:", "playlists" in response.json())  # This will print the response
    assert response.status_code == 200
    assert "playlists" in response.json()


#################### TEST CASE 7: Get News articles based on playlist  ###################

def test_get_news_articles(test_client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    data = {"news_id_list": [3315, 3316, 3317]}  
    response = test_client.post("/get_news_articles", json=data, headers=headers)
    assert response.status_code == 200
    assert "news_result" in response.json()
    news_results = response.json()["news_result"]
    for article in news_results:
        assert article


######################## TEST CASE 8 : UPDATE PLAYLIST ####################################
    
def test_update_playlist(test_client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    data = {
        "playlist_name": "My New Playlist",
        "news_id_list": [3378, 3379]  
    }
    response = test_client.post("/update_playlist", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json() == ['success'] 


######################## TEST CASE 9 : DELETE PLAYLIST ####################################


def test_delete_playlist(test_client, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}
    data = {
        "playlist_name": "My New Playlist1",  # Name of the playlist to delete
    }
    response = test_client.post("/delete_playlist", json=data, headers=headers)
    assert response.status_code == 200
    assert response.json() == ['success'] 



