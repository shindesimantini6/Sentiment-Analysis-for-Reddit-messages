from  pprint import pprint
from config import CONFIGURE
from pymongo import MongoClient
from sqlalchemy import create_engine
import pymongo
import time
from sqlalchemy import text
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import logging
import os
# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


user_name = CONFIGURE["POSTGRES_USERNAME"]
host = CONFIGURE["POSTGRES_HOST"]
password = CONFIGURE["POSTGRES_PASSWORD"]
dbname = 'reddit_ethicalAI'
slack_token = CONFIGURE["SLACK_TOKEN"]

# Clients mongo and postgres
def connect_to_database(database_client, container_name, dbname, user_name = False, password = False,):
    """
    Connect to postgres or mongodb database.

    """

    if database_client == "postgres":
        conn = create_engine(f'postgresql://{user_name}:{password}@{container_name}:5432/{dbname}', echo=True)
        print('Engine created')
        return conn
    else:
        conn = pymongo.MongoClient(container_name)
        return conn[dbname]

# Create tables in postgres 
def create_tables_postgres():
    """
    Create tables inside the postgres database.

    """
    database_client = 'postgres'

    # Connect to the postgres database
    pg = connect_to_database(database_client = database_client, user_name = user_name , password = password , container_name = host, dbname = dbname)
    print('Enginer created again')
    # Create a SQL statement with the sql query
    sql_statement = '''
    CREATE TABLE IF NOT EXISTS reddit_posts(
    post_id          VARCHAR(500),
    post_title       VARCHAR,
    post_text        VARCHAR,
    sentiment_title  FLOAT,
    sentiment_text   FLOAT
    );
    '''
    time.sleep(10)

    with pg.connect() as connection:
        print('Connection Created')
        connection.execute(text(sql_statement))
        connection.commit()

# extract: read the db from mongodb
def extract_clean_data_from_database(database_client, dbname):
    """
    Extract data from a database. The database could be either mongodb or postgres.

    """

    # do a sleep of 10 sec
    time.sleep(10)
    
    # Create connection to the mongo db
    conn = connect_to_database(database_client = database_client, container_name = CONFIGURE['MONGODB_CONN'], dbname = dbname)
    print('Connection to Mondodb created')

    # Read the docs from mongodb
    docs = conn.reddit_table.find()
    return docs

# transform: cleaning + sentiment analysis
def sentiment_analysis(post_title, post_text):
    """
    Gives a sentiment score to each title and text.

    """

    s  = SentimentIntensityAnalyzer()
    sentiment_title = s.polarity_scores(post_title) 
    sentiment_text = s.polarity_scores(post_text) 
    score_title = sentiment_title['compound']
    score_text = sentiment_text['compound']
    return score_title, score_text

def insert_into_postgres_table():
    """
    Insert the data values and the sentiment scores into the postgres table. 

    """

    database_client = 'postgres'

    # Connect to the postgres database
    pg = connect_to_database(database_client = database_client, user_name = user_name , password = password , container_name = host, dbname = dbname)
    print('Enginer created again')
    time.sleep(10)
    
    docs = extract_clean_data_from_database('mongodb', 'reddit_ethicalAI')
    for doc in docs:
        post_id = doc['post_id'].replace("'", "").replace(",", "").replace("*", "").replace("!", "")
        print(f'This is the post_id:{post_id}')
        post_title = doc['post_title'].replace("'", "").replace(",", "").replace("*", "").replace("!", "")
        print(f'This is the post_title:{post_title}')
        post_text = doc['post_text'].replace("'", "").replace(",", "").replace("*", "").replace("!", "")
        print(f'This is the post_text:{post_text}')
        sentiment_title, sentiment_text = sentiment_analysis(post_title, post_text)

        sql_statement = f"""
        INSERT INTO reddit_posts(post_id, post_title, post_text, sentiment_title, sentiment_text)
        VALUES ('{post_id}', '{post_title}', '{post_text}', '{sentiment_title}', '{sentiment_text}');
        """

        with pg.connect() as connection:
            print('Connection Created')
            connection.execute(text(sql_statement))
            connection.commit()

def post_tweet_into_slack():
    """
    Extracts one tweet at a time and posts it in slack.
    """

    database_client = 'postgres'
    
    # Create connection to postgress
    pg = connect_to_database(database_client = database_client, user_name = user_name , password = password , container_name = host, dbname = dbname)
    print('Engine created to read the tweets')
    time.sleep(10)

    sql_statement = """
    SELECT * FROM reddit_posts;
    """

    with pg.connect() as connection:
            print('Connection Created')
            cursor = connection.execute(text(sql_statement))
            posts = cursor.fetchall()

    for post in posts:
        time.sleep(20)
        print(post)
        post_title = post[1]
        print(post_title)
        title_score = json.dumps(post[3])
        print(title_score)
        post_text = post[2]
        print(post_text)
        post_score = json.dumps(post[4])
        print(post_score)

        webhook_url = CONFIGURE["SLACK_WEBHOOK"]
        print(webhook_url)
        # data1 = {'text': post_title}
        # requests.post(url=webhook_url, json = data1)
        # print('Post of data1 sent')
        # data2 = {'text': title_score}
        # requests.post(url=webhook_url, json = data2)

        # data3 = {'text': post_text}
        # requests.post(url=webhook_url, json = data3)
        # print('Post of data3 sent')
        # data4 = {'text': post_score}
        # requests.post(url=webhook_url, json = data4)
        # print('Post of data4 sent')
        return title_score

def create_charts():
    """
    Creates a summary chart and sends it to the slack.

    """
    title_scores = []
    title_score = post_tweet_into_slack()
    title_scores.append(title_score)
    sentiments = []
    positive_sentiments = []
    negative_sentiments = []
    neutral_sentiments = []
    for score in title_scores:
        if float(score) > 0.05:
            sentiment = 'positive'
            positive_sentiments.append(sentiment)
        elif float(score) > -0.05 and float(score) < 0.05:
            sentiment = 'neutral'
            neutral_sentiments.append(sentiment)
        else:
            sentiment = 'negative'
            negative_sentiments.append(sentiment)
        sentiments.append(sentiment)

    chart = {
        "type": "bar",
        "data": {
            "datasets": [
            {
                "data": [5, 6, 9],
                "label": "Sentiment Analysis"
            }
            ],
            "labels": ["Positive", "Negative", "Neutral"]
        }
    }
    image_url = f"https://image-charts.com/chart.js/2.8.0?bkg=white&c={chart}"

    data = {'blocks': [{
            "type": "section",
            "accessory": {
                "type": "image",
                "image_url": f"{image_url}",
                "alt_text": "alt text for image"
            }
        }]}
    webhook_url = CONFIGURE["SLACK_WEBHOOK"]
    # requests.post(url=webhook_url, json = data)

    data = pd.DataFrame(sentiments, columns = ['sentiment'])
    print(data)

    sns.set_style("dark")
    sns.countplot(x=data["sentiment"])
    plt.title('Grouped Sentiments for today')
    plt.xlabel('Sentiments', fontsize = 12)
    plt.ylabel('Count of sentiments as calculated by Vader', fontsize = 12)
    plt.savefig('./final_sentiments.png') 
    # attachments = [{"title": "test",
                # "image_url": "C:\file.png"}]
    image_url = './final_sentiments.png'


    # with open(image_url, "rb") as f:
    #     im_bytes = f.read()        
    # files = {'media': open(image_url, 'rb')}
    # print(files)
    # requests.post(url = webhook_url, files=files)
    # print("Post sent")

    # WebClient instantiates a client that can call API methods
    # When using Bolt, you can use either `app.client` or the `client` passed to listeners.
    client = WebClient(token=os.environ.get(slack_token))
    logger = logging.getLogger(__name__)
    # The name of the file you're going to upload
    file_name = "./myFileName.gif"
    # ID of channel that you want to upload file to
    channel_id = "C04QE3D8DTK"

    try:
        # Call the files.upload method using the WebClient
        # Uploading files requires the `files:write` scope
        result = client.files_upload(
            channels=channel_id,
            initial_comment="Here's my file :smile:",
            file=image_url,
        )
        # Log the result
        logger.info(result)

    except SlackApiError as e:
        logger.error("Error uploading file: {}".format(e))


def post_image(filename, token, channels):
    f = {'file': (filename, open(filename, 'rb'), 'image/png', {'Expires':'0'})}
    print(f)
    response = requests.post(url=f'https://slack.com/api/files.upload?token={token}', data=
       {'channels': channels, 'media': f}, 
       headers={'Accept': 'application/json'}, files=f)
    return response.text

    # return image_url

# def send_chart_to_slack():

#     image_url = create_charts()
#     slack = Slacker(slack_token)
#     slack.files.upload(image_url, channels="@ethicalai")


# Create tables in postgres
create_tables_postgres()
insert_into_postgres_table()
create_charts()
# post_image(filename='./final_sentiments.png', token=slack_token,
#     channels ="#ethicalai")