# 导入函数库
from jqdata import *
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
import calendar
import cPickle as pickle
from six import StringIO
from jqfactor import winsorize_med
from jqfactor import neutralize
from jqfactor import standardlize
import statsmodels.api as sm


#去除上市距beginDate不足3个月的股票
def delect_stop(stocks,beginDate,n=30*3):
    stockList = []
    beginDate = datetime.datetime.strptime(beginDate, "%Y-%m-%d")
    for stock in stocks:
        start_date = get_security_info(stock).start_date
        if start_date < (beginDate-datetime.timedelta(days = n)).date():
            stockList.append(stock)
    return stockList

#获取股票池
def get_stock_A(begin_date):
    begin_date = str(begin_date)
    stockList = get_index_stocks('000002.XSHG',begin_date)+get_index_stocks('399107.XSHE',begin_date)
    #剔除ST股
    st_data = get_extras('is_st', stockList, count = 1, end_date=begin_date)
    stockList = [stock for stock in stockList if not st_data[stock][0]]
    #剔除停牌、新股及退市股票
    stockList = delect_stop(stockList, begin_date)
    return stockList

#获取指定周期的日期列表 'W、M、Q'
def get_period_date(peroid,start_date, end_date):
    #设定转换周期period_type  转换为周是'W',月'M',季度线'Q',五分钟'5min',12天'12D'
    stock_data = get_price('000001.XSHE',start_date,end_date,'daily',fields=['close'])
    #记录每个周期中最后一个交易日
    stock_data['date']=stock_data.index
    #进行转换，周线的每个变量都等于那一周中最后一个交易日的变量值
    period_stock_data=stock_data.resample(peroid,how='last')
    date=period_stock_data.index
    pydate_array = date.to_pydatetime()
    date_only_array = np.vectorize(lambda s: s.strftime('%Y-%m-%d'))(pydate_array )
    date_only_series = pd.Series(date_only_array)
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    start_date=start_date-datetime.timedelta(days=1)
    start_date = start_date.strftime("%Y-%m-%d")
    date_list=date_only_series.values.tolist()
    date_list.insert(0,start_date)
    return date_list
    
# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000905.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'error')
    # 层数
    g.num = 1
    # 总层数
    g.total_num = 10
    g.n = 0
    # 调仓天数
    g.N = 20
    g.Day= 3

    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
    run_daily(market_open, time='9:30', reference_security='000905.XSHG')

## 开盘时运行函数
def market_open(context):
    if g.n%g.N == 0:
        factorWeight = GetWeight(context, g.Day)
        predict = GetPredict(context, factorWeight)
        stockList = list(predict.index)
        buyList = stockList[int(len(stockList)*(g.num-1)/g.total_num):int(len(stockList)*g.num/g.total_num)]
        # 进行股票交易
        for stock in context.portfolio.positions.keys():
            order_target_value(stock,0)
        weight=context.portfolio.total_value/len(buyList)
        for stock in buyList: 
            order_target_value(stock,weight)        
    g.n += 1
    
def GetWeight(context, N):
    date = context.previous_date
    stockList = get_stock_A(date)
    df_close = get_price(stockList, count = N+1, end_date = date, frequency='1d', fields=['close'])['close']
    pchg = df_close.pct_change().shift(-1).iloc[:-1]
    pchg = pchg.T
    weight = pd.DataFrame()
    for i in pchg.columns:
        df_fund = get_fundamentals(query(valuation.code, valuation.turnover_ratio, valuation.capitalization).filter(valuation.code.in_(stockList)), date = i)       
        df_fund = df_fund.set_index(['code'])
        # 去极值
        df_fund = winsorize_med(df_fund, scale=1, inclusive=True, inf2nan=True, axis=0)
        # 标准化
        df_fund = standardlize(df_fund, inf2nan=True, axis=0)
        df_fund['pchg'] =  pchg[i]
        df_fund = df_fund.dropna()
        if not df_fund.empty:
            X = df_fund[['turnover_ratio', 'capitalization']]
            y = df_fund['pchg']  
            # WLS回归
            wls = sm.OLS(y, X)
            result = wls.fit()
            weight[i] = result.params
    weight = weight.mean(axis = 1)
    print weight
    return weight

def GetPredict(context, weight):
    date = context.previous_date
    stockList = get_stock_A(date)
    df_fund = get_fundamentals(query(valuation.code, valuation.turnover_ratio, valuation.capitalization).filter(valuation.code.in_(stockList)), date = date)
    df_fund = df_fund.set_index(['code'])
    # 去极值
    df_fund = winsorize_med(df_fund, scale=1, inclusive=True, inf2nan=True, axis=0)
    # 标准化
    df_fund = standardlize(df_fund, inf2nan=True, axis=0)
    df_data = df_fund.dot(weight)
    df_data.sort(ascending = False)
    return df_data