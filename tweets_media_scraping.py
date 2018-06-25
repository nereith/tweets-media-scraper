#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
import requests
import re
import mysql.connector
import configparser
import io
import os
from bs4 import BeautifulSoup

class ConfigParser(configparser.RawConfigParser):
	def get(self, section, option):
		val = configparser.RawConfigParser.get(self, section, option)
		return val.strip('"')

conf_str = '[settings]\n' + open('simple-db-migrate.conf', 'r').read()
conf_fp = io.StringIO(conf_str)
config = ConfigParser()
config.readfp(conf_fp)

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
		orig_size_url = url + ":orig"
		image_data = requests.get(orig_size_url).content
		try:
			sql = 'INSERT INTO crawl_tweets_img_data(user_id, img_url, img_data) VALUES (%s, %s)'
			cur.execute(sql, (screen_name,url,image_data))
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
		orig_size_url = image_url + ":orig"
		image_data = requests.get(orig_size_url).content
		"""
		filename = image_url.replace('https://pbs.twimg.com/media/','')
		print(filename)
		fullpath = os.path.join("./scraping/", filename)
		print(image_url)
		print(tweet_ref_url)
		with open(fullpath, "wb") as fout:
			fout.write(image_data)
		"""
		try:
			sql = 'INSERT INTO crawl_search_tweets_img_data(search_word, screen_name, user_id, tweet_ref_url, img_url, img_data) VALUES (%s, %s, %s, %s, %s, %s)'
			cur.execute(sql, (search_word, screen_name, user_id, tweet_ref_url, image_url, image_data))
			cnx.commit()
		except:
			cnx.rollback()
			raise

	last_tweet_id = last_tweet.attrs['data-status-id']
	return last_tweet_id


@click.group()
@click.option('--host', '-h', default=config.get('settings','database_host'))
@click.option('--user', '-u', default=config.get('settings','database_user'))
@click.option('--password', '-p', default=config.get('settings','database_password'))
@click.option('--database', '-d', default=config.get('settings','database_name'))
@click.option('--port', '-P', default=config.get('settings','database_port'))
@click.pass_context
def cmd(ctx, host, user, password, database, port):
	cnx = mysql.connector.connect(user=user, password=password,
							  host=host,
							  database=database,
							  port=port,
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
