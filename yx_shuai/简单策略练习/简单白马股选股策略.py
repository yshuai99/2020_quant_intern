# 白马股选股策略入门
# 2015-01-01 到 2017-05-17, ￥2000000, 每天
from jqdata import *

'''
================================================================================
总体回测前
================================================================================
'''
#总体回测前要做的事情

#1
#设置策略参数
def initialize (context):
    set_params()
    set_backtest()
    run_daily(trade, 'every_bar')

def set_params():
    g.days=0    
    g.refresh_rate=10 
    g.stocknum=5   

#2
#设置回测条件   
def set_backtest():
    set_benchmark('000905.XSHG') 
    set_option('use_real_price', True)  

    log.set_level('order', 'error')

'''
================================================================================
每天开盘前
================================================================================
'''
#每天开盘前要做的事情
def before_trading_start(context):
    set_slip_fee(context)

# 根据不同的时间段设置滑点与手续费
def set_slip_fee(context):

    set_slippage(FixedSlippage(0.02)) 

    dt=context.current_dt

    if dt>datetime.datetime(2013,1, 1):
        set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')

    else:
        set_order_cost(OrderCost(open_tax=0, open_commission=0.003,close_commission=0.003, close_tax=0.001,min_commission=5), type='stock')

# 过滤停牌股票
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]

'''
================================================================================
每天交易时
================================================================================
'''    
def trade(context):
    if g.days%g.refresh_rate == 0:
        stock_to_choose = get_fundamentals(query(
        valuation.code, valuation.pe_ratio, valuation.market_cap, indicator.eps, indicator.inc_return, indicator.inc_net_profit_annual
    ).filter(
        valuation.pe_ratio < 45,
        valuation.pe_ratio > 20,
        indicator.eps > 0.3,
        indicator.inc_net_profit_annual > 0.30,
        indicator.roe > 15
    ).order_by(
        indicator.roe.desc()
    ).limit(
        50), date=None)

        stockset=list(stock_to_choose['code'])
        stockset = filter_paused_stock(stockset)

        ## 获取持仓列表
        sell_list = list(context.portfolio.positions.keys())
        #log.info('sell info',sell_list)

        for stock in sell_list:
            if stock not in stockset[:g.stocknum]:
                stock_sell = stock
                order_target_value(stock_sell, 0) 

            ## 分配资金
        if len(context.portfolio.positions) < g.stocknum :
            Num = g.stocknum - len(context.portfolio.positions)
            Cash = context.portfolio.cash/Num
        else: 
            Cash = 0
            Num = 0

        ## 买入股票
        for stock in stockset[:g.stocknum]:
            if stock in sell_list:
                pass
            else:
                stock_buy = stock
                order_target_value(stock_buy, Cash)
                Num = Num - 1
                if Num==0:
                    break

        # 天计数加一
        g.days = 1
    else:
        g.days += 1