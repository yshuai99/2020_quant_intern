#frame demo

'''
================================================================================
总体回测前
================================================================================
'''
#总体回测前要做的事情

def initialize(context):
	set_params()             #设置参数
	set_variables()          #设置中间变量
	set_backtest()           #设置回测条件
	run_daily(market_open, time='every_bar', reference_security='000300.XSHG')

#设置参数
def set_params():
	g.tc=15                  #调仓频率
	g.N=20                   #持仓数目



#设置中间变量    
def set_variables():          
	g.t=0                   #记录回测的天数
	g.if_trade=False        #当天是否交易
	
	
#设置回测条件
def set_backtest():
	set_benchmark('000300.XSHG')       #以沪深300为基准进行回测，默认为沪深300
	set_option('use_real_price',True)  #用真实价格回测
	log.set_level('order','error')


'''
==================================================================================
每天开盘前                                                                       
==================================================================================
'''


#开盘前要做的事情
def before_trading_start(context):
	if g.t%g.tc==0:                                                #每g.tc天，调仓一次
		g.if_trade=True                                            #设置滑点
		set_slip_fee(context)									   #设置滑点和手续费 
		g.all_stocks=set_feasible_stocks(context)                  #筛选出符合条件的股票
	g.t+=1

def set_slip_fee(context):                                         #根据不同的时间设置滑点和手续费
	set_slippage(PriceRelatedSlippage(0.00246),type='stock')
	dt=context.current_dt
	log.info(type(context.current_dt))
	
	if dt>datetime.datetime(2013,1,1):
		set_commission(PerTrade(buy_cost=0.0003,sell_cost=0.0013,min_cost=5))       
	elif dt>datetime.datetime(2011,1,1):
		set_commission(PerTrade(buy_cost=0.001,sell_cost=0.002,min_cost=5))       
	elif dt>datetime.datetime(2009,1,1):
		set_commission(PerTrade(buy_cost=0.002,sell_cost=0.003,min_cost=5))        
	else:
		set_commission(PerTrade(buy_cost=0.0003,sell_cost=0.0013,min_cost=5))

def filter(security_list):                                 #筛选掉停牌、退市以及ST的股票 
	current_data = get_current_data()
	return[stock for stock in security_list  
		if not current_data[stock].paused   
		and not '退' in current_data[stock].name   
		and not current_data[stock].is_st]

def set_feasible_stocks(context):
	df = get_fundamentals(query(valuation.code))
	stockset = list(df['code'])
	stockset = filter(stockset)

def market_open(context):
    return

		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
