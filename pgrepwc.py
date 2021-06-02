import os
import pickle
import pathlib
import sys
import math
from multiprocessing import Lock, Process, Value, Queue
import datetime
import signal
import time


def readTextFiles(textFileName):

    """ 
    Read a given file.

    Requires: textFileName is a str.
    Ensures: list with lists each containing one line from the file.
    """

    linesList = []
    fileIn = open(textFileName, 'r')

    linesList = []
    #iterates the file's lines and appends them to a list containing all the info about the file

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

    #List that will contain all the lines that have a ocurrence
    matchLines = []

    #Number of ocurrences 
    matchCounter = 0

    #Number of lines that have an ocurrence
    lineCounter = 0

    #Number of the last appended line
    lastLineAppended = 0
    
    #iterating the list that contains all the lines from the file in question
    for line in linesList:
        lineCounter += 1
        line = line #the file line
        
        if inputWord in line:
            wordList = line.split() #we seperate all the words in the line into a list for comparison atempts
            
            for word in wordList:
                if inputWord in word:
                    #defining input words boundaries so we can compare and see if its truly the word we are looking for
                    startingIndex = word.find(inputWord)
                    #defining input words boundaries so we can compare and see if its truly the word we are looking for
                    endingIndex = startingIndex + inputWordLength - 1
                    #in case the word as no other characters, either left or right, besides the word itsef
                    if startingIndex == 0 and endingIndex == len(word)-1:
                        matchCounter += 1
                        #checking if we have not added the line before so we dont repeat it
                        if lastLineAppended != lineCounter: 
                            matchLines.append(linesList[lineCounter-1])
                            lastLineAppended = lineCounter

                    #when the word in question has some characters to the right besides the word itself        
                    elif startingIndex == 0 and endingIndex != len(word)-1:
                        
                        #checking if it's a valid character
                        if not word[endingIndex+1].isalpha(): 
                            matchCounter += 1
                            if lastLineAppended != lineCounter:
                                matchLines.append(linesList[lineCounter-1])
                                lastLineAppended = lineCounter
                                
                    #when the word in question has some characters to the left besides the word itself          
                    elif startingIndex != 0 and endingIndex == len(word)-1:
                        #checking if it's a valid character
                        if not word[startingIndex-1].isalpha(): 
                            matchCounter += 1
                            if lastLineAppended != lineCounter:
                                matchLines.append(linesList[lineCounter-1])
                                lastLineAppended = lineCounter
                                
                    else:
                        #checking if it's a valid character and checking the situation when the word 
                        #in question has characters to the left and right besides the word itself
                        if (not (word[startingIndex-1].isalpha())) and (not (word[endingIndex+1].isalpha())): 
                            
                            matchCounter += 1
                            if lastLineAppended != lineCounter:
                                matchLines.append(linesList[lineCounter-1])
                                lastLineAppended = lineCounter
                                
    return ([matchCounter, matchLines])


def resultsOutput(matchList):

    """ 
    This function will print the results of the search for a given file

    Requires: matchList is a list with 2 integers the first one being the number
    of ocurrences the word being searched has on the given file and the second
    integer being the number of lines where those ocurrences happened
    Ensures: number of ocurrences in the file if the -c option was given or
    the number of lines where those ocurrences happened
    """

    matchCounter, matchLines = matchList[0:]

    #In case the word that the user suplied is not found in the files
    if matchCounter == 0: 
        print("Não foram encontradas ocorrências da palavra", inputWord, "nesta parte do ficheiro")
        
    else:
        for line in matchLines:
            print(line)

    print()

    #In case the user uses the "-c" the output tells the user the amout of matches he got in a certain file
    if countingOption == "-c": 
        print("Ocorrências de", inputWord, "nesta parte do ficheiro =", matchCounter)
        print()

        return matchCounter

    #In case the user uses the "-l" the output tells the user the amout of lines with matches
    else:  
        print("Número de linhas com ocorrências de", inputWord, "nesta parte do ficheiro =", len(matchLines))
        print()

        return len(matchLines)


def fileDivider():

    """ 
    This function will split the lines of each file to give to each process

    Requires: fileNameList is a list which contains the names of the files
    to be searched and parallelization level is a int > 0
    Ensures: list that contains lists each of these representing the workload 
    each process will receive in lists, each of these lists representing the lines
    of a file that the process will search for the given word. 
    """


    #list that will hold the lines each process will have to process
    processWorkLoad = []
    #creating a number of lists inside the list equal to the parallelizationLevel
    for i in range(parallelizationLevel):
        processWorkLoad.append([])

    partOfFilePerProcess = 1 / parallelizationLevel

    for file in fileNameList: 
    
        listLineFile = readTextFiles(file)
        totalFileLines = len(listLineFile)
        linesPerProcess = totalFileLines * partOfFilePerProcess

        lastCheckPoint = 0

        if linesPerProcess.is_integer():

            linesPerProcess = int(linesPerProcess)

            for processLoad in processWorkLoad:
                giveToProcess = listLineFile[lastCheckPoint: (lastCheckPoint + linesPerProcess)]
                lastCheckPoint += linesPerProcess
                processLoad.append(giveToProcess)

        else:

            linesPerProcess = int(linesPerProcess)
  
            for i in range(parallelizationLevel):
                if (i < parallelizationLevel - 1):
                    giveToProcess = listLineFile[lastCheckPoint: (lastCheckPoint + linesPerProcess)]
                    lastCheckPoint += linesPerProcess
                    processWorkLoad[i].append(giveToProcess)
                else:
                    giveToProcess = listLineFile[lastCheckPoint:]
                    processWorkLoad[i].append(giveToProcess)

    return processWorkLoad


def searchWord():
    
    """ 
    In this function we call other functions so that we can obtain the lines
    from the file search those lines for the word and output the results
    """

    #in this cicle we apply the reading and searching method in the received file names
    for fileName in fileNameList:
        print(fileName)
        linesList = readTextFiles(fileName)
        matchList = wordSearcher(linesList)
        totalOcurrences.value  += resultsOutput(matchList)
        filesCompleted.value += 1


def searchFiles(fileNameList, processNumber, pidQueue, fileQueue, searchTimeQueue, fileMatches):
    
    """ 
    In this function we call other functions so that we can obtain the lines
    from the file then search those lines for the word and output the results
    
    Requires: fileNameList is a list which contains the names of the files
    to be searched, pidQueue is a queue contaning processes id's, fileQueue 
    is a queue containing the files for each process, searchTimeQueue is a queue 
    contaning the search time of each process and fileMatches is a queue contaning 
    all the files each process takes care off

    """

    mutex.acquire()

    toAppendPid = os.getpid()
    pidQueue.put(toAppendPid)

    fileNamesToProcess = ""
    for fileName in fileNameList:
        fileNamesToProcess += fileName + " "

    fileQueue.put(fileNamesToProcess)
    print("== Filho " + str(processNumber) + " -", fileNamesToProcess + "==")
    startingSearchTime = datetime.datetime.now()
    #in this loop we apply the reading and searching method in the received file names

    for fileName in fileNameList:

        if len(fileNameList) > 0:
            print(fileName)
            linesList = readTextFiles(fileName)
            matchList = wordSearcher(linesList)
            toAddQueue = resultsOutput(matchList)
            totalOcurrences.value  += toAddQueue
            filesCompleted.value += 1
            fileMatches.put(toAddQueue)

            if (CTRLC.value != 0):
                fileNameList = []


    endingSearchTime = datetime.datetime.now()
    searchTime = endingSearchTime - startingSearchTime
    searchTimeQueue.put(searchTime)
    mutex.release()


def searchLines(workLoad, processNumber, pidQueue, fileQueue, searchTimeQueue, fileMatches):

    """ 
    In this function we call other functions so that we can search the given lines
    for the word and output the results
    
    Requires: lines is a list containing lists that contain and fileNameList
    is a list which contains the names of the files to be searched, pidQueue 
    is a queue contaning processes id's, fileQueue 
    is a queue containing the files for each process, searchTimeQueue is a queue 
    contaning the search time of each process and fileMatches is a queue contaning 
    all the files each process takes care off

    """
    
    mutex.acquire()    

    toAppendPid = os.getpid()
    pidQueue.put(toAppendPid)

    global fileNameList
    
    fileNamesToProcess = ""

    for fileName in fileNameList:
        fileNamesToProcess += fileName + " "
            
    fileQueue.put(fileNamesToProcess)
    print("== Filho " + str(processNumber) + " -", fileNamesToProcess + "==")

     

    currentFile = 0
    startingSearchTime = datetime.datetime.now()

    for filelines in workLoad:
        
        if (len(fileNameList) > 0):

            print(fileNameList[currentFile])
            currentFile += 1
            matchList = wordSearcher(filelines)
            toAddQueue = resultsOutput(matchList)
            totalOcurrences.value += toAddQueue               
            fileMatches.put(toAddQueue)

            if (CTRLC.value != 0):
                fileNameList = []

    endingSearchTime = datetime.datetime.now()
    searchTime = endingSearchTime - startingSearchTime
    searchTimeQueue.put(searchTime)
    mutex.release()

            
def processHandler():

    """ 
    This function allocates the files or lines to be searched to a given number of
    processes and prints the results of each process and the total number
    of ocurrences in all given files
    """

    #Checks if there are more processes than files to process
    if parallelizationLevel > len(fileNameList):
        workLoadList = fileDivider()
        processes = processLines(workLoadList)
          
    #Checks if the remainder of the divison between the number of files to be processed and the number of processes is 0
    elif len(fileNameList) % parallelizationLevel == 0:
        numFilePerProcess = len(fileNameList) // parallelizationLevel
        processes = processFiles(numFilePerProcess)

    #If the remainder of the divison between the number of files to be processed and the number of processes is not 0
    else:
        extraProcesses =  len(fileNameList)  % parallelizationLevel   
        numFilePerProcess = (len(fileNameList) // parallelizationLevel)
        numFilePerProcess = int(math.ceil(numFilePerProcess))
        processes = processFiles(numFilePerProcess, extraProcesses)

    return processes 


def processLines(workLoadList):

    """ 
    This function will create processes that will search for the given word in the given lines 
    and store information about that search in queues 

    Requires: workLoadList is a list that contains lists each of these representing the workload 
    each process will receive in lists, each of these lists representing the lines
    of a file that the process will search for the given word. 
    Ensures: list that 
    """

    pidQueue = Queue()
    searchTimeQueue = Queue()
    fileQueue = Queue()
    fileMatches = Queue()
    

    
    processes = []
    processNumber = 1
    searchTimeList = []
    pidList = []
    filePerProcessList = []   
    totalInfoList = []
    matchesByFileList = []

    for processWorkLoad in workLoadList:      
        proc = Process(target=searchLines, args=(processWorkLoad, processNumber, pidQueue, fileQueue, searchTimeQueue, fileMatches))
        processNumber += 1    
        processes.append(proc)    
        proc.start()      
      
    for process in processes:
        searchTimeList.append(searchTimeQueue.get())
        totalInfoList.append(searchTimeList)
        pidList.append(pidQueue.get())
        totalInfoList.append(pidList)
        filePerProcessList.append(fileQueue.get())      
        totalInfoList.append(filePerProcessList) 
        matchesByFileList.append(fileMatches.get())
        totalInfoList.append(matchesByFileList)
        
        process.join()
        
    filesCompleted.value += len(fileNameList)

    if CTRLC.value == 0:
        if countingOption == "-c":
            print("Número de ocorrências totais =", totalOcurrences.value)
        else:
            print("Número total de linhas com ocorrências =", totalOcurrences.value)
    else:
        if countingOption == "-c": 
            print("Número de ocorrências nos ficheiros processados =", totalOcurrences.value)
        else:
            print("Número de linhas com ocorrências nos ficheiros processados =", totalOcurrences.value)    

    return totalInfoList

    
def processFiles(numFilePerProcess, extraProcesses = 0):

    """
    This function will create processes that will search for the given word in the given files 
    and store information about that search in queues. 

    Requires: numFilePerProcess is a int representing the number of files each process needs to
    search in and extraProcesses is a int representing the number of files that the first process
    will have to search in addition to the numFilePerProcess.
    Ensures: list 
    """
    pidQueue = Queue()
    searchTimeQueue = Queue()
    fileQueue = Queue()
    fileMatches = Queue()

    processNumber = 1
    lastFileIndex = numFilePerProcess + extraProcesses
    searchTimeList = []
    pidList = []
    filePerProcessList = [] 
    matchesByFileList = []  
    totalInfoList = []

    #List that will hold the following processes
    processes = []
    
    #this process is declared out of the for cicle since this one takes the most files if the number is uneven
    p = Process(target=searchFiles, args=(fileNameList[0:lastFileIndex], processNumber, pidQueue, fileQueue, searchTimeQueue, fileMatches))    
    processNumber += 1
    processes.append(p)

    #Starting index for the following processes
    fileIndex = lastFileIndex

    #distributing files per child process after giving the extraFiles to the first process
    for i in range(parallelizationLevel - 1):        
        processes.append(Process(target=searchFiles, args=(fileNameList[(fileIndex):(fileIndex + numFilePerProcess)], processNumber, pidQueue, fileQueue, searchTimeQueue, fileMatches)))
        processNumber += 1
        fileIndex += 1 
    
    #iterating over each process in the list of processes
    for process in processes:
        process.start()
        
    for process in processes:
        searchTimeList.append(searchTimeQueue.get())
        totalInfoList.append(searchTimeList)
        pidList.append(pidQueue.get())
        totalInfoList.append(pidList)
        filePerProcessList.append(fileQueue.get())      
        totalInfoList.append(filePerProcessList) 
        matchesByFileList.append(fileMatches.get())
        totalInfoList.append(matchesByFileList)
        process.join()

    if CTRLC.value == 0:
        if countingOption == "-c":
            print("Número de ocorrências totais =", totalOcurrences.value)
        else:
            print("Número total de linhas com ocorrências =", totalOcurrences.value)
    else:
        if countingOption == "-c": 
            print("Número de ocorrências nos ficheiros processados =", totalOcurrences.value)
        else:
            print("Número de linhas com ocorrências nos ficheiros processados =", totalOcurrences.value) 
    
    return totalInfoList



def historyFileHandlerSingleProcess(fileNameInput, endingExecuteTimer, startingExecutionTime, allFilesList, fatherPid, timeSearch):
    """
    This function creates a binary file contaning the information of the last 
    search the files did, like: search timer, execution times, files per process and number of matches

    Requires: fileNameInput wich is the name of the created text file, endingExecuteTimer that is the timer that the exceution ends,
    startingExecutionTime that is the timer that the execution starts, allFilesList wich is a list containing all the files, 
    fatherPid that contains the id of the process, timeSearch that contains the time it took to search the word
    """
    #formats and calculates needed timers
    toWrite = startingExecutionTime.strftime("%d/%m/%y, %H:%M:%S:%f")
    timeRunning = str(endingExecuteTimer - startingExecutionTime)
    timeRunning = timeRunning.replace(".", ":")

    currentDir = pathlib.Path().absolute()
    filesSizesForProcess = []

    #gets the size of each file
    for file in allFilesList:
        sizeFile = os.path.getsize(str(currentDir) + "/" + str(file))
        filesSizesForProcess.append(sizeFile)
    


    firstLine = ("Início da execução da pesquisa: " + toWrite)
    space = ("\n")
    secondLine = ("Duração da execução: " + timeRunning)   
     
    headerToDump = [firstLine, secondLine, space]
    idToDump = ("Processo: " + str(fatherPid))

    # formats the file names
    allFilesList = str(allFilesList).replace("[", "")
    allFilesList = allFilesList.replace("]", "")


    filesToDump = ("   ficheiro: " + str(allFilesList))
        
    searchTimeToDump = ("       tempo de pesquisa: " + str(timeSearch))
        
    finalStringHolder = str(filesSizesForProcess).replace("[", "")
    finalStringHolder = finalStringHolder.replace("]", "")
    finalStringHolder = finalStringHolder.replace(",", " e")

    fileDimToDump = ("       dimensão do ficheiro: " + finalStringHolder + " bytes")


    #gets the matches according to the method selected by the user
    if countingOption == "-c": 
        typeOcurToDump = ("       número de ocorrências: " + str(totalOcurrences.value))
            
    else:
        typeOcurToDump = ("       número de linhas ocorrências: " + str(totalOcurrences.value))

    listToAppend = [idToDump, filesToDump, searchTimeToDump, fileDimToDump, typeOcurToDump, space]
    headerToDump.append(listToAppend)

    #dumps all the info into the binary file using pickle
    with open(fileNameInput, "wb") as o:
        pickle.dump(headerToDump, o)
       

    o.close()


def historyFileHandler(fileNameInput, endingExecuteTimer, startingExecutionTime, listInfo):
    """
    This function creates a binary file contaning the information of the last 
    search the files did, like: search timer, execution times, files per process and number of matches

    Requires: fileNameInput wich is the name of the created text file, endingExecuteTimer that is the timer that the exceution ends,
    startingExecutionTime that is the timer that the execution starts and a listInfo than contains all the info about all the
    processes like: search timers, processes id's, files per process and number of matches by process
    """
    #selects the last part of infoList
    updatedListInfo = listInfo[-4:]
    
    #atributes each list to its respective variable
    searchTimers = updatedListInfo[0]
    pidProcesses = updatedListInfo[1]
    filePerProcess = updatedListInfo[2]
    matchesPerProcess = updatedListInfo[3]
    
    #formats and calculates needed timers
    toWrite = startingExecutionTime.strftime("%d/%m/%y, %H:%M:%S:%f")
    timeRunning = str(endingExecuteTimer - startingExecutionTime)
    timeRunning = timeRunning.replace(".", ":")

    currentDir = pathlib.Path().absolute()
    filesSizesPerProcess = []
    allSizesPerProcess = []
    #gets each files size
    for i in range(len(pidProcesses)):
        filesSizesPerProcess = []
        sizesToCalculate = filePerProcess[i].split()
        for file in sizesToCalculate:
            sizeFile = os.path.getsize(str(currentDir) + "/" + str(file))
            filesSizesPerProcess.append(sizeFile)
        allSizesPerProcess.append(filesSizesPerProcess)
    

    firstLine = ("Início da execução da pesquisa: " + toWrite)
    space = ("\n")
    secondLine = ("Duração da execução: " + timeRunning)   
     
    headerToDump = [firstLine, secondLine, space]
    
    #writes the info of each file according to the number of processes
    for process in range(len(pidProcesses)):
        idToDump = ("Processo: " + str(pidProcesses[process]))
       
        filesToDump = ("   ficheiro: " + str(filePerProcess[process]))
        
        searchTimeToDump = ("       tempo de pesquisa: " + str(searchTimers[process]))
        
        finalStringHolder = str(allSizesPerProcess[process]).replace("[", "")
        finalStringHolder = finalStringHolder.replace("]", "")
        finalStringHolder = finalStringHolder.replace(",", " e")

        fileDimToDump = ("       dimensão do ficheiro: " + finalStringHolder + " bytes")
        
        if countingOption == "-c": 
            typeOcurToDump = ("       número de ocorrências: " + str(matchesPerProcess[process]))
            
        else:
            typeOcurToDump = ("       número de linhas ocorrências: " + str(matchesPerProcess[process]))
            
        listToAppend = [idToDump, filesToDump, searchTimeToDump, fileDimToDump, typeOcurToDump, space]
        headerToDump.append(listToAppend)
    

    #dumps the info into the ninary file using pickle
    with open(fileNameInput, "wb") as o:
        pickle.dump(headerToDump, o)
       
    o.close()

def signalHandler(sig, NULL):
    """
    This function will handle the SIGINT signal
    """

    CTRLC.value = 1


def outputStatus(sig, NULL):
    """
    This function will print to the stdout the status of the search 
    """

    if (CTRLC.value == 0):

        if countingOption == "-c": 
            print("Número de ocorrências nos ficheiros processados =", totalOcurrences.value)
        else:
            print("Número de linhas com ocorrências nos ficheiros processados =", totalOcurrences.value) 

        print("Número de ficheiros completamente processados =", filesCompleted.value)

        tempoDecorrido = datetime.datetime.now() - startingExecutionTime
        tempoDecorrido = int(tempoDecorrido.total_seconds() * 1000000)

        print("Tempo decorrido desde o inicio da execução =", tempoDecorrido)

#---------------------------------------------------------------------------------------------------------------------------

signal.signal(signal.SIGINT, signalHandler)
signal.signal(signal.SIGALRM, outputStatus)

mutex = Lock()

filesCompleted = Value("i", 0)
totalOcurrences = Value("i", 0)
CTRLC = Value("i", 0)

fatherPid = os.getpid()

#List containing the names of the files to be searched    
fileNameList = [] 

inputList = sys.argv
#inputList = ["", "-c", "-p", "2", "railways", "ola.txt", "file2.txt", "adeus.txt"]

startingExecutionTime = datetime.datetime.now()

#Checks if the optional argument -p was used


if inputList[2] == "-p":

    if inputList[4] == "-a":

        if inputList[6] == "-f":
            # p a f

            #Checks if there were no filenames given in the arguments
            if len(inputList) < 10:
                inputFileName = input("Insira os nomes dos ficheiros separados apenas por espaços:")
                fileNameList = inputFileName.split()
                countingOption, parallelizationOption, parallelizationLevel, statusOption, statusTimer, historyOption, historyFile, inputWord = inputList[1:9]
                parallelizationLevel = int(parallelizationLevel)
                signal.setitimer(signal.ITIMER_REAL, 0.1, float(statusTimer))
                processes = processHandler()
                endingExecuteTimer = datetime.datetime.now()
                historyFileHandler(historyFile, endingExecuteTimer, startingExecutionTime, processes)

            #Checks if more than one filename was given 
            elif len(inputList) > 10:             
                fileNameList = inputList[9:]
                countingOption, parallelizationOption, parallelizationLevel, statusOption, statusTimer, historyOption, historyFile, inputWord = inputList[1:9]
                parallelizationLevel = int(parallelizationLevel)
                signal.setitimer(signal.ITIMER_REAL, 0.1, float(statusTimer))
                processes = processHandler()
                endingExecuteTimer = datetime.datetime.now()
                historyFileHandler(historyFile, endingExecuteTimer, startingExecutionTime, processes)
                            
            #If there was only one filename given
            else:                               
                countingOption, parallelizationOption, parallelizationLevel, statusOption, statusTimer, historyOption, historyFile, inputWord, textFileName = inputList[1:]  
                parallelizationLevel = int(parallelizationLevel)
                fileNameList.append(textFileName)
                signal.setitimer(signal.ITIMER_REAL, 0.1, float(statusTimer))
                processes = processHandler()
                endingExecuteTimer = datetime.datetime.now()
                historyFileHandler(historyFile, endingExecuteTimer, startingExecutionTime, processes)

        else:
            # p a

            #Checks if there were no filenames given in the arguments
            if len(inputList) < 8:
                inputFileName = input("Insira os nomes dos ficheiros separados apenas por espaços:")
                fileNameList = inputFileName.split()
                countingOption, parallelizationOption, parallelizationLevel, statusOption, statusTimer, inputWord = inputList[1:7]
                parallelizationLevel = int(parallelizationLevel)
                signal.setitimer(signal.ITIMER_REAL, 0.1, float(statusTimer))
                processes = processHandler()
                
            #Checks if more than one filename was given 
            elif len(inputList) > 8:             
                fileNameList = inputList[7:]
                countingOption, parallelizationOption, parallelizationLevel, statusOption, statusTimer, inputWord = inputList[1:7]
                parallelizationLevel = int(parallelizationLevel)
                signal.setitimer(signal.ITIMER_REAL, 0.1, float(statusTimer))
                processes = processHandler()
                            
            #If there was only one filename given
            else:                               
                countingOption, parallelizationOption, parallelizationLevel, statusOption, statusTimer, inputWord, textFileName = inputList[1:]  
                parallelizationLevel = int(parallelizationLevel)
                fileNameList.append(textFileName)
                signal.setitimer(signal.ITIMER_REAL, 0.1, float(statusTimer))
                processes = processHandler()

    elif inputList[4] == "-f":
    # p f

        #Checks if there were no filenames given in the arguments
        if len(inputList) < 8:
            inputFileName = input("Insira os nomes dos ficheiros separados apenas por espaços:")
            fileNameList = inputFileName.split()
            countingOption, parallelizationOption, parallelizationLevel, historyOption, historyFile, inputWord = inputList[1:7]
            parallelizationLevel = int(parallelizationLevel)
            processes = processHandler()
            endingExecuteTimer = datetime.datetime.now()
            historyFileHandler(historyFile, endingExecuteTimer, startingExecutionTime, processes)
            
        #Checks if more than one filename was given 
        elif len(inputList) > 8:             
            fileNameList = inputList[7:]
            countingOption, parallelizationOption, parallelizationLevel, historyOption, historyFile, inputWord = inputList[1:7]
            parallelizationLevel = int(parallelizationLevel)
            processes = processHandler()
            endingExecuteTimer = datetime.datetime.now()
            historyFileHandler(historyFile, endingExecuteTimer, startingExecutionTime, processes)
                        
        #If there was only one filename given
        else:                               
            countingOption, parallelizationOption, parallelizationLevel, historyOption, historyFile, inputWord, textFileName = inputList[1:]  
            parallelizationLevel = int(parallelizationLevel)
            fileNameList.append(textFileName)
            processes = processHandler()
            endingExecuteTimer = datetime.datetime.now()
            historyFileHandler(historyFile, endingExecuteTimer, startingExecutionTime, processes)

    #a opção -a e -f não foram pedidas
    else:   
    # p

        #Checks if there were no filenames given in the arguments
        if len(inputList) < 6:
            inputFileName = input("Insira os nomes dos ficheiros separados apenas por espaços:")
            fileNameList = inputFileName.split()
            countingOption, parallelizationOption, parallelizationLevel, inputWord = inputList[1:5]
            parallelizationLevel = int(parallelizationLevel)
            processes = processHandler()
            
        #Checks if more than one filename was given 
        elif len(inputList) > 6:             
            fileNameList = inputList[5:]
            countingOption, parallelizationOption, parallelizationLevel, inputWord = inputList[1:5]
            parallelizationLevel = int(parallelizationLevel)
            processes = processHandler()
                        
        #If there was only one filename given
        else:                               
            countingOption, parallelizationOption, parallelizationLevel, inputWord, textFileName = inputList[1:]  
            parallelizationLevel = int(parallelizationLevel)
            fileNameList.append(textFileName)
            processes = processHandler()
        
#If the -p option was not used        
else:

    if inputList[2] == "-a":
        
        if inputList[4] == "-f":
            #a f

            #Checks if there were no filenames given in the arguments
            if len(inputList) < 8:
                inputFileName = input("Insira os nomes dos ficheiros separados apenas por espaços:")
                fileNameList = inputFileName.split()
                countingOption, statusOption, statusTimer, historyOption, historyFile, inputWord = inputList[1:7]
                signal.setitimer(signal.ITIMER_REAL, 0.1, float(statusTimer))
                startingSearchTimeSingleProcess = datetime.datetime.now()
                searchWord()
                endingSearchTimeSingleProcess = datetime.datetime.now()
                searchTimeSingleProcess = endingSearchTimeSingleProcess - startingSearchTimeSingleProcess
                print("Número de ocorrências totais =", totalOcurrences.value)
                endingExecuteTimer = datetime.datetime.now()
                historyFileHandlerSingleProcess(historyFile, endingExecuteTimer, startingExecutionTime, fileNameList, fatherPid, searchTimeSingleProcess)
                

            #Checks if more than one filename was given
            elif len(inputList) > 8:         
                fileNameList = inputList[7:]
                countingOption, statusOption, statusTimer, historyOption, historyFile, inputWord = inputList[1:7]
                signal.setitimer(signal.ITIMER_REAL, 0.1, float(statusTimer))
                startingSearchTimeSingleProcess = datetime.datetime.now()
                searchWord()
                endingSearchTimeSingleProcess = datetime.datetime.now()
                searchTimeSingleProcess = endingSearchTimeSingleProcess - startingSearchTimeSingleProcess
                print("Número de ocorrências totais =", totalOcurrences.value)
                endingExecuteTimer = datetime.datetime.now()
                historyFileHandlerSingleProcess(historyFile, endingExecuteTimer, startingExecutionTime, fileNameList, fatherPid, searchTimeSingleProcess)
                
            #If there was only one filename given   
            else:                               
                countingOption, statusOption, statusTimer, historyOption, historyFile, inputWord, textFileName = inputList[1:]
                fileNameList.append(textFileName)
                signal.setitimer(signal.ITIMER_REAL, 0.1, float(statusTimer))
                startingSearchTimeSingleProcess = datetime.datetime.now()
                searchWord()
                endingSearchTimeSingleProcess = datetime.datetime.now()
                searchTimeSingleProcess = endingSearchTimeSingleProcess - startingSearchTimeSingleProcess
                print("Número de ocorrências totais =", totalOcurrences.value)
                endingExecuteTimer = datetime.datetime.now()
                historyFileHandlerSingleProcess(historyFile, endingExecuteTimer, startingExecutionTime, fileNameList, fatherPid, searchTimeSingleProcess)

        else:
            #a
            
            #Checks if there were no filenames given in the arguments
            if len(inputList) < 6:
                inputFileName = input("Insira os nomes dos ficheiros separados apenas por espaços:")
                fileNameList = inputFileName.split()
                countingOption, statusOption, statusTimer, inputWord = inputList[1:5]
                signal.setitimer(signal.ITIMER_REAL, 0.1, float(statusTimer))
                searchWord()
                print("Número de ocorrências totais =", totalOcurrences.value)

            #Checks if more than one filename was given
            elif len(inputList) > 6:         
                fileNameList = inputList[5:]
                countingOption, statusOption, statusTimer, inputWord = inputList[1:5]
                signal.setitimer(signal.ITIMER_REAL, 0.1, float(statusTimer))
                searchWord()
                print("Número de ocorrências totais =", totalOcurrences.value)
                
            #If there was only one filename given   
            else:                               
                countingOption, statusOption, statusTimer, inputWord, textFileName = inputList[1:]
                fileNameList.append(textFileName)
                signal.setitimer(signal.ITIMER_REAL, 0.1, float(statusTimer))
                searchWord()
                print("Número de ocorrências totais =", totalOcurrences.value)

    elif inputList[2] == "-f":
        #f

        #Checks if there were no filenames given in the arguments
            if len(inputList) < 6:
                inputFileName = input("Insira os nomes dos ficheiros separados apenas por espaços:")
                fileNameList = inputFileName.split()
                countingOption, historyOption, historyFile, inputWord = inputList[1:5]
                startingSearchTimeSingleProcess = datetime.datetime.now()
                searchWord()
                endingSearchTimeSingleProcess = datetime.datetime.now()
                searchTimeSingleProcess = endingSearchTimeSingleProcess - startingSearchTimeSingleProcess
                print("Número de ocorrências totais =", totalOcurrences.value)
                endingExecuteTimer = datetime.datetime.now()
                historyFileHandlerSingleProcess(historyFile, endingExecuteTimer, startingExecutionTime, fileNameList, fatherPid, searchTimeSingleProcess)

            #Checks if more than one filename was given
            elif len(inputList) > 6:         
                fileNameList = inputList[5:]
                countingOption, historyOption, historyFile, inputWord = inputList[1:5]
                startingSearchTimeSingleProcess = datetime.datetime.now()
                searchWord()
                endingSearchTimeSingleProcess = datetime.datetime.now()
                searchTimeSingleProcess = endingSearchTimeSingleProcess - startingSearchTimeSingleProcess
                print("Número de ocorrências totais =", totalOcurrences.value)
                endingExecuteTimer = datetime.datetime.now()
                historyFileHandlerSingleProcess(historyFile, endingExecuteTimer, startingExecutionTime, fileNameList, fatherPid, searchTimeSingleProcess)
                
            #If there was only one filename given   
            else:                               
                countingOption, historyOption, historyFile, inputWord, textFileName = inputList[1:]
                fileNameList.append(textFileName)
                startingSearchTimeSingleProcess = datetime.datetime.now()
                searchWord()
                endingSearchTimeSingleProcess = datetime.datetime.now()
                searchTimeSingleProcess = endingSearchTimeSingleProcess - startingSearchTimeSingleProcess
                print("Número de ocorrências totais =", totalOcurrences.value)
                endingExecuteTimer = datetime.datetime.now()
                historyFileHandlerSingleProcess(historyFile, endingExecuteTimer, startingExecutionTime, fileNameList, fatherPid, searchTimeSingleProcess)

    #a opção -a e -f não foram pedidas
    else: 

        #Checks if there were no filenames given in the arguments
        if len(inputList) < 4:
            inputFileName = input("Insira os nomes dos ficheiros separados apenas por espaços:")
            fileNameList = inputFileName.split()
            countingOption, inputWord = inputList[1:3]
            searchWord()
            print("Número de ocorrências totais =", totalOcurrences.value)

        #Checks if more than one filename was given
        elif len(inputList) > 4:         
            fileNameList = inputList[3:]
            countingOption, inputWord = inputList[1:3]
            searchWord()
            print("Número de ocorrências totais =", totalOcurrences.value)
            
        #If there was only one filename given   
        else:                               
            countingOption, inputWord, textFileName = inputList[1:]
            fileNameList.append(textFileName)
            searchWord()
            print("Número de ocorrências totais =", totalOcurrences.value)