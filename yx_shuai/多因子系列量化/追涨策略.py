'''
基本思路：
筛选出符合：0<市盈率（pe_ratio）<30, 市净率（pb_ratio)<3, 净利润环比增长率(inc_net_profit_annual)>0.3的股票，按照销售毛利率进行降序排列，选取前150只
买入：股票成交量突破20日内最高并且股票价格向上突破10日均线；
卖出：成交量创10日内新低或者股价向下突破5日新低
止损：当个股价格比买入价下跌超过10%时卖出止损
'''
#追涨杀跌策略的特点简单来概括就是“跟风”，在股票涨势和成交量喜人时入市，在二者表现不佳时平仓。因此这里只是简单的对产生这样趋势的股票“资质”进行初步筛选。






import jqdata
def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    log.set_level('order', 'error')
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    run_daily(market_open, time='every_bar', reference_security='000300.XSHG')

def paused_filter(security_list):
    #获得当前时间的涨跌，停牌等信息
    current_data = get_current_data()
    #过滤停牌的股票并储存在list中
    security_list = [stock for stock in security_list if not current_data[stock].paused]
    return security_list


#过滤退市股票
def delisted_filter(security_list):
    current_data = get_current_data()
    #将股票名称中不带‘退’的储存在list中
    security_list = [stock for stock in security_list if not '退' in current_data[stock].name]
    return security_list

#过滤ST股票
def st_filter(security_list):
    current_data = get_current_data()
    security_list = [stock for stock in security_list if not current_data[stock].is_st]
    return security_list


'''
#也可以用一个函数去过滤停牌，ST和退市股票：
def filter(security_list):  
    current_data = get_current_data()  
    return[stock for stock in stock_list  
        if not current_data[stock].paused   
        and not '退' in current_data[stock].name   
        and not current_data[stock].is_st]
'''

def market_open(context):
    df = get_fundamentals(query(
        valuation.code, valuation.pe_ratio, valuation.market_cap,valuation.pb_ratio,indicator.eps, indicator.inc_return, indicator.inc_net_profit_annual
    ).filter(
        #筛选出市盈率在0-30倍之间
        valuation.pe_ratio>0,
        valuation.pe_ratio<30,
        #筛选出市净率小于3
        valuation.pb_ratio<3,
        #净利润增长大于0.3
        indicator.inc_net_profit_annual > 0.30
    ).order_by(
        #按照净利润环比增长率降序排列
        indicator.gross_profit_margin.desc()
    ).limit(
        150), date=None)
    stockset = list(df['code'])
    stockset = paused_filter(stockset)
    stockset = delisted_filter(stockset)
    stockset = st_filter(stockset)  


'''
设置buylisy为空列表，不断填充需要购买的股票代码
股票需满足三个条件：
    1.已经筛选过一次
    2.买入：股票成交量突破20日内最高并且股票价格向上突破10日均线
    3.卖出：成交量创10日内新低或者股价向下突破5日新低
'''
    buylist = []
    for stock in stockset:
        #设置所需的变量
        close_data = attribute_history(stock, 11, '1d', ['close'])
        volume = attribute_history(stock, 21, '1d', ['volume'])

        max20_vol = max(volume['volume'][:20])
        min_vol = min(volume['volume'][11:20])

        max10 = close_data['close'][:10].mean()
        min5 = min(close_data['close'][5:10])

        cur_vol = volume['volume'][-1]
        cur_price = close_data['close'][-1]

        #context.portfolio.positions.keys()获得现在持有的股票代码
        sell_list = list(context.portfolio.positions.keys())
        #如果成交量创10日心底 or 股价向下突破至5日新低
        if (cur_vol < min_vol) or (cur_price < min5):
            stock_sell = stock
            order_target_value(stock_sell, 0) 
            #如果成交量突破20日内最高 and 股票向上突破10日均线 and 股票不在出售列表中
        elif (cur_vol >= max20_vol) and (cur_price >= max10) and (stock not in sell_list):
            buylist.append(stock)
    if len(buylist)==0: 
        Cash = context.portfolio.available_cash
    else:
        Cash = context.portfolio.available_cash/len(buylist)
    for stock in buylist:
        order_target_value(stock, Cash)

#个股跌幅超过loss值时止损
def security_stoploss(context,loss=0.1):
    if len(context.portfolio.positions)>0:
        for stock in context.portfolio.positions.keys():
            avg_cost = context.portfolio.positions[stock].avg_cost
            current_price = context.portfolio.positions[stock].price
            if 1 - current_price/avg_cost >= loss:
                log.info(str(stock) + '  跌幅达个股止损线，平仓止损！')
                order_target_value(stock, 0)