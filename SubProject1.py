import os, re, json
from nltk import stem, word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from typing import List, Dict
from tabulate import tabulate

def splitIntoArticles() -> List[str]: #read all files in directory, put everything into one string, split into list of articles 
    data = ""
    try:
        dir = input("Enter the directory: ")
        listOfFiles = os.listdir(dir)
    except Exception as e: 
        print(e)
        return 
    for filename in listOfFiles:
        if filename.endswith(".sgm"):
            filepath = dir + "/" + filename
            with open(filepath, "r") as f:
                data += f.read()
    return makeList(data.split("</REUTERS>"))

def makeList(listOfArticles: List) -> List: #want to get all newids of articles, then add them to a list, then combine both lists into dictionary with key new id : value article
    articles = []
    for i in range(len(listOfArticles)): 
        foundNewID = re.search('NEWID="([0-9]+)"', listOfArticles[i])
        if foundNewID is not None:
            newId = re.search('[0-9]+', foundNewID.group(0)) #not between text tags, might need to add that later.
            if newId is not None:
                articles= documentTermDocIdPairs(word_tokenize(listOfArticles[i]), newId.group(0), articles)
    return articles
   
    
def documentTermDocIdPairs(tokenizedDocument: List, ID: str, articles: List) -> List: #makes list of tuples for each document (each document is it's own list)
    for tokens in tokenizedDocument:
        articles.append((tokens, ID))
    return articles

def sortAndRemoveDuplicates(articles: List) -> List:    
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
def distinctLossyDictionaryCompression(postingsDict: Dict, postingsList: List):
    unfilteredDistinct = len(postingsDict)
    unfiltered = len(postingsList)
    #remove numbers
    noNumbers = []
    noNumbersDistinct = {}
    for term in postingsDict:
        if not term.isdecimal():
            noNumbersDistinct[term] = postingsDict[term]
    for term in postingsList:
        if not term[0].isdecimal():
            noNumbers.append(term)
    lowerCaseDistinct, lowerCase = caseFolding(noNumbersDistinct, noNumbers)
    stopWords30Distinct, stopWords150Distinct, stopWords30, stopWords150 = removeStopWords(lowerCaseDistinct, lowerCase)
    porterStemmerDistinct, porterStemmer = stemming(stopWords150Distinct, stopWords150)
    printTable(unfilteredDistinct, len(noNumbersDistinct), len(lowerCaseDistinct), len(stopWords30Distinct), len(stopWords150Distinct), len(porterStemmerDistinct),
    unfiltered, len(noNumbers), len(lowerCase), len(stopWords30), len(stopWords150), len(porterStemmer))
    

def caseFolding(noNumbersDistinct: Dict, noNumbers: List):
    lowerCaseDistinct = {}
    lowerCase = []
    for term in noNumbersDistinct:
        if bool(re.match(r'.*[A-Z].*', term)): #check if term contains any uppercase characters
            if term.lower() in noNumbersDistinct:
                lowerCaseDistinct[term.lower()] = list(set(noNumbersDistinct[term] + noNumbersDistinct[term.lower()]))
            else:
                lowerCaseDistinct[term.lower()] = noNumbersDistinct[term]
        else:
            lowerCaseDistinct[term] = noNumbersDistinct[term]
    for term in noNumbers:
        if bool(re.match(r'.*[A-Z].*', term[0])):
            lowerCaseTuple = (term[0].lower(), term[1])
            lowerCase.append(lowerCaseTuple)
        else:
            lowerCase.append(term)
    lowerCase = sortAndRemoveDuplicates(lowerCase)
    return lowerCaseDistinct, lowerCase

def removeStopWords(lowerCaseDistinct: Dict, lowerCase: List) :
    stopWords30Distinct = {}
    stopWords150Distinct = {}
    stopWords30 = []
    stopWords150 = []
    nltkStopwords = stopwords.words('english')
    for term in lowerCaseDistinct:
        if term not in nltkStopwords[:30]:
            stopWords30Distinct[term] = lowerCaseDistinct[term]
        if term not in nltkStopwords[:150]:
            stopWords150Distinct[term] = lowerCaseDistinct[term]
    for term in lowerCase:
        if term[0] not in nltkStopwords[:30]:
            stopWords30.append(term)
        if term[0] not in nltkStopwords[:150]:
            stopWords150.append(term) 
    return (stopWords30Distinct, stopWords150Distinct, stopWords30, stopWords150)

def stemming(stopWords150Distinct: Dict, stopWords150: List)-> Dict: #what happens if two words stem to same thing, if they do need to add contents to 
    porterStemmerDistinct = {}
    porterStemmer = []
    ps = PorterStemmer()
    for term in stopWords150Distinct:
        stemmedTerm = ps.stem(term)
        if stemmedTerm in porterStemmerDistinct:
            porterStemmerDistinct[stemmedTerm] = list(set(porterStemmerDistinct[stemmedTerm] + stopWords150Distinct[term]))
        else:
            porterStemmerDistinct[stemmedTerm] = stopWords150Distinct[term]
    for term in stopWords150:
        stemmedTerm = ps.stem(term[0])
        stemTuple = (stemmedTerm, term[1])
        # if stemTuple not in porterStemmer:
        porterStemmer.append(stemTuple)
    porterStemmer = sortAndRemoveDuplicates(porterStemmer)
    return (porterStemmerDistinct, porterStemmer)

def printTable(d_unfiltered: int, d_number: int, d_case: int, d_stop30: int, d_stop150: int, d_stem: int, 
               unfiltered: int, number: int, case: int, stop30: int, stop150: int, stem: int):
    header = ["operations", "distinct_number", "delta %", "total %", "number", "delta %", "total %"] 
    data = []
    #unfiltered row
    data.append(["unfiltered", d_unfiltered, "", "", unfiltered])
    #remove numbers
    data.append(["no numbers", d_number, int((1-(d_number/d_unfiltered))*100), int((1-(d_number/d_unfiltered))*100), number, int((1-(number/unfiltered))*100), int((1-(number/unfiltered))*100)])
    #case insensitive
    data.append(["case folding", d_case, int((1-(d_case/d_number))*100), int((1-(d_case/d_unfiltered))*100), case, int((1-(case/number))*100), int((1-(case/unfiltered))*100)])
    #30 stop words
    data.append(["30 stop words", d_stop30, int((1-(d_stop30/d_case))*100), int((1-(d_stop30/d_unfiltered))*100), stop30, int((1-(stop30/case))*100), int((1-(stop30/unfiltered))*100)])
    #150 stop words
    data.append(["150 stop words", d_stop150, int((1-(d_stop150/d_stop30))*100), int((1-(d_stop150/d_unfiltered))*100), stop150, int((1-(stop150/stop30))*100), int((1-(stop150/unfiltered))*100)])
    #150 stemming
    data.append(["stemming", d_stem, int((1-(d_stem/d_stop150))*100), int((1-(d_stem/d_unfiltered))*100), stem, int((1-(stem/stop150))*100), int((1-(stem/unfiltered))*100)])
    print(tabulate(data, headers=header, tablefmt="grid"))
    with open("compressionTable.txt", "w") as outfile:
        json.dump(tabulate(data, headers=header, tablefmt="grid"), outfile)


articles = sortAndRemoveDuplicates(splitIntoArticles())
articles2 = postingsList(articles)
distinctLossyDictionaryCompression(articles2, articles)

