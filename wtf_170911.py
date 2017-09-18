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
	import numpy as np
	import pandas as pd

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


def buySig(pre,post,threshold=1,weights={'V':0.8,'P':0.2}):
	if pre==None or post==None:
		raise ValueError()
	if sum(weights.values())!=1:
		raise ValueError('weights must be sum to 1')
	if threshold==None or not (0<threshold):
		raise ValueError('threshold: '+str(threshold))
	if post["P"]-pre["P"]>0:
		if ((post["V"]-pre["V"])/pre["V"])*weights['V']+((post["P"]-pre["P"])/pre["P"])*weights['P']>=threshold:
			return True
	return False

def sellSig(cur,purPrice,threshold=-0.05):
	if cur==None or purPrice==None:
		raise ValueError()
	if threshold==None or not (threshold<0):
		raise ValueError('threshold: '+str(threshold))
	if (cur['P']-purPrice)/purPrice<=threshold:
		return True
	return False

def rollingWindow(data,checkInterval=60,warning_time_gap=3):
	#-------------------------------
	#we are assuming input data is a list of json object
	#this is following https://docs.google.com/document/d/1XCX_g96ro82I-nFQC6RHXKQkDu2uP1WrXbPvD64qe54/edit#
	#fixed check interval without smoothing will result in very volatile signals
	#Note, checkInterval unit is min
	#-------------------------------
	import datetime
	import time
	import numpy as np
	import pandas as pd
	import collections as c
	#basic sanity check
	if data==None or len(data)<=5:
		raise ValueError("erroneous input data: "+str(len(data)))
	if checkInterval==None:
		raise ValueError('checkInterval must be a number')
	if warning_time_gap==None or (not 0<warning_time_gap):
		raise ValueError('warning_time_gap >0')
	#sort data to make sure its time ascending
	data.sort(key=lambda x:x['T'])

	#initialization
	rw,buySignal,sellSignal=c.deque(),[0]*len(data),[]
	#start scanning
	for i in range(len(data)):
		rw.append({'V':data[i]['V'],'P':data[i]['C'],'ts':time.mktime(datetime.datetime.strptime(data[i]['T'],"%Y-%m-%dT%H:%M:%S").timetuple()),'T':data[i]['T']})
		# if sellSig(rw[-1],purPrice=,threshold=-0.05):
		# 	sellSignal.append(data[i])
		pre,post=rw[0],rw[-1]
		if post['ts']-pre['ts']>=checkInterval*60:
			if post['ts']-pre['ts']>=warning_time_gap*checkInterval*60:
				#logger here
				print('warning')
			if buySig(pre,post):
				#buySignal.append(post)
				buySignal[i]=post['V']
			while len(rw)>0 and rw[-1]['ts']-rw[0]['ts']>=checkInterval*60:
				tmp=rw.popleft()
	return (buySignal,sellSignal)
















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









