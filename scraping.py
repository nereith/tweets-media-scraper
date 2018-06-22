#!/usr/bin/env python
# -*- coding: utf-8 -*-

import click
import requests
import re
import mysql.connector
from bs4 import BeautifulSoup

def crawling(url, cnx, cur, amount):
	html = requests.get(url).text
	print(url)
	try:
		soup = BeautifulSoup(html, "lxml")
	except:
		soup = BeautifulSoup(html, "html5lib")
	links = soup.find_all("div", class_="AdaptiveMedia-photoContainer js-adaptive-photo ")
	tweets = soup.find_all("div", class_="tweet-timestamp js-permalink js-nav js-tooltip")
	for link in links:
		url = link.attrs['data-image-url']
		print(url)
	for tweet in tweets:
		tweet_id = tweet.attrs['data-conversation-id']
		print(tweet_id)
		#https://twitter.com/i/profiles/show/*/media_timeline?include_available_features=1&include_entities=1&max_position=1009690383180165127&oldest_unread_id=0&reset_error_state=false
		'''
		html = requests.get(url).text
		try:
			soup = BeautifulSoup(html, "lxml")
		except:
			soup = BeautifulSoup(html, "html5lib")
		print
		try:
			sql = 'INSERT INTO hair_catalog_data(sex, shop_name, style_name, menu, length, color, image, types_amount, types_hardness, types_thickness, types_curliness, facetypes, catalog_url, photo_url_main, photo_url_front, photo_url_side, photo_url_back, photo_data_main, photo_data_front, photo_data_side, photo_data_back ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
			cur.execute(sql, (sex, shop_name, style_name, menu, length, color, image, types_amount, types_hardness, types_thickness, types_curliness, facetypes, catalog_url, photo_main, photo_front, photo_side, photo_back, photo_main_data, photo_front_data, photo_side_data, photo_back_data))
			cnx.commit()
		except:
			cnx.rollback()
			raise
			'''

@click.command()
@click.option('--host', '-h', default='127.0.0.1')
@click.option('--user', '-u', default='username')
@click.option('--password', '-p', default='password')
@click.option('--database', '-d', default='database_name')
@click.option('--amount', '-a', default=1)
@click.option('--screen-name', '-s', default="twitter")
def cmd(host, user, password, database, amount, screen_name):
	url = 'https://twitter.com/{screen_name}/media'.format(screen_name=screen_name)

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
	crawling(url, cnx, cur, amount)
	cur.close()
	cnx.close()

def main():
	cmd()


if __name__ == '__main__':
	main()
