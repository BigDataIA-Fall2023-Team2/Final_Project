# Final_Project

### AI-Enhanced NewsFlow: A Personalized News Digest Platform

The project is a news application that allows user to read and add latest news into their playlist. It also allows users to listen to the news. The project gets data from google news, bbc, nytimes etc and displays it to user based on preferences. The user can listen them by adding it to queue if the user doesnt want to store in database. The user can also add the articles to playlist to access them later. All our news articles are summarized to save users time.

## Project Resources

Google collab notebook: https://colab.research.google.com/drive/1-u0u6Ib5aPGprUhVwmp_Yj_Ie-FEaNgi?usp=sharing

Google codelab: [https://codelabs-preview.appspot.com/?file_id=1Ih2p01AQZP2_p7pM-CWIECQJQams-EnPEwdwYNav838#0](https://codelabs-preview.appspot.com/?file_id=1tJ3JqcmwDDNBPkk97BcidnZiWHzzjm5QJaESpIeejAw#0)

App link: http://34.118.251.190:8501/

Airflow: http://34.118.251.190:8080/home

FAST API: http://34.118.251.190:8000/docs

### Tech Stack
Python | Streamlit | OPENAI | Azure SQL | Pinecone | Docker | Google Cloud | Fast API | Airflow

### Architecture diagram ###


### Project Flow

The user first registers in our application. The user will then give preferences on what sections are found interesting such as America, Business, Enviornment etc. After registration, the user logs in and the user will be able to see top 5 news in his selected section. The user can read the article or listen to them by playing it. Apart from that, the user can add the prefered articles into a queue so that all of them are played one after the other. The queue will not be saved to database. The user can create a new playlist where the user can add the required articles into the playlist for acessing it later as playlists are stored in database. Accordingly, the user can modify or delete playlists.

The user login implementation using the concept of JWT. Apart from that, there is an Airflow written that is scheduled to run every 3 minutes and will store all the articles into the database. 'Add only new/changed articles' feature has beeen added into the airflow.


### Repository Structure


### Contributions

| Name                            | Contribution                                                                            |  
| ------------------------------- | ----------------------------------------------------------------------------------------|
| Shardul Chavan                  | Text to speech Integration, Streamlit layout, Speech to Text Integration, Playlists     | 
| Chinmay Gandi                   | Airflow, Pinecone Integration, Playlists , Azure Data Storage                           | 
| Dhawal Negi                     | JWT, Dockerization, GCP Deployment, FAST API                                            |                                                  

### Additional Notes
WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK. 

