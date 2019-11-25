#!/usr/bin/env python
# coding: utf-8

""" 
By: Yevhen Sapolovych, e.sapolovych@gmail.com
This is a 'generic' script we use to convert our Zotero texts to the structured JSON file. For it to work properly, you will need to:
 - install all required libs (including pdf2text)
 - specify the correct input and output paths (lines 21 and 105)
 - provide with the correct file (Zotero collection exported as a CSV, in UTF-8 without BOM)

Mind that 100% workability is not guaranteed (mostly due to the possible encoding issues).
Also mind that the author does not claim this script to be a perfect, or even a very efficiently coded solution.
"""

# %%load libs
import pandas as pd
from bs4 import BeautifulSoup as bs
import re
import numpy as np
import os.path
import json
from textract import process
# %%load the file for process
with open('your/path/zotero_export.csv', 'r') as file:
    data = pd.read_csv(file, low_memory=False)  # note that Zotero also exports JSON but without a filepath
print('loaded Zotero CSV')

# drop textless records and reset rows numbering
data.dropna(subset = ['File Attachments'], inplace = True)
print(f'{len(data.index)} texts after removing blanks')

#dedupe
data.drop_duplicates(["Title", "Publication Title", "Url"], inplace=True)
print('duplicate rows dropped')

# reset df index
data.reset_index(inplace=True)
# %%removing all unnecessary columns
data = data.loc[:, ['Title','Author','Url','Place','Publication Title','Date','File Attachments','Date Added', 'Manual Tags']]
print('unnecessary columns removed')

#add a column for text
data.loc[:,'fulltext']=''
# %%extract records from the files
pattern = re.compile('[^/]+$') #extract the filename from the end of a path
missing_ind = [] #create a list for indexes of files with no texts - to show us which ones are blank
drop_markers = ['Buy Article Now', 'No content preview'] #text which directly shows there is no article inside
for ind, row in data.iterrows(): #iterate over rows of data
    filepath = row['File Attachments'] #get a full filepath
    if '.html' in filepath: #if attachment is html
        with open(filepath, 'r') as html_file: 
            soup = bs(html_file, 'html.parser') #create a beautifulsoup object
        try:
            text = soup.get_text() #get the text from the bs obj
        except:
                data.loc[ind, 'fulltext'] = np.nan
                missing_ind.append(ind)
                print('bs could not retrieve the text')
    elif '.pdf' in filepath: #if attachment is pdf
        zotero_cache = re.sub(pattern,'zotero-ft-cache', filepath) #replace .pdf with zotero cache file if it exists
        if os.path.exists(zotero_cache):
            with open(zotero_cache, 'r') as cache_file:
                data.loc[ind, 'fulltext'] = cache_file
        else:
            try:
                data.loc[ind, 'fulltext'] = textract.process(filepath,  input_encoding=None, output_encoding="utf8")
            except:
                data.loc[ind, 'fulltext'] = np.nan
                missing_ind.append(ind)
    else:
        data.loc[ind, 'fulltext'] = np.nan
        missing_ind.append(ind)

print(f'Records extracted! Missing {len(missing_ind)} texts total')
# %%drop rows without texts
data.dropna(subset = ['fulltext'], axis=0, inplace = True)
data.drop(['File Attachments', 'Date Added', 'Manual Tags'], axis = 1, inplace = True)
# %%

print(f'{len(data.index)} texts overall')

json_dict = json.loads(data.to_json(orient = 'records', force_ascii=False))
with open('your/path/output.json', 'w') as outfile:
    outfile.write(json.dumps(json_dict, indent=2, ensure_ascii=False))

print('Done!')