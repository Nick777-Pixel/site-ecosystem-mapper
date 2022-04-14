import requests
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.parse import urlparse, urlunparse
from urllib.error import HTTPError
import re
import collections
from collections import defaultdict
import heapq
import pandas as pd
import csv
import lxml
import altair as alt
import traceback

#https://www.crummy.com/software/BeautifulSoup/bs4/doc/

#TO DO:

#re making the labels not be trimmed
#you might be able to do via switching to bind(point_label=...) from bind(point_title...),
#and if that borks, maybe via doing point_label + inline html (point_title wouldn't accept html, just text, while label
# is the full object). More intense embeddings will use the JS API to do custom labels, but that's overkill for here.
# i did the above and i think it's not working but also, i have no idea what it's doing tbh or if i'm doing it right
# error handling that tries https first then http

#make subdomains like ru.southfront.org be included in base domain.

#clean this code especially re redundancies like len(thing) > 4: and stripping www in multiple places + just document better


def check_status(url):
    ''' Checks to see if there's an XML sitemap. '''
    # https://github.com/linasfx/sitemap-URL-s/blob/master/sitemap.py
    url=('http://'+url)

    r  = requests.get(url)
    site_map="/sitemap.xml"

    req=requests.head(url+site_map)
    status_code=req.status_code

    if status_code==200:
	    return "This site has an XML map! Code now running."
    else:
        return "This site doesn't seem to have an XML site map which we normally use to map its links.\
                 Instead, we will crawl outward from the homepage links.\
                 Status code=" + str(status_code)



#used to make crawler more innocuous
#https://stackoverflow.com/questions/13055208/httperror-http-error-403-forbidden
hdr = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201'}

def parse_base_url(url):
    ''' Takes a full url and spits out the base url ie facebook.com '''
    parsed_uri = urlparse(url)
    baseURL = str('{uri.netloc}'.format(uri=parsed_uri))
    if baseURL:
        if len(baseURL) > 4:
            if baseURL[:4] == 'www.':
                baseURL = baseURL[4:]
    print("parsing of " + baseURL + " successful")

    return baseURL



def link_crawler(url):
    ''' Crawls through normal html pages for links and creates a list of results. '''
    link_list = []
    edges = pd.DataFrame(columns = ['src','dst'])
    #this needs more elaborate try except wrt to the error messages bc some errors are fine?
    img_list = ['.png','.jpg','jpeg']
    if url[-4:] not in img_list:
        try:
            #make requests
            base_url = parse_base_url(url)
            req = Request(url,headers=hdr)
            html_page = urlopen(req)
            soup = BeautifulSoup(html_page, 'html.parser')
            print("crawling "+ url)

            #get all links
            for link in soup.findAll('a'):
                link_list.append(link.get('href'))
                base_link = parse_base_url(link.get('href'))
                if len(base_url) and len(base_link) > 4:
                    edges.loc[len(edges) + 1] = [base_url, base_link]

        except HTTPError as err:
            print("ERRORRRRRRRR")
            print(err)
            pass
        #this is why it was showing up Nones on the graph bc it attaches this blank list
    return link_list, edges


def hops_link_crawler(full_source_URL, hop_1_limit, hop_2_limit):
    ''' Crawls over lists of html sites and collects links. '''
    link_list, __ = link_crawler(full_source_URL)
    link_list_hop_2 = []
    edges = pd.DataFrame(columns = ['src','dst'])
    for link in link_list:
      if len(link_list_hop_2) < hop_2_limit:
        try:
          new_list, new_edges = link_crawler(link)
          edges = edges.append(new_edges)
          link_list_hop_2 = link_list_hop_2 + new_list
        except:
          pass

    return link_list, link_list_hop_2, edges

def link_parser(full_source_URL, hop_1_limit, hop_2_limit):
    ''' Decides if site has XML sitemap or not. Crawls through xml or html to find links. 2 hops. '''
    full_source_XML_URL = full_source_URL + "/sitemap.xml"
    print(full_source_XML_URL)
    try:
        req = Request(full_source_XML_URL, headers=hdr)
        html_page = urlopen(req).read()

        # this first crawl is just an xml map of xml maps basically. not links yet.
        xml_list_hop_1 = []
        soup = BeautifulSoup(html_page, 'xml')
        for url in soup.find_all('loc'):
            xml_list_hop_1.append(url.text)

        edges = pd.DataFrame(columns = ['src','dst'])
        for xml_link in xml_list_hop_1:
            try:
                html_page = urlopen(xml_link).read()
                soup = BeautifulSoup(html_page,'xml')

                #this hop has some actual links but it's still on an xml map
                xml_list_hop_2 = []
                for url in soup.find_all('loc'):
                    #this can get unwieldy quickly. controlling number of sites.
                    if len(xml_list_hop_2) < hop_1_limit:
                        xml_list_hop_2.append(url.text)
                print("len of xml hop 2 (first real links)")
                print(len(xml_list_hop_2))

                #this hop is really the second hop (re incongruence below) but it's the first actual html pages.
                xml_list_hop_3 = []
                for url in xml_list_hop_2:
                    if len(xml_list_hop_3) < hop_2_limit:
                        try:
                            base_url = parse_base_url(url)
                            new_links, unwanted_edges = link_crawler(url)
                            try:
                                xml_list_hop_3 = xml_list_hop_3 + new_links
                                for link in new_links:
                                    base_link = parse_base_url(link)
                                    if len(base_url) and len(base_link) > 4:
                                        edges.loc[len(edges) + 1] = [base_url, base_link]
                            except Exception as e:
                                print(e)
                                print(traceback.format_exc())
                                pass
                        except Exception as e:
                            print(e)
                            print(traceback.format_exc())
                            pass

                return(xml_list_hop_2, xml_list_hop_3, edges)
            except:
                # this is because sometimes there is an xml map but it's worthless
                # this also seems not to be following the link limits?
                # or mb following them wrong hop?
                return hops_link_crawler(full_source_URL, hop_1_limit, hop_2_limit)

    except HTTPError as err:
        print("HTTP ERROR CRAWLING REGULAR URLS" + str(err))
        return hops_link_crawler(full_source_URL, hop_1_limit, hop_2_limit)




def make_summed_base_URL_df(url_list, num_of_URLs_graphed, graph_source_URL, sourceBaseURL):
    ''' Creates a dictionary of base urls and uses it to count frequency. '''
    URL_dict = defaultdict(int)
    for url in url_list:
        baseURL = parse_base_url(url)

        if baseURL:
            if len(baseURL) > 4:
                if baseURL[:4] == 'www.':
                    baseURL = baseURL[4:]

                if graph_source_URL == 'no':
                    if baseURL != sourceBaseURL:
                        URL_dict[baseURL] += 1

                else:
                    URL_dict[baseURL] += 1


    top_URLs = heapq.nlargest(
        int(num_of_URLs_graphed),
        URL_dict,
        key=URL_dict.get)  # gets highest URLs

    URLs_ranked = {}  # makes dictionary of just highest ones
    for url in top_URLs:
        URLs_ranked[url] = URL_dict[url]

    df = pd.DataFrame.from_dict(URLs_ranked,
                                      orient='index',
                                      columns=['URL Frequency'])


    return df


def format_chart_data(df):
    new_df = df.reset_index()
    new_df.rename(columns={'index': 'URL', 'URL Frequency': 'URL Frequency'}, inplace=True)
    # sns.set(style="whitegrid")
    # ax = sns.barplot(x="URL Frequency", y='URL', data=new_df).set_title('Frequency of links on ' + sourceBaseURL)
    return new_df


def create_chart(dataframe, sourceBaseURL):  # : DataFrame #-> Chart
    """Make a chart."""
    return alt.Chart(dataframe.reset_index(),
                     title=('Frequency of links on ' + sourceBaseURL)).mark_bar().encode(
                         x='sum(URL Frequency):Q',
                         y=alt.Y(
                             'index:N',
                             sort=alt.EncodingSortField(
                                 field='URL Frequency',  # The field to use for the sort
                                 op="sum",  # The operation to run on the field prior to sorting
                                 order="descending"),  # The order to sort in
                             title='URLs')) #.configure_mark(color='#00035b')

# def create_chart(df, sourceBaseURL):
#     new_df = df.reset_index()
#     new_df.rename(columns={'index': 'URL', 'URL Frequency': 'URL Frequency'}, inplace=True)
#     sns.set(style="whitegrid")
#     ax = sns.barplot(x="URL Frequency", y='URL', data=new_df).set_title('Frequency of links on ' + sourceBaseURL)
#     return ax
