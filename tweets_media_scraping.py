#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
import requests
import re
import mysql.connector
from bs4 import BeautifulSoup

def crawling(url, screen_name, cnx, cur, amount, flag=True):
	if flag:
		html = requests.get(url).text
		print(url)
	else:
		json = requests.get(url).json()
		html = json["items_html"]
	try:
		soup = BeautifulSoup(html, "lxml")
	except:
		soup = BeautifulSoup(html, "html5lib")
	links = soup.find_all("div", class_="AdaptiveMedia-photoContainer js-adaptive-photo ")
	last_tweet = soup.find_all("a", class_="tweet-timestamp js-permalink js-nav js-tooltip")[-1]
	for link in links:
		url = link.attrs['data-image-url']
		print(url)
		try:
			sql = 'INSERT INTO crawl_tweets_img_data(user_id, img_url) VALUES (%s, %s)'
			cur.execute(sql, (screen_name,url))
			cnx.commit()
		except:
			cnx.rollback()
			raise

	last_tweet_id = last_tweet.attrs['data-conversation-id']
	return last_tweet_id

@click.command()
@click.option('--host', '-h', default='127.0.0.1')
@click.option('--user', '-u', default='username')
@click.option('--password', '-p', default='password')
@click.option('--database', '-d', default='database_name')
@click.option('--amount', '-a', default=1)
@click.option('--screen-name', '-s', default="twitter")
def cmd(host, user, password, database, amount, screen_name):

	cnx = mysql.connector.connect(user=user, password=password,
							  host=host,
							  database=database,
							  charset='utf8')
	cur = cnx.cursor()
	if cnx.is_connected():
		print('connected')
	else:
		print('couldnot connect')
		exit()
	for i in range(1, amount + 1):
		if i == 1:
			url = 'https://twitter.com/{screen_name}/media'.format(screen_name=screen_name)
			last_tweet_id = crawling(url, screen_name, cnx, cur, amount)
		else:
			url = "https://twitter.com/i/profiles/show/{screen_name}/media_timeline?include_available_features=1&include_entities=1&max_position={last_tweet_id}&oldest_unread_id=0&reset_error_state=false".format(screen_name=screen_name, last_tweet_id=last_tweet_id)
			last_tweet_id = crawling(url, screen_name, cnx, cur, amount, False)

	cur.close()
	cnx.close()

def main():
	cmd()


if __name__ == '__main__':
	main()
