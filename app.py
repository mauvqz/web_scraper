#!/usr/bin/python

from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
from urllib.parse import urlsplit
import math
import random
import sys, getopt

app = Flask(__name__)

supportedSites = {
    'shopee.tw': {'altsite':'https://shopee.tw','item-class':'shopee-search-item-result__item', 'search-method':'search?keyword='},
    'jd.hk':     {'altsite':'https://search.jd.hk','item-class':'gl-item', 'search-method':'Search?keyword='},
    }

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = request.form['keyword']
        website = request.form['website']

        siteDetails = get_site_details(website)
        if(siteDetails is None):
            print("This website is not currently supported")
            # We could render a site where we can add support for the given site
            return render_template('index.html')

        browser = get_headless_browser()
        siteHTML = get_html_site(browser, keyword, siteDetails['altsite'], search_attribute=siteDetails['search-method'])

        found = scrape_for_results(siteHTML, siteDetails['item-class'])
        print("Matches found: {}".format(len(found)))
        return render_template('index.html', matches=len(found))

    return render_template('index.html')

def scrape_for_results(siteHTML, class_str="shopee-search-item-result__item"):
    '''
    Search for a given class in the given html site

    :param siteHTML : website in html
    :class_str : class attribute to search in the given site
    '''
    soup = BeautifulSoup(siteHTML, features="html.parser")
    # print(soup.prettify())
    kywrd = soup.find_all(["div", "li"], class_=class_str)
    return kywrd

def get_headless_browser():
    '''
    This function sets up the Chrome driver and Chrome options
    to enable headless browsing
    '''
    myOptions = Options()
    myOptions.headless = True

    return webdriver.Chrome(options = myOptions)

def get_html_site(browser, keyword, website, search_attribute="search?keyword=", lazy_loading=True):
    '''
    Uses a browser to look for a keyword in a given site

    The search attribute can be modified to adapt to other sites

    :param browser : Chrome Browser instance for headless browsing
    :param keyword : Keyword used in search
    :param website : initial website used for scraping
    :param search_attributes: user defined search attribute to set in url
    :param lazy_loading : enables or disables scrolling through webpage to load objects
    '''
    siteEncoding = "&enc=utf-8"
    siteWithSearch = website + '/' + search_attribute + keyword.replace(" ", "%20") + siteEncoding
    print("Searching for results of keyword: {} in generated site url: {}".format(keyword, siteWithSearch))

    browser.get(siteWithSearch)

    if(lazy_loading):
        maxHeight = browser.execute_script("return document.documentElement.scrollHeight")
        windowSize = browser.get_window_size()['height']
        scrollSteps = math.ceil(maxHeight / windowSize)

        # Scrolls through page
        for step in range(0, scrollSteps):
            browser.execute_script("window.scrollTo(0, {});".format(step * windowSize))
            sleep(random.uniform(0.5, 0.7))

    siteHtml = browser.page_source
    browser.close()

    return siteHtml

def get_site_details(website):
    '''
    Gets the class element to search for if website is known by the app
    '''
    if("http://" not in website and "https://" not in website):
        website = 'https://' + website

    baseSite = urlsplit(website).netloc.replace('www.', '')
    print("base site: {}".format(baseSite))
    return supportedSites.get(baseSite)

def perform(keyword, website):
    siteDetails = get_site_details(website)
    if(siteDetails is None):
        print("This website is not currently supported")
        # We could render a site where we can add support for the given site
        return

    browser = get_headless_browser()
    siteHTML = get_html_site(browser, keyword, siteDetails['altsite'], search_attribute=siteDetails['search-method'])

    found = scrape_for_results(siteHTML, siteDetails['item-class'])
    print("Matches found: {}".format(len(found)))
    return

def main(argv):
    keyword = ''
    website = ''
    try:
      opts, args = getopt.getopt(argv,"s:k:",["site=","keyword="])
    except getopt.GetoptError:
      print('app.py -s <website> -k <keyword>')
      sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('app.py -s <website> -k <keyword>')
            sys.exit()
        elif opt in ("-k", "--keyword"):
            keyword = arg
        elif opt in ("-s", "--site"):
            website = arg
    
    print("website: {}, keyword: {}".format(website, keyword))
    perform(keyword, website)


if __name__ == "__main__":
   main(sys.argv[1:])
