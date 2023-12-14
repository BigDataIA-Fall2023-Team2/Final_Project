from datetime import datetime, timedelta,  timezone
from airflow import DAG
from airflow.operators.python import PythonOperator
import pandas as pd
import pymssql
import requests
from bs4 import BeautifulSoup
from airflow.utils.dates import days_ago
#from openai import OpenAI
import pandas as pd
import pinecone
import openai
from airflow.models import Variable

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'retries': 1,
}


pine_cone_api = Variable.get("pinecone_api")
pine_cone_environment = Variable.get("environment")
pinecone.init(api_key=pine_cone_api, environment=pine_cone_environment)
server = Variable.get("server")
database = Variable.get("database")
username = Variable.get("username")
password = Variable.get("password")
openai.api_key = Variable.get("openai_api_key")


def get_last_present_record():
    conn = pymssql.connect(server=server, database=database, user=username, password=password)
    cursor = conn.cursor(as_dict=True)
    cursor.execute("select top 1 Id from all_news order by Id desc")
    record = cursor.fetchone()
    conn.close()
    if record:
        return record['Id']
    else:
        return 0 
     

def generate_embeddings(text):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"  
    )
    return response["data"][0]["embedding"]

def record_exists(title, summary):
    with pymssql.connect(server, username, password, database) as conn:
        with conn.cursor(as_dict=True) as cursor:
            cursor.execute(
                "SELECT COUNT(*) as count FROM all_news WHERE Title = %s AND Summary = %s",
                (title, summary)
            )
            result = cursor.fetchone()
            return result['count'] > 0

def extract_date_time(published):
    if published is None or not published.strip():
        return None
    
    if published is not None:
        if 'GMT' in published:
            date_time_obj = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S GMT")
            date_time_utc = date_time_obj.replace(tzinfo=timezone.utc)
        else:
            date_time_obj = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z")
            date_time_utc = date_time_obj if date_time_obj.tzinfo else date_time_obj.replace(tzinfo=timezone.utc)
        return date_time_utc

def fetch_news_from_rss(feed_url):
    news_items = []
    response = requests.get(feed_url)
    soup = BeautifulSoup(response.content, features='xml')
    items = soup.findAll('item')

    for item in items:
        news_item = {
            "title": item.title.text,
            "link": item.link.text,
            "published": item.pubDate.text if item.pubDate else "",
            "summary": item.description.text if item.description else "",
            "image_url": item.find('media:content')['url'] if item.find('media:content') else ""
        }
        news_items.append(news_item)

    return news_items

def fetch_and_insert_data(**kwargs):
    last_record = get_last_present_record()
    kwargs['ti'].xcom_push(key='last_record', value=last_record)

    # RSS feed URLs
    rss_feeds = {
        "The New York Times_World" : "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "The New York Times_America" : "https://rss.nytimes.com/services/xml/rss/nyt/Americas.xml",
        "The New York Times_Politics" : "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
        "The New York Times_Business" : "https://rss.nytimes.com/services/xml/rss/nyt/EnergyEnvironment.xml",
        "The New York Times_Enviornment" : "https://rss.nytimes.com/services/xml/rss/nyt/EnergyEnvironment.xml",
        "The New York Times_Technology" : "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "The New York Times_Sports" : "https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml",
        "The New York Times_Soccer" : "https://rss.nytimes.com/services/xml/rss/nyt/Soccer.xml",
        "The New York Times_Media" : "https://rss.nytimes.com/services/xml/rss/nyt/MediaandAdvertising.xml",
        "The New York Times_Science" : "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
        "The New York Times_Health" : "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
        "CNN_World" : "http://rss.cnn.com/rss/cnn_world.rss",
        "CNN_America" : "http://rss.cnn.com/rss/cnn_us.rss",
        "CNN_Politics" : "http://rss.cnn.com/rss/cnn_allpolitics.rss",
        "CNN_Technology" : "http://rss.cnn.com/rss/cnn_tech.rss",
        "CNN_Health" : "http://rss.cnn.com/rss/cnn_health.rss",
        "CNN_Entertainment" : "http://rss.cnn.com/rss/cnn_showbiz.rss",
        "CNN_Travel" : "http://rss.cnn.com/rss/cnn_travel.rss",
        "BBC_World" : "https://feeds.bbci.co.uk/news/world/rss.xml",
        "BBC_Business" : "https://feeds.bbci.co.uk/news/business/rss.xml",
        "BBC_Politics" : "https://feeds.bbci.co.uk/news/politics/rss.xml",
        "BBC_Health" : "https://feeds.bbci.co.uk/news/health/rss.xml",
        "BBC_Science" : "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "BBC_Technology" : "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "BBC_Entertainment" : "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
        "Reuters_Business" : "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
        "Reuters_Politics" : "https://www.reutersagency.com/feed/?best-topics=political-general&post_type=best",
        "Reuters_Enviornment" : "https://www.reutersagency.com/feed/?best-topics=environment&post_type=best",
        "Reuters_Technology" : "https://www.reutersagency.com/feed/?best-topics=tech&post_type=best",
        "Reuters_Health" : "https://www.reutersagency.com/feed/?best-topics=health&post_type=best",
        "Reuters_Sports" : "https://www.reutersagency.com/feed/?best-topics=sports&post_type=best",
        "Reuters_Entertainment" : "https://www.reutersagency.com/feed/?best-topics=lifestyle-entertainment&post_type=best",
        "Reuters_America" : "https://www.reutersagency.com/feed/?best-regions=north-america&post_type=best"
      
    }
    all_news_items = []
    for source, url in rss_feeds.items():
        print(f" ----- Fetching news from {source}...")
        news_items = fetch_news_from_rss(url)
        for item in news_items:
            item['source'] = source
            item['category'] = source.split('_')[1]
            item['published_datetime'] = extract_date_time(item['published'])
            
            if not record_exists(item['title'], item['summary']):
                if item['summary'] != '' and item['summary'] and item['link'] and item['link'] and item['published'] :
                    all_news_items.append(item)
                    with pymssql.connect(server, username, password, database) as conn:
                        with conn.cursor(as_dict=True) as cursor:
                            cursor.execute(
                                "INSERT INTO all_news (title, link, published, summary, source, category, published_datetime, image_link) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                (item['title'], item['link'], item['published'], item['summary'], item['source'], item['category'], item['published_datetime'], item['image_url'])
                            )
                        conn.commit()
                    print(f"Record added {item['title']}")
                else:
                    print(f"Record does not exits but summary is blank {item['title']}")    
            else:
                print(f"Record already exits {item['title']}")
    news_df = pd.DataFrame(all_news_items)
    news_df.to_csv('news_data.csv', index=False)

def upsert_to_pinecone(**kwargs):
    ti = kwargs['ti']
    last_record = ti.xcom_pull(task_ids='fetch_and_insert_task', key='last_record')
    print(f"the last record is - {last_record}")
    conn = pymssql.connect(server=server, database=database, user=username, password=password)
    cursor = conn.cursor(as_dict=True)
    cursor.execute(f"SELECT Id, Title FROM all_news WHERE id > {last_record}")
    records = cursor.fetchall()
    conn.close()
    index_name = "test-index"
    existing_indexes = pinecone.list_indexes()
    if index_name not in existing_indexes:
        pinecone.create_index(index_name, dimension=1536, metric="cosine")
    index = pinecone.Index(index_name)
    upserted_count = 0
    for record in records:
        title_embedding = generate_embeddings(record['Title'])
        if title_embedding:
            title_embedding_values = [float(val) for val in title_embedding]
        
            metadata = {
                "id": str(record['Id']),
            }
            index.upsert(vectors=[{"id": str(record['Id']), "values": title_embedding_values}], metadata=metadata)
            upserted_count += 1
            print(f"Upserting {upserted_count} records")
    print(f"Upserted {upserted_count} records to Pinecone index.")


dag = DAG(
    'rss_to_sql_dag',
    default_args=default_args,
    description='Fetch news from RSS feeds and insert into Azure SQL table',
    schedule_interval=None,  
    catchup=False,
)

fetch_and_insert_task = PythonOperator(
    task_id='fetch_and_insert_task',
    python_callable=fetch_and_insert_data,
    provide_context=True,
    dag=dag,
)

upsert_to_pinecone_task = PythonOperator(
    task_id='upsert_to_pinecone_task',
    python_callable=upsert_to_pinecone,
    provide_context=True,
    dag=dag,
)

fetch_and_insert_task >> upsert_to_pinecone_task
