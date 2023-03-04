# Sentiment-Analysis-for-Reddit-messages

Build a dockerised data pipeline to extract Reddit messages via Reddit API, load these into Mongodb and transform them to conduct sentiment analysis with Python package VaderSentiment, and load these sentiments and messages in Postgres and send them to the desired channel via a Slack bot.

### Requirements
- Python 3.8 and above
- Docker
- Postgres
- pandas
- pymongo
- sqlalchemy
- vaderSentiment
- seaborn
- matplotlib
- slack_cleaner2

### Usage
- In the terminal run the command `docker-compose build` to build images and containers
- Run `docker-compose up` to run the functionality in the code.
- If the container and images need to be deleted, run `docker-compose down`
