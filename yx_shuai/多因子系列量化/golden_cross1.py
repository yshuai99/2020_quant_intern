import jqdata

#初始化策略
def initialize(context):
    #设置
    g.security = '000001.XSHE'
    set_benchmark('000300.XSHG')
    set_option('use_real_price',True)
    run_daily(market_open,time = 'every_bar')
    
def market_open(context):
    security = g.security
    close_data = attribute_history(security,5,'1d',['close'])
    MA5 = close_data['close'].mean()
    current_price = close_data['close'][-1]
    cash = context.portfolio.available_cash
    
    if current_price > 1.01*MA5:
        order_value(security,cash)
        log.info('Buying %s' % (security))
    elif current_price < MA5 and context.portfolio.positions[security].closeable_amount > 0:
        order_target(security,0)
        log.info('Selling %s' % (security))
        
    record(stock_price = current_price)