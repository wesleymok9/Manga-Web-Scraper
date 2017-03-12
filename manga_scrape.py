#program makes use of file manipulation and web scraping
#used to query a website
#https://tech4lib.wordpress.com/2015/06/21/sending-http-requests-with-python-httplib-vs-requests/
#out of scope but could look into checking setting a progress bar based on size of content length for each download // response.headers.get('content-length') 

import requests
#to scrape the site
from bs4 import BeautifulSoup
#will allow for retrieving a string from webpage and wrap the string in a StringIO object so that it behaves like a file
#from io import BytesIO
import io
#using the Python Imaging library to process images //https://automatetheboringstuff.com/chapter17/
from PIL import Image

import os

#scrapes the main page of the site and cross references the text file with the manga you would like to read
#presents user with the URL of the manga they desire
def getMangaURL():
	main_page = "http://www.mangahere.co/mangalist/"
	get_main_page = requests.get(main_page)
	soup_main_page = BeautifulSoup(get_main_page.text, "html.parser")
	get_all_title = soup_main_page.findAll("a", class_="manga_info")
	with open('manga_title.txt', 'r', encoding='utf8') as manga_titles:
		reader = manga_titles.readlines()
		for title in reader:
			for titles in get_all_title:
				if titles.text == title.rstrip():
					manga_title_url = titles.get("href")
					#print(manga_title)
					getTotalChapters(manga_title_url, title)	
					break
				if titles.text != title.rstrip() and titles == get_all_title[-1]:
					print("Did not enter Manga Title {} correctly or title does not exist.".format(title.rstrip()))

#will get the total number of chapters for the manga and create the appropriate directories if manga is available for download
def getTotalChapters(manga_title_url, title):
	chapter_numbers = [] #this will be necessary as there are some mangas where the chapters are in decimal format and not all mangas have just integers making it hard to calculate all the chapters
	get_manga_page = requests.get(manga_title_url)
	soup_manga_page = BeautifulSoup(get_manga_page.text, "html.parser")
	if "has been licensed, it is not available in MangaHere" in get_manga_page.text:
		print("The Manga {} has been deemed as licensed and will not be available for download".format(title.rstrip()))
	else:
		makeMangaDirectory(title)
		get_manga_chapters = soup_manga_page.findAll("a")
		#Used to read through the file and find all the chapter numbers to create a directory for each chapter
		for chap in get_manga_chapters:
			if manga_title_url in chap.get("href"):
				#print(chap.text)
				#print(title)
				if title.rstrip() in chap.text:
					#to make sure only the correct tags with chapter numbers get retrieved
					if "." in chap.text.strip(' \t\n\r')[len(title.rstrip())+1::]:
						if chap.text.strip(' \t\n\r')[len(title.rstrip())+1:chap.text.strip(' \t\n\r').find(".")].isdigit() == True:
							chapter_numbers.append(chap.text.strip(' \t\n\r')[len(title.rstrip())+1::])
					elif chap.text.strip(' \t\n\r')[len(title.rstrip())+1::].isdigit() == True:
						chapter_numbers.append(chap.text.strip(' \t\n\r')[len(title.rstrip())+1::]) #removes all unnecessary spacing
		#creates the folder
		for num in chapter_numbers:
			makeChapterDirectory(title, num)
		getChapterURL(manga_title_url, soup_manga_page, title)

				
def makeMangaDirectory(title):
	if not os.path.exists(title.rstrip()):
		os.makedirs(title.rstrip())
	#print(os.getcwd())

def makeChapterDirectory(title, num):
	if not os.path.exists("{}\\Chapter {}".format(title.rstrip(), num)):
		os.makedirs("{}\\Chapter {}".format(title.rstrip(), num))

def getChapterURL(manga_title_url, soup_manga_page, title):
	get_manga_chapters_block = soup_manga_page.findAll("li")
	for li in get_manga_chapters_block:
		li.find("a")
		try:
			if manga_title_url in li.find("a")["href"]:
				manga_chapter = li.find("a")["href"] #chapter URLs
				#chapter will always be the last section in the URL and will look like similar to c001 will need to substring with a [1::] to get number without the c
				#lstrip to get rid of the leading 0s
				#use -2 because last value is empty string
				##print(li.find("a")["href"].split("/")[-2][1::].lstrip("0"))
				chap_num = li.find("a")["href"].split("/")[-2][1::].lstrip("0")
				#print(manga_chapter)
				#break
				getPageURLs(manga_chapter, title, chap_num)
		except TypeError:
			continue
	
def getPageURLs(manga_chapter, title, chap_num):
	#need to enter page 1 of the chapter which is the URL stored in variable manga_chapter
	#from page 1 there is a drop down available where it can be scraped to find the total amount of pages for the chapter
	get_manga_page_num = requests.get(manga_chapter)
	if "<p>Sorry, <strong>{} {}</strong> is not available yet. We will update <strong>{} {}</strong> as soon as the chapter is released".format(title.rstrip(), chap_num, title.rstrip(), chap_num) not in get_manga_page_num.text:
		soup_manga_page_num = BeautifulSoup(get_manga_page_num.text, "html.parser")
		get_manga_page_dropdown = soup_manga_page_num.findAll("option")
		#the page always has 2 dropdown lists one on top and one on bottom so there is only need to loop through half the list to avoid redundancy
		chapter_directory = "{}\\Chapter {}".format(title.rstrip(), chap_num)
		if os.listdir(chapter_directory) == []: #checks to make sure no pages there already will save time from downloading everything again
			for page_num in get_manga_page_dropdown[0:int(len(get_manga_page_dropdown)/2)]:
				#dropdown lists store the other page URLs in their value parameter
				page_url = page_num.get("value")
				getPage(page_url, page_num.text, chapter_directory)
				#break
	
def getPage(page_url, page_num, chapter_directory):
	#print(page_url)
	page = requests.get(page_url)
	soup_page = BeautifulSoup(page.text, "html.parser")
	images = soup_page.findAll("img")
	for img in images:
		if "h.mhcdn.net/store/manga" in img.get("src"):
			page_image = img.get('src')
			image = requests.get(page_image)
			#print(image.status_code)
			imagedl = Image.open(io.BytesIO(image.content))
			#below line is for python 2
			#The StringIO and cStringIO modules are gone. Instead, import the io module and use io.StringIO or io.BytesIO for text and data respectively.
			#StringIO is an in-memory stream for text only. Use BytesIO instead.
			#imagedl = Image.open(StringIO(image.getvalue()))
			imagedl.save("{}\\Page {}.jpg".format(chapter_directory,page_num))
			#break #typically 1 pic URL for current page and another for the next page and will want to break out after the first one
		
getMangaURL()