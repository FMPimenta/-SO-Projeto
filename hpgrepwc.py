import sys
import pickle

inputList = sys.argv



if inputList[0] == "hpgrepwc.py":

    with open(inputList[1],"rb") as inputF:
        file = pickle.load(inputF)
        i = 0
        for index in file:
            
            if i < 3:
                print(str(index))
            else:
                for u in index:
                    print(str(u))
            i = i + 1
       
    inputF.close() 