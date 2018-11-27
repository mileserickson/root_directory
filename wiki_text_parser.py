from bs4 import BeautifulSoup as bs
from bson.objectid import ObjectId
from urllib.parse import unquote
import subprocess
import os
import sys
import mwparserfromhell
import re
import json
from timeit import default_timer as timer
from multiprocessing import Pool 
import tqdm 
from itertools import chain
from functools import partial
import pandas as pd
import numpy as np
import glob
from pymongo import MongoClient
from gensim.corpora import wikicorpus


def mongodb_page_stream(db_name, collection_name):
    """yield a new page from a mongodb collection"""
    mc = MongoClient()
    db = mc[db_name]
    collection = db[collection_name]
    document_generator = collection.find()
    return document_generator

def parse_update_database(db_name, collection_name):
    """parse and update a mongodb database with cleaned xml"""
    document_generator = mongodb_page_stream(db_name, collection_name)
    for document in document_generator:
        yield parse_page(document)

 # Find math content:
re_math = re.compile(r'<math([> ].*?)(</math>|/>)', re.DOTALL|re.UNICODE)
# Find all other tags:
re_all_tags = re.compile(r'<(.*?)>', re.DOTALL|re.UNICODE)
# Find category markup:
re_categories = re.compile(r'\[\[([cC]ategory:[^][]*)\]\]', re.UNICODE) 
# rm File and Image templates:
re_rm_file_image = re.compile(r'\[\[([fF]ile:|[iI]mage)[^]]*(\]\])', re.UNICODE)
# Capture interlinks text and article linked:
re_interlinkstext_link = re.compile(r'\[{2}(.*?)\]{2}', re.UNICODE)
# Simplify links, keep description:
re_simplify_link = re.compile(r'\[([^][]*)\|([^][]*)\]', re.DOTALL|re.UNICODE)
# Keep image Description:
re_image_description = re.compile(r'\n\[\[[iI]mage(.*?)(\|.*?)*\|(.*?)\]\]', re.UNICODE)
# Keep file descirption:
re_file_description = re.compile(r'\n\[\[[fF]ile(.*?)(\|.*?)*\|(.*?)\]\]', re.UNICODE)
# External links:
re_external_links = re.compile(r'<nowiki([> ].*?)(</nowiki>|/>)', re.DOTALL|re.UNICODE)

    
def parse_page(document):
    """parse the xml of a mondodb document"""
    # grab the raw xml from the document
    xml = document['full_raw_xml']
    # extract links from xml
    links = get_links(xml)
    # extract image text from xml
    image_desc = clean_image_desc(xml)
    # extract file text from xml
    file_desc = clean_file_desc(xml)
    # extract the categories
    categories = re_categories.findall(xml)
    # clean xml of category information
    clean_xml = replace_categories_in_xml(xml, categories)
    # clean categories of Category: links
    cleaned_links = clean_links_list(links)
    # make BeautifulSoup object from cleaned xml
    soup = bs(clean_xml, 'lxml')
    # extract the title out
    page_title = soup.select_one('title').text
    # extract the timestamp
    timestamp = soup.select_one('timestamp').text
    # extract headers
    headers = get_headers(soup.text)
    markup_text = soup.select_one('text').text
    return headers
    remove_markup = mwparserfromhell.parse(wikicorpus.remove_markup(markup_text)).strip_code()
    remove_markup = remove_markup.replace('\n','')
    strip_code = mwparserfromhell.parse(markup_text).strip_code()
    return {'timestamp': timestamp, 'strip_code': strip_code, 'xml': xml, 'soup': soup.text, 'remove_markup': remove_markup, 'clean_links':cleaned_links, 'categories': {page_title: categories} ,}

    # math = re_math.findall(markup_text)
    return file_desc
    return links
    return unquoted_links
    return {'parent_categories': {page_title: categories},}

def get_links(xml):
    links = re_interlinkstext_link.findall(xml)
    clean_links = []
    for link in links:
        if '|' in link:
            clean_links.append(link.partition('|')[0])
        else: 
            clean_links.append(link)
    return clean_links

def clean_image_desc(xml):
    image_desc = re_image_description.findall(xml)
    if image_desc != []:
        image_desc = ' '.join(image_desc[0][2:])
        image_desc = wikicorpus.remove_markup(image_desc)
    return image_desc

def clean_file_desc(xml):
    file_desc = re_file_description.findall(xml)
    if file_desc != []:
        file_desc = ' '.join(file_desc[0][1:])[1:]
        file_desc = wikicorpus.remove_markup(file_desc)
    return file_desc

def replace_categories_in_xml(xml, categories):
    for category in categories:
        cleaned_xml = xml.replace(category, ' ')
    return cleaned_xml

def clean_links_list(links_list):
    clean_links = []
    for link in links_list:
        if 'File:' not in link and \
           'Category:' not in link and \
           'Wikipedia:' not in link and \
           'en:' not in link and \
           'Image:' not in link:
            clean_links.append(link)
    return clean_links

def get_headers(text):
    headers = []
    lines = text.split('\n')
    for line in lines:
        if line.startswith('='):
            header = line.replace('=', '').strip()
            headers.append(mwparserfromhell.parse(header).strip_code())
    return headers

def update_document():
    pass


def _identify_page(self, raw_xml):
    """Indentify whether or not article is in self.titles_to_find"""
    # Find math content:
    re_math = re.compile(r'<math([> ].*?)(</math>|/>)', re.DOTALL|re.UNICODE)
    # Find all other tags:
    re_all_tags = re.compile(r'<(.*?)>', re.DOTALL|re.UNICODE)
    # Find category markup:
    re_categories = re.compile(r'\[\[Category:[^][]*\]\]', re.UNICODE)
    # rm File and Image templates:
    re_rm_file_image = re.compile(r'\[\[([fF]ile:|[iI]mage)[^]]*(\]\])', re.UNICODE)
    # Capture interlinks text and article linked:
    re_interlinkstext_link = re.compile(r'\[{2}(.*?)\]{2}', re.UNICODE)
    # Simplify links, keep description:
    re_simplify_link = re.compile(r'\[([^][]*)\|([^][]*)\]', re.DOTALL|re.UNICODE)
    # Keep image Description:
    re_image_description = re.compile(r'\n\[\[[iI]mage(.*?)(\|.*?)*\|(.*?)\]\]', re.UNICODE)
    # Keep file descirption:
    re_file_description = re.compile(r'\n\[\[[fF]ile(.*?)(\|.*?)*\|(.*?)\]\]', re.UNICODE)
    # External links:
    re_external_links = re.compile(r'<nowiki([> ].*?)(</nowiki>|/>)', re.DOTALL|re.UNICODE)
    
    soup = bs(raw_xml, 'lxml')
    title = soup.select_one('title').text
    if title in self.titles_to_find:
        id_ = soup.select_one('id').text
        markup_text = soup.select_one('text').text
        #use regex to delete 'Category' tags and text from raw_xml
        cleaned_text = []
        kw = ('[[Category:', 'thumb')
        for line in markup_text.split('\n'):
            if line.startswith(kw):
                continue
            cleaned_text.append(line)
        categories = re_categories.findall(raw_xml)
        tags = re_all_tags.findall(raw_xml)
        file_desc = re_file_description.findall(raw_xml)
        if file_desc != []:
            file_desc = ' '.join(file_desc[0][1:])[1:]
            file_desc = wikicorpus.remove_markup(file_desc)
        image_desc = re_image_description.findall(raw_xml)
        if image_desc != []:
            image_desc = ' '.join(image_desc[0][2:])
            image_desc = wikicorpus.remove_markup(image_desc)
        external_links = re_external_links.findall(raw_xml)
        simple_links = re_simplify_link.findall(raw_xml)
        interlinks = re_interlinkstext_link.findall(raw_xml)
        math = wikicorpus.RE_P10.findall(markup_text)

        for category in categories:
            raw_xml = raw_xml.replace(category, ' ')
        timestamp = soup.select_one('timestamp').text
        wiki = mwparserfromhell.parse(markup_text)

        wikilinks = []
        for link in wiki.filter_wikilinks():
            link = link.strip('[]')
            if 'File:' not in link and \
            'Category:' not in link and \
                'Wikipedia:' not in link and \
                'en:' not in link and \
                'Image:' not in link:
                wikilinks.append(link)

        return {
            'title': title,
            'full_raw_xml': raw_xml,
            'target': self.target,
            }