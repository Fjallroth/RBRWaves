##Import relevant modules

import oceanlyz
import numpy as np
import matplotlib.pyplot as plt
import csv
import pandas as pd
import seaborn as sns
from datetime import datetime , timedelta

##Define user needs

print ("This script is used to process data from Ruskin software for RBR. Make sure this script is saved in the same folder as the csv file containing burst data downloaded from Ruskin. Bulk parameters will be calculated and plotted. \nIf you have only burst data from Ruskin, please enter 1. If you have already processed the data and just want to plot data from RBR, please enter 2. \nIn the latter case, make sure the csv files named Hs.csv; Hm01.csv and Tp.csv are in the same folder as this python script.")
res=int(input("Enter 1 or 2:"))


##Extract water level data
if (res !=1 and res!=2):
    print("There was an error in your entry. Please run again this script.")
    quit()


elif res == 1:
    print("This script will extract only the depth data from the RSK input, the process will take quite some time for large files")
    print("It is assumed at this stage you have exported the zip file from Ruskin and extracted the data into your working folder")
    file = input("please enter file name from Ruskin. The data should be saved in the same folder as the python script. Include the extention e.g. .csv ")
    freq = int(input("state sampling frequency in Hz "))
    period = int(input("How long do you want the burst period in minutes to be? (normally 30 minutes) "))

    print("Script started")

    with open('outputb.csv', 'w', newline='') as outputfile:
        with open(file, newline='') as feed:
            writer = csv.writer(outputfile, delimiter=',', quotechar='"')
            reader = csv.reader(feed, delimiter=',', quotechar='"')
            for row in reader:
                writer.writerow([row[3]])

    print('depth data extracted, removing header')

    with open("outputb.csv",'r') as f:
        with open("inputfile.csv",'w') as f1:
            next(f) # skip header line
            for line in f:
                f1.write(line)
    print('data saved as inputfile.csv')

    file = open("inputfile.csv")
    reader = csv.reader(file)
    lines= len(list(reader))

    print('the data has', lines, 'data points')

    burst = (lines // (period*60*freq))
    print("\033[1;35mNumber of bursts is", burst, "bursts")
    print("The water level data is now saved in the csv file inputfile.csv")



    ##Calculation wave statistics

    print("The calculation of wave statistics has started. This could take some time for large files. Burst statistics will appear in this window while they are being calculated. All data will then be saved in csv files.")

    ocn=oceanlyz.oceanlyz()

    waterlevel = np.genfromtxt('inputfile.csv') #Load data

    #Defines data type and what will be calculated in this script
    ocn.data=waterlevel.copy()
    ocn.InputType='waterlevel' # Data extracted before is water level data
    ocn.OutputType='wave+waterlevel'
    ocn.AnalysisMethod='spectral' # Spectral analysis used

    #Parameters of the dataset
    ocn.n_burst=burst
    ocn.burst_duration=period*60
    ocn.fs=freq
    ocn.heightfrombed=0.4      #Height of the sensor from the seabed

    #Define number of data points in discrete Fourier transform
    ocn.nfft=2**10

    #Separation between wind seas and swell seas
    ocn.SeparateSeaSwell='no'
    ocn.fpminswell=0.1
    ocn.fmaxswell=0.25

    #Pressure attenuation
    ocn.pressureattenuation='all'
    ocn.fmaxpcorrCalcMethod='auto'
    ocn.Kpafterfmaxpcorr='constant'
    ocn.fminpcorr=0.15
    ocn.fmaxpcorr=0.55


    #Cutting the spectra below and above given frequencies
    ocn.mincutoff='off'
    ocn.fmin=0.04
    ocn.maxcutoff='off'
    ocn.fmax=1


    #Tail correction
    ocn.tailcorrection='off'
    ocn.ftailcorrection=0.9
    ocn.tailpower=-5


    #Display the results while they are calculated
    ocn.dispout='yes'

    #Seawater density (Varies)
    ocn.Rho=1024


    #Run OCEANLYZ
    ocn.runoceanlyz()
    plt.show


    #save Hm0 to CSV
    Hs = ocn.wave["Hm0"]
    np.savetxt("Hs.csv", Hs, delimiter=",")

    #save Tp to CSV
    Tp = ocn.wave["Tp"]
    np.savetxt("Tp.csv", Tp, delimiter=",")

    #save fp to CSV
    fp = ocn.wave["fp"]
    np.savetxt("fp.csv", fp, delimiter=",")

    #save f to CSV
    f = ocn.wave["f"]
    np.savetxt("f.csv", f, delimiter=",")

    #save Syy to CSV
    Syy = ocn.wave["Syy"]
    np.savetxt("Syy.csv", Syy, delimiter=",")

    #save Tm to CSV
    Tm = ocn.wave["Tm01"]
    np.savetxt("Tm01.csv", Tm, delimiter=",")


##Plotting results

#import data from user input
print("This part of the python script will read the RBR data as obtained after the extraction of data in Ruskin and the processing with the oceanlyz routine.  \nThis .py file you are currently running must be saved in the same folder location as the data obtained after running the oceanlyz routine. The graphs will be saved in the same folder as PNG files.\nIf you have already run this script, please delete the file Wave_data_vetted.csv, all png files and the Wave_analysis.txt file created before going further with this process. Otherwise, there might be errors raising during the process. ")


##reading data
# Importing significant wave height, peak period and mean period data

Hs=pd.read_csv('Hs.csv',na_values={'-','Inf'})
Tp=pd.read_csv('Tp.csv',na_values={'-','Inf'})
Tm=pd.read_csv('Tm01.csv',na_values={'-','Inf'})

#define combined_csv as the data set containing all previous data

combined_csv=pd.concat([Hs,Tp,Tm], axis=1)
combined_csv.columns=['Significant Wave Height (m)','Peak Period (s)', 'Mean Period (s)']

#Starting date and time of recording
print('\033[1;35mPlease enter the first sample time (the one from Ruskin in Overview section). \nBy default, this script considers that the combined_csv has counted 30-minute bursts. If this is not the case, change the delta parameter in the script.')
date_string=input ("Enter the first sample time in the following format: dd/mm/yyyy HH:MM:SS  :")
start_date=datetime.strptime(date_string,'%d/%m/%Y %H:%M:%S')
date=[start_date]
for i in range (len(Hs)-1):
    date.append(date[i]+timedelta(minutes=30))

#Check that the ending date corresponds to what was announced by Ruskin
print('\033[1;32mPlease check that the last sample time from Ruskin coincides with the following date :'+str(date[-1]))

#Add the date column based on the starting date
combined_csv.insert(0,'Date', date)

#Create a csv file containing all wave data
combined_csv.to_csv("Wave_data_vetted.csv", index=False, encoding='utf-8-sig')

#Reading this new file
#combined_csv = pd.read_csv('Wave_data_vetted.csv', usecols= ['Date', 'Significant Wave Height (m)', 'Peak Period (s)', 'Mean Period (s)'])

#remove spaces and replace with _
combined_csv.columns = combined_csv.columns.str.replace(' ','_')

#make time the index
combined_csv['Date'] = pd.to_datetime(combined_csv['Date'], format = '%d/%m/%Y %H:%M:%S')
#print (combined_csv.head())
combined_csv.index = combined_csv['Date']
del combined_csv['Date']

# Delete duplicates (in case of raising error)
combined_csv = combined_csv[~combined_csv.index.duplicated()]

##Calculations peak period according to DNV-RP-C205

#This sections aims at calculating peak period from mean period. Indeed, Spotter and RBR use a frequency grid for spectrum so peak frequency can only take on discretised values on this frequency grid. Therefore the peak period is also discretised, which makes no physical sense.
# According to DNV-RP-C205, some calculations can be done to get the peak period from the mean period, depending on the parameter gamma. This parameter was estimated thanks to some trials on data, but it can be modified below.

gamma=4
Tp=[]
for i in range (len(combined_csv['Mean_Period_(s)'])):
    Tp.append(combined_csv['Mean_Period_(s)'][i]/(0.7303+0.04936*gamma-0.006556*gamma**2+0.0003610*gamma**3))
combined_csv['Calculated_Tp_(s)']=Tp

##creating plots

#time series of sig wave height
sns.set_theme(style ="darkgrid", font='sans-serif')
plt.figure(figsize = (15,8))
sigWave = sns.lineplot(x ='Date', y = 'Significant_Wave_Height_(m)', data = combined_csv, linewidth=0.8)
sigWave.set_xlabel("Date", fontsize = 20)
sigWave.set_ylabel("Significant Wave Height (m)", fontsize = 20)
sigWave.set_title("Timeseries of Significant Wave Height", fontsize=20, fontweight='bold')
fig_sigWave = sigWave.get_figure()
fig_sigWave.savefig("sigWave.png")

#time series of peak period
plt.figure(figsize = (15,8))
peakP = sns.lineplot(x ='Date', y = 'Peak_Period_(s)', data = combined_csv, linewidth=0.5)
peakP.set_xlabel("Date", fontsize = 20)
peakP.set_ylabel("Peak Period (s)", fontsize = 20)
peakP.set_title("Timeseries of Peak Period", fontsize=20, fontweight='bold')
fig_peakP = peakP.get_figure()
fig_peakP.savefig("peakP.png")

#time series of peak period calculated with DNV
plt.figure(figsize = (15,8))
peakP = sns.lineplot(x ='Date', y = 'Calculated_Tp_(s)', data = combined_csv, linewidth=0.5)
peakP.set_xlabel("Date", fontsize = 20)
peakP.set_ylabel("Peak Period (s)", fontsize = 20)
peakP.set_title("Timeseries of Peak Period", fontsize=20, fontweight='bold')
fig_peakP = peakP.get_figure()
fig_peakP.savefig("peakP_DNV_gamma4.png")

#time series of mean period
plt.figure(figsize = (15,8))
meanP = sns.lineplot(x ='Date', y = 'Mean_Period_(s)', data = combined_csv, linewidth=0.5)
meanP.set_xlabel("Date", fontsize = 20)
meanP.set_ylabel("Mean Period (s)", fontsize = 20)
meanP.set_title("Timeseries of Mean Period", fontsize=20, fontweight='bold')
fig_meanP = meanP.get_figure()
fig_meanP.savefig("meanP.png")


#scatter plot Hs vs Peak Period
plt.figure(figsize = (10,10))
hsPeakScatter = sns.scatterplot(data= combined_csv, x = 'Peak_Period_(s)', y = 'Significant_Wave_Height_(m)')
hsPeakScatter.set_xlabel("Peak Period (s)", fontsize = 20)
hsPeakScatter.set_ylabel("Significant Wave Height (m)", fontsize = 20)
hsPeakScatter.set_title("Scatterplot of Significant Wave Height vs Peak Period", fontsize=20, fontweight='bold')
fig_hsPeakScatter = hsPeakScatter.get_figure()
fig_hsPeakScatter.savefig("hsPeakScatter.png")

#scatter plot Hs vs Peak Period (calculated DNV)
plt.figure(figsize = (10,10))
hsPeakScatter = sns.scatterplot(data= combined_csv, x = 'Calculated_Tp_(s)', y = 'Significant_Wave_Height_(m)')
hsPeakScatter.set_xlabel("Peak Period (s)", fontsize = 20)
hsPeakScatter.set_ylabel("Significant Wave Height (m)", fontsize = 20)
hsPeakScatter.set_title("Scatterplot of Significant Wave Height vs Peak Period", fontsize=20, fontweight='bold')
fig_hsPeakScatter = hsPeakScatter.get_figure()
fig_hsPeakScatter.savefig("hsPeakScatter_DNV_gamma4.png")


#scatter plot Hs vs Mean Period
plt.figure(figsize = (10,10))
hsMeanScatter = sns.scatterplot(data= combined_csv, x = 'Mean_Period_(s)', y = 'Significant_Wave_Height_(m)')
hsMeanScatter.set_xlabel("Mean Period (s)", fontsize = 20)
hsMeanScatter.set_ylabel("Significant Wave Height (m)", fontsize = 20)
hsMeanScatter.set_title("Scatterplot of Significant Wave Height vs Mean Period", fontsize=20, fontweight='bold')
fig_hsMeanScatter = hsMeanScatter.get_figure()
fig_hsMeanScatter.savefig("hsMeanScatter.png")

#Histogram significant wave height
plt.figure (figsize = (15,8))
hsHistogram = sns.histplot(data = combined_csv, x = 'Significant_Wave_Height_(m)',stat='percent',binwidth=0.02)
hsHistogram.set_xlabel ("Significant Wave Height (m)", fontsize = 20)
hsHistogram.set_ylabel ("Frequency (%)", fontsize = 20)
hsHistogram.set_title("Histogram of Significant Wave Height Over Measurement Period", fontsize=20, fontweight='bold')
fig_hsHistogram = hsHistogram.get_figure()
fig_hsHistogram.savefig("hsHistogram.png")

#Histogram peak period
plt.figure (figsize = (15,8))
peakPHistogram = sns.histplot(data = combined_csv, x = 'Peak_Period_(s)',stat='percent',binwidth=0.25)
peakPHistogram.set_xlabel ("Peak Period (s)", fontsize = 20)
peakPHistogram.set_ylabel ("Frequency (%)", fontsize = 20)
peakPHistogram.set_title("Histogram of Peak Wave Period Over Measurement Period", fontsize=20, fontweight='bold')
fig_peakPHistogram = peakPHistogram.get_figure()
fig_peakPHistogram.savefig("peakPHistogram.png")

#Histogram peak period DNV
plt.figure (figsize = (15,8))
peakPHistogram = sns.histplot(data = combined_csv, x = 'Calculated_Tp_(s)',stat='percent',binwidth=0.25)
peakPHistogram.set_xlabel ("Peak Period (s)", fontsize = 20)
peakPHistogram.set_ylabel ("Frequency (%)", fontsize = 20)
peakPHistogram.set_title("Histogram of Peak Wave Period Over Measurement Period", fontsize=20, fontweight='bold')
fig_peakPHistogram = peakPHistogram.get_figure()
fig_peakPHistogram.savefig("peakPHistogram_DNV_gamma4.png")

#Histogram mean period
plt.figure (figsize = (15,8))
meanPHistogram = sns.histplot(data = combined_csv, x = 'Mean_Period_(s)',stat='percent',binwidth=0.25)
meanPHistogram.set_xlabel ("Mean Period (s)", fontsize = 20)
meanPHistogram.set_ylabel ("Frequency (%)", fontsize = 20)
meanPHistogram.set_title("Histogram of Mean Wave Period Over Measurement Period", fontsize=20, fontweight='bold')
fig_meanPHistogram = meanPHistogram.get_figure()
fig_meanPHistogram.savefig("meanPHistogram.png")

plt.show()


## Creating a txt file with some results

#Write highest 10 values of significant wave height in text file 'Wave_analysis.txt'
#using previously defined Hs

Hs=round(combined_csv['Significant_Wave_Height_(m)'],2)

sorted_index_array = np.argsort(Hs)
sorted_array = Hs[sorted_index_array]
n= 10
rslt = sorted_array[-n : ]
Hsmax=float(rslt[-1])
H=round(2*Hsmax/3,2)
H100=round(1.67*Hsmax,2)
Hmax=round(2*Hsmax,2)

file=open("Wave_analysis.txt","x")
file.writelines(["{} largest values of Hs and corresponding time:\n".format(n),str(rslt)])
file.close()


print("\033[1;34mThis script has been successfully completed. You will find the graphs in your working directory as well as a txt file with the 10 highest significant wave heights recorded.")
