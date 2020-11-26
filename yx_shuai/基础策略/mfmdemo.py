

#多因子策略入门
#代码主体来源于 jointquant.com/post/1399

'''
整体回测前
'''

#初始化
def initialize(context):
    set_params()             #设置参数
    set_variables()          #设置中间变量
    set_backtest()           #设置回测条件


#设置参数
def set_params():
    g.tc=15                  #调仓频率
    g.yb=63                  #样本长度
    g.N=20                   #持仓数目
    g.factors=["market_cap","roe"]  #因子
    g.weights=[[1],[-1]]     #因子权重


#设置中间变量    
def set_variables():          
    g.t=0                   #记录回测的天数
    g.if_trade=False        #当天是否交易
    
    
#设置回测条件
def set_backtest():
    set_option('use_real_price',True)  #用真实价格回测
    log.set_level('order','error')
    
    
'''
每天开盘前
'''


#开盘前要做的事情
def before_trading_start(context):
    if g.t%g.tc==0:
        #每g.tc天，调仓一次
        g.if_trade=True
        #设置滑点
        set_slip_fee(context)
        #设置可行股票池：获得当前开盘的沪深300股票池并剔除
        g.all_stocks=set_feasible_stocks(get_index_stocks('000300.XSHG'),g.yb,context)
        #查询可行股票池中股票的财务因子
        g.q=query(valuation,balance,cash_flow,income,indicator).filter(valuation.code.in_(g.all_stocks))
    g.t+=1


#设置可行的股票池并过滤已经停牌的股票
def set_feasible_stocks(stock_list,days,context):
    #get_price返回一个dataframe，从中提出提出paused数据并转置
    suspened_info_df=get_price (list(stock_list),start_date=context.current_dt,end_date=context.current_dt,frequency='daily',fields='paused')['paused'].T
    #过滤出停牌的股票
    unsuspened_index=suspened_info_df.iloc[:,0]<1
    #得到当日未停牌股票代码list
    unsuspened_stocks=suspened_info_df[unsuspened_index].index
    #进一步筛选出前days天未停牌的股票list
    feasible_stocks=[]
    current_data=get_current_data()
    for stock in unsuspened_stocks:
        if sum(attribute_history(stock,days,unit='1d',fields=('paused'),skip_paused=False))[0]==0:
            feasible_stocks.append(stock)
    return feasible_stocks


#根据不同的时间段设置滑点和手续费
def set_slip_fee(context):
    set_slippage(FixedSlippage(0))
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
        
        
'''
每天交易时
'''



def handle_data(context,data):
    if g.if_trade==True:
        #计算总资产并等额权重分配给每一只股票
        g.everyStock=context.portfolio.portfolio_value/g.N
        #获得今天日期的字符集
        todayStr=str(context.current_dt)[0:10]
        #获得因子排序
        a,b=getRankedFactors(g.factors,todayStr)
        #计算每个因子的权重
        points=np.dot(a,g.weights)
        #复制股票代码
        stock_sort=b[:]
        #对股票的得分进行排名
        points,stock_sort=bubble(points,stock_sort)
        #提取前g.N名的股票
        toBuy=stock_sort[0:g.N].values
        #对于不需要持仓的股票，全仓卖出
        order_stock_sell(context,data,toBuy)
        #对于不需要持仓的股票，按照分到的份额买入
        order_stock_buy(context,data,toBuy)
    g.if_trade=False


#获得卖出信号，执行卖出
def order_stock_sell(context,data,toBuy):
    #获取股票池
    list_position=context.portfolio.positions.keys()
    #如果当前股票不在tobuy list 则卖出
    for stock in list_position:
        if stock not in toBuy:
            order_target(stock,0)

#获得买入信号，执行买入
def order_stock_buy(context,data,toBuy):
    #对于不需要持仓的股票，按照分到的份额买入
    for i in range (0,len(g.all_stocks)):
        if indexOf(g.all_stocks[i],toBuy)>-1:
            order_target_value(g.all_stocks[i],g.everyStock)


#查询一个一个元素在数组中的位置，如果不存在则返回-1
def indexOf(e,a):
    for i in range(0,len(a)):
        if e==a[i]:
            return i
    return -1
    

#输出因子数据和股票代码  
def getRankedFactors(f,d):
    #获得股票的基本面数据，g.q是一个通用的全局查询
    df=get_fundamentals(g.q,d)
    res=[([0]*len(f)) for i in range(len(df))]
    #把数据填充到刚刚定义的数组里面
    for i in range (0,len(df)):
        for j in range(0,len(f)):
            res[i][j]=df[f[j]][i]
    #用均值填充空值
    fillNan(res)
    #将数据变成排名
    getRank(res)
    return res,df['code']
    
#把每列原始数据变成排序的数据    
def getRank(r):
    indexes=list(range(0,len(r)))
    for k in range(len(r[0])):
        for i in range(len(r)):
            for j in range(i):
                if r[j][k] < r[i][k]:
                    indexes[j], indexes[i] = indexes[i], indexes[j]
                    for l in range(len(r[0])):
                        r[j][l], r[i][l] = r[i][l], r[j][l]

        for i in range(len(r)):
            r[i][k]=i+1
    for i in range(len(r)):
        for j in range(i):
            if indexes[j] > indexes[i]:
                indexes[j], indexes[i] = indexes[i], indexes[j]
                for k in range(len(r[0])):
                    r[j][k], r[i][k] = r[i][k], r[j][k]
    return r


#用均值填充Nan        
def fillNan(m):
    #计算出因子数据有多少行（行是不同的股票）
    rows=len(m)
    #计算出因子数据有多少列（列是不同的因子）
    columns=len(m[0])
    #对每一列进行操作
    for j in range(0,columns):
        #定义一个临时变量，用来计算每列加总的值
        sum=0.0
        #定义一个临时变量，用来计算非Nan值的个数
        count=0.0
        #计算非Nan值的总和和个数
        for i in range(0,rows):
            if not(isnan(m[i][j])):
                sum+=m[i][j]
                count+=1
        #计算平均值，为防止全是Nan，如果当整列都是Nan时认为平均值是0
        avg=sum/max(count,1)
        for i in range(0,rows):
            if isnan(m[i][j]):
                m[i][j]=avg
    return m
    
def bubble(numbers,indexes):
    for i in range(len(numbers)):
        for j in range(i):
            if numbers[j][0] < numbers[i][0]:
                numbers[j][0], numbers[i][0] = numbers[i][0], numbers[j][0]
                indexes[j], indexes[i] = indexes[i], indexes[j] 
    return numbers,indexes


'''
每天收盘后
'''
def after_trading_end(context):
    return
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        



