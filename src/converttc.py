import sys;
import os;
import re;

def convertTestCases(dir):
    """ Converts test cases from old to new format """
    for filename in os.listdir(dir):
        if filename.endswith(".txt"):
            with open(os.path.join(dir,filename)) as file:
                text = file.read()
            text = text.replace("FCA","FCRA").replace("FKA","FKRA")
            with open(os.path.join(dir,filename),"w") as file:
                file.write(text)


if __name__ == "__main__":
    if(len(sys.argv) < 2):
        print("Invalid arguments -> converttc inputdir")
    
    inputDir = sys.argv[1]
    convertTestCases(inputDir)
    print("Converting successful")
