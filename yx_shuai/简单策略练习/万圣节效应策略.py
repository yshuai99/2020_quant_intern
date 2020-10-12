# 导入聚宽函数库
import jqdata

# 初始化此策略
def initialize(context):
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)

    # 设置我们要操作的股票池，这里我们选择蓝筹股
    g.stocks = ['000001.XSHE','600000.XSHG','600019.XSHG','600028.XSHG','600030.XSHG','600036.XSHG','600519.XSHG','601398.XSHG','601857.XSHG','601988.XSHG']

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    # 得到每只股票可以花费的现金，这里我们使用总现金股票数数量
    cash = context.portfolio.available_cash / len(g.stocks)
    # 获取数据
    hist = history(1,'1d','close',g.stocks)
    # 循环股票池
    for security in g.stocks:
        # 得到当前时间
        today = context.current_dt
        # 得到该股票上一时间点价格
        current_price = hist[security][0]
        # 如果当前为10月且日期大于15号，并且现金大于上一时间点价格，并且当前该股票空仓
        if today.month == 10 and today.day > 15 and cash > current_price and context.portfolio.positions[security].closeable_amount == 0:
            order_value(security, cash)
            # 记录这次买入
            log.info("Buying %s" % (security))
        # 如果当前为5月且日期大于15号，并且当前有该股票持仓，则卖出
        elif today.month == 5 and today.day > 15 and context.portfolio.positions[security].closeable_amount > 0:
            # 全部卖出
            order_target(security, 0)
            # 记录这次卖出
            log.info("Selling %s" % (security))