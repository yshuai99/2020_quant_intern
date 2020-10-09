import jqdata

#策略核心：如果股票有上涨趋势，买入，如果股票有下跌趋势，卖出
#量化：如果收盘价大于过去五天的平均价格，买入。如果收盘价小于过去五天的平均价格，卖出
#需要的变量：收盘价，过去五天的平均收盘价
#反思：如何在加仓时调整为整数百股购买，订单委托失败的原因以及处理方案


#初始化策略
def initialize(context):
    #设置平安银行为交易对象
    g.security = '000001.XSHE'
    #设置基准股票为沪深300
    set_benchmark('000300.XSHG')
    #以真实价格复权
    set_option('use_real_price',True)
    #每日交易
    run_daily(market_open,time = 'every_bar')
    
def market_open(context):
    #初始化变量
    security = g.security
    #取得过去五天的收盘价格
    close_data = attribute_history(security,5,'1d',['close'])
    #取得过去五天的平均收盘价
    MA5 = close_data['close'].mean()
    #取得上一时间点的价格
    current_price = close_data['close'][-1]
    #取得可用现金
    cash = context.portfolio.available_cash
    
    #如果当前价格大于平均价格，买入
    if current_price > 1.01*MA5:
        order_value(security,cash)
        log.info('Buying %s' % (security))
    #如果收盘价小于平均价格，空仓卖出
    elif current_price < MA5 and context.portfolio.positions[security].closeable_amount > 0:
        order_target(security,0)
        log.info('Selling %s' % (security))
    #取得上一时间点的价格
    record(stock_price = current_price)