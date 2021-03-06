from __future__ import print_function

import time
import datetime
import os, fnmatch
import psutil
import csv
import sys
import numpy as pynum
import pickle
#import sqlite3  
import mysql.connector

from secrets import randbelow


pFile = ""
table = ""

PriceCol = 0
SignalCol = 1
FdaCol = 2
FdaAll = 3	

period = 0 # period for calculating FDA in our adaptive thing

arrReports=[]
	
fda_low = 0.0
fda_high = 0.0
	
def write2mysql(ss):
	mydb = mysql.connector.connect(
		host="localhost",
		user="root",
		passwd="xsjhk%123SD==-Ghk11",
		database="altreva"
	)

	mycursor = mydb.cursor()
	for s in ss:
	
		#print (s)
		a = s.split(",")
	
		#print(table)
		'''
		0 05k_7btc_3-optimized.pkl,
		1 period
		2 0.55,
		3 0.55,
		4 1,
		5 0.5,
		6 -2855.340000000004,
		7 -18.049999999997453
		'''
		sql = "INSERT INTO " + table + " (file, fda_period, fda_min, fda_max, maj_threshold, fda_all_min, dd,  PnL) VALUES ('" + a[0] + "'," + str(period) + "," + a[1] + "," + a[2]+ "," +a[3] + "," + a[4] + "," + a[5] + "," + a[6] + ")"
		#print(sql)
		mycursor.execute(sql)
	
	mydb.commit()
	mydb.close()
	#print('wrote to mysql')

	

def system_test():

	mmin = 1
	mmax = 1 # len(arrReports)/3 # TODO: actually delete that value by 4! ///  this gets us the amount of models in total
	mstep = 1
	sql =""
	
	
	#print(len(arrReports),arrReports[0])
	#exit()
	rows = len(arrReports[0])
	s = []
	

	for fda_all_t in pynum.arange(0.50, 0.52, 0.005): # pynum.arange(0.50, 0.52, 0.005):
		# majority voting threshold value
		#print("mmax: ", mmax)
		for maj_threshold in [1]: # pynum.arange(mmin, mmax, mstep):
			try:
				pips = 0 # p&l in pips, start calculating from row 2
				dd = 0 # TODO: add drawdown calculations
				for r in range(rows-1): # because we can't calculate PnL of the last row (we don't know values of the next one!)
					# that's header
					if (r<2+period): # we know the future price only on the next row of a signal, so row 1 has no future price / also we need quite aa number of rows for the period calculation
						continue
					else:
						row_signal = 0 # signal across a row with all models
						m = 1
						for model in arrReports:	
							#if ((model[r][FdaCol])==""): model[r][FdaCol]=0 # some of the initial values might have spaces
							# if ( float(model[r][FdaCol]) >= fda_low and float(model[r][FdaCol]) <= fda_high and float(model[r][FdaAll]) >= fda_all_t): # make sure FDA is within needed range, then we count that signal
							
							fda = 0.0
							#  TODO optimization: calculate historical fda using numpy array from {row-period to row}
							for row in pynum.arange(r-period, r, 1):
								if (model[r][FdaCol] != ""): fda += float(model[r][FdaCol]) 
							fda = fda / period # average
							if ( fda >= fda_low and fda <= fda_high and float(model[r][FdaAll]) >= fda_all_t): # make sure FDA is within needed range, then we count that signal
								row_signal += model[r][SignalCol]
							m+=1
	
						model = arrReports[0] # just take first model for calculations
						if ( abs(row_signal) >= maj_threshold): # it was a valid signal and we execute it
							if (row_signal > 0):
								pips += float(model[r+1][PriceCol]) - float(model[r][PriceCol])
							elif (row_signal < 0):
								pips += float(model[r][PriceCol]) - float(model[r+1][PriceCol])
							
						if (pips < 0 and pips < dd):
							dd = pips
						
				#print(pFile + "," + str(fda_low) + "," + str(fda_high)  + "," + str(maj_threshold) + "," + str(fda_all_t)  + "," + str(dd) + "," + str(pips) )
				s.append ( pFile + "," + str(fda_low) + "," + str(fda_high)  + "," + str(maj_threshold) + "," + str(fda_all_t)  + "," + str(dd) + "," + str(pips) )
					
			except:	
				print("Unexpected error:", sys.exc_info()[0])
				print("file: ", pFile)
				print("row: ", r)
				print("model: ", m)
				print("model[r][FdaCol])=", model[r][FdaCol], "/")
				raise
		
	write2mysql(s)

	
# this will be called from the main function
def adaptive_system_test():

	mmin = 1
	mmax = 1 # len(arrReports)/5 # TODO: actually delete that value by 4! ///  this gets us the amount of models in total
	mstep = 1
	sql =""
	
	
	#print(len(arrReports),arrReports[0])
	#exit()
	rows = len(arrReports[0])
	s = []
	

	for fda_all_t in pynum.arange(0.50, 0.52, 0.005): # pynum.arange(0.50, 0.52, 0.005):
		# majority voting threshold value
		for maj_threshold in [1,2,3]: # pynum.arange(mmin, mmax, mstep):
			try:
				pips = 0 # p&l in pips, start calculating from row 2
				dd = 0 # TODO: add drawdown calculations
				for r in range(rows-1): # because we can't calculate PnL of the last row (we don't know values of the next one!)
					# that's header
					if (r<2+period): # we know the future price only on the next row of a signal, so row 1 has no future price / also we need quite aa number of rows for the period calculation
						continue
					else:
						row_signal = 0 # signal across a row with all models
						m = 1
						for model in arrReports:	
							#if ((model[r][FdaCol])==""): model[r][FdaCol]=0 # some of the initial values might have spaces
							# if ( float(model[r][FdaCol]) >= fda_low and float(model[r][FdaCol]) <= fda_high and float(model[r][FdaAll]) >= fda_all_t): # make sure FDA is within needed range, then we count that signal
							
							fda = 0.0
							#  TODO optimization: calculate historical fda using numpy array from {row-period to row}
							for row in pynum.arange(r-period, r, 1):
								if (model[r][FdaCol] != ""): fda += float(model[r][FdaCol]) 
							fda = fda / 44 # average
							if ( fda >= fda_low and fda <= fda_high and float(model[r][FdaAll]) >= fda_all_t): # make sure FDA is within needed range, then we count that signal
								row_signal += model[r][SignalCol]
							m+=1
	
						model = arrReports[0] # just take first model for calculations
						if ( abs(row_signal) >= maj_threshold): # it was a valid signal and we execute it
							if (row_signal > 0):
								pips += float(model[r+1][PriceCol]) - float(model[r][PriceCol])
							elif (row_signal < 0):
								pips += float(model[r][PriceCol]) - float(model[r+1][PriceCol])
							
						if (pips < 0 and pips < dd):
							dd = pips
						
				print(pFile + "," + str(fda_low) + "," + str(fda_high)  + "," + str(maj_threshold) + "," + str(fda_all_t)  + "," + str(dd) + "," + str(pips) )
				s.append ( pFile + "," + str(fda_low) + "," + str(fda_high)  + "," + str(maj_threshold) + "," + str(fda_all_t)  + "," + str(dd) + "," + str(pips) )
					
			except:	
				print("Unexpected error:", sys.exc_info()[0])
				print("file: ", pFile)
				print("row: ", r)
				print("model: ", m)
				print("model[r][FdaCol])=", model[r][FdaCol], "/")
				raise
		
	write2mysql(s)	
	
	
# print something with timestamp
def ts(s):	
	now = datetime.datetime.now()
	print(now.strftime("%Y-%m-%d %H:%M:%S") + " // " + s)

			
	
if __name__ == "__main__":
	
	
	#
	
	pFile = sys.argv[1]
	#ts("::>> started " + pFile)
	pkl_file = open(pFile, 'rb')
	arrReports = pickle.load(pkl_file)
	pkl_file.close()
	
	table = sys.argv[2]
	
	period = int(sys.argv[3])
	
	fda_low = float(sys.argv[4])
	
	fda_high = float(sys.argv[5])
	
	#print("array file: " + pFile)
	#print("table: " + table)
	#print("period:" + str(period))
	
	system_test()
	
	
	#ts("<<:: finished " + pFile)
