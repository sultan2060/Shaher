import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go

# 1. تهيئة الصفحة
st.set_page_config(
    page_title="Paper Quant Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. تحسين مظهر الواجهة عبر CSS لضمان ملاءمة الجوال والكمبيوتر
st.markdown("""<style>
.stApp { background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
.block-container { padding: 0.8rem !important; }

/* التنبيه المختصر */
.disclaimer-bar {
    background-color: #161b22;
    border-right: 3px solid #d29922;
    color: #8b949e;
    font-size: 11px;
    padding: 6px 10px;
    border-radius: 4px;
    margin-bottom: 10px;
    direction: rtl;
}

/* شريط الإشارة */
.signal-header {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px;
    text-align: center;
    margin-bottom: 10px;
}
.signal-call { border-right: 4px solid #2ea043; }
.signal-put { border-right: 4px solid #da3633; }

/* شبكة الأهداف */
.targets-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 8px;
    margin-bottom: 10px;
}
.target-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 8px;
    text-align: center;
}
.t-label { font-size: 11px; color: #8b949e; font-weight: bold; }
.t-val { font-size: 14px; color: #58a6ff; font-weight: bold; margin: 2px 0; }
.t-time { font-size: 10px; color: #3fb950; }
</style>""", unsafe_allow_html=True)

# 3. إشعار التحليل التجريبي المختصر
st.markdown("""<div class="disclaimer-bar">
⚠️ <b>تحليل تجريبي للتداول الورقي والتعليم فقط</b> | نماذج واختبارات نمط الشموع، ليست توصية مالية.
</div>""", unsafe_allow_html=True)

# 4. الشريط الجانبي مع إضافة سهم MU
with st.sidebar:
    st.header("⚙️ Config")
    stocks_list = {
        "MU": "MU",
        "SPX": "^GSPC", 
        "TSLA": "TSLA", 
        "NVDA": "NVDA", 
        "AAPL": "AAPL",
        "META": "META", 
        "AMZN": "AMZN", 
        "MSFT": "MSFT", 
        "GOOGL": "GOOGL"
    }
    selected_stock = st.selectbox("Symbol", list(stocks_list.keys()))
    stock_symbol = stocks_list[selected_stock]
    
    timeframe_config = {
        "1m": {"interval": "1m", "days": 2, "mins": 1},
        "5m": {"interval": "5m", "days": 7, "mins": 5},
        "15m": {"interval": "15m", "days": 15, "mins": 15},
        "1h": {"interval": "1h", "days": 30, "mins": 60}
    }
    selected_tf = st.selectbox("Timeframe", list(timeframe_config.keys()), index=3)
    tf_info = timeframe_config[selected_tf]

# 5. تحميل البيانات ومعالجتها
@st.cache_data(ttl=15)
def load_data(symbol, interval, days):
    end_d = datetime.now()
    start_d = end_d - timedelta(days=days)
    df = yf.download(symbol, start=start_d, end=end_d, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

df = load_data(stock_symbol, tf_info['interval'], tf_info['days'])

if not df.empty and len(df) > 5:
    ep = float(df['Close'].iloc[-1])
    
    # حساب ATR
    df['TR'] = np.maximum(df['High'] - df['Low'], np.abs(df['High'] - df['Close'].shift(1)))
    atr = float(df['TR'].rolling(14).mean().iloc[-1])
    if np.isnan(atr) or atr == 0:
        atr = ep * 0.005  # قيمة احتياطية للتذبذب
        
    is_bull = float(df['Close'].iloc[-1]) >= float(df['Open'].iloc[-1])
    direction = "CALL 🟢" if is_bull else "PUT 🔴"
    card_style = "signal-call" if is_bull else "signal-put"
    
    sl = ep - (atr * 1.5) if is_bull else ep + (atr * 1.5)
    
    # 6. عرض شريط البيانات المختصر
    st.markdown(f"""<div class="signal-header {card_style}">
<span style="font-size:12px; color:#8b949e;">{selected_stock} [{selected_tf}]</span> | 
<b style="font-size:16px;">{direction}</b> | 
<span style="font-size:13px;">EP: <b>${ep:.2f}</b></span> | 
<span style="font-size:13px; color:#f85149;">SL: <b>${sl:.2f}</b></span>
</div>""", unsafe_allow_html=True)
    
    # 7. بناء كروت الأهداف (T1, T2, T3, T4)
    targets_html = '<div class="targets-container">'
    for i, m in enumerate([1.0, 2.0, 3.0, 4.0], 1):
        tp = ep + (atr * 1.5 * m) if is_bull else ep - (atr * 1.5 * m)
        dist = abs(tp - ep)
        est_bars = max(1, int(dist / (atr * 0.75)))
        est_mins = est_bars * tf_info['mins']
        
        time_txt = f"~{est_mins}m" if est_mins < 60 else f"~{round(est_mins/60, 1)}h"
        
        targets_html += f'<div class="target-card"><div class="t-label">T{i}</div><div class="t-val">${tp:.2f}</div><div class="t-time">⏱️ {time_txt}</div></div>'
    targets_html += '</div>'
    
    st.markdown(targets_html, unsafe_allow_html=True)

    # 8. الشارت المصحح مع إلغاء الفراغات الزمنية
    df_chart = df.tail(60).copy()
    df_chart['DateStr'] = df_chart.index.strftime('%m-%d %H:%M')

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df_chart['DateStr'],
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close'],
        name="Price"
    ))
    
    # خطوط الأهداف على الشارت
    for i, m in enumerate([1.0, 2.0, 3.0, 4.0], 1):
        tp = ep + (atr * 1.5 * m) if is_bull else ep - (atr * 1.5 * m)
        fig.add_hline(y=tp, line_dash="dot", line_width=1, line_color="#3fb950" if is_bull else "#f85149")

    # ضبط محور X ليصبح Category لمنع انكماش الفترات المغلقة
    fig.update_xaxes(
        type='category',
        nticks=6,
        showgrid=True,
        gridcolor='#21262d'
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor='#21262d'
    )

    fig.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
else:
    st.error("تعذر جلب البيانات. يرجى التأكد من رمز السهم أو تغيير الفريم الزمني.")
