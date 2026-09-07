import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
import time

# 1. تهيئة الصفحة
st.set_page_config(
    page_title="📊 منصة Tshren Crypto الخوارزمية المدمجة",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #e6edf3; }
    .stApp { background-color: #0b0e14; }
    .disclaimer-box {
        background-color: #2a1215;
        border: 1px solid #ff4d4d;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. التعهد والإقرار القانوني
st.markdown("""
<div class="disclaimer-box">
    <h5 style="color:#ff4d4d; margin:0;">⚠️ تنبيه قانوني (للتداول الورقي والتعليم فقط)</h5>
    <p style="font-size:12px; color:#d1d5db; margin:5px 0 0 0;">
    هذه الخوارزمية أداة برمجية تجريبية تعتمد على معادلات رياضية وفحص أنماط الشموع (Tshren Strategy). النتائج والمدد الزمنية هي تقديرات إحصائية قابلة للخطأ ولا تعتبر توصية مالية أو استثمارية.
    </p>
</div>
""", unsafe_allow_html=True)

agreed = st.sidebar.checkbox("أقر بأن المنصة للتعليم والتداول الورقي فقط", value=True)
if not agreed:
    st.info("👈 يرجى الموافقة على الإقرار لتشغيل التحليل.")
    st.stop()

# 3. إعداد القائمة والخيارات
stocks_list = {
    "SPX (S&P 500)": "^GSPC",
    "Tesla (TSLA)": "TSLA",
    "Micron (MU)": "MU",
    "Meta (META)": "META",
    "Apple (AAPL)": "AAPL",
    "Google (GOOGL)": "GOOGL",
    "Microsoft (MSFT)": "MSFT",
    "Amazon (AMZN)": "AMZN",
    "Nvidia (NVDA)": "NVDA",
    "Netflix (NFLX)": "NFLX"
}

selected_stock = st.sidebar.selectbox("اختر السهم/المؤشر", list(stocks_list.keys()))
stock_symbol = stocks_list[selected_stock]

timeframe_config = {
    "1 دقيقة": {"interval": "1m", "days": 3, "minutes": 1},
    "5 دقائق": {"interval": "5m", "days": 10, "minutes": 5},
    "15 دقيقة": {"interval": "15m", "days": 20, "minutes": 15},
    "30 دقيقة": {"interval": "30m", "days": 40, "minutes": 30},
    "1 ساعة": {"interval": "1h", "days": 60, "minutes": 60},
    "1 يوم": {"interval": "1d", "days": 365, "minutes": 1440}
}

selected_tf = st.sidebar.selectbox("⏰ الفريم الزمني", list(timeframe_config.keys()))
tf_info = timeframe_config[selected_tf]

# 4. خوارزمية فحص نموذج Tshren Strategy (قاع/قمة مكسورة + الشموع المتعاقبة)
def detect_tshren_setup(df):
    if len(df) < 5:
        return None
    
    closes = df['Close'].values
    opens = df['Open'].values
    highs = df['High'].values
    lows = df['Low'].values
    
    # فحص آخر 3 شموع
    c3_open, c3_close = opens[-3], closes[-3] # الشمعة الأولى
    c2_open, c2_close = opens[-2], closes[-2] # الشمعة الثانية المفردة
    c1_open, c1_close = opens[-1], closes[-1] # الشمعة الأخيرة (إعادة الاختبار)
    
    # شرط الكول (CALL): خضراء مفردة بعد كسر ثم شمعة حمراء
    is_c2_green = c2_close > c2_open
    is_c1_red = c1_close < c1_open
    if is_c2_green and is_c1_red and (lows[-2] < lows[-4]):
        return "CALL"
        
    # شرط البوت (PUT): حمراء مفردة بعد اختراق ثم شمعة خضراء
    is_c2_red = c2_close < c2_open
    is_c1_green = c1_close > c1_open
    if is_c2_red and is_c1_green and (highs[-2] > highs[-4]):
        return "PUT"
        
    return "CALL" if closes[-1] >= opens[-1] else "PUT"

# 5. جلب البيانات
@st.cache_data(ttl=15)
def load_data(symbol, interval, days):
    end_d = datetime.now()
    start_d = end_d - timedelta(days=days)
    d = yf.download(symbol, start=start_d, end=end_d, interval=interval, progress=False)
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    return d.dropna()

df = load_data(stock_symbol, tf_info['interval'], tf_info['days'])

if df is not None and not df.empty:
    current_p = float(df['Close'].iloc[-1])
    
    # حساب ATR للسرعة والتذبذب
    df['TR'] = np.maximum(
        df['High'] - df['Low'],
        np.abs(df['High'] - df['Close'].shift(1))
    )
    atr = float(df['TR'].rolling(14).mean().iloc[-1])
    
    # تطبيق نمط التداول
    setup_type = detect_tshren_setup(df)
    is_bull = (setup_type == "CALL")
    
    # عرض نوع الصفقة والنمط المكتشف
    st.subheader(f"⚡ إشارة النموذج المكتشف: {setup_type} ({'صعود 🚀' if is_bull else 'هبوط 🔻'})")
    
    # 6. حساب الأهداف الأربعة مع الزمن المتوقع
    risk = atr * 1.2
    targets = {}
    for i, m in enumerate([1.0, 2.0, 3.0, 4.0], 1):
        t_price = current_p + (risk * m) if is_bull else current_p - (risk * m)
        dist = abs(t_price - current_p)
        est_bars = max(1, int(dist / (atr * 0.7)))
        est_mins = est_bars * tf_info['minutes']
        
        if est_mins < 60:
            t_str = f"~{est_mins} دقيقة"
        elif est_mins < 1440:
            t_str = f"~{round(est_mins/60, 1)} ساعة"
        else:
            t_str = f"~{round(est_mins/1440, 1)} يوم"
            
        targets[f"هدف {i}"] = {"price": t_price, "time": t_str}

    # عرض الأهداف بكروت منظمة وبسيطة
    cols = st.columns(4)
    for idx, (tk, tv) in enumerate(targets.items()):
        cols[idx].metric(label=f"🎯 {tk}", value=f"${tv['price']:.2f}", delta=f"الزمن: {tv['time']}")

    st.markdown("---")

    # 7. الشارت البصري النظيف (Clean UI دون تشتت)
    st.subheader(f"📈 رسم بياني نظيف خالٍ من التشتت البصري - {selected_stock}")
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="السعر"
    ))

    # رسم الأهداف بخطوط خفيفة أنيقة
    colors = ['#26a69a', '#00e676', '#ffb300', '#e040fb']
    for idx, (tk, tv) in enumerate(targets.items()):
        fig.add_hline(
            y=tv['price'],
            line_dash="dot",
            line_width=1.5,
            line_color=colors[idx],
            annotation_text=f"{tk}: ${tv['price']:.2f}",
            annotation_position="top right"
        )

    fig.update_layout(
        template="plotly_dark",
        height=500,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("❌ تعذر جلب البيانات. يرجى إعادة المحاولة.")
