#!/usr/bin/env python
# coding: utf-8

# In[1]:


import math
import argparse
import linecache
from collections import Counter
import time
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import re

import re
import heapq
import os
import sys
import time
import xml.sax
from nltk.corpus import stopwords
from nltk.stem.porter import *
from collections import defaultdict


# In[2]:


'''
This class traverses various index files and return the required data
'''
class FileTraverser():

    def __init__(self):

        pass

    def binary_search_token_info(self, high, filename, inp_token):
        
        low = 0
        while low < high:
            
            mid = (low + high)//2
            line = linecache.getline(filename, mid)
            token = line.split('-')[0]

            if inp_token == token:
                token_info = line.split('-')[1:-1]
                return token_info
            
            elif inp_token > token:
                low = mid + 1
            
            else:
                high = mid

        return None

    def title_search(self, page_id):

        title = linecache.getline('hindi_wiki_index/id_title_map.txt', int(page_id)+1).strip()
        title = title.split('-', 1)[1]

        return title


    def search_field_file(self, field, file_num, line_num):
        
        if line_num != '':
            line = linecache.getline(f'hindi_wiki_index/{field}_data_{str(file_num)}.txt', int(line_num)).strip()
            postings = line.split('-')[1]

            return postings

        return ''

'''
This class implements the ranking functionality on the returned postings.
'''
class Ranker():

    def __init__(self, num_pages):

        self.num_pages = num_pages

    def do_ranking(self, page_freq, page_postings):
        
        result = defaultdict(float)
        weightage_dict = {'title':1.0, 'body':0.6, 'category':0.4, 'infobox':0.75, 'link':0.20, 'reference':0.25}
        
        for token, field_post_dict in page_postings.items():
            
            for field, postings in field_post_dict.items():
                
                weightage = weightage_dict[field]
                
                if len(postings)>0:
                    for post in postings.split(';'):
                        
                        id, post = post.split(':')
                        result[id] += weightage*(1+math.log(int(post)))*math.log((self.num_pages-int(page_freq[token]))/int(page_freq[token]))

        return result

class TextPreProcessor():

    def __init__(self, html_tags, stem_words, stop_words):
        
        self.html_tags=html_tags
        self.stem_words=stem_words
        self.stop_words=stop_words

    def remove_stopwords(self, text_data):
        
        cleaned_text = [word for word in text_data if word not in self.stop_words]
        
        return cleaned_text

    def stem_word(self, word):

        for wrd in self.stem_words:
            if word.endswith(wrd):
                word = word[:-len(wrd)]
                return word

        return word

    def stem_text(self, text_data):
        
        cleaned_text = [self.stem_word(word) for word in text_data]
        
        return cleaned_text

    def remove_html_tags(self, text_data):
        
        cleaned_text = re.sub(self.html_tags, ' ', text_data)
        
        return cleaned_text

    def remove_special_chars(self, text_data):
        
        cleaned_text = ''.join(ch if ch.isalnum() else ' ' for ch in text_data)
        
        return cleaned_text

    def remove_select_keywords(self, text_data):
        
        text_data = text_data.replace('\n', ' ').replace('File:', ' ')
        text_data = re.sub('(http://[^ ]+)', ' ', text_data)
        text_data = re.sub('(https://[^ ]+)', ' ', text_data)
        
        return text_data

    def tokenize_sentence(self, text_data, flag=False):
        
        if flag:
            text_data = self.remove_select_keywords(text_data)
            text_data = re.sub('\{.*?\}|\[.*?\]|\=\=.*?\=\=', ' ', text_data)
        cleaned_text = self.remove_html_tags(text_data)
        cleaned_text = self.remove_special_chars(cleaned_text)
        
        return cleaned_text.split()

    def preprocess_text(self, text_data, flag=False):

        cleaned_data = self.tokenize_sentence(text_data.lower(), flag)
        cleaned_data = self.remove_stopwords(cleaned_data)
        cleaned_data = self.stem_text(cleaned_data)
        
        return cleaned_data


'''
This class takes query as input and returns the corresponding postings along with theis fields
'''
class QueryResults():

    def __init__(self, file_traverser):

        self.file_traverser = file_traverser

    def simple_query(self, preprocessed_query, num_tokens, tokens_info_pointer):

        page_freq, page_postings = {}, defaultdict(dict)
        
        char_list = [chr(i) for i in range(97,123)]
        for token in preprocessed_query:
            
            token_info = self.file_traverser.binary_search_token_info(num_tokens, tokens_info_pointer, token)

            if token_info:
                file_num, freq, title_line, body_line, category_line, infobox_line, link_line, reference_line = token_info
                line_map = {
                        'title' : title_line, 'body' : body_line, 'category' : category_line, 'infobox' : infobox_line, 'link' : link_line, 'reference' : reference_line
                    }

                for field_name, line_num in line_map.items():
                    
                    if line_num!='':
                        posting = self.file_traverser.search_field_file(field_name, file_num, line_num)

                        page_freq[token] = len(posting.split(';'))
                        page_postings[token][field_name] = posting

        return page_freq, page_postings


    def field_query(self, preprocessed_query_final, num_tokens, tokens_info_pointer):

        page_freq, page_postings = {}, defaultdict(dict)
        char_list = [chr(i) for i in range(97,123)]

        for field, token in preprocessed_query_final:

            token_info = self.file_traverser.binary_search_token_info(num_tokens, tokens_info_pointer, token)

            if token_info:
                
                file_num, freq, title_line, body_line, category_line, infobox_line, link_line, reference_line = token_info
                line_map = {
                    'title':title_line, 'body':body_line, 'category':category_line, 'infobox':infobox_line, 'link':link_line, 'reference':reference_line
                }
                field_map = {
                    't':'title', 'b':'body', 'c':'category', 'i':'infobox', 'l':'link', 'r':'reference'
                }

                field_name = field_map[field]
                line_num = line_map[field_name]

                posting = self.file_traverser.search_field_file(field_name, file_num, line_num)

                page_freq[token] = len(posting)
                page_postings[token][field_name] = posting

        return page_freq, page_postings


'''
This class runs the above functions to implement search and ranking and returns the required results.
'''	
class RunQuery():

    def __init__(self, text_pre_processor, file_traverser, ranker, query_results):

        self.file_traverser = file_traverser
        self.text_pre_processor = text_pre_processor
        self.ranker = ranker
        self.query_results = query_results

    def identify_query_type(self, query):
        
        field_replace_map = {
                ' t:':';t:',
                ' b:':';b:',
                ' c:':';c:',
                ' i:':';i:',
                ' l:':';l:',
                ' r:':';r:',
            }

        if ('t:' in query or 'b:' in query or 'c:' in query or 'i:' in query or 'l:' in query or 'r:' in query) and query[0:2] not in ['t:', 'b:', 'i:', 'c:', 'r:', 'l:']:

            for k, v in field_replace_map.items():
                if k in query:
                    query = query.replace(k, v)

            query = query.lstrip(';')

            return query.split(';')[0], query.split(';')[1:]

        elif 't:' in query or 'b:' in query or 'c:' in query or 'i:' in query or 'l:' in query or 'r:' in query:

            for k, v in field_replace_map.items():
                if k in query:
                    query = query.replace(k, v)

            query = query.lstrip(';')

            return query.split(';'), None

        else:
            return query, None

    def return_query_results(self, query, query_type, num_tokens, tokens_info_pointer):

        if query_type=='field':
            preprocessed_query = [[qry.split(':')[0], self.text_pre_processor.preprocess_text(qry.split(':')[1])] for qry in query]
        else:
            preprocessed_query = self.text_pre_processor.preprocess_text(query)

        if query_type == 'field':

            preprocessed_query_final = []
            for field, words in preprocessed_query:
                for word in words:
                    preprocessed_query_final.append([field, word])

            page_freq, page_postings = self.query_results.field_query(preprocessed_query_final, num_tokens, tokens_info_pointer)
        
        else:
            
            page_freq, page_postings = self.query_results.simple_query(preprocessed_query, num_tokens, tokens_info_pointer)

        ranked_results = self.ranker.do_ranking(page_freq, page_postings)

        return ranked_results

    def take_input_from_file(self, file_name, num_results, num_tokens, tokens_info_pointer):
        results_file = file_name.split('.txt')[0]

        with open(file_name, 'r') as f:
            fp = open(results_file+'_op.txt', 'w')
            for i, query in enumerate(f):
                s = time.time()

                query = query.strip()
                query1, query2 = self.identify_query_type(query)

                if query2:
                    ranked_results1 = self.return_query_results(query1, 'simple', num_tokens, tokens_info_pointer)

                    ranked_results2 = self.return_query_results(query2, 'field', num_tokens, tokens_info_pointer)

                    ranked_results = Counter(ranked_results1) + Counter(ranked_results2)
                    results = sorted(ranked_results.items(), key = lambda item : item[1], reverse=True)
                    results = results[:num_results]

                    if results:
                        for id, _ in results:
                            title= self.file_traverser.title_search(id)
                            fp.write(id + ', ' + title)
                            fp.write('\n')
                    else:
                        fp.write('No matching Doc found')
                        fp.write('\n')

                elif type(query1)==type([]):

                    ranked_results = self.return_query_results(query1, 'field', num_tokens, tokens_info_pointer)

                    results = sorted(ranked_results.items(), key = lambda item : item[1], reverse=True)
                    results = results[:num_results]

                    if results:
                        for id, _ in results:
                            title= self.file_traverser.title_search(id)
                            fp.write(id + ', ' + title)
                            fp.write('\n')
                    else:
                        fp.write('No matching Doc found')
                        fp.write('\n')

                else:
                    ranked_results = self.return_query_results(query1, 'simple', num_tokens, tokens_info_pointer)

                    results = sorted(ranked_results.items(), key = lambda item : item[1], reverse=True)
                    results = results[:num_results]

                    if results:
                        for id, _ in results:
                            title= self.file_traverser.title_search(id)
                            fp.write(id + ', ' + title)
                            fp.write('\n')
                    else:
                        fp.write('No matching Doc found')
                        fp.write('\n')
                e = time.time()
                fp.write('Finished in ' + str(e-s) + ' seconds')
                fp.write('\n\n')

                print('Done query', i+1)

            fp.close()

        print('Done writing results')

    def take_input_from_user(self, query, num_results, num_tokens, tokens_info_pointer):

        start = time.time()

#             query = input('Enter Query:- ')

        s = time.time()
        query = query.strip()
        if query=='close':
            return

        query = transliterate(query, sanscript.ITRANS, sanscript.DEVANAGARI)
        query1, query2 = self.identify_query_type(query)

        if query2:
            ranked_results1 = self.return_query_results(query1, 'simple', num_tokens, tokens_info_pointer)

            ranked_results2 = self.return_query_results(query2, 'field', num_tokens, tokens_info_pointer)

            ranked_results = Counter(ranked_results1) + Counter(ranked_results2)
            results = sorted(ranked_results.items(), key = lambda item : item[1], reverse=True)
            results = results[:num_results]

            for id, _ in results:
                title= self.file_traverser.title_search(id)
                link = ('https://hi.wikipedia.org/wiki/'+ title).replace(' ', '_')
                print(id+',', title+ '  ' +  link  )

        elif type(query1)==type([]):

            ranked_results = self.return_query_results(query1, 'field', num_tokens, tokens_info_pointer)

            results = sorted(ranked_results.items(), key = lambda item : item[1], reverse=True)
            results = results[:num_results]

            for id, _ in results:
                title= self.file_traverser.title_search(id)
                link = ('https://hi.wikipedia.org/wiki/'+ title).replace(' ', '_')
                print(id+',', title+ '  ' +  link  )

        else:
            ranked_results = self.return_query_results(query1, 'simple', num_tokens, tokens_info_pointer)

            results = sorted(ranked_results.items(), key = lambda item : item[1], reverse=True)
            results = results[:num_results]

            for id, _ in results:
                title= self.file_traverser.title_search(id)
                link = ('https://hi.wikipedia.org/wiki/'+ title).replace(' ', '_')
                print(id+',', title+ '  ' +  link  )

#         e = time.time()
#         print('Finished in', e-s, 'seconds')
#         print()
        return


# In[3]:


def run_hindi_search(query, num_results):
    start = time.time()

    file_name = None
    num_results = 10

    # print('Loading search engine ')
    html_tags = re.compile('&amp;|&apos;|&gt;|&lt;|&nbsp;|&quot;')
    with open('hindi_stopwords.txt', 'r', encoding='utf8') as f:
        stop_words = [word.strip() for word in f]

    with open('hindi_stem_words.txt', 'r',encoding='utf8') as f:
        stem_words = [word.strip() for word in f]

    with open('hindi_wiki_index/num_pages.txt', 'r',encoding='utf8') as f:
        num_pages = float(f.readline().strip())

    with open('hindi_wiki_index/num_tokens.txt', 'r',encoding='utf8') as f:
        num_tokens = int(f.readline().strip())

    tokens_info_pointer = 'hindi_wiki_index/tokens_info.txt'
    text_pre_processor = TextPreProcessor(html_tags, stem_words, stop_words)
    file_traverser = FileTraverser()
    ranker = Ranker(num_pages)
    query_results = QueryResults(file_traverser)
    run_query = RunQuery(text_pre_processor, file_traverser, ranker, query_results)

    temp = linecache.getline('hindi_wiki_index/id_title_map.txt', 0)

    # print('Loaded in', time.time() - start, 'seconds')

    # print('Starting Querying')

    # start = time.time()

    if file_name is not None:

        run_query.take_input_from_file(file_name, num_results, num_tokens, tokens_info_pointer)

    else:
        run_query.take_input_from_user(query, num_results, num_tokens, tokens_info_pointer)
#     print('Done')
    return
    # print('Done querying in', time.time() - start, 'seconds')


# In[ ]:




