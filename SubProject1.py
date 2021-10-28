import os, re, json, string
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from typing import List, Dict
from tabulate import tabulate
from datetime import datetime

def splitIntoArticles() -> List[str]: #read all files in directory, put everything into one string, split into list of articles 
    data = ""
    try:
        dir = input("Enter the directory: ")
        listOfFiles = os.listdir(dir)
    except Exception as e: 
        print(e)
        return 
    for filename in listOfFiles: #read each file in the directory that ends with .sgm
        if filename.endswith(".sgm"):
            filepath = dir + "/" + filename
            with open(filepath, "r") as f:
                data += f.read()
    return makeList(data.split("</REUTERS>")) #creates list of articles split on the </REUTERS> tag 

def makeList(listOfArticles: List) -> List: 
    articles = []
    for i in range(len(listOfArticles)): 
        foundNewID = re.search('NEWID="([0-9]+)"', listOfArticles[i])
        if foundNewID is not None:
            newId = re.search('[0-9]+', foundNewID.group(0)) #gets the id of the article
            if newId is not None:
                # listOfArticles[i] = extractBody(listOfArticles[i])
                articles= documentTermDocIdPairs(word_tokenize(extractBody(listOfArticles[i])), newId.group(0), articles) #tokenizes the articles one at a time 
    return articles
   
def extractBody(document: str) -> str: #remove everything that isn't between the body tags, if there are no text tags present return empty string 
    startText = document.find("<BODY>")
    endText = document.find("</BODY>")
    if startText != -1 and endText != -1:
        document = document[startText:endText+7]
        return document
    return ""

def documentTermDocIdPairs(tokenizedDocument: List, ID: str, articles: List) -> List: #makes list of tuples (term, docID) 
    specialChar = string.punctuation
    exp = "[{schar}]".format(schar = specialChar)
    for tokens in tokenizedDocument:
        if not bool(re.match(exp, tokens)):
            articles.append((tokens, ID))
    return articles

def sortAndRemoveDuplicates(articles: List) -> List: #removes duplicate tuples ie: ('a', 1), ('a', 1) -> ('a', 1) and sorts the tuples
    return sorted(list(set(articles)))

 
def postingsList(articles: List) -> Dict: # creates the dictionary where the key is each term in every article and the value is a list which represents each docID the term is present in
    postingList = {}
    i = 0
    while(i < (len(articles)-1)):
        token = articles[i][0]
        ids = [articles[i][1]]
        while (i < (len(articles)-1)) and (articles[i][0] == articles[i+1][0]):
            ids.append(articles[i+1][1]) 
            i += 1
        i += 1
        postingList[token] = ids
    
    for terms, postings in postingList.items(): #sort the docIDs of each term in increasing order
        postings = postings.sort(key=int)
    with open("term-docID.txt", "w") as outfile:
        json.dump(postingList, outfile)
    return postingList

#Subproject 2
#Single word query
def queryProcessor(postingsList: Dict, afterCompression = False):
    
    while True:
        query = input("Enter single word query: ")
        if not query:
            break
        if afterCompression:#checks after the lossy compression so need to also alter the query to find any results
            ps = PorterStemmer()
            stemmedQuery = ps.stem(query.lower())
            print(query, stemmedQuery, postingsList.get(stemmedQuery, []))
            with open("compressedQueries.txt", "a") as outfile:
                json.dump((query, stemmedQuery, postingsList.get(stemmedQuery, [])), outfile)
        else:#checks the term-docID pairs before any compression has been done
            print(query,postingsList.get(query, []))
            with open("queries.txt", "a") as outfile:
                json.dump((query, postingsList.get(query, [])), outfile)
    # return (query,postingsList.get(query, []))

#Subproject 3
#1 Implement the lossy dictionary compression techiniques of table 5.1
def distinctLossyDictionaryCompression(postingsDict: Dict) -> Dict:
    unfilteredTerms = len(postingsDict)
    unfilteredPostings = 0
    for term, postings in postingsDict.items():
        unfilteredPostings += len(postings)
    #remove numbers
    noNumbersTerms = {}
    noNumbersPostings = 0
    for term in postingsDict:
        if not bool(re.match(r'.*[0-9].*', term)): # #decided to remove terms that were entirely digits, so terms that have some digits and some letters are accepted
            noNumbersTerms[term] = postingsDict[term]
            noNumbersPostings += len(noNumbersTerms[term])
    lowerCaseTerms, lowerCasePostings = caseFolding(noNumbersTerms) 
    stopWords30Terms, stopWords150Terms, stopWords30Postings, stopWords150Postings = removeStopWords(lowerCaseTerms) #removes stop words
    porterStemmerTerms, porterStemmerPostings = stemming(stopWords150Terms)
    printTable(unfilteredTerms, len(noNumbersTerms), len(lowerCaseTerms), len(stopWords30Terms), len(stopWords150Terms), len(porterStemmerTerms),
    unfilteredPostings, noNumbersPostings, lowerCasePostings, stopWords30Postings, stopWords150Postings, porterStemmerPostings)
    with open("lossyCompression.txt", "w") as outfile:
        json.dump(porterStemmerTerms, outfile)
    return porterStemmerTerms
    

def caseFolding(noNumbersDistinct: Dict):
    lowerCaseTerms = {}
    lowerCasePostings = 0
    for term in noNumbersDistinct:
        if bool(re.match(r'.*[A-Z].*', term)): #check if term contains any uppercase characters
            if term.lower() in lowerCaseTerms.keys(): #if lowercase term already exists in dictionary, append the lists 
                lowerCaseTerms.update({term.lower() : list(set(lowerCaseTerms[term.lower()] + noNumbersDistinct[term]))})
                lowerCaseTerms[term.lower()].sort(key=int)
            else:
                lowerCaseTerms[term.lower()] = noNumbersDistinct[term]
        elif term in lowerCaseTerms.keys(): #appending lower case postings from original list to the postings present in new dictionary from the upper case value
            lowerCaseTerms.update({term: list(set(lowerCaseTerms[term] + noNumbersDistinct[term]))})
            lowerCaseTerms[term].sort(key=int)
    
        elif term not in lowerCaseTerms:
            lowerCaseTerms[term] = noNumbersDistinct[term]

    for term in lowerCaseTerms:
        lowerCasePostings += len(lowerCaseTerms[term])
    return lowerCaseTerms, lowerCasePostings

def removeStopWords(lowerCaseTerms: Dict) :
    stopWords30Terms = {}
    stopWords150Terms = {}
    stopWords30Postings = 0
    stopWords150Postings = 0
    nltkStopwords = stopwords.words('english')
    for term in lowerCaseTerms: 
        if term not in nltkStopwords[:30]: #remove occurences of first 30 stop words from the new dictionary
            stopWords30Terms[term] = lowerCaseTerms[term]
            stopWords30Postings += len(stopWords30Terms[term])
        if term not in nltkStopwords[:150]: #remove occurences of first 150 stop words from the new dictionary 
            stopWords150Terms[term] = lowerCaseTerms[term]
            stopWords150Postings += len(stopWords150Terms[term])
 
    return (stopWords30Terms, stopWords150Terms, stopWords30Postings, stopWords150Postings)

def stemming(stopWords150Terms: Dict)-> Dict: #what happens if two words stem to same thing, if they do need to add contents to 
    porterStemmerTerms = {}
    porterStemmerPostings = 0
    ps = PorterStemmer()
    for term in stopWords150Terms:
        stemmedTerm = ps.stem(term)
        if stemmedTerm in porterStemmerTerms: #if the stemmed term exists in the new list, append the postings to each other
            porterStemmerTerms.update({stemmedTerm : list(set(porterStemmerTerms[stemmedTerm] + stopWords150Terms[term]))})
            porterStemmerTerms[stemmedTerm].sort(key=int) 
        else:
            porterStemmerTerms[stemmedTerm] = stopWords150Terms[term]
    for term in porterStemmerTerms:
        porterStemmerPostings += len(porterStemmerTerms[term])       

    return (porterStemmerTerms, porterStemmerPostings)

def printTable(d_unfiltered: int, d_number: int, d_case: int, d_stop30: int, d_stop150: int, d_stem: int, 
               unfiltered: int, number: int, case: int, stop30: int, stop150: int, stem: int): #creates the table
    header = ["operations", "terms", "delta %", "total %", "posting size", "delta %", "total %"] 
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


starttime = datetime.now()
articles = sortAndRemoveDuplicates(splitIntoArticles())
articles2 = postingsList(articles)
print(queryProcessor(articles2))
final = distinctLossyDictionaryCompression(articles2)
print(queryProcessor(final, True))
print(datetime.now()- starttime)
