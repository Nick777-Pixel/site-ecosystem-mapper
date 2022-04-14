import streamlit as st
from src.tools.xml_crawler import link_parser, check_status, make_summed_base_URL_df, format_chart_data, create_chart
from src.utils import build_download_link
import graphistry
import pandas as pd
import traceback

#heroku/streamlit/gitlab
#https://gilberttanner.com/blog/deploying-your-streamlit-dashboard-with-heroku
# secrets https://gitlab.com/smat-project/<REPOSITORY-NAME>/-/settings/ci_cd

#to look into later
# https://github.com/TeamHG-Memex/autopager
# https://github.com/TeamHG-Memex/Formasaurus
# https://github.com/TeamHG-Memex/undercrawler


#BUG and TO-DO LIST:
#more elaborate error handling for xml check bc some errors are okay.
#hop 2 at 10k sometimes returns none after a long wait?
#for xml second error condition not following hop len limits?
# add option for third hop for both network graph and
#make this based on number of sites crawled v length of list.
# st.progress() or #with st.spinner("Running query...")
# why for some sites is the number of second hop and the graphistry nodes wayyyy bigger than
# the number of graphed entities
# also is there any way to make the data frame have everything for the csv instead of just the top n?


st.title('Site Ecosystem Mapper')
st.header('Link crawler')
st.markdown(
"This app takes a base url from a site and uses it to crawl all\
 the pages and graphs the external links. This can help \
 determine what media ecosystem a site is a part of especially in studying\
  disinformation or conspiracies. It may take a \
 while if there are a lot of links but you'll see the running logo in the top.\
 This project is a part of the Social Media Analysis Toolkit or [Appmuno](https://appmuno.com/)."
 )



sourceBaseURL = st.text_input("site (use format: 'thegrayzone.com')", value='thegrayzone.com')
st.markdown('The starting URL often has many more links than any other which can skew the graphs.')
graph_source_URL = st.radio("Include starting URL in graph?", ('no', 'yes'))
st.markdown("This app starts with a URL then crawls outward from the links on the starting point.\
 A hop is each new level of links it starts crawling. The higher these limits, the more results you'll \
have, but also the more time it will take to crawl everything looking for links.")
hop_1_limit = st.slider("Hop 1 limit:", min_value=5, max_value = 100, value = 30)
hop_2_limit = st.slider("Hop 2 limit:", min_value=25, max_value = 10000, value = 500)
num_of_URLs_graphed = st.slider("Number of sites to graph:", min_value=5, max_value = 50, value = 25)
st.markdown("If you have a Graphistry 1.0 API key, you can use this app to make beautiful interactive network graphs as well!")
graphistry_API_key = st.text_input("Graphistry API Key:", value='')
st.markdown(check_status(sourceBaseURL))

full_source_URL = "https://" + sourceBaseURL

# if len(sourceBaseURL) > 2: #something like this to prevent an error on
link_list, link_list_hop_2, edges = link_parser(full_source_URL, hop_1_limit, hop_2_limit)

#eventually make a number of hops feature and a network map of one more hop?


st.markdown("Length of hop 1: " + str(len(link_list)))
st.markdown("Length of hop 2: " + str(len(link_list_hop_2)))

try:
    graphistry.register(graphistry_API_key, api=2)
    print('Graphistry API Connection - OK')
    print('\n✨ Graphistry API Connection - OK')
    g = graphistry.bind(source="src", destination="dst", node = "dst", point_label= "dst").nodes(edges).edges(edges) #node="dst",
    plot = g.settings(url_params={'play': 1000, 'bg': '%230a0a0a'}).plot(render=False)
    iframe = '<iframe src="' + plot + '", height="800", width="100%"></iframe>'
    st.markdown(iframe, unsafe_allow_html=True)
except Exception as ex:
    print(ex)
    print(traceback.format_exc())
    print("problem var")
    st.markdown('Network graph not available without Graphistry API key.')


df = make_summed_base_URL_df(link_list_hop_2,num_of_URLs_graphed, graph_source_URL, sourceBaseURL)


#change to using altair for more customizability
# st.bar_chart(df)
st.altair_chart(create_chart(df, sourceBaseURL))


build_download_link(
                    st,
                    filename="site_ecosystem_mapper.csv",
                    df=df.reset_index(),
                )


st.table(df)








# st.markdown("Notes: Currently this app is only mapping the first xml file in the sitemap because it can quickly become a huge search.")
