import os, re, json
from nltk import word_tokenize
from nltk.corpus import stopwords
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

#sort list of docs in increasing order?
def postingsList(articles: List) -> List:
    #Loop through each tuple
    # postingList = []
    postingList = {}
    i = 0
    while(i < (len(articles)-1)):
        token = articles[i][0]
        ids = [articles[i][1]]
        while (i < (len(articles)-1)) and (articles[i][0] == articles[i+1][0]):
            ids.append(articles[i+1][1]) 
            i += 1
            
        i += 1
        # postingList.append((token, ids))
        postingList[token] = ids
    # with open("test2.txt", "w") as outfile:
    #     json.dump(postingList, outfile)
    return postingList

#Single word query
def queryProcessor(postingsList: List) -> List:
    query = input("Enter single word query: ")
    for term in postingsList:
        if term[0] == query:
            return term
    return []

#Subproject 3
#1 Implement the lossy dictionary compression techiniques of table 5.1
def distinctLossyDictionaryCompression(postingsList: Dict):
    unfiltered = len(postingsList)
    #remove numbers
    noNumbers = {}
    for term in postingsList:
        if not term.isdecimal():
            noNumbers[term] = postingsList[term]
    lowerCase = caseFolding(noNumbers)
    stopWords30, stopWords150 = removeStopWords(lowerCase)
    porterStemmer = stemming(stopWords150)
    print(unfiltered)
    print(len(noNumbers))
    print(len(lowerCase))
    print(len(stopWords30))
    print(len(stopWords150))
    print(len(porterStemmer))

def caseFolding(noNumbers: Dict) -> Dict:
    lowerCase = {}
    for term in noNumbers:
        if bool(re.match(r'.*[A-Z].*', term)): #check if term contains any uppercase characters
            if term.lower() in noNumbers:
                lowerCase[term.lower()] = list(set(noNumbers[term] + noNumbers[term.lower()]))
            else:
                lowerCase[term.lower()] = noNumbers[term]
        else:
            lowerCase[term] = noNumbers[term]
    return lowerCase

def removeStopWords(lowerCase: Dict) -> Dict :
    stopWords30 = {}
    stopWords150 = {}
    nltkStopwords = stopwords.words('english')
    for term in lowerCase:
        if term not in nltkStopwords[:30]:
            stopWords30[term] = lowerCase[term]
        if term not in nltkStopwords[:150]:
            stopWords150[term] = lowerCase[term]
    return (stopWords30, stopWords150)

def stemming(stopWords150: Dict)-> Dict: #what happens if two words stem to same thing, if they do need to add contents to 
    porterStemmer = {}
    ps = PorterStemmer()
    for term in stopWords150:
        stemmedTerm = ps.stem(term)
        if stemmedTerm in porterStemmer:
            porterStemmer[stemmedTerm] = list(set(porterStemmer[stemmedTerm] + stopWords150[term]))
        else:
            porterStemmer[stemmedTerm] = stopWords150[term]
    return porterStemmer 

articles = sortAndRemoveDuplicates(splitIntoArticles())
articles = postingsList(articles)
distinctLossyDictionaryCompression(articles)
# print(queryProcessor(articles))


