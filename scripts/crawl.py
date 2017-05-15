#!/usr/bin/python
# -*- coding: utf-8 -*-

from TorCtl import TorCtl
from lxml import html
from pprint import pprint
import urllib2
import urllib
import sys
import datetime
import os
import requests
import csv

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers={'User-Agent':user_agent, 'Referer' : 'http://grams7enufi7jmdl.onion/'}
cookies = {'adnum':'a0', 'csr_prot' : '250a2dee96e7edb8e188e4dc66b5b9ab' , 'Grams_session' : 'e8NeeJeSG0%2BJjhgH095%2BM0wXR2VFx0nV2A8aQr1wRgw6JCVMQpeZM7tQEYPEgpBvhrIvoa5UVY8kIYdAJKBR6Z7ZSEymu57TAk9Yo%2BL%2B%2BEZRx%2BrNUexUVdsKPoQQfqDGV8Im4t5TTcEV1EYWeKYIu1%2F%2FDDO1zp1cDKrIY7Pr8ozJVVJrVhv0UNScvQpQUMN9V7ZpX7xPwGrLa1lv8X%2FCEHNaSdxbMpY5Z1FZ61x5DFDKITSUCafm9WooGSDMdshiIskNe%2FykJ7BjvN9WIaGzSCA0d%2FNGIy5lFXoljdOfxD00aRuoX7p4k9%2BecVaKLf%2FxyHA9tNtpT5Ws9UIRcLeK%2FcZegrqJfhcLAbORFGG0gocoYf9bEBG3DEa8KDar0KTgwCLGM%2BIgJrgJQdAiR3AGv4DB9MmA3%2Ba5XDHowJj2C6%2FnzsdxfA0JyZU0Rs45SBDEqsX6b7MHOaHQmfTP20RIQg%3D%3D','beenhere' : 'true'}
proxies = {
      'http': 'http://127.0.0.1:8118',
      'https': 'http://127.0.0.1:8118',
    }

def get_content(url, data):
    def _set_urlproxy():
        proxy_support = urllib2.ProxyHandler({"http" : "127.0.0.1:8118"})
        opener = urllib2.build_opener(proxy_support)
        urllib2.install_opener(opener)
    _set_urlproxy()
    if data != None:
        request=urllib2.Request(url, data, headers)
    else:
        request=urllib2.Request(url, None, headers)
    return urllib2.urlopen(request).read()

def renew_connection():
    conn = TorCtl.connect(controlAddr="127.0.0.1", controlPort=9051, passphrase="")
    conn.send_signal("NEWNYM")
    conn.close()

def crawl_get(url, title):
    print "Starting crawling of "+title+"!"
    print "Your TOR IP for this crawl is "+get_content("http://icanhazip.com", None)+" :)"
    request = get_content(url, None)
    create_file(request, title, None)

def crawl_post(action, data, title):
    print "Starting crawling of "+title+"!"
    print "Your TOR IP for this crawl is "+get_content("http://icanhazip.com", None)+" :)"
    request = requests.post(action, data=data, proxies=proxies, headers=headers, cookies=cookies)
    create_file(request, title, '1')

def create_file(request, title, grams):
    directory = "output/"+title+"/"
    if not os.path.exists(directory):
        try:
            print "Creating directory "+directory
            os.makedirs(directory)
        except Exception as e:
            print "Error creating directory "+directory

    name = directory+"crawl"+title+datetime.datetime.strftime(datetime.datetime.now(), '%d%m%Y_%H%M%S')
    if grams != None:
        tree = html.fromstring(request.text)
        results = tree.xpath('//div[@class="media-body"]//a/text()')
        results_href = tree.xpath('//div[@class="media-body"]//a/@href')

        parser = csv.reader(x.encode('utf-8') for x in results)
        parser_href = csv.reader(x.encode('utf-8') for x in results_href)
        
        try:
            file = open(name, 'w')
            file_href = open(name+"_href", 'w')
            wr = csv.writer(file, quoting=csv.QUOTE_ALL)
            wr_href = csv.writer(file_href, quoting=csv.QUOTE_ALL)
            print "Writing files "+name+", "+name+"_href..."
            for fields in parser:
                for i,f in enumerate(fields):
                    wr.writerow(['Result', f])
            for fields in parser_href:
                for i,f in enumerate(fields):
                    wr_href.writerow(['Result', f])
            file.close()
            file_href.close()
            print "Crawl for "+title+" successfully created."
            print "<===========>"
        except BaseException as e:
            print "Crawl for "+title+" failed."
            print str(e)
            sys.exit(0)

    else:
        try:
            file = open(name, 'w')
            print "Writing file "+name+"..."
            file.write(request)
            file.close()
            print "Crawl for "+title+" successfully created."
            print "<===========>"
        except Exception, e:
            print "Crawl for "+title+" failed."
            sys.exit(0)

def get_torch(query):
    url = "http://xmh57jrzrnw6insl.onion/5dc02cc7lc/search.cgi?q="+query+"&cmd=Search!"
    return url

print "Renewing TOR's IP..."
renew_connection()

#Some examples

#data = {'csr_prot':'250a2dee96e7edb8e188e4dc66b5b9ab', 'searchstr':'Bristol+Pound'}
#crawl_post("http://grams7enufi7jmdl.onion/results", data, "Grams_Bristol_Pound")
#data = {'csr_prot':'250a2dee96e7edb8e188e4dc66b5b9ab', 'searchstr':'Brixton+Pound'}
#crawl_post("http://grams7enufi7jmdl.onion/results", data, "Grams_Brixton_Pound")
