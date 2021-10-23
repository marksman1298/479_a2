import os, re, json
from nltk import word_tokenize
from nltk.stem.porter import PorterStemmer
from typing import List, Dict

def splitIntoArticles() -> List[str]: #read all files in directory, put everything into one string, split into list of articles 
    data = ""
    try:
        dir = input("Enter the directory: ")
        listOfFiles = os.listdir(dir)
    except Exception as e: 
        print(e)
        return 
    # specificFile = input("Enter a specific file: ")
    for filename in listOfFiles:
        if filename.endswith(".sgm"):
            filepath = dir + "/" + filename
            with open(filepath, "r") as f:
                data += f.read()
    return makeDict(data.split("</REUTERS>"))

def makeDict(listOfArticles: List) -> List: #want to get all newids of articles, then add them to a list, then combine both lists into dictionary with key new id : value article
    articles = []
    
    # specificArticle = input("Enter desired articles separated by space: ")
    # listArticles = specificArticle.split(" ")
    
    for i in range(len(listOfArticles)): 
    # print(word_tokenize(listOfArticles[0]))
        foundNewID = re.search('NEWID="([0-9]+)"', listOfArticles[i])
        if foundNewID is not None:
            newId = re.search('[0-9]+', foundNewID.group(0)) #not between text tags, might need to add that later.
            if newId is not None:
                articles= documentTermDocIdPairs(word_tokenize(listOfArticles[i]), newId.group(0), articles)
                # ids.append(newId.group(0))
    # articles = {ids[i]: listOfArticles[i] for i in range(len(ids))}
    return articles
    # if not len(listArticles) == 0:
    #     tableArticles = {} 
    #     for articleId in listArticles:
    #         try:
    #             tableArticles[articleId] = articles[articleId]
    #         except Exception as e:
    #             print("Not a valid key", e)
    #             return extractText(articles)
    #     return extractText(tableArticles)
       
    # return extractText(articles)   

def documentTermDocIDpairs(tokenizedDocument: List, ID: str) -> Dict: #makes dictionary for each document with key being the token and id the value, 
    termDocId = {tokens: ID for tokens in tokenizedDocument}
    return termDocId
    
def documentTermDocIdPairs(tokenizedDocument: List, ID: str, articles: List) -> List: #makes list of tuples for each document (each document is it's own list)
    for tokens in tokenizedDocument:
        articles.append((tokens, ID))
    # articles.append(tuple((tokens, ID) for tokens in tokenizedDocument))
    return articles

def sortAndRemoveDuplicates(articles: List) -> List:  #case insensitive? 
    # articles = sorted(articles)   
    return sorted(list(set([termDocId for termDocId in articles])))

    

print(sortAndRemoveDuplicates(splitIntoArticles()))
