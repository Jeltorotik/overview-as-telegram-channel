from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

import time
import sys
import logging

import parser
import utils

args   = utils.parse_arguments()
config = utils.parse_config(args.config)

logging.basicConfig(
    filename = 'overview.log',
    level=logging.INFO, 
    format= '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

overview_db = utils.OverView_db(config['overview'])

parser_config = config['parser']

driver = webdriver.Firefox()
driver.get(parser_config['daily_url'])

soup = BeautifulSoup(driver.page_source, 'lxml')

total_posts = []

posts = []
for content_html in soup.findAll('div', class_='daily__OverviewContent-sc-7emf19-4 ebZhgG'):
    post = parser.parse_post_body_from_html(content_html)

    posts.append(post)


links = []
for link_html in soup.findAll('div', class_='daily__OverviewImg-sc-7emf19-5 eAIJgU'):
    url_without_params, url_with_proper_params = parser.parse_link_from_html(link_html, parser_config['img_params'])

    path_to_image, epoch_id = parser.get_link_info(url_without_params, parser_config['img_storage'])

    links.append({
        "path_to_image": path_to_image,
        "epoch_id":      int(epoch_id)
    })
    logging.info('going to sleep 3 secs')
    time.sleep(3)

if(len(links) == len(posts)):
    for i in range(0, len(links)):
        post = {**(posts[i]), **(links[i])}
        total_posts.append(post)
        logging.info("succesfully processed " + len(posts) + ' posts')
else:
    logging.error('length of links and length of posts are not equal, url: ' + driver.current_url)

epoch_id = [x['epoch_id'] for x in total_posts]
not_parsed_posts_epoch_id = overview_db.get_not_parsed_posts_epoch_id(epoch_id)
if len(not_parsed_posts_epoch_id) == 0:
    logging.warn('No new posts found')
    sys.exit()

not_parsed_posts = [post for post in total_posts if post['epoch_id'] in not_parsed_posts_epoch_id]
overview_db.add_posts(not_parsed_posts)
