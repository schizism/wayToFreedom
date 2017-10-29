#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#170912 irrExpSmth funciton is used to do the irregular time series exponential smoothing
#170916 add partial logic
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def irrExpSmth(data
				,checkInterval=5
				,buy_threshold=0.1
				,sell_threshold=-0.1
				,alpha=0.4
				,gamma=0.1
				,n_0=5):
	#-------------------------------
	#we are assuming input data is a list of json object
	#this is following https://dml.cz/bitstream/handle/10338.dmlcz/134655/AplMat_51-2006-6_4.pdf
	#equation (9)-(12)
	#Note, the unit used in the recorded time is important for that it will affect the power in calculations, we use min here
	#-------------------------------

	#basic sanity checks
	if data==None or len(data)<=5:
		raise ValueError("erroneous input data: "+str(len(data)))
	if checkInterval==None:
		raise ValueError('checkInterval must be a number')
	if buy_threshold==None or (not 0<buy_threshold):
		raise ValueError('buy_threshold >0')
	if sell_threshold==None or (not sell_threshold<0):
		raise ValueError('buy_threshold <0')
	if alpha==None or not (0<alpha<1):
		raise ValueError('alpha must satisfy 0<alpha<1')
	if gamma==None or not (0<gamma<1):
		raise ValueError('gamma must satisfy 0<gamma<1')
	if n_0==None or not (4<n_0<len(data)/4):
		raise ValueError('n_0 must satisfy 4<n_0<len(data)')

	import datetime
	import time
	#import numpy as np
	#import pandas as pd

	#sort data to make sure its time ascending
	data.sort(key=lambda x:x['T'])
	df=pd.DataFrame(data)
	#minus all timestamp with the min ts in this dataset to avoid the constant problem
	intercept=time.mktime(datetime.datetime.strptime(data[0]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())
	df['ts']=df['T'].apply(lambda x:(time.mktime(datetime.datetime.strptime(x,"%Y-%m-%dT%H:%M:%S").timetuple())-intercept)/60.0000)

	#initialization
	S_t,alpha_t,T_t,gamma_t,signal=[None]*len(df),[None]*len(df),[None]*len(df),[None]*len(df),[]

	#https://en.wikipedia.org/wiki/Simple_linear_regression
	x,y=df['ts'][:n_0],df['C'][:n_0]
	x_bar=np.mean(x)
	y_bar=np.mean(y)

	nu,de=0,0
	for i in range(len(x)):
		tmp=x[i]-x_bar
		nu+=tmp*(y[i]-y_bar)
		de+=tmp**2

	b1=np.divide(nu,de)
	b0=y_bar-b1*x_bar
	#get average time spacing of data
	q=np.mean(df['ts']-df['ts'].shift(1))
	if not (0<q<5):
		raise ValueError('erroneous average time interval, possiblly from ill defined time unit: '+str(q))
	alpha_t[n_0],gamma_t[n_0]=1-np.power(1-alpha,q),1-np.power(1-gamma,q)
	S_t[n_0],T_t[n_0]=b0,b1

	#start smoothing
	time_tic=df['ts'][n_0]
	pre_S=S_t[n_0]
	pre_T=T_t[n_0]
	for t_n in range(n_0+1,len(df)):
		#calculation here only depend on previous numbers, thus can be optimized into O(1) memory
		alpha_t[t_n]=np.divide(alpha_t[t_n-1],alpha_t[t_n-1]+np.power(1-alpha,df['ts'][t_n]-df['ts'][t_n-1]))
		gamma_t[t_n]=np.divide(gamma_t[t_n-1],gamma_t[t_n-1]+np.power(1-gamma,df['ts'][t_n]-df['ts'][t_n-1]))
		S_t[t_n]=alpha_t[t_n]*df['C'][t_n]+(1-alpha_t[t_n])*(S_t[t_n-1]+(df['ts'][t_n]-df['ts'][t_n-1])*T_t[t_n-1])
		T_t[t_n]=gamma_t[t_n]*np.divide(S_t[t_n]-S_t[t_n-1],df['ts'][t_n]-df['ts'][t_n-1])+(1-gamma_t[t_n])*T_t[t_n-1]
		
		#detecting signal
		# if df['ts'][t_n]-time_tic>=checkInterval:
		# 	if df['ts'][t_n]-time_tic>=5*checkInterval:
		# 		print("warning")
		# 	#print(df['T'][t_n],df['ts'][t_n]-time_tic,np.divide(S_t[t_n]-pre_S,pre_S))
		# 	if np.divide(S_t[t_n]-pre_S,pre_S)>=buy_threshold:
		# 		signal.append((df['T'][t_n],1))
		# 	elif np.divide(S_t[t_n]-pre_S,pre_S)<=sell_threshold:
		# 		signal.append((df['T'][t_n],-1))
		# 	else:
		# 		pass
		# 	time_tic=df['ts'][t_n]
		# 	pre_S=S_t[t_n]
		# 	pre_T=T_t[t_n]

	return (S_t,T_t)




def buySig(tradingPair,currPrice,prePrice,currRWVolumeSum,preRWVolumeSum,twentyFourHourBTCVolume,weights={'V':0.8,'P':0.2},thresholds={'V':1,'P':0.05,'twentyFourHourBTCVolume':300}):
	if currPrice==None or prePrice==None or twentyFourHourBTCVolume==None:
		print(currPrice)
		print(prePrice)
		print(twentyFourHourBTCVolume)
		raise ValueError('erroneous currPrice OR prePrice OR twentyFourHourBTCVolume')
	if currRWVolumeSum==None or preRWVolumeSum==None or currRWVolumeSum<=0 or preRWVolumeSum<=0:
		raise ValueError()
	if sum(weights.values())!=1:
		raise ValueError('weights must be sum to 1')
	if thresholds==None:
		raise ValueError('threshold: '+str(thresholds))
	# if currPrice<prePrice:
	# 	print(tradingPair+' has a lower price (curr:'+str(currPrice)+') vs (pre:'+str(prePrice)+')')
	# 	return None
	if twentyFourHourBTCVolume<thresholds['twentyFourHourBTCVolume']:
		print(tradingPair+' twentyFourHourBTCVolume < '+str(thresholds['twentyFourHourBTCVolume']))
		return None
	vThresholdValue=(currRWVolumeSum-preRWVolumeSum)/preRWVolumeSum
	pThresholdValue=(currPrice-prePrice)/prePrice
	if vThresholdValue<thresholds['V']:
		print(tradingPair+' not passing Volume threshold ('+str(vThresholdValue)+' vs '+str(thresholds['V'])+')')
		return None
	if pThresholdValue<thresholds['P']:
		print(tradingPair+' not passing price threshold ('+str(pThresholdValue)+' vs '+str(thresholds['P'])+')')
		return None
	return vThresholdValue/thresholds['V']*weights['V']+pThresholdValue/thresholds['P']*weights['P']


def sellSig(holdingStatus,currPrice,currTS,thresholds={'stopLoss':-0.07,'stopPeakLoss':-0.1,'stopGain':0.2,'lowMovementCheckTimeGap':60,'LowPurchaseQuantity':0.001},peakPriceTrailingIntervals=[0.1,0.2],peakPriceTrailingThreshold=[0.5,0.6,0.7]):
	#{u'TimeStamp': u'2017-09-30 19:45:20.873574', u'HoldingStatus': u'False', u'MarketName': u'BTC-1ST', u'PeakPrice': u'0', u'BuyPrice': u'0'}
	import sys
	if holdingStatus==None or holdingStatus['HoldingStatus']=='False':
		return None
	if holdingStatus['BuyPrice']==None or currPrice==None or thresholds==None:
		raise ValueError('erroneous holdingStatus('+str(holdingStatus['BuyPrice'])+') OR currPrice('+str(currPrice)+') OR thresholds('+str(thresholds)+')')
	if len(peakPriceTrailingIntervals)<=0 or len(peakPriceTrailingIntervals)!=len(set(peakPriceTrailingIntervals)):
		raise ValueError('erroneous peakPriceTrailingIntervals: '+str(peakPriceTrailingIntervals))
	if len(peakPriceTrailingThreshold)<=0 or len(peakPriceTrailingThreshold)!=len(peakPriceTrailingIntervals)+1:
		raise ValueError('erroneous peakPriceTrailingThreshold: '+str(peakPriceTrailingThreshold)+' OR peakPriceTrailingIntervals: '+str(peakPriceTrailingIntervals))
	if holdingStatus['BuyPrice']<=0 or currPrice<0:
		raise ValueError('erroneous holdingStatus('+str(holdingStatus)+') OR currPrice('+str(currPrice)+')')
	#
	peakPriceTrailingIntervals.sort()
	peakPriceTrailingIntervals=([-sys.maxint] if peakPriceTrailingIntervals[0]>-sys.maxint else [])+peakPriceTrailingIntervals+([sys.maxint] if peakPriceTrailingIntervals[-1]<sys.maxint else [])
	holdingStatus['BuyPrice']=float(holdingStatus['BuyPrice'])
	holdingStatus['PeakPrice']=float(holdingStatus['PeakPrice'])
	
	if (currPrice-holdingStatus['BuyPrice'])<=thresholds['stopLoss']*holdingStatus['BuyPrice']:
		return {'sig':sys.maxint,'comPrice':(1-thresholds['stopLoss'])*holdingStatus['BuyPrice']}
	# if (currPrice-holdingStatus['PeakPrice'])/holdingStatus['PeakPrice']<=thresholds['stopPeakLoss']:
	# 	return sys.maxint
	# if (currPrice-holdingStatus['BuyPrice'])/holdingStatus['BuyPrice']>=thresholds['stopGain']:
	# 	return sys.maxint
	if holdingStatus['PeakPrice']>holdingStatus['BuyPrice']:
		risePct=(holdingStatus['PeakPrice']-holdingStatus['BuyPrice'])/holdingStatus['BuyPrice']
		for i in range(1,len(peakPriceTrailingIntervals)):
			if peakPriceTrailingIntervals[i-1]<risePct<=peakPriceTrailingIntervals[i]:
				comPrice=(1-peakPriceTrailingThreshold[i-1])*holdingStatus['BuyPrice']+peakPriceTrailingThreshold[i-1]*holdingStatus['PeakPrice']
				if currPrice<=comPrice:
					print('info: peak price trailing conditions: ',holdingStatus['PeakPrice'],holdingStatus['BuyPrice'],currPrice,peakPriceTrailingIntervals[i-1],peakPriceTrailingIntervals[i],peakPriceTrailingThreshold[i-1],comPrice)
					return {'sig':sys.maxint,'comPrice':comPrice}
				break
	# if (currTS - holdingStatus['buyTimeStamp']>thresholds['lowMovementCheckTimeGap']*60) and (floor((currTS - holdingStatus['buyTimeStamp'])/86400) * price change threshold %  > (last price / buy price - 1) )
	# if holdingStatus['BuyPrice']*holdingStatus['Q']<thresholds['LowPurchaseQuantity']:
	# 	print('info: LowPurchaseQuantity',holdingStatus,thresholds['LowPurchaseQuantity'])
	# 	return sys.maxint
	return None



def rollingWindow(tradingPair,data,histTimeInterval=1,rwLength=60,checkTimeInterval=5,warningTimeGap=60,maxLatency=5,lastVCheckTimeSpan=5,lastPCheckTimeSpan=5,lastPVCheckThreshold={'p':0,'v':30}):
	#-------------------------------
	#this function is for trading strategy 1
	#this function is used to deal with singal trading pair, e.g. bit-omg
	#the time units for rwLength and checkTimeInterval and inputTimeInterval are min 
	#we are assuming input data is a list of json object
	#this is following https://docs.google.com/document/d/1XCX_g96ro82I-nFQC6RHXKQkDu2uP1WrXbPvD64qe54/edit#
	#fixed check interval without smoothing will result in very volatile signals
	#-------------------------------
	import datetime
	import time
	#import numpy as np
	#import pandas as pd
	#import collections as c
	#basic sanity check
	if tradingPair==None:
		raise ValueError("erroneous tradingPair: "+str(tradingPair))
	if data==None or len(data)<=5:
		#here need to check with sell logic, for that if data==None, which means we dont have this pair's history, but this doesn't mean it's not trading (due to lag or anything else), if this's the case we may lose the sell signal
		raise ValueError("erroneous input data: "+str(data))
	#sort data to make sure its time ascending
	data.sort(key=lambda x:x['T'])
	print('latest timeStamp: '+str(tradingPair)+' '+str(data[-1]['T']))
	#check sell signal before everything else
	currPrice,currTS=data[-1]['C'],time.mktime(datetime.datetime.strptime(data[-1]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())
	#read holding position here
	holdingStatus=getHoldingStatus(tradingPair)
	sellSignal=sellSig(holdingStatus=holdingStatus,currPrice=currPrice,currTS=currTS,thresholds={'stopLoss':-0.07,'stopPeakLoss':-0.1,'stopGain':1000,'lowMovementCheckTimeGap':60,'LowPurchaseQuantity':0.001},peakPriceTrailingIntervals=[0.1,0.2],peakPriceTrailingThreshold=[0.5,0.6,0.7])
	

	if warningTimeGap==None or (not 0<warningTimeGap):
		raise ValueError('warningTimeGap >0')
	if histTimeInterval>=warningTimeGap:
		raise ValueError('histTimeInterval: '+str(histTimeInterval)+'must be less than warningTimeGap: '+str(warningTimeGap))
	if lastVCheckTimeSpan==None or lastVCheckTimeSpan<0 or lastVCheckTimeSpan>1440:
		raise ValueError('erroneous lastVCheckTimeSpan: '+str(lastVCheckTimeSpan))
	if lastPCheckTimeSpan==None or lastPCheckTimeSpan<0 or lastPCheckTimeSpan>1440:
		raise ValueError('erroneous lastPCheckTimeSpan: '+str(lastPCheckTimeSpan))
	if lastPVCheckThreshold==None:
		raise ValueError('erroneous lastPVCheckThreshold')
	if maxLatency==None or maxLatency>6:
		raise ValueError('None maxLatency or maxLatency('+str(maxLatency)+') cannot exceed 6min due to dynamic last timeStamp')
	if time.time()-currTS>maxLatency*60:
		print('warning: '+str(tradingPair)+' last update timestamp too old: '+str(data[-1]['T']))
		return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
	if lastPCheckTimeSpan<maxLatency or lastVCheckTimeSpan<maxLatency:
		print('warning: lastPCheckTimeSpan('+str(lastPCheckTimeSpan)+') or lastVCheckTimeSpan('+str(lastVCheckTimeSpan)+') is less than maxLatency('+str(maxLatency)+') which means trading pairs which last entry satisfying (currentTime-maxLatency <= timeStamp < currentTime-last[P,V]CheckTimeSpan) will automatically fail last min checks')
	if time.mktime(datetime.datetime.strptime(data[-1]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())-time.mktime(datetime.datetime.strptime(data[0]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())<86400:
		print('history not exceeding 24h'+str(data[-1]['T'])+' '+str(data[0]['T']))
		return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}

	#initialization
	prePrice=None
	currRWtimeFrame,preRWtimeFrame={'start':currTS-rwLength*60,'end':currTS},{'start':currTS-checkTimeInterval*60-rwLength*60,'end':currTS-checkTimeInterval*60}
	currRWtimeWriteFlag,preRWtimeWriteFlag=False,False
	stopTime=currRWtimeFrame['end']-86400
	currRWVolumeSum,preRWVolumeSum,twentyFourHourBTCVolume=0,0,0
	preTs=None
		#last X min check
	lastMinCheck=True
	lastV,lastP=0,None
	lastVtimeFrame={'start':currRWtimeFrame['end']-lastVCheckTimeSpan*60,'end':currRWtimeFrame['end']}


	for i in range(len(data)-1,-1,-1):
		ts=time.mktime(datetime.datetime.strptime(data[i]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())
		if preTs!=None:
			if preTs-ts>warningTimeGap*60:
				print('warning, '+str(tradingPair)+' time interval exceeds warningTimeGap('+str(warningTimeGap)+') '+str(data[i]['T'])+' '+str(data[i+1]['T']))
				return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
			if preTs-ts<histTimeInterval*60:
				print(str(data[i-1]))
				print(str(data[i]))
				print('data timestamp overlapping, will skip this trading pair')
				return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
		if ts<stopTime:
			break
		if ts>currRWtimeFrame['end']:
			print('warning: data last time stamp('+str(data[i]['T'])+') is larger than current time stamp('+str(currRWtimeFrame['end'])+')')
			return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
		if prePrice==None and ts<=currRWtimeFrame['end']-rwLength*60:
			prePrice=data[i]['C']
		if lastMinCheck:
			if lastP==None and ts<=currRWtimeFrame['end']-lastPCheckTimeSpan*60:
				lastP=data[i]
			if ts>=lastVtimeFrame['start']:
				lastV+=float(data[i]['BV'])
			else:
				if lastP==None:
					pass
				elif currPrice-lastP['C']>lastPVCheckThreshold['p'] and lastV>lastPVCheckThreshold['v']:
					lastMinCheck=False
				else:
					print('warning: tradingPair '+str(tradingPair)+' not passing last min checks (lastPrice:'+str(lastP)+' currPrice:'+str(data[-1])+' vs lastPriceThreshold:'+str(lastPVCheckThreshold['p'])+', lastVolume:'+str(lastV)+' vs lastVolumeThreshold:'+str(lastPVCheckThreshold['v'])+')')
					print('lastVCheckTimeSpan: '+str(lastVCheckTimeSpan)+'min, lastPCheckTimeSpan: '+str(lastPCheckTimeSpan)+'min')
					return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
		if currRWtimeFrame['start']<=ts<=currRWtimeFrame['end']:
			currRWVolumeSum+=float(data[i]['BV'])
			currRWtimeWriteFlag=True
		if preRWtimeFrame['start']<=ts<=preRWtimeFrame['end']:
			preRWVolumeSum+=float(data[i]['BV'])
			preRWtimeWriteFlag=True
		if stopTime<=ts<=currRWtimeFrame['end']:
			twentyFourHourBTCVolume+=float(data[i]['BV'])
		preTs=ts

	if not (currRWtimeWriteFlag and preRWtimeWriteFlag):
		print(currRWtimeFrame,preRWtimeFrame,stopTime)
		print(data[:5])
		print(data[-5:])
		print('not writing, currRWVolumeSum: '+str(currRWVolumeSum)+', preRWVolumeSum: '+str(preRWVolumeSum))
		return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
	return {'buySig':buySig(tradingPair=tradingPair,currPrice=currPrice,prePrice=prePrice,currRWVolumeSum=currRWVolumeSum,preRWVolumeSum=preRWVolumeSum,twentyFourHourBTCVolume=twentyFourHourBTCVolume,weights={'V':0.8,'P':0.2},thresholds={'V':0.5,'P':0.025,'twentyFourHourBTCVolume':300}),'sellSig':sellSignal,'twentyFourHourBTCVolume':twentyFourHourBTCVolume,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}

#following are designed to parallel run
def rollingWindow_2(tradingPair,data,histTimeInterval=1,warningTimeGap=60,maxLatency=5,checkTS=[-45,-30,-15],Pthres=[0.0001,0.0001,0.0001],Vtimespan=45,Vthres=50,lastPthres=0.05):
	#-------------------------------
	#this function is for trading strategy 2
	#the time units are still min
	#Note, code will check current price regardless of checkTS, thus the length of Pthres is equal to checkTS (not less than 1)
	#-------------------------------
	import datetime
	import time
	#import collections as c
	if tradingPair==None:
		raise ValueError("erroneous tradingPair: "+str(tradingPair))
	if data==None or len(data)<=5:
		#here need to check with sell logic, for that if data==None, which means we dont have this pair's history, but this doesn't mean it's not trading (due to lag or anything else), if this's the case we may lose the sell signal
		raise ValueError("erroneous input data: "+str(data))
	#sort data to make sure its time ascending
	data.sort(key=lambda x:x['T'])
	print('latest timeStamp: '+str(tradingPair)+' '+str(data[-1]['T']))
	#check sell signal before everything else
	currPrice,currTS=data[-1]['C'],time.mktime(datetime.datetime.strptime(data[-1]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())
	#read holding position here
	holdingStatus=getHoldingStatus(tradingPair)
	sellSignal=sellSig(holdingStatus=holdingStatus,currPrice=currPrice,currTS=currTS,thresholds={'stopLoss':-0.07,'stopPeakLoss':-0.1,'stopGain':1000,'lowMovementCheckTimeGap':60,'LowPurchaseQuantity':0.001},peakPriceTrailingIntervals=[0.1,0.2],peakPriceTrailingThreshold=[0.5,0.6,0.7])
	if sellSignal!=None:
		return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}

	if warningTimeGap==None or (not 0<warningTimeGap):
		raise ValueError('warningTimeGap >0')
	if histTimeInterval>=warningTimeGap:
		raise ValueError('histTimeInterval: '+str(histTimeInterval)+'must be less than warningTimeGap: '+str(warningTimeGap))
	if maxLatency==None or maxLatency>6:
		raise ValueError('None maxLatency or maxLatency('+str(maxLatency)+') cannot exceed 6min due to dynamic last timeStamp')
	if time.time()-currTS>maxLatency*60:
		print('warning: '+str(tradingPair)+' last update timestamp too old: '+str(data[-1]['T']))
		return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
	if len(checkTS)<=0 or len(checkTS)!=len(Pthres) or len(checkTS)<=2:
		raise ValueError('erroneous checkTS('+str(checkTS)+') or Pthres('+str(Pthres)+')')
	checkTS.sort()
	if checkTS[-1]>=0:
		raise ValueError('last checkTS('+str(checkTS)+') must less than 0')
	if Vtimespan==None or Vtimespan<=0 or Vthres==None:
		raise ValueError('erroneous Vtimespan('+str(Vtimespan)+') or Vthres('+str(Vthres)+')')
	Vthres=float(Vthres)
	if time.mktime(datetime.datetime.strptime(data[0]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())-time.mktime(datetime.datetime.strptime(data[-1]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())>checkTS[0]*60:
		print('history not exceeding desired check timeStamp: '+str(checkTS[0])+' '+str(data[-1]['T'])+' '+str(data[0]['T']))
		return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
	#initialization
	prices=[None]*len(checkTS)+[float(data[-1]['C'])]
	checkTSunix=[currTS+entry*60 for entry in checkTS]
	checkTSpointer=len(checkTS)-1
	stopTime=currTS+min(checkTS[0],-1*Vtimespan)*60
	BTCVolume,vWindow=data[-1]['V']*data[-1]['C'],{'start':currTS-Vtimespan*60,'end':currTS}
	preTs=currTS
	#start loop
	for i in range(len(data)-2,-1,-1):
		ts=time.mktime(datetime.datetime.strptime(data[i]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())
		cp=float(data[i]['C'])
		if cp<=0:
			print('warning: erroneous data closing price('+str(cp)+')')
			return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}			
		if abs(preTs-ts)>warningTimeGap*60:
			print('warning, '+str(tradingPair)+' time interval exceeds warningTimeGap('+str(warningTimeGap)+') '+str(data[i]['T'])+' '+str(data[i+1]['T']))
			return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
		if abs(preTs-ts)<histTimeInterval*60:
			print(str(data[i-1]))
			print(str(data[i]))
			print('data timestamp overlapping, will skip this trading pair')
			return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
		if checkTSpointer>=0 and ts<=checkTSunix[checkTSpointer]:
			if checkTSpointer>0 and ts<=checkTSunix[checkTSpointer-1]:
				print('time gap between data record for trading pair '+str(tradingPair)+' are too big or checkTS intervals are too frequent')
				print(checkTSpointer,checkTSunix[checkTSpointer],checkTSunix[checkTSpointer-1],ts)
				return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
			prices[checkTSpointer]=cp
			if prices[checkTSpointer]<=0:
				print('erroneous '+str(tradingPair)+' closing price: '+str(cp))
				return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
			if (prices[checkTSpointer+1]-prices[checkTSpointer])>Pthres[checkTSpointer]*prices[checkTSpointer]:
				pass
			else:
				print('warning: '+str(tradingPair)+' not passing increasing threshold: prices('+str(prices)+') Pthres('+str(Pthres)+')')
				return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
			checkTSpointer-=1
		if vWindow['start']<=ts<=vWindow['end']:
			BTCVolume+=float(data[i]['BV'])
		if ts<stopTime:
			break
		preTs=ts
	if BTCVolume<Vthres:
		print('warning: tradingPair '+str(tradingPair)+' not passing last Vthres('+str(Vthres)+') BTCVolume('+str(BTCVolume)+')')
		return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
	if prices[0]>0 and (prices[-1]-prices[0])<=lastPthres*prices[0]:
		print(prices)
		print('warning: tradingPair '+str(tradingPair)+' not passing last lastPthres('+str(lastPthres)+')')
		return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
	return {'buySig':BTCVolume/Vthres+(prices[-1]-prices[-2])/prices[-2],'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
	#print(BTCVolume/Vthres+(prices[-1]-prices[-2])/prices[-2])
	#return {'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}



def generateCandidates(marketHistoricalData):
	import heapq as hq
	import time
	if marketHistoricalData==None:
		raise ValueError('erroneous marketHistoricalData')
	buyCand,sellCand=[],[]
	for pair in marketHistoricalData.keys():
		ans=rollingWindow_2(tradingPair=pair,data=marketHistoricalData[pair],histTimeInterval=1,warningTimeGap=10,maxLatency=5,checkTS=[-45,-30,-15],Pthres=[0.00001,0.00001,0.00001],Vtimespan=45,Vthres=50,lastPthres=0.03)
		if ans!=None and ans['buySig']!=None:
			hq.heappush(buyCand,(-ans['buySig'],{'pair':pair,'twentyFourHourBTCVolume':ans['twentyFourHourBTCVolume'],'peakPrice':ans['peakPrice'],'buyPrice':ans['buyPrice'],'currPrice':ans['currPrice'],'currentTS':time.time()}))
		if ans!=None and ans['sellSig']!=None:
			hq.heappush(sellCand,(-ans['sellSig']['sig'],{'comPrice':ans['sellSig']['comPrice'],'pair':pair,'twentyFourHourBTCVolume':ans['twentyFourHourBTCVolume'],'peakPrice':ans['peakPrice'],'buyPrice':ans['buyPrice'],'currPrice':ans['currPrice'],'currentTS':time.time()}))
	return (buyCand,sellCand)



# item=heapq.heappop(buyCand)
# -item[0] is the score
# item[1] is the dict that containing this trading pair's info

# buyingCandidates,sellingCandidates = generateCandidates(marketHistoricalData)
# print('buyingCandidates:',buyingCandidates)
# print('sellingCandidates:',sellingCandidates)





#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#scratch paper
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# df['S_t']=S_t
# df['T_t']=T_t
# df[['C','S_t']]

# ax=df['C'].plot()
# df['S_t'].plot(ax=ax)
# plt.show()


df = pd.DataFrame(data)
df['ts']=df['T'].apply(lambda x:(time.mktime(datetime.datetime.strptime(x,"%Y-%m-%dT%H:%M:%S").timetuple())))
df['buy']=buySignal

ax=df['V'].plot()
df['buy'].plot(ax=ax)
# df['CP']=df['C']*1000000
# df['CP']
plt.show()









