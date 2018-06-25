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

def crawling_search(url, search_word, cnx, cur, amount, flag=True):
	headers = {
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:60.0) Gecko/20100101 Firefox/60.0',
}
	if flag:
		html = requests.get(url,headers=headers).text
		print(url)
	else:
		json = requests.get(url,headers=headers).json()
		html = json["items_html"]
	try:
		soup = BeautifulSoup(html, "lxml")
	except:
		soup = BeautifulSoup(html, "html5lib")

	links = soup.find_all("span", {"class" : "AdaptiveStreamGridImage"})

	last_tweet = links[-1]
	for link in links:
		image_url = link.attrs['data-url']
		screen_name = link.attrs['data-screen-name']
		user_id = link.attrs['data-user-id']
		status_id = link.attrs['data-status-id']
		tweet_ref_url = "https://twitter.com" + link.attrs['data-permalink-path']

		print(image_url)
		print(tweet_ref_url)
		try:
			sql = 'INSERT INTO crawl_search_tweets_img_data(search_word, screen_name, user_id, tweet_ref_url, img_url) VALUES (%s, %s, %s, %s, %s)'
			cur.execute(sql, (search_word, screen_name, user_id, tweet_ref_url, image_url))
			cnx.commit()
		except:
			cnx.rollback()
			raise

	last_tweet_id = last_tweet.attrs['data-status-id']
	return last_tweet_id

@click.group()
@click.option('--host', '-h', default='127.0.0.1')
@click.option('--user', '-u', default='username')
@click.option('--password', '-p', default='password')
@click.option('--database', '-d', default='database_name')
@click.pass_context
def cmd(ctx, host, user, password, database):
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
	ctx.obj['CNX'] = cnx
	ctx.obj['CUR'] = cur


@cmd.command()
@click.argument('screen_name')
@click.option('--amount', '-a', default=1)
@click.pass_context
def user(ctx, screen_name, amount):

	cur = ctx.obj['CUR']
	cnx = ctx.obj['CNX']

	for i in range(1, amount + 1):
		if i == 1:
			url = 'https://twitter.com/{screen_name}/media'.format(screen_name=screen_name)
			last_tweet_id = crawling(url, screen_name, cnx, cur, amount)
		else:
			url = "https://twitter.com/i/profiles/show/{screen_name}/media_timeline?include_available_features=1&include_entities=1&max_position={last_tweet_id}&oldest_unread_id=0&reset_error_state=false".format(screen_name=screen_name, last_tweet_id=last_tweet_id)
			last_tweet_id = crawling(url, screen_name, cnx, cur, amount, False)

	cur.close()
	cnx.close()

@cmd.command()
@click.option('--language', '-l', default=None)
@click.argument('search_word')
@click.option('--amount', '-a', default=1)
@click.pass_context
def search(ctx, language, search_word, amount):

	cur = ctx.obj['CUR']
	cnx = ctx.obj['CNX']

	for i in range(1, amount + 1):
		if i == 1:
			url = 'https://twitter.com/search?f=images&q={search_word}&qf=off&lang=ja'.format(search_word=search_word)
			last_tweet_id = crawling_search(url, search_word, cnx, cur, amount)
		else:
			url = "https://twitter.com/i/search/timeline?f=images&vertical=default&q={search_word}&qf=off&include_available_features=1&include_entities=1&lang=ja&max_position=TWEET--{last_tweet_id}--T-0-0&reset_error_state=false".format(search_word=search_word, last_tweet_id=last_tweet_id)
			last_tweet_id = crawling_search(url, search_word, cnx, cur, amount, False)

	cur.close()
	cnx.close()


def main():
	cmd(obj={})


if __name__ == '__main__':
	main()
