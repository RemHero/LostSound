import collections
import contextlib
from energyRatioByVAD import getEnergyRatio
from os import curdir, path
import sys
import wave
from matplotlib.pyplot import bar_label

from numpy import compare_chararrays, true_divide

import webrtcvad


def read_wave(path):
    """Reads a .wav file.

    Takes the path, and returns (PCM audio data, sample rate).
    """
    with contextlib.closing(wave.open(path, 'rb')) as raw:
        num_channels=raw.getnchannels()
        if(num_channels>1):
            import subprocess
            import os
            newPath="单声道音频/tmp.wav"
            cmd='ffmpeg -y -i %s -ar %s -ac 1  %s' %(path,16000,newPath) #16000是我设定的采样率
            os.system(cmd.encode('utf-8').decode('utf-8'))
            subprocess.call(cmd,shell=True)
            path=newPath

    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000, 48000)
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate


def write_wave(path, audio, sample_rate):
    """Writes a .wav file.

    Takes path, PCM audio data, and sample rate.
    """
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)


class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    """Generates audio frames from PCM audio data.

    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.

    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


def vad_collector(sample_rate, frame_duration_ms,
                  padding_duration_ms, vad, frames,carrier):
    """Filters out non-voiced audio frames.

    Given a webrtcvad.Vad and a source of audio frames, yields only
    the voiced audio.

    Uses a padded, sliding window algorithm over the audio frames.
    When more than 90% of the frames in the window are voiced (as
    reported by the VAD), the collector triggers and begins yielding
    audio frames. Then the collector waits until 90% of the frames in
    the window are unvoiced to detrigger.

    The window is padded at the front and back to provide a small
    amount of silence or the beginnings/endings of speech around the
    voiced frames.

    Arguments:

    sample_rate - The audio sample rate, in Hz.
    frame_duration_ms - The frame duration in milliseconds.
    padding_duration_ms - The amount to pad the window, in milliseconds.
    vad - An instance of webrtcvad.Vad.
    frames - a source of audio frames (sequence or generator).

    Returns: A generator that yields PCM audio data.
    """
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    # We use a deque for our sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
    # NOTTRIGGERED state.
    triggered = False

    voiced_frames = []
    print(len(frames)) #有20052个10ms 时长3:20

    timeSpan=0.0
    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, sample_rate)

        sys.stdout.write('1' if is_speech else '0')
        timeSpan+=0.01
        #currentResult=[('%.2f'%timeSpan), is_speech,]
        carrier.append([('%.2f'%timeSpan), is_speech,])
        if not triggered:
            
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])
            # If we're NOTTRIGGERED and more than 90% of the frames in
            # the ring buffer are voiced frames, then enter the
            # TRIGGERED state.
            if num_voiced > 0.9 * ring_buffer.maxlen:
                #计算num_voiced/ring_buffer.maxlen > 0.9 则设定为有人声！
                triggered = True
                sys.stdout.write('+(%s)' % (ring_buffer[0][0].timestamp,))
                # We want to yield all the audio we see from now until
                # we are NOTTRIGGERED, but we have to start with the
                # audio that's already in the ring buffer.
                for f, s in ring_buffer:
                    voiced_frames.append(f)
                ring_buffer.clear()
        else:
            # We're in the TRIGGERED state, so collect the audio data
            # and add it to the ring buffer.
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])
            # If more than 90% of the frames in the ring buffer are
            # unvoiced, then enter NOTTRIGGERED and yield whatever
            # audio we've collected.
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
                sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
                triggered = False
                yield b''.join([f.bytes for f in voiced_frames])
                ring_buffer.clear()
                voiced_frames = []
    if triggered:
        sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
    sys.stdout.write('\n')
    # If we have any leftover voiced audio when we run out of input,
    # yield it.
    if voiced_frames:
        yield b''.join([f.bytes for f in voiced_frames])


def testSingleSong(path,recorder,songName):
    
    audio, sample_rate = read_wave(path)
    vad = webrtcvad.Vad(3)
    span=10
    frames = frame_generator(span, audio, sample_rate)
    frames = list(frames)

    #carrier保存了时间节点、概率
    carrier=[]
    segments = vad_collector(sample_rate, span, span*5, vad, frames,carrier)
    for i, segment in enumerate(segments):
        pass
        '''
        path = 'chunk-%002d.wav' % (i,)
        print(' Writing %s' % (path,))
        write_wave(path, segment, sample_rate)
        '''
    '''
    for x in carrier:
        print(x[0],x[1])
    '''
    #将下划线全部替换为空格，得到真实歌名formalName
    formalName=list(songName)
    maxpos=len(songName)-1
    i=0
    while(i<=maxpos):
        if(formalName[i]=='_'):
            formalName[i]=' '
        if(formalName[i]=='%'):
            formalName[i]='&'
        i+=1
    tmpstr=""
    for x in formalName:
        tmpstr+=x
    formalName=tmpstr

    #1、先将carrier复制到finalCarrier
    finalCarrier=[]
    for timeP in carrier:
        if(timeP[1]==True):
            timeP[1]=1
        else:
            timeP[1]=0
        duplicate=[]
        for x in timeP:
            duplicate.append(x)
        duplicate[1]=4
        finalCarrier.append(duplicate)

    #仅用于测试
    print("修正前")
    for x in carrier:
        print(x[1],end='')

    #2、为了解决保证连续性，只需考虑周围4个元素是否一致
    #若一致，则直接同化carrier[i]
    i=0
    maxpos=len(carrier)-1
    while(i<=maxpos):
        flag=True
        k=i-4
        commonValue=None
        if(i-1>=0):
            commonValue=carrier[i-1][1]
        else:
            commonValue=carrier[i+1][1]
        while(k<=i+4 and flag):
            if((not k==i)and k>=0 and k<=maxpos and carrier[k][1]!=commonValue):
                flag=False
            k+=1
        if(flag==True):
            #则finalcarrier[i]被周围同化，并且i-4 i+4全部被同化
            k=i-4
            while(k<=i+4):
                if(k>=0 and k<=maxpos):
                    finalCarrier[k][1]=commonValue
                    carrier[k][1]=commonValue
                k+=1
        if(flag==False):
            #如果1之间的0的个数较少，则将0全部翻转为1
            left=i-1
            while(left>0 and left>=i-4):
                if(carrier[left][1]==1):break
                left-=1
            right=i+1
            while(right<=maxpos and right<=i+4):
                if(carrier[right][1]==1):break
                right+=1
            if(left>0 and left>=i-4 and right<=maxpos and right<=i+4):
                if(right-left<=6):
                    k=left
                    while(k<=right):
                        carrier[k][1]=1
                        finalCarrier[k][1]=1
                        k+=1
        i+=1




    energyArr=getEnergyRatio(path)
    #最后一步：将4填充为0.9 0.8……
    
    i=0
    for x in finalCarrier:
        if(x[1]>1):
            #用能量比例代替
            pos=i
            if(pos>len(energyArr)-1):
                pos=len(energyArr)-1
            x[1]=energyArr[pos]
        i+=1
    
    print("分割线-------------分割线")
    
    for x in finalCarrier:
        if(x[1]>1):
            print("出问题了")
            tmp=input()
        elif(x[1]>0 and x[1]<1):
            print("6",end='')
        else:
            print(x[1],end='')

        
    if(len(carrier)==len(finalCarrier)):
        print("两者等长")
        print("长度为",len(finalCarrier))
    else:
        print("出问题了")


    #开始写入文件
    import csv
    carrier=finalCarrier
    csvWriter=csv.writer(recorder)
    for timePerhaps in carrier:
        line=[formalName,]
        for i in timePerhaps:
            line.append(i)
        csvWriter.writerow(line)

def main():
    #testSingleSong('cleanSample/VOCALS1/Georgia_Wonder_-_Siren/vocals.wav')
    import csv
    recorder=open('resultForTest3.csv','w',encoding='utf-8',newline="")
    import os
    vocalGroup=os.listdir('cleanSample')
    import energyRatioByVAD
    for vocalx in vocalGroup:
        if os.path.isdir('cleanSample/'+vocalx):
            songGroup=os.listdir('cleanSample/'+vocalx)
            for singleSong in songGroup:
                
                path='cleanSample'+'/'+vocalx+'/'+singleSong+'/'+'vocals.wav'
                print('歌名:',path)
                testSingleSong(path,recorder,singleSong)

    recorder.close()        
if __name__ == '__main__':
    main()
