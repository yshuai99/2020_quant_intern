#当股票在当日收盘30分钟内涨幅到达9.5%~9.9%时间段的时候，我们进行买入，在第二天开盘卖出
#分两步，第一步头天买入，第二步当天卖出






import jqdata

def initialize(context):
    #选自计算机技术相关板块
    g.stocks = get_industry_stocks('I64') + get_industry_stocks('I65')
    #防止板块之间股票重复
    g.stocks = set(g.stocks)
    g.daily_buy_count  = 5
    set_option('use_real_price',True)
    run_daily(morning_sell_all,'09:30')
    
def morning_sell_all(context):
    for security in context.portfolio.positions:
        order_target(security,0)
        log.info("Selling %s" % (security))

def before_trading_start(context):
    g.today_bought_stocks = set()
    g.last_df = history(1,'1d','close',g.stocks)

def handle_data(context,data):
    #确定交易时间
    if context.current_dt.hour < 13:
        return
    #每天只买5只股票
    if len(g.today_bought_stocks) > g.daily_buy_count:
        return
    for security in (g.stocks - g.today_bought_stocks):
        price = data[security].close
        last_close = g.last_df[security][0]
        
        if price/last_close > 1.095 and price/last_close < 1.099 and data[security].high_limit - last_close >= 1.0:
            cash = context.portfolio.available_cash
            need_count = g.daily_buy_count - len(g.today_bought_stocks)
            buy_cash = context.portfolio.available_cash / need_count
            order_value(security, buy_cash)
            g.today_bought_stocks.add(security)
            log.info("Buying %s" % (security))
            if len(g.today_bought_stocks) >= g.daily_buy_count:
                break