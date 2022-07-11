"""
Functions used in the project
"""

######      Import Packages     ######
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import h5py
import random

import mplfinance as mpf
from PIL import Image # load and show an image with Pillow
#import PIL
#print('Pillow Version:', PIL.__version__)
from numpy.random import randint
from numpy.random import seed

from datetime import datetime, timedelta #Date arithmetic
import datetime
import time
import os
import gc
import multiprocessing as mp
from os.path import exists

import glob #read csv files pattern matching
import re #regex

#import tensorflow as tf
#import tensorflow_io as tfio


######   Config params  ######
DATE_WINDOW = 6 # Sliding window for generating the charts
UP_THRESHOLD_PCT = 1 # Stock price change above this will be treated as 'UP' movement
DOWN_THRESHOLD_PCT = 1 # Stock price change below this will be treated as 'DOWN' movement
IMG_SIZE = 128

########    Data Functions   ########



def samplesCount(noOfFiles,folder):
    file_counter = 1
    samples = 0
    for file in os.listdir(folder):
        if file_counter > noOfFiles:
            break
        if file.endswith(".h5"):
            fname = os.path.join(folder, file)
            file = h5py.File(fname, "r")
            set_x = file["set_x"][:]
            
            # print(set_x.shape[0])
            samples = samples + set_x.shape[0]

            file.close()
            file_counter += 1
    # print(samples)        
    return samples


def createIODataset(noOfFiles,folder):    
    firstFile = True
    file_counter = 1
    samples_counter = 0
    for file in os.listdir(folder):
        # print(file)
        if file_counter > noOfFiles:
            break       
    
        if file.endswith(".h5"):
            fname = os.path.join(folder, file)
            # print(fname)

            if firstFile:
                set_x = tfio.IODataset.from_hdf5(filename=fname, dataset='/set_x')
                set_y = tfio.IODataset.from_hdf5(filename=fname, dataset='/set_y')
                firstFile = False
            else:
                set_x = set_x.concatenate(tfio.IODataset.from_hdf5(filename=fname, dataset='/set_x'))
                set_y = set_y.concatenate(tfio.IODataset.from_hdf5(filename=fname, dataset='/set_y'))
                
            # file.close()
            file_counter += 1

    out = tf.data.Dataset.zip((set_x,set_y))
    
    return out




def readXYfromDisk(noOfFiles,folder):
    """
    Reads .h5 files
    Appends them to a list
    Finally converts the list to np
    """

    set_x = []
    set_y = []
    
    file_counter = 1
    for file in os.listdir(folder):
        # print(file)
        if file_counter > noOfFiles:
            break
        if file.endswith(".h5"):
            fname = os.path.join(folder, file)
            file = h5py.File(fname, "r")
            set_x_temp = file["set_x"][:]
            set_y_temp = file["set_y"][:]

            # print('X Shape : ', set_x_temp.shape, 'Y Shape: ',set_y_temp.shape,' ',fname)

            set_x.append(set_x_temp)
            set_y.append(set_y_temp)

            file.close()
            file_counter += 1

    # Since set_x and set_y are list of arrays, use np.concatenate()
    # Better than result_array = np.array(result) ?

    set_x = np.concatenate(set_x,axis=0)
    set_y = np.concatenate(set_y,axis=0)

    # print('X Shape : ', set_x.shape, calcArrayMemorySize(set_x)
    #         ,'Y Shape: ',set_y.shape)
    # values, counts = np.unique(set_y, axis=0, return_counts=True)
    # print('Values, counts, Avg Performance : ', values,counts,counts / counts.sum())

    return set_x,set_y


def computeMeanRGB(noOfFiles,folder):
    """
    
    """

    meanRGB = np.array([])

    file_counter = 1
    for file in os.listdir(folder):
        # print(file)
        if file_counter > noOfFiles:
            break
        if file.endswith(".h5"):

            fname = os.path.join(folder, file)
            file = h5py.File(fname, "r")
            set_x = file["set_x"][:]            

            set2D = set_x.reshape(set_x.shape[0],-1)
            set2Dmean = np.mean(set2D,1)
           
            # print(set2Dmean.shape)
            meanRGB = np.concatenate((meanRGB,set2Dmean),axis=0)

            file.close()
            file_counter += 1

    
    return meanRGB


def plotImageHist(noOfFiles,folder):
    """
    
    """

    file_counter = 1
    for file in os.listdir(folder):
        # print(file)
        if file_counter > noOfFiles:
            break
        if file.endswith(".h5"):

            fname = os.path.join(folder, file)
            file = h5py.File(fname, "r")
            set_x = file["set_x"][:]            

            set2D = set_x.reshape(set_x.shape[0],-1)
            set2Dmean = np.mean(set2D,1)
            plt.hist(set2Dmean,bins=20)
            plt.title(file)
            plt.show()
    
            file.close()
            file_counter += 1

    
    return 0



def updateYtoBinary(fromFolder,toFolder):
    """ The target variable was setup for multi-class classification
    Change to Binary
    """
    
    file_counter = 1
    for file in os.listdir(fromFolder):
        if file.endswith(".h5"):
            in_fname = os.path.join(fromFolder, file)
            in_file = h5py.File(in_fname, "r")

            out_fname = os.path.join(toFolder, file)
            out_file = h5py.File(out_fname, "w")

            set_x = in_file["set_x"]
            set_y = in_file["set_y"][:]

            set_y[set_y == 1] = 0
            set_y[set_y == 2] = 1
            
            out_file.create_dataset('set_x', data=set_x,dtype='uint8')
            out_file.create_dataset('set_y', data=set_y,dtype='uint8')

            in_file.close()
            out_file.close()

            file_counter += 1



def cleanOutliers(fromFolder,toFolder,LOWER_RANGE,UPPER_RANGE):
    """ Create datasets without outliers
    """
    
    file_counter = 1
    for file in os.listdir(fromFolder):
        if file.endswith(".h5"):
            in_fname = os.path.join(fromFolder, file)
            in_file = h5py.File(in_fname, "r")

            out_fname = os.path.join(toFolder, os.path.splitext(file)[0] + '_CLEAN'+os.path.splitext(file)[1])            
            out_file = h5py.File(out_fname, "w")

            set_x = in_file["set_x"][:]
            set_y = in_file["set_y"][:]

            # print(set_x.shape)
            # print(set_y.shape)

            set_x_mean = np.mean(set_x.reshape(set_x.shape[0],-1),1)
            indicesWithinRange = np.where([(set_x_mean > LOWER_RANGE) & (set_x_mean < UPPER_RANGE)])[1]

            # print(indicesWithinRange.shape)
            set_x = set_x[indicesWithinRange]
            set_y = set_y[indicesWithinRange]
            
            # print(set_x.shape)
            # print(set_y.shape)
            # print("\n\n\n")

            out_file.create_dataset('set_x', data=set_x,dtype='uint8')
            out_file.create_dataset('set_y', data=set_y,dtype='uint8')

            in_file.close()
            out_file.close()

            file_counter += 1
    return print("cleaned")



def upsamplePositives(fromFolder,toFolder):
    """ Create dataset with 80% positive samples
    """
    
    file_counter = 1
    for file in os.listdir(fromFolder):
        if file.endswith(".h5"):
            in_fname = os.path.join(fromFolder, file)
            in_file = h5py.File(in_fname, "r")

            out_fname = os.path.join(toFolder, os.path.splitext(file)[0] + '_UPSAMPLED'+os.path.splitext(file)[1])            
            out_file = h5py.File(out_fname, "w")

            set_x = in_file["set_x"][:]
            set_y = in_file["set_y"][:]

            # Take all the positives
            set_x_P = set_x[set_y == 1]
            set_y_P = set_y[set_y == 1]

            #Include some random negatives (20%)
            positives_count = set_y[set_y == 1].shape[0]
            negatives_count = set_y[set_y == 0].shape[0]

            negatives_random = random.sample(range(0,negatives_count-1),np.int(round(positives_count * 0.2,0)))

            set_x_N = set_x[negatives_random]
            set_y_N = set_y[negatives_random]          

            # Combine            
            set_x = np.concatenate((set_x_P,set_x_N),axis = 0)
            set_y = np.concatenate((set_y_P,set_y_N),axis = 0)

            out_file.create_dataset('set_x', data=set_x,dtype='uint8')
            out_file.create_dataset('set_y', data=set_y,dtype='uint8')

            in_file.close()
            out_file.close()

            file_counter += 1






def saveXYtoDisk(result,folder,fname):
    """
    Function that separates x and y
    And also created .h5 files to save the arrays
    """
    first = [x for (x,y) in result]
    set_y = np.concatenate(first,axis =0)

    second = [y for (x,y) in result]
    set_x = np.concatenate(second,axis =0)

    print(fname)

    file = h5py.File(folder + fname + ".h5", "w")
    file.create_dataset('set_x', data=set_x,dtype='uint8')
    file.create_dataset('set_y', data=set_y,dtype='uint8')
    file.close()


def setTargetLabel(val):    
    if val >= UP_THRESHOLD_PCT: out = 2
    elif val <= -DOWN_THRESHOLD_PCT: out = 1
    else: out = 0
    return out


def dataPrep(fname):
    df = pd.read_csv(fname,parse_dates=[1]) #,index_col=1)
    df.columns = ['Symbol','Date','Open','High','Low','Close','Volume','Adjusted']
    df = df[df['Close'] > 0]
    #Compute Growth and Target column
    df['Close_Prev'] = df.groupby(['Symbol'])['Close'].shift(1)
    df = df[df['Close_Prev'] > 0] #Remove rows with no data
    df['Target_val'] = (100 * ((df['Close']/df['Close_Prev']) - 1))
    df['Target'] = (100 * ((df['Close']/df['Close_Prev']) - 1)).apply(setTargetLabel)
    #df.groupby(['Target'])['Target'].count()
    return df

def createCandlesticksPlot(data,index,targetLabel,inRAM = False):  
    """
    Core function that creates the plot and saves to a file
    Argument:
    data -- to be done
    index -- to be done
    Returns:
    None -- to be done

    """      
    title = data[:1]['Date'].item().strftime('%d-%b-%Y') + " " + data[-1:]['Date'].item().strftime('%d-%b-%Y') + " Lbl:" + str(targetLabel)

    # To set a datetime as an index
    data = data.set_index(pd.DatetimeIndex(data['Date'])) 


   
    #Create custom styles
    mc = mpf.make_marketcolors(up='black'
                               ,down='black'
                               ,volume='black'
                               ,ohlc='black'
                               ,edge='inherit'
                               ,wick={'up':'black','down':'black'}
                               ,alpha = 1.0)

    rc = {'xtick.major.bottom':False
        ,'ytick.major.left':False
        ,'xtick.major.size':0
        ,'ytick.major.size':0
        ,'axes.labelsize' : 0
        #,'savefig.jpeg_quality' : 95
        ,'savefig.bbox':'tight'
        ,'savefig.facecolor':'white'
        ,'axes.spines.left' :False #plot border
        ,'axes.spines.top' :False
        ,'axes.spines.bottom' :False
        ,'axes.spines.right' :False

        }
    s  = mpf.make_mpf_style(marketcolors=mc,rc = rc,mavcolors = ['black'])
    
    # First we set the kwargs that we will use for all of these examples:
    kwargs = dict(type='ohlc',volume=True,figratio=(3,3) #was (5,5)
                    ,figscale=3, mav = (2,6)
                    #,title = title
                    )
    #mpf.plot(data,**kwargs,style = s,savefig=r'data/temp_image.png')
    
    #mpf.plot(data,**kwargs,style = s,savefig='data/temp_image'+ str(index) +'.png')
    #mpf.plot(data,**kwargs,style = s,savefig='/ramdisk/temp_image'+ str(index) +'.png')

    if inRAM == True:
        mpf.plot(data
                ,**kwargs
                ,scale_width_adjustment=dict(ohlc=1,lines=2,volume=1)
                ,update_width_config=dict(ohlc_linewidth=8,volume_linewidth=0.01)
                ,style = s
                ,savefig='temp_image'+ str(index) +'.png') #'/ramdisk/temp_image'+ str(index) +'.png')
    elif inRAM == False:
        mpf.plot(data,**kwargs,style = s,savefig='data/temp_image'+ str(index) +'.png')


    #time.sleep(1)


def applyParallel_groupby(dfGrouped, func):
    """To be used when data is split using df.groupby() """
    with mp.Pool(processes = mp.cpu_count()) as p:
        ret_list = p.map(func, [group for name, group in dfGrouped])
    p.close()    
    #p.join()    
    return ret_list
    #return pd.concat(ret_list)

def applyParallel_npsplit(dfGrouped, func):
    """To be used when data is split using np.array_split """
    with mp.Pool(processes = mp.cpu_count()) as p:
        ret_list = p.map(func, dfGrouped)
    p.close()    
    return ret_list


def createXYarrays(group):

    """
    Function that will be called by multiprocessing 
    Separate process will spawned for each Symbol
    First attempt was creating set_x_sub as a list but later settled with single array containing both x and y ie set_xy
    """

    loop_range=  (group['Symbol'].count()) -  (DATE_WINDOW) - 10        
    #loop_range = 5
    symbolDate = group[-1:]['Date'].item()
    symbolDate = symbolDate.strftime('%Y%m%d')

    fname = str(group[-1:]['Symbol'].item()[0:3]) + str(symbolDate)
    #random_no = randint(1e10) #Random number for each CPU to be appended to the file name

    set_xy = (np.empty(shape=(loop_range),dtype = 'uint8')
            ,np.empty(shape=(loop_range,IMG_SIZE,IMG_SIZE,3)))

    
    for i in range(loop_range):    
        
        if i % 100 == 0:
            print("Iter:" + str(i))    

        targetLabel = group[-1:]['Target'].item()
        set_xy[0][i] = targetLabel

        #print(set_xy[0][i])
        #Remove the last row and plot
        group = group[:-1]        
        

        ### Create temp file ON HARD DISK ## 
        #create_candlesticks(group[-DATE_WINDOW:],fname,inRAM=False)
        #img_asNumpy = np.array(Image.open('data/temp_image'+ fname + '.png').resize((IMG_SIZE,IMG_SIZE)))
        
        ### Create temp file ON RAM DISK ## 
        createCandlesticksPlot(group[-DATE_WINDOW:],fname
                            ,targetLabel = targetLabel
                            ,inRAM=True)
        img_asNumpy = np.array(Image.open('temp_image'+ fname + '.png').resize((IMG_SIZE,IMG_SIZE)))
        
        #image_without_alpha 
        img_asNumpy = img_asNumpy[:,:,:3]
        
        set_xy[1][i] = img_asNumpy
    
    #out = {"set_y": set_y_sub,"set_x": set_x_sub}
    #return out
    #return [set_y_sub,set_x_sub]
    return set_xy


def calcArrayMemorySize(array):
    return "Memory size is : " + str(array.nbytes/1024/1024) + " Mb"



