#                                  CS657 Project
## Group 15
### Group Members:
Akshay Kumar Chittora - 21111007 - akshay21@iitk.ac.in <br>
Jeet Sarangi - 21111032 - jeets@iitk.ac.in <br>
Vishwas Choudhary - 180876 - vishwasc@iitk.ac.in <br>


## File Structure:
`english_indexer.py` : Used for creating indexes for the english language dataset<br>
`hindi_indexer.py` : Used to create indexes for hindi language dataset <br>
`hindi_stem_words.txt` & `hindi_stop_words.txt`: Contains data for preprocessing<br>
`Query_runner.ipynb` : Notebook containing code for query processing and examples

## Link to Dataset:
 Link to English dumps: https://dumps.wikimedia.org/enwiki/20220420/
Link to Hindi dumps: https://dumps.wikimedia.org/hiwiki/20220420/

## Steps to run:
##### Create `english_wiki_index` and `hindi_wiki_index` in the same directory as indexer files to run them.<br>
For english indexing : `python3 english_indexer.py --input input_dataset_in_xml`<br>
For hindi indexing : `python3 hindi_indexer.py --input input_dataset_in_xml`<br>
These will create the necessary index files.

For Query Processing: Run the `Query_runner.ipynb`. run_query() function gives information about using the function.

## Link for indexed data: 
#### Smaller index data: https://iitk-my.sharepoint.com/:u:/g/personal/vishwasc_iitk_ac_in/ERxrF3J6vxxJrGltNm6lv-sBztQ0ITKtQakJTwRzrD3xvw?e=1Fawhs
#### Complete Index data : https://iitk-my.sharepoint.com/:u:/g/personal/vishwasc_iitk_ac_in/EZHC0EaOPelIuGjk-0W6CkYBFe6pwynb-yG-KazNUr_AQw?e=07wu7F

The files contain the english_wiki_index and hindi_wiki_index directories.
