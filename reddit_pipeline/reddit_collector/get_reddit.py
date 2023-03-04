"""
This script gets reddits titles from the reddit api 
and serve in the first step of the dockerized pipeline.
TODO
- add Mongodb connection with pymongo and insert reddits into Mongodb on WED morning
"""

from  pprint import pprint
from config import CONFIGURE
import requests
from requests.auth import HTTPBasicAuth
from pymongo import MongoClient 

## PREPARE AUTHENTIFICATION INFORMATION ##
## FOR REQUESTING A TEMPORARY ACCESS TOKEN ##
basic_auth = HTTPBasicAuth(
    username=CONFIGURE['APP_ID'],
    password=CONFIGURE['SECRET']
)

print(basic_auth)

GRANT_INFORMATION = dict(
    grant_type="password",
    username=CONFIGURE['REDDIT_USERNAME'], # REDDIT USERNAME
    password=CONFIGURE['REDDIT_PASSWORD'] # REDDIT PASSWORD
)

headers = {
    'User-Agent': "Mozilla"
}

### POST REQUEST FOR ACCESS TOKEN

POST_URL = "https://www.reddit.com/api/v1/access_token"

access_post_response = requests.post(
    url=POST_URL,
    headers=headers,
    data=GRANT_INFORMATION,
    auth=basic_auth).json()

# print(type(access_post_response), access_post_response)

### ADDING TO HEADERS THE Authorization KEY

headers['Authorization'] = access_post_response.get('token_type') + ' ' + access_post_response.get('access_token')

# print(headers)

## Send a get request to download most popular (hot) Python subreddits title using the new headers.

topic = 'ethicalAI'
URL = f"https://oauth.reddit.com/r/{topic}/hot"

response = requests.get(
    url=URL,
    headers=headers).json()

# pprint(response)

# pprint(len(response.get('data').get('children')))
full_response = response.get('data').get('children')

mongo_dict = dict()

conn = 'mongodb://mongo_tahini'

## Connect to container, create DB and collections in DB
client = MongoClient(conn)

reddit_ethicalAI = client.reddit_ethicalAI #use reddit_hot_topics database

# go through the full response and save each title with the corresponding id 
for post in full_response:
    id_ = post.get('data').get('id')
    # pprint(id_)
    title = post.get('data').get('title')
    # pprint(title)
    selftext = post.get('data').get('selftext')
    reddit_ethicalAI.reddit_table.insert_one({'post_id':id_, 'post_title':title, 'post_text':selftext})

    # mongo_dict[id_] = title

# print(mongo_dict)

# # write to a collection called reddit_hot_topics
# reddit_db.insert_many([mongo_dict])
