#!/usr/bin/env python
# coding: utf-8

# In[21]:


import re
import heapq
import os
import sys
import time
import xml.sax
from nltk.corpus import stopwords
from nltk.stem.porter import *
from collections import defaultdict
from tqdm import tqdm
import argparse


# In[2]:


html_tags = re.compile('&amp;|&apos;|&gt;|&lt;|&nbsp;|&quot;')
stop_words = (set(stopwords.words("english")))
stemmer = PorterStemmer()
index_map = defaultdict(str)
page_no = 0
file_no = 0
id_to_title = {}


# In[3]:


def removeStopWords(text_data):
    
    text = [word for word in text_data if word not in stop_words]
    
    return text

def stem(text):
    
#     text = stemmer.stemWords(text)
    text = [stemmer.stem(w) for w in text]
    
    return text
def remove_non_ascii(text):
    text = ''.join([i if ord(i) < 128 else ' ' for i in text])
    return text
def remove_html_tags(text):
    text = re.sub(html_tags, ' ', text)
    return text
def remove_special_chars(text):
    
    text = ''.join(ch if ch.isalnum() else ' ' for ch in text)
    
    return text


# In[4]:


def tokenize(text, flag=False):

    if flag:
#         text = self.remove_select_keywords(text)
        text = re.sub('\{.*?\}|\[.*?\]|\=\=.*?\=\=', ' ', text)
    text = remove_non_ascii(text)
    text = remove_html_tags(text)
    text = remove_special_chars(text)

    return text.split()


# In[5]:


def preprocess_text(text, flag=False):

    text = tokenize(text.lower(), flag)
    text = remove_stopwords(text)
    text = stem(text)

    return text



# In[6]:


def extractTitle(text):

        data = tokenize(text)
        data = removeStopWords(data)
        data = stem(data)
        return data

def extractInfobox(text):

        data = text.split('\n')
        flag = 0
        info = []
        for line in data:
            if re.match(r'\{\{infobox', line):
                flag = 1
                info.append(re.sub(r'\{\{infobox(.*)', r'\1', line))
            elif flag == 1:
                if line == '}}':
                    flag = 0
                    continue
                info.append(line)

        data = tokenize(' '.join(info))
        data = removeStopWords(data)
        data = stem(data)
        return data

def extractReferences(text):

        data = text.split('\n')
        refs = []
        for line in data:
            if re.search(r'<ref', line):
                refs.append(re.sub(r'.*title[\ ]*=[\ ]*([^\|]*).*', r'\1', line))

        data = tokenize(' '.join(refs))
        data = removeStopWords(data)
        data = stem(data)
        return data
def extractCategories(text):
        
        data = text.split('\n')
        categories = []
        for line in data:
            if re.match(r'\[\[category', line):
                categories.append(re.sub(r'\[\[category:(.*)\]\]', r'\1', line))
        
        data = tokenize(' '.join(categories))
        data = removeStopWords(data)
        data = stem(data)
        return data
def extractExternalLinks(text):
        
        data = text.split('\n')
        links = []
        for line in data:
            if re.match(r'\*[\ ]*\[', line):
                links.append(line)
        
        data = tokenize(' '.join(links))
        data = removeStopWords(data)
        data = stem(data)
        return data
 
        data = removeStopWords(data)
        data = stem(data)
        return data

def extractBody( text):

        data = re.sub(r'\{\{.*\}\}', r' ', text)
        
        data = tokenize(data)
        data = removeStopWords(data)
        data = stem(data)
        return data


# In[7]:


def processText(text, title):
        
        text = text.lower() #Case Folding
        data = text.split('==references==')
        if len(data) == 1:
            data = text.split('== references == ')
        if len(data) == 1:
            references = []
            links = []
            categories = []
        else:
            references = extractReferences(data[1])
            links = extractExternalLinks(data[1])
            categories = extractCategories(data[1])
        info = extractInfobox(data[0])
        body = extractBody(data[0])
        title = extractTitle(title.lower())
    
        return title, body, info, categories, links, references


# In[8]:


class Handler(xml.sax.ContentHandler):
    
    def __init__(self):
        
        self.tag = ''
        self.title = ''
        self.text = ''
        
    def startElement(self,tag,a):
        self.tag=tag
        
    def characters(self, content):
        
        if self.tag == 'title':
            self.title += content

        if self.tag == 'text':
            self.text += content
    
    def endElement(self,name):
        
        if name=='page':
            
            print(page_no)
            tit = self.title.encode("ascii", errors="ignore").decode()
            title, body, category, infobox, link, reference = processText(tit, self.text)
            id_to_title[page_no]=tit.lower()
            create_index(title, body, category, infobox, link, reference)

            self.tag = ""
            self.title = ""
            self.text = ""


# In[9]:


def get_diff_postings(token, postings, final_tag):

        postings = sorted(postings.items(), key = lambda item : int(item[0]))

        final_posting = token+'-'
        for id, freq in postings:
            final_posting+=str(id)+':'+freq+';'

        final_tag.append(final_posting.rstrip(';'))

        return final_tag

def write_diff_postings(tag_type, final_tag, num_files_final):

    with open(f'english_wiki_index/{tag_type}_data_{str(num_files_final)}.txt', 'w') as f:
        f.write('\n'.join(final_tag))


# In[10]:


def write_final_files(data_to_merge, num_files_final):

        title_dict, body_dict, category_dict, infobox_dict, link_dict, reference_dict = defaultdict(dict), defaultdict(dict), defaultdict(dict), defaultdict(dict), defaultdict(dict), defaultdict(dict)

        unique_tokens_info = {}

        sorted_data = sorted(data_to_merge.items(), key = lambda item : item[0])

        for i, (token, postings) in enumerate(sorted_data):
            for posting in postings.split(';')[:-1]:

                id = posting.split(':')[0]

                fields = posting.split(':')[1]

                if 't' in fields:
                    title_dict[token][id] = re.search(r'.*t([0-9]*).*', fields).group(1)

                if 'b' in fields:
                    body_dict[token][id] = re.search(r'.*b([0-9]*).*', fields).group(1)

                if 'c' in fields:
                    category_dict[token][id] = re.search(r'.*c([0-9]*).*', fields).group(1)

                if 'i' in fields:
                    infobox_dict[token][id] = re.search(r'.*i([0-9]*).*', fields).group(1)

                if 'l' in fields:
                    link_dict[token][id] = re.search(r'.*l([0-9]*).*', fields).group(1)

                if 'r' in fields:
                    reference_dict[token][id] = re.search(r'.*r([0-9]*).*', fields).group(1)

            token_info = '-'.join([token, str(num_files_final), str(len(postings.split(';')[:-1]))])
            unique_tokens_info[token] = token_info+'-'

        final_titles, final_body_texts, final_categories, final_infoboxes, final_links, final_references = [], [], [], [], [], []

        for i, (token, _) in enumerate(sorted_data):

            if token in title_dict.keys():
                posting = title_dict[token]
                final_titles = get_diff_postings(token, posting, final_titles)
                t = len(final_titles)
                unique_tokens_info[token]+=str(t)+'-'
            else:
                unique_tokens_info[token]+='-'

            if token in body_dict.keys():
                posting = body_dict[token]
                final_body_texts = get_diff_postings(token, posting, final_body_texts)
                t = len(final_body_texts)
                unique_tokens_info[token]+=str(t)+'-'
            else:
                unique_tokens_info[token]+='-'

            if token in category_dict.keys():
                posting = category_dict[token]
                final_categories = get_diff_postings(token, posting, final_categories)
                t = len(final_categories)
                unique_tokens_info[token]+=str(t)+'-'
            else:
                unique_tokens_info[token]+='-'

            if token in infobox_dict.keys():
                posting = infobox_dict[token]
                final_infoboxes = get_diff_postings(token, posting, final_infoboxes)
                t = len(final_infoboxes)
                unique_tokens_info[token]+=str(t)+'-'
            else:
                unique_tokens_info[token]+='-'

            if token in link_dict.keys():
                posting = link_dict[token]
                final_links = get_diff_postings(token, posting, final_links)
                t = len(final_links)
                unique_tokens_info[token]+=str(t)+'-'
            else:
                unique_tokens_info[token]+='-'

            if token in reference_dict.keys():
                posting = reference_dict[token]
                final_references = get_diff_postings(token, posting, final_references)
                t = len(final_references)
                unique_tokens_info[token]+=str(t)+'-'
            else:
                unique_tokens_info[token]+='-'

        with open(f'english_wiki_index/tokens_info.txt', 'a') as f:
            f.write('\n'.join(unique_tokens_info.values()))
            f.write('\n')

        write_diff_postings('title', final_titles, num_files_final)

        write_diff_postings('body', final_body_texts, num_files_final)

        write_diff_postings('category', final_categories, num_files_final)

        write_diff_postings('infobox', final_infoboxes, num_files_final)

        write_diff_postings('link', final_links, num_files_final)

        write_diff_postings('reference', final_references, num_files_final)

        num_files_final+=1

        return num_files_final


# In[11]:


def merge_files(filecount):
    files = {}
    lines = {}
    postings = {}
    open_files = [0]*filecount
    top_words = []
    
    for i in range(filecount):
        files[i] = open(f'english_wiki_index/index_{i}.txt', 'r')
        lines[i] = files[i].readline().strip('\n')
        postings[i] = lines[i].split('-')
        open_files[i] = 1
        token = postings[i][0]
        
        if token not in top_words:
            heapq.heappush(top_words,token)
    
    num_files = 0
    num_processed_postings = 0
    merge_data = defaultdict(str)
    
    while any(open_files) == 1:
        token = heapq.heappop(top_words)
        num_processed_postings+=1
        
        if num_processed_postings%30000==0:
            num_files = write_final_files(merge_data, num_files)
            merge_data = defaultdict(str)
            
        i=0
        while i < filecount:
            
            if open_files[i] == 1:
                
                if postings[i][0] == token:
                    merge_data[token]+=(postings[i][1])
                    lines[i] = files[i].readline().strip('\n')
                    
                    if len(lines[i]):
                        postings[i]=lines[i].split('-')
                        new_token = postings[i][0]
                        
                        if new_token not in top_words:
                            heapq.heappush(top_words, new_token)
                    else:
                        open_files[i] = 0
                        files[i].close()
                        print(f'Removing file {str(i)}')
                        os.remove(f'english_wiki_index/index_{str(i)}.txt')
                        
            i += 1
    num_files = write_final_files(merge_data, num_files)
    return num_files    


# In[12]:


def write_inter():
    global file_no
    temp_index = sorted(index_map.items() , key = lambda item : item[0])
    
    res = []
    for word, post in temp_index:
        t = word+"-"+post
        res.append(t)
    with open(f'english_wiki_index/index_{file_no}.txt','w') as f:
        f.write('\n'.join(res))
    file_no += 1
#     if(file_no == 10):
#         merge_files(file_no)


# In[13]:


def write_id_title():
    temp_map = sorted(id_to_title.items(),key = lambda item: int(item[0]))
    res = []
    for id, title in temp_map:
        t = str(id)+'-'+title.strip()
        res.append(t)
        
    with open(f"english_wiki_index/id_title_map.txt", 'a') as f:
            f.write('\n'.join(res))
            f.write('\n')


# In[14]:


def create_index(title, body, category, infobox, link, reference):
    global page_no
    global index_map
    
    unique_words = set()
    
    title_dict = defaultdict(int)
    for w in title:
        title_dict[w] += 1
    
    body_dict = defaultdict(int)
    for w in body:
        body_dict[w] += 1
    
    category_dict = defaultdict(int)
    for w in category:
        category_dict[w] += 1
        
    infobox_dict = defaultdict(int)
    for w in infobox:
        infobox_dict[w] += 1
        
    link_dict = defaultdict(int)
    for w in link:
        link_dict[w] += 1
        
    reference_dict = defaultdict(int)
    for w in reference:
        reference_dict[w] += 1
    
    unique_words.update(title)
    unique_words.update(body)
    unique_words.update(category)
    unique_words.update(infobox)
    unique_words.update(reference)
    
    for word in unique_words:
        temp = re.sub(r'^((.)(?!\2\2\2))+$',r'\1', word)
        if len(temp) != len(word):
            posting = str(page_no)+":"
            if title_dict[word]:
                posting += 't'+str(title_dict[word])

            if body_dict[word]:
                posting += 'b'+str(body_dict[word])

            if category_dict[word]:
                posting += 'c'+str(category_dict[word])

            if infobox_dict[word]:
                posting += 'i'+str(infobox_dict[word])

            if link_dict[word]:
                posting += 'l'+str(link_dict[word])

            if reference_dict[word]:
                posting += 'r'+str(reference_dict[word])
            posting += ";"
            
            index_map[word] += posting
            
    page_no += 1
    if page_no%20000 == 0:
        write_id_title()
        write_inter()
        
        index_map = defaultdict(str)
        id_to_title = {}
        


# In[ ]:


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('--input', action='store', type=str)

args = arg_parser.parse_args()

file_name = args.input


# In[1]:


parser = xml.sax.make_parser()
parser.setFeature(xml.sax.handler.feature_namespaces,False)
content_handler = Handler()
parser.setContentHandler(content_handler)
# parser.parse("english-data.xml")
parser.parse(file_name)
write_inter()
write_id_title()
num_files_final = merge_files(file_no)

with open('english_wiki_index/num_pages.txt', 'w') as f:
    f.write(str(page_no))

num_tokens_final = 0
with open('english_wiki_index/tokens_info.txt', 'r') as f:
    for line in f:
        num_tokens_final+=1

with open('english_wiki_index/num_tokens.txt', 'w') as f:
    f.write(str(num_tokens_final))

char_list = [chr(i) for i in range(97,123)]
num_list = [str(i) for i in range(0,10)]

with open(f'english_wiki_index/tokens_info.txt', 'r') as f:
    for line in tqdm(f):
        if line[0] in char_list:
            with open(f'english_wiki_index/tokens_info_{line[0]}.txt', 'a') as t:
                t.write(line.strip())
                t.write('\n')

        elif line[0] in num_list:
            with open(f'english_wiki_index/tokens_info_{line[0]}.txt', 'a') as t:
                t.write(line.strip())
                t.write('\n')

        else:
            with open(f'english_wiki_index/tokens_info_others.txt', 'a') as t:
                t.write(line.strip())
                t.write('\n')

for ch in tqdm(char_list):
    tok_count = 0
    with open(f'english_wiki_index/tokens_info_{ch}.txt', 'r') as f:
        for line in f:
            tok_count+=1

    with open(f'english_wiki_index/tokens_info_{ch}_count.txt', 'w') as f:
        f.write(str(tok_count))

for num in tqdm(num_list):
    tok_count = 0
    with open(f'english_wiki_index/tokens_info_{num}.txt', 'r') as f:
        for line in f:
            tok_count+=1

    with open(f'english_wiki_index/tokens_info_{num}_count.txt', 'w') as f:
        f.write(str(tok_count))

try:
    tok_count = 0
    with open('english_wiki_index/tokens_info_others.txt', 'r') as f:
        tok_count+=1

    with open(f'english_wiki_index/tokens_info_others_count.txt', 'w') as f:
        f.write(str(tok_count))
except:
    pass

os.remove('english_wiki_index/tokens_info.txt')
print('Total tokens',num_tokens_final)
print('Final files', num_files_final)


# In[ ]:




