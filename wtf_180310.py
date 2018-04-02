#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#170912 irrExpSmth funciton is used to do the irregular time series exponential smoothing
#170916 add partial logic
#180310 add moving average logic
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def calculateMv(i,ts,cp,ma_timeLength,mv_sum,mv_cnt,mv_ans,mv_lastP,data):
	if mv_sum==None or mv_cnt==None or mv_ans==None or mv_lastP==None or data==None:
		raise ValueError('calculateMv error:',mv_sum,mv_cnt,mv_ans,mv_lastP,data)
	if abs(data[mv_lastP]['T']-ts)<=ma_timeLength:
		mv_sum+=cp
		mv_cnt+=1
	else:
		mv_ans.append(mv_sum/mv_cnt)
		while mv_lastP>i and abs(data[mv_lastP]['T']-ts)>ma_timeLength:
			mv_sum-=data[mv_lastP]['C']
			mv_cnt-=1
			mv_lastP-=1
		mv_sum+=cp
		mv_cnt+=1
	return mv_lastP,mv_sum,mv_cnt,mv_ans


def calMovingAverage(tradingPair
					,data
					,histTimeInterval=1
					,warningTimeGap=60
					,maxLatency=5
					#,checkTS=[-45,-30,-15]
					#,Pthres=[0.0001,0.0001,0.0001]
					#,Vtimespan=45
					#,Vthres=50
					#,lastPthres=0.05
					#,lastWinMomentumThres=0.2
					#,maxPriceTimeSpan=24*60
					,ma1_timeLength=5
					,ma2_timeLength=10
						#Note, ma1_timeLength will be always less than ma2_timeLength

					):
	#-------------------------------
	#this function is for moving average strategy
	#this function will only compare 2 moving average window, for multiple window comparison, use multiple of this function
	#the time units are still min
	#-------------------------------
	import datetime
	import time
	import calendar
	import collections as c
	if tradingPair==None:
		print("erroneous tradingPair: "+str(tradingPair))
		return {'dynamicBalanceFactor':None,'buySig':None,'sellSig':None,'twentyFourHourBTCVolume':None,'peakPrice':None,'buyPrice':None,'currPrice':None}
	if data==None or len(data)<=5:
		#here need to check with sell logic, for that if data==None, which means we dont have this pair's history, but this doesn't mean it's not trading (due to lag or anything else), if this's the case we may lose the sell signal
		print("erroneous input data: "+str(data))
		return {'dynamicBalanceFactor':None,'buySig':None,'sellSig':None,'twentyFourHourBTCVolume':None,'peakPrice':None,'buyPrice':None,'currPrice':None}
	#sort data to make sure its time ascending
	data.sort(key=lambda x:x['T'])
	print('latest timeStamp: '+str(tradingPair)+' '+str(data[-1]['T']))
	#
	currPrice,currTS=float(data[-1]['C']),calendar.timegm(datetime.datetime.strptime(data[-1]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())
	startTS=calendar.timegm(datetime.datetime.strptime(data[0]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())
	#read holding position here
	holdingStatus=holdingStatusTable.getHoldingStatus(tradingPair)
	#deprecated, sell and buy are completely seperated
	sellSignal=None

	if warningTimeGap==None or (not 0<warningTimeGap):
		raise ValueError('warningTimeGap >0')
	if ma1_timeLength==None or ma1_timeLength<=0:
		raise ValueError('ma1_timeLength is None or ma1_timeLength <=0')
	if ma1_timeLength<=min(warningTimeGap,histTimeInterval):
		raise ValueError('ma1_timeLength('+str(ma1_timeLength)+') <= warningTimeGap('+str(warningTimeGap)+') or histTimeInterval('+str(histTimeInterval)+')')
	if ma2_timeLength==None or ma2_timeLength<=0:
		raise ValueError('ma2_timeLength is None or ma2_timeLength <=0')
	if ma2_timeLength<=min(warningTimeGap,histTimeInterval):
		raise ValueError('ma2_timeLength('+str(ma2_timeLength)+') <= warningTimeGap('+str(warningTimeGap)+') or histTimeInterval('+str(histTimeInterval)+')')
	if ma1_timeLength==ma2_timeLength:
		raise ValueError('ma1_timeLength and ma2_timeLength cannot be of equal length')
	if ma1_timeLength>ma2_timeLength:
		ma1_timeLength,ma2_timeLength=ma2_timeLength,ma1_timeLength
	# if maxPriceTimeSpan==None or (not 0<maxPriceTimeSpan):
	# 	raise ValueError('maxPriceTimeSpan: '+str(maxPriceTimeSpan))
	if histTimeInterval>=warningTimeGap:
		raise ValueError('histTimeInterval: '+str(histTimeInterval)+'must be less than warningTimeGap: '+str(warningTimeGap))
	if maxLatency==None or maxLatency>6:
		raise ValueError('None maxLatency or maxLatency('+str(maxLatency)+') cannot exceed 6min due to dynamic last timeStamp')
	if calendar.timegm(datetime.datetime.utcnow().utctimetuple())-currTS>maxLatency*60:
		print('warning: '+str(tradingPair)+' last update timestamp too old: '+str(data[-1]['T']))
		return {'mv1_ans':None,'mv2_ans':None,'dynamicBalanceFactor':None,'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
	# if len(checkTS)<=0 or len(checkTS)!=len(Pthres) or len(checkTS)<=2:
	# 	raise ValueError('erroneous checkTS('+str(checkTS)+') or Pthres('+str(Pthres)+')')
	#checkTS.sort()
	# if checkTS[-1]>=0:
	# 	raise ValueError('last checkTS('+str(checkTS)+') must less than 0')
	# if Vtimespan==None or Vtimespan<=0 or Vthres==None or Vthres<=0:
	# 	raise ValueError('erroneous Vtimespan('+str(Vtimespan)+') or Vthres('+str(Vthres)+')')
	# Vthres=float(Vthres)
	# if startTS-calendar.timegm(datetime.datetime.strptime(data[-1]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())>checkTS[0]*60:
	# 	print('history not exceeding desired check timeStamp: '+str(checkTS[0])+' '+str(data[-1]['T'])+' '+str(data[0]['T']))
	# 	return {'mv1_ans':None,'mv2_ans':None,'dynamicBalanceFactor':None,'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}

	#initialization
	# prices=[None]*len(checkTS)+[float(data[-1]['C'])]
	# checkTSunix=[currTS+entry*60 for entry in checkTS]
	# checkTSpointer=len(checkTS)-1
	
	#convert to seconds
	ma1_timeLength=ma1_timeLength*60
	ma2_timeLength=ma2_timeLength*60

	stopTime=calendar.timegm(datetime.datetime.strptime(data[-2]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())-ma2_timeLength
	if startTS>stopTime:
		print('Trading pair '+str(tradingPair)+' oldest record('+str(data[0]['T'])+') not exceeding stopTime('+str(stopTime)+')')
		return {'mv1_ans':None,'mv2_ans':None,'dynamicBalanceFactor':None,'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
	# BTCVolume,vWindow=float(data[-1]['BV']),{'start':currTS-Vtimespan*60,'end':currTS}
	preTs=currTS
	# maxPriceTimeSpan_p=float(data[-1]['C'])
	# lastWindowMax,lastWindowMin=prices[-1],prices[-1]
	mv1_sum,mv1_cnt=currPrice,1
	mv2_sum,mv2_cnt=currPrice,1

	#Note, both mv_ans is in reverse order of time
	mv1_ans,mv2_ans=[],[]
	mv1_lastP,mv2_lastP=len(data)-1,len(data)-1
	data[-1]['T']=currTS
	#start loop
	for i in range(len(data)-2,-1,-1):
		ts=calendar.timegm(datetime.datetime.strptime(data[i]['T'],"%Y-%m-%dT%H:%M:%S").timetuple())
		data[i]['T']=ts
		cp=float(data[i]['C'])
		data[i]['C']=cp
		if cp<=0:
			print('warning: erroneous data closing price('+str(cp)+')')
			return {'mv1_ans':None,'mv2_ans':None,'dynamicBalanceFactor':None,'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}			
		if abs(preTs-ts)>warningTimeGap*60:
			print('warning, '+str(tradingPair)+' time interval exceeds warningTimeGap('+str(warningTimeGap)+') '+str(data[i]['T'])+' '+str(data[i+1]['T']))
			return {'mv1_ans':None,'mv2_ans':None,'dynamicBalanceFactor':None,'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
		if abs(preTs-ts)<histTimeInterval*60:
			print(str(data[i-1]))
			print(str(data[i]))
			print('data timestamp overlapping, will skip this trading pair')
			return {'mv1_ans':None,'mv2_ans':None,'dynamicBalanceFactor':None,'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}
		mv1_lastP,mv1_sum,mv1_cnt,mv1_ans=calculateMv(i=i,ts=ts,cp=cp,ma_timeLength=ma1_timeLength,mv_sum=mv1_sum,mv_cnt=mv1_cnt,mv_ans=mv1_ans,mv_lastP=mv1_lastP,data=data)
		mv2_lastP,mv2_sum,mv2_cnt,mv2_ans=calculateMv(i=i,ts=ts,cp=cp,ma_timeLength=ma2_timeLength,mv_sum=mv2_sum,mv_cnt=mv2_cnt,mv_ans=mv2_ans,mv_lastP=mv2_lastP,data=data)
		if len(mv1_ans)>=2 and len(mv2_ans)>=2:
			break
	# print(list(reversed(mv1_ans)))
	# print(list(reversed(mv2_ans)))
	return {'mv1_ans':mv1_ans,'mv2_ans':mv2_ans,'dynamicBalanceFactor':None,'buySig':None,'sellSig':sellSignal,'twentyFourHourBTCVolume':None,'peakPrice':(holdingStatus['PeakPrice'] if holdingStatus!=None else None),'buyPrice':(holdingStatus['BuyPrice'] if holdingStatus!=None else None),'currPrice':currPrice}









def generateBuyCandidates(marketHistoricalData):
	import heapq as hq
	import time
	import calendar
	import datetime
	if marketHistoricalData==None:
		raise ValueError('erroneous marketHistoricalData')
	buyCand=[]
	for pair in marketHistoricalData.keys():
		ans=calMovingAverage(tradingPair=pair
							,data=marketHistoricalData[pair]
							,histTimeInterval=1
							,warningTimeGap=60
							,maxLatency=5
							#,checkTS=[-45,-30,-15]
							#,Pthres=[0.0001,0.0001,0.0001]
							#,Vtimespan=45
							#,Vthres=50
							#,lastPthres=0.05
							#,lastWinMomentumThres=0.2
							#,maxPriceTimeSpan=24*60
							,ma1_timeLength=5
							,ma2_timeLength=10
							)
		if ans!=None and len(ans['mv1_ans'])>=2 and len(ans['mv2_ans'])>=2:
			if ans['mv1_ans'][0]>ans['mv2_ans'][0] and ans['mv1_ans'][1]<=ans['mv2_ans'][1]:
				hq.heappush(buyCand,(-1,{'dynamicBalanceFactor':ans['dynamicBalanceFactor'],'pair':pair,'twentyFourHourBTCVolume':ans['twentyFourHourBTCVolume'],'peakPrice':ans['peakPrice'],'buyPrice':ans['buyPrice'],'currPrice':ans['currPrice'],'currentTS':calendar.timegm(datetime.datetime.utcnow().utctimetuple())}))
	return buyCand






def generateSellCandidates(marketHistoricalData):
	import heapq as hq
	import time
	import calendar
	import datetime
	if marketHistoricalData==None:
		raise ValueError('erroneous marketHistoricalData')
	sellCand=[]
	for pair in marketHistoricalData.keys():
		ans=calMovingAverage(tradingPair=pair
							,data=marketHistoricalData[pair]
							,histTimeInterval=1
							,warningTimeGap=60
							,maxLatency=5
							#,checkTS=[-45,-30,-15]
							#,Pthres=[0.0001,0.0001,0.0001]
							#,Vtimespan=45
							#,Vthres=50
							#,lastPthres=0.05
							#,lastWinMomentumThres=0.2
							#,maxPriceTimeSpan=24*60
							,ma1_timeLength=5
							,ma2_timeLength=10
							)
		if ans!=None and len(ans['mv1_ans'])>=2 and len(ans['mv2_ans'])>=2:
			if ans['mv1_ans'][0]<ans['mv2_ans'][0] and ans['mv1_ans'][1]>=ans['mv2_ans'][1]:
				hq.heappush(sellCand,(-1,{'comPrice':None,'pair':pair,'currentTS':calendar.timegm(datetime.datetime.utcnow().utctimetuple())}))
	return sellCand






# item=heapq.heappop(buyCand)
# -item[0] is the score
# item[1] is the dict that containing this trading pair's info

# buyingCandidates,sellingCandidates = generateCandidates(marketHistoricalData)
# print('buyingCandidates:',buyingCandidates)
# print('sellingCandidates:',sellingCandidates)



http://www.learndatasci.com/python-finance-part-3-moving-average-trading-strategy/
https://stackoverflow.com/questions/13728392/moving-average-or-running-mean
https://gordoncluster.wordpress.com/2014/02/13/python-numpy-how-to-generate-moving-averages-efficiently-part-2/

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#scratch paper
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------













