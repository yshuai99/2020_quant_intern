# 克隆自聚宽文章：https://www.joinquant.com/post/6582
# 标题：电影好看 影视类股票收益率同样精彩！
# 作者： Quant中找米吃的阿鼠

# 导入聚宽函数库
#回测时间：2012-12-01到2016-12-31
import jqdata

# 初始化此策略
def initialize(context):
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 设置我们要操作的股票池，通过get_industry_stocks将影视行业的股票代码提取出来
    set_benchmark('000300.XSHG')
    stocks = get_industry_stocks('R86')
    
    
    fundamental_df = get_fundamentals(
        query(
            indicator.roe,
            indicator.gross_profit_margin,
            valuation.pb_ratio, valuation.code,cash_flow.subtotal_operate_cash_inflow           
        )
        .filter(
            valuation.code.in_ (stocks)
        )
        .filter(
            indicator.roe>0
        )
        .filter(
            indicator.gross_profit_margin>0.3
        )
        .filter(
            valuation.pb_ratio<3
        )
        .filter(
            cash_flow.subtotal_operate_cash_inflow>0
        )
        .order_by(
            valuation.pb_ratio.asc()
        )
        .limit(10)
        
    )
    g.stocks = fundamental_df['code']
    

# 每个单位时间调用一次
def handle_data(context, data):
    #将全部先进平均分到每一只股票中
    if len(g.stocks)==0: 
        cash = context.portfolio.available_cash
    else:
        cash = context.portfolio.available_cash/len(g.stocks)
    
    #调用历史数据进行分析，每日的收盘数据
    hist = history(1,'1d','close',g.stocks)
 
    for security in g.stocks:
        today = context.current_dt
        current_price = hist[security][0]
        #买入卖出时间的确定
        # 如果当前为12月且日期大于1号，并且现金大于上一时间点价格，并且当前该股票空仓
        if today.month == 12 and today.day > 1 and cash > current_price and context.portfolio.positions[security].closeable_amount == 0:
            order_value(security, cash)
            # 记录这次买入
            log.info("Buying %s" % (security))
            
        # 如果当前为6月且日期大于12号，并且当前有该股票持仓，则卖出
        elif today.month == 6 and today.day > 12 and context.portfolio.positions[security].closeable_amount > 0:
            # 全部卖出
            order_target(security, 0)
            # 记录这次卖出
            log.info("Selling %s" % (security))