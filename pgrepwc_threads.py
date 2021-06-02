import sys
import math
from threading import Thread

def readTextFiles(textFileName):

    """ 
    Read a given file.

    Requires: textFileName is a str.
    Ensures: list with lists each containing one line from the file.
    """

    linesList = []
    fileIn = open(textFileName, 'r')

    linesList = []
    #iterates the file's lines and then appends them to a list containing all the info about said file

    for line in fileIn:	
        lineToAppend = line.strip("\n").strip("\r")
        linesList.append(lineToAppend)

    fileIn.close()

    return linesList

def wordSearcher(linesList):

    """ 
    This function will search for the word inside the file, returning 
    the number of times it appears in the file and the lines where it appears.

    Requires: list with lists each containing one line from the file.
    Ensures: the number of times it appears in the file and a list with the lines where it appears.
    """


    inputWordLength = len(inputWord)
    matchLines = []
    matchCounter = 0
    lineCounter = 0
    lastLineAppended = 0
    #iterating the list that contains all the lines from the file in question
    for line in linesList:
        lineCounter += 1
        loweredInputWord = inputWord.lower() # the input word is placed in lower case for comparison atempts
        line = line.lower() #the file line is placed in lower case for comparison atempts
        if loweredInputWord in line:
            wordList = line.split() #we seperate all the words in the line into a list
            for word in wordList:
                if loweredInputWord in word:
                    startingIndex = word.find(loweredInputWord) #defining input words boundaries so we can compare and see if its truly the word we are looking for
                    endingIndex = startingIndex + inputWordLength - 1 #defining input words boundaries so we can compare and see if its truly the word we are looking for
                    if startingIndex == 0 and endingIndex == len(word)-1: #in case the word as no other characters, either left or right, besides the word itsefl
                        matchCounter += 1
                        if lastLineAppended != lineCounter: #checking if we have not added the line before so we dont repeat it
                            matchLines.append(linesList[lineCounter-1])
                            lastLineAppended = lineCounter
                            
                    elif startingIndex == 0 and endingIndex != len(word)-1: #when the word in question has some characters to the right besides the word itself
                        if not word[endingIndex+1].isalpha(): #checking if it's a valid character
                            matchCounter += 1
                            if lastLineAppended != lineCounter:
                                matchLines.append(linesList[lineCounter-1])
                                lastLineAppended = lineCounter
                                
                    elif startingIndex != 0 and endingIndex == len(word)-1: #when the word in question has some characters to the left besides the word itself
                        if not word[startingIndex-1].isalpha(): #checking if it's a valid character
                            matchCounter += 1
                            if lastLineAppended != lineCounter:
                                matchLines.append(linesList[lineCounter-1])
                                lastLineAppended = lineCounter
                                
                    else:
                        if (not (word[startingIndex-1].isalpha())) and (not (word[endingIndex+1].isalpha())): #checking if it's a valid character and checking the situation when the word in question has characters to the left and right besides the word itself
                            
                            matchCounter += 1
                            if lastLineAppended != lineCounter:
                                matchLines.append(linesList[lineCounter-1])
                                lastLineAppended = lineCounter
                                
    return ([matchCounter, matchLines])


    
def resultsOutput(matchList, textFileName):

    """ 
    This function will print the results of the search for a given file

    Requires: matchList isa list with 2 integers the first one being the number
    of ocurrences the word being searched has on the given file and the second
    integer being the number of lines where those ocurrences happened
    Ensures: number of ocurrences in the file if the -c option was given or
    the number of lines where those ocurrences happened
    """

    matchCounter, matchLines = matchList[0:]

    if matchCounter == 0: #In case the word that the user suplied is not found in the files
        print("Não foram encontradas ocorrências da palavra", inputWord, "neste ficheiro")
        
    else:
        for line in matchLines:
            print(line)

    print()
    
    if countingOption == "-c": #In case the user uses the "-c" the output tells the user the amout of matches he got in a certain file
        print("ocorrências de", inputWord, "neste ficheiro =", matchCounter)
        print()

        return matchCounter

    else: #In case the user uses the "-l" the output tells the user the amout of lines with matches 
        print("número de linhas com ocorrências de", inputWord, "neste ficheiro =", len(matchLines))
        print()

        return len(matchLines)

def searchFiles(fileNameList):

    """ 
    In this function we call other functions so that we can obtain the lines
    from the file search those lines for the word and output the results
    
    Requires: fileNameList is a list which contains the names of the files
    to be searched  
    """
    #since thread can use global variables unlike processes we declare the one we need here
    global totalOcurrences
    #in this cicle we aplly the reading and searching methos in the received file names
    for fileName in fileNameList:
        print(fileName)
        linesList = readTextFiles(fileName)
        matchList = wordSearcher(linesList)
        totalOcurrences += resultsOutput(matchList, fileName)

def threadHandler(fileNameList, parallelizationLevel):

    """ 
    This function allocates the files to be searched to a given number of
    threads and prints the results of each thread and the total number
    of ocurrences in all given files

    Requires: fileNameList is a list which contains the names of the files
    to be searched, parallelization level is a int > 0 
    """

    global totalOcurrences
    extraProcesses = 0
    parallelizationLevel = int(parallelizationLevel)

    #Checks if there are more processes than files to process
    if parallelizationLevel > len(fileNameList):
        parallelizationLevel = len(fileNameList)
        numFilePerProcess = 1
            

    #Checks if the remainder of the divison between the number of files to be processed and the number of processes is 0
    elif len(fileNameList) % parallelizationLevel == 0:
        numFilePerProcess = len(fileNameList) // parallelizationLevel

     #If the remainder of the divison between the number of files to be processed and the number of processes is not 0
    else:
        extraProcesses =  len(fileNameList)  % parallelizationLevel   
        numFilePerProcess = (len(fileNameList) // parallelizationLevel)
        numFilePerProcess = int(math.ceil(numFilePerProcess))

    processes = []
    
    lastFileIndex = numFilePerProcess + extraProcesses
    #this thread is declared outo of the for cicle ahead since this one takes the most files if the number is uneven
    p = Thread(target=searchFiles, args=(fileNameList[0:lastFileIndex], ))

    fileNamesToProcess = ""
    for fileName in fileNameList[0:lastFileIndex]:
        fileNamesToProcess += fileName + " "

    print("== Filho  1 -", fileNamesToProcess + "==")
    p.start()
    p.join()

    fileIndex = lastFileIndex
    
    processes = []
    filesNamesToPrint = []

    #distributing files per child process after giving the extraFiles to the first process, in a list just creating them 
    for i in range(parallelizationLevel-1):
        processes.append(Thread(target=searchFiles, args=(fileNameList[(fileIndex):(fileIndex + numFilePerProcess)], )))
        #here the spare files are distributed by the restant threads
        fileNamesToProcess = "" 
        for fileName in fileNameList[(fileIndex):(fileIndex + numFilePerProcess)]:
            fileNamesToProcess += fileName + " "

        filesNamesToPrint.append(fileNamesToProcess)
        
        fileIndex += numFilePerProcess

    processNumber = 0
    #starting each process in the list of processes
    for process in processes:
        #to access the files that each thread is handling
        fileIndex = lastFileIndex
        
        #here we start the threads inside the list (processes)
        print("== Filho", processNumber+2, "-", filesNamesToPrint[processNumber] + "==")
        process.start()
        process.join()
        
        processNumber += 1

    if countingOption == "-c":
        print("número de ocorrências totais =", totalOcurrences)
    else:
        print("número total de linhas com ocorrências =", totalOcurrences)        

totalOcurrences = 0

#List containing the names of the files to be searched    
fileNameList = [] 

inputList = sys.argv

#Checks if the optional argument "-p" was used
if inputList[2] == "-p":

    #Checks if there were no filenames given in the arguments
    if len(inputList) < 6:
        inputFileName = input("Insira os nomes dos ficheiros separados apenas por espaços:")
        fileNameList = inputFileName.split()
        countingOption, parallelizationOption, parallelizationLevel, inputWord = inputList[1:5]
        threadHandler(fileNameList, parallelizationLevel)
        
    #Checks if more than one filename was given 
    elif len(inputList) > 6:             
        fileNameList =inputList[5:]
        countingOption, parallelizationOption, parallelizationLevel, inputWord = inputList[1:5]
        threadHandler(fileNameList, parallelizationLevel)
                     
    #If there was only one filename given
    else:                               
        countingOption, parallelizationOption, parallelizationLevel, inputWord, textFileName = inputList[1:]  
        fileNameList.append(textFileName)
        threadHandler(fileNameList, parallelizationLevel)
        
#If the "-p" option was not used        
else:

    #Checks if there were no filenames given in the arguments
    if len(inputList) < 4:
        inputFileName = input("Insira os nomes dos ficheiros separados apenas por espaços:")
        fileNameList = inputFileName.split()
        countingOption, inputWord = inputList[1:3]
        searchFiles(fileNameList)
        print("número de ocorrências totais =", totalOcurrences)

    #Checks if more than one filename was given
    elif len(inputList) > 4:         
        fileNameList = inputList[3:]
        countingOption, inputWord = inputList[1:3]
        searchFiles(fileNameList)
        print("número de ocorrências totais =", totalOcurrences)
        
    #If there was only one filename given   
    else:                               
        countingOption, inputWord, textFileName = inputList[1:]
        fileNameList.append(textFileName)
        searchFiles(fileNameList)
        print("número de ocorrências totais =", totalOcurrences)

