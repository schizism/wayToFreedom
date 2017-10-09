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


def sellSig(holdingStatus,currPrice,thresholds={'stopLoss':-0.1,'stopGain':0.2}):
	#{u'TimeStamp': u'2017-09-30 19:45:20.873574', u'HoldingStatus': u'False', u'MarketName': u'BTC-1ST', u'PeakPrice': u'0', u'BuyPrice': u'0'}
	import sys
	if holdingStatus==None or holdingStatus['HoldingStatus']=='False':
		return None
	if holdingStatus['BuyPrice']==None or currPrice==None or thresholds==None:
		print(holdingStatus)
		print(currPrice)
		print(thresholds)
		raise ValueError('erroneous holdingStatus OR currPrice OR thresholds')
	holdingStatus['BuyPrice']=float(holdingStatus['BuyPrice'])
	holdingStatus['PeakPrice']=float(holdingStatus['PeakPrice'])
	if holdingStatus['BuyPrice']<0 or currPrice<0:
		print(holdingStatus)
		print(currPrice)
		raise ValueError('erroneous holdingStatus OR currPrice')
	if (currPrice-holdingStatus['BuyPrice'])/holdingStatus['BuyPrice']<=thresholds['stopLoss']:
		return sys.maxint
	if (currPrice-holdingStatus['BuyPrice'])/holdingStatus['BuyPrice']>=thresholds['stopGain']:
		return sys.maxint
	return 0



def rollingWindow(tradingPair,data,histTimeInterval=1,rwLength=60,checkTimeInterval=5,warningTimeGap=10,maxLatency=20):
	#-------------------------------
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
	import collections as c
	#basic sanity check
	if data==None or len(data)<=5:
		raise ValueError("erroneous input data: "+str(data))
	if warningTimeGap==None or (not 0<warningTimeGap):
		raise ValueError('warningTimeGap >0')
	if histTimeInterval>=warningTimeGap:
		raise ValueError('histTimeInterval: '+str(histTimeInterval)+'must be less than warningTimeGap: '+str(warningTimeGap))
	#sort data to make sure its time ascending
	data.sort(key=lambda x:x['T'])
	print('latest timeStamp: '+str(tradingPair)+' '+str(data[-1]['T']))

	if maxLatency==None or time.time()-time.mktime(datetime.datetime.strptime(data[-1]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())>maxLatency*60:
		print('warning: '+str(tradingPair)+' last update timestamp is too old: '+str(data[-1]['T']))
		return None
	if time.mktime(datetime.datetime.strptime(data[-1]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())-time.mktime(datetime.datetime.strptime(data[0]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())<24*60*60:
		raise ValueError('history not exceeding 24h'+str(data[-1]['T'])+' '+str(data[0]['T']))

	#initialization
	rw,currPrice,prePrice=c.deque(),data[-1]['C'],None
	currRWtimeFrame,preRWtimeFrame={'start':time.time()-rwLength*60,'end':time.time()},{'start':time.time()-checkTimeInterval*60-rwLength*60,'end':time.time()-checkTimeInterval*60}
	currRWtimeWriteFlag,preRWtimeWriteFlag=False,False
	stopTime=currRWtimeFrame['end']-24*60*60
	currRWVolumeSum,preRWVolumeSum,twentyFourHourBTCVolume=0,0,0
	preTs=None


	for i in range(len(data)-1,-1,-1):
		ts=time.mktime(datetime.datetime.strptime(data[i]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())
		if preTs!=None:
			if preTs-ts>warningTimeGap*60:
				pass
				#print('warning, '+str(tradingPair)+' time interval exceeds warningTimeGap('+str(warningTimeGap)+') '+str(data[i]['T'])+' '+str(data[i+1]['T']))
			if preTs-ts<histTimeInterval*60:
				print(str(data[i-1]))
				print(str(data[i]))
				raise ValueError('data timestamp overlapping')
		if ts<stopTime:
			break
		if prePrice==None and ts<=currRWtimeFrame['end']-60*60:
			prePrice=data[i]['C']
		if currRWtimeFrame['start']<=ts<=currRWtimeFrame['end']:
			currRWVolumeSum+=data[i]['V']
			currRWtimeWriteFlag=True
		if preRWtimeFrame['start']<=ts<=preRWtimeFrame['end']:
			preRWVolumeSum+=data[i]['V']
			preRWtimeWriteFlag=True
		if stopTime<=ts<=currRWtimeFrame['end']:
			twentyFourHourBTCVolume+=data[i]['V']*data[i]['C']
		preTs=ts

	if not (currRWtimeWriteFlag and preRWtimeWriteFlag):
		raise ValueError('not writing, currRWVolumeSum: '+str(currRWVolumeSum)+', preRWVolumeSum: '+str(preRWVolumeSum))
	#read holding position here
	holdingStatus = getHoldingStatus(tradingPair)
	return {'buySig':buySig(tradingPair=tradingPair,currPrice=currPrice,prePrice=prePrice,currRWVolumeSum=currRWVolumeSum,preRWVolumeSum=preRWVolumeSum,twentyFourHourBTCVolume=twentyFourHourBTCVolume,weights={'V':0.8,'P':0.2},thresholds={'V':0.5,'P':0.025,'twentyFourHourBTCVolume':300}),'sellSig':sellSig(holdingStatus=holdingStatus,currPrice=currPrice,thresholds={'stopLoss':0.1,'stopGain':0.25}),'twentyFourHourBTCVolume':twentyFourHourBTCVolume}



def generateCandidates(marketHistoricalData):
	import heapq as hq
	import time
	if marketHistoricalData==None:
		raise ValueError('erroneous marketHistoricalData')
	buyCand,sellCand=[],[]
	for pair in marketHistoricalData.keys():
		ans=rollingWindow(tradingPair=pair,data=marketHistoricalData[pair],histTimeInterval=1,rwLength=60,checkTimeInterval=5,warningTimeGap=10,maxLatency=10)
		if ans!=None and ans['buySig']!=None:
			hq.heappush(buyCand,(-ans['buySig'],pair,ans['twentyFourHourBTCVolume'],time.time()))
		if ans!=None and ans['sellSig']!=None:
			hq.heappush(sellCand,(-ans['sellSig'],pair,ans['twentyFourHourBTCVolume'],time.time()))
	return (buyCand,sellCand)





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









