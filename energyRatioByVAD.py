from numpy import radians
from vad import VoiceActivityDetector
import argparse
import json

def save_to_file(data, filename):
    with open(filename, 'w') as fp:
        json.dump(data, fp)

def getEnergyRatio(audioPath):
    #parser = argparse.ArgumentParser(description='Analyze input wave-file and save detected speech interval to json file.')
    #parser.add_argument('inputfile', metavar='INPUTWAVE',
                        #help='the full path to input wave file')
    #parser.add_argument('outputfile', metavar='OUTPUTFILE',
                        #help='the full path to output json file to save detected speech intervals')
    #args = parser.parse_args()
    
    
    v = VoiceActivityDetector(audioPath)

    carrier=[] #用于存储各个10ms区间的能量比例
    raw_detection = v.detect_speech(carrier) #这个执行时间最长

    speech_labels = v.convert_windows_to_readible_labels(raw_detection)
    #print(speech_labels)   #label就是很长的、写到json中的那一长条
    #print("这个是label")
    for segment in speech_labels:
        print("人声开始时间：",segment['speech_begin'],end='\t')
        print("人声结束时间：",segment['speech_end'])
    
    save_to_file(speech_labels, './results.json')
    return carrier
 

if __name__ == "__main__":
    ratioSamples=getEnergyRatio('cleanSample/VOCALS1/Buitraker_-_Revo_X/vocals.wav')
    t=0.01
    
    count=0
    for x in ratioSamples:
        count+=1
        print(('%.2f'%t),':',x)
        if(x>1.0):
            print("fuck")
            tmp=input()
        if(x>0.9):
            print("正常")
            if(count%1000==0):
                tmp=input()
        t+=0.01
    