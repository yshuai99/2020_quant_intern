#multiple stocks golden cross


#多股票进行均线操作
#核心：有上涨趋势就买入，有下跌趋势就卖出。
#量化：收盘价大于三日均价，买入，小于三日均价，卖出。


import jqdata

def initialize(context):
    g.stocks = ['000001.XSHE','000002.XSHE','000004.XSHE','000005.XSHE']
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    
def handle_data(context,data):
    for security in g.stocks:
        vwap = data[security].vwap(3)
        price = data[security].close
        cash = context.portfolio.available_cash
        
        if price > 1.005*vwap and cash > 0:
            order(security,100)
            log.info('Buying %s' % (security))
        elif price < 0.995*vwap and context.portfolio.positions[security].closeable_amount > 0:
            order(security,-100)
            log.info('Selling %s' % (security))


'''
import jqdata

def initialize(context):
    g.stocks = ['000001.XSHE','000002.XSHE','000004.XSHE','000005.XSHE']
    set_benchmark('000300.XSHG')
    set_option('use_real_price',True)
    run_daily(Buying_stocks, time='every_bar')
    
def Buying_stocks(context):
    for security in g.stocks:
        close_data = attribute_history(security,3,'1d',['close'])
        MA3 = close_data['close'].mean()
        current_price = close_data['close'][-1]
        cash = context.portfolio.available_cash
        
        if current_price > 1.005*MA3 and cash > 0:
            order(security,100)
            log.info('Buying %s' % (security))
        elif current_price < 0.995*MA3 and context.portfolio.positions[security].closeable_amount > 0:
            order(security,-100)
            log.info('Selling %s' % (security))

'''     
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
