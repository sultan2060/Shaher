import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import time
import numpy as np

# إعدادات الصفحة
st.set_page_config(
    page_title="📈 منصة تحليل تجريبي للتعلم - تنفيذ ورقي (تجريبي)",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS مخصص للواجهة
st.markdown("""
    <style>
    .main {
        background-color: #0f1419;
        color: #ffffff;
    }
    .metric-box {
        background-color: #1a1f2e;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #00d4ff;
    }
    .performance-box {
        background-color: #1a2635;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ffa500;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("منصة تحليل تجريبي للتعلم - تنفيذ ورقي (تجريبي)")
st.caption("🔰 بيانات تجريبية للتعلم على التنفيذ الورقي — غير متصلة بالتداول الحقيقي.")

# شريط المدخلات الجانبي
st.sidebar.header("⚙️ إعدادات البحث والتحديث")

# قائمة الأسهم المشهورة
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

selected_stock = st.sidebar.selectbox("اختر السهم أو العملة", list(stocks_list.keys()))
stock_symbol = stocks_list[selected_stock]

# اختيار الفترة الزمنية - محدثة حسب الطلب
period_options = {
    "1 دقيقة": ("1m", 7, "1 دقيقة"),
    "5 دقائق": ("5m", 60, "5 دقائق"),
    "15 دقيقة": ("15m", 60, "15 دقيقة"),
    "30 دقيقة": ("30m", 60, "30 دقيقة"),
    "60 دقيقة": ("60m", 60, "60 دقيقة"),
    "1 ساعة": ("1h", 730, "1 ساعة"),
    "4 ساعات": ("4h", 730, "4 ساعات"),
    "12 ساعة": ("12h", 1095, "12 ساعة"),
    "24 ساعة (يوم)": ("1d", 3650, "24 ساعة"),
    "أسبوع واحد": ("1wk", 10000, "أسبوع واحد")
}

selected_period_label = st.sidebar.selectbox("⏰ اختر الفترة الزمنية", list(period_options.keys()))
interval, days, period_name = period_options[selected_period_label]

# خيار التحديث التلقائي
auto_refresh = st.sidebar.checkbox("🔄 تحديث بيانات حية (كل 60 ثانية)", value=True)
refresh_interval = st.sidebar.slider("سرعة التحديث (ثواني)", 30, 300, 60, step=30)

# متتبع الأداء
st.sidebar.markdown("---")
st.sidebar.header("📊 متتبع الأداء")
performance_placeholder = st.sidebar.empty()

# تحميل البيانات مع قياس الوقت
def load_stock_data_with_timing(symbol, interval, days):
    start_time = time.time()
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # تحميل البيانات من Yahoo Finance
        data = yf.download(symbol, start=start_date, end=end_date, interval=interval, progress=False)
        
        load_time = time.time() - start_time
        
        # الحصول على معلومات إضافية
        ticker = yf.Ticker(symbol)
        info = ticker.info if hasattr(ticker, 'info') else {}
        
        return data, load_time, info
    except Exception as e:
        load_time = time.time() - start_time
        st.error(f"❌ خطأ في تحميل البيانات: {e}")
        return None, load_time, {}

# تحديث البيانات
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
    st.session_state.refresh_count = 0

# حساب الوقت منذ آخر تحديث
time_since_refresh = (datetime.now() - st.session_state.last_refresh).total_seconds()

# إعادة تحميل البيانات إذا تجاوز الوقت
if auto_refresh and time_since_refresh >= refresh_interval:
    st.rerun()

# تحميل البيانات
data, load_time, ticker_info = load_stock_data_with_timing(stock_symbol, interval, days)

if data is not None and len(data) > 0:
    st.session_state.last_refresh = datetime.now()
    st.session_state.refresh_count += 1
    
    # عرض معلومات الأداء
    with performance_placeholder.container():
        st.markdown(f"""
        <div class="performance-box">
        ⏱️ <b>وقت جلب البيانات:</b> {load_time:.2f} ثانية<br>
        🔄 <b>عدد التحديثات:</b> {st.session_state.refresh_count}<br>
        📅 <b>آخر تحديث:</b> {st.session_state.last_refresh.strftime('%H:%M:%S')}<br>
        📊 <b>عدد الشموع:</b> {len(data)}
        </div>
        """, unsafe_allow_html=True)
    
    # الحصول على معلومات السهم الحالية - مع معالجة الأخطاء
    # تأكد أن لدينا عمود Close صالح أو نستخدم Adj Close كبديل، ونتجاهل القيم NaN في نهاية السلسلة
    if 'Close' not in data.columns:
        if 'Adj Close' in data.columns:
            data['Close'] = data['Adj Close']
        else:
            st.error("❌ العمود 'Close' غير موجود في البيانات المستلمة من Yahoo Finance.")
            st.stop()

    # إزالة القيم الفارغة من سلسلة الإغلاق ثم أخذ آخر قيمة صالحة
    close_series = data['Close'].dropna()
    if close_series.empty:
        st.error("❌ لا توجد قيم صالحة في عمود 'Close' (كل القيم NaN أو الإطار فارغ).")
        st.stop()

    current_price = float(close_series.iloc[-1])
    if len(close_series) > 1:
        previous_price = float(close_series.iloc[-2])
    else:
        previous_price = current_price
    
    # حساب التغيير
    if previous_price != 0:
        price_change = current_price - previous_price
        price_change_pct = (price_change / previous_price) * 100
    else:
        price_change = 0
        price_change_pct = 0
    
    # الأعلى والأقل
    # تحقق من وجود الأعمدة قبل استخدامهم
    if 'High' in data.columns and not data['High'].dropna().empty:
        high_price = float(data['High'].max())
    else:
        high_price = current_price

    if 'Low' in data.columns and not data['Low'].dropna().empty:
        low_price = float(data['Low'].min())
    else:
        low_price = current_price

    if 'Volume' in data.columns and not data['Volume'].dropna().empty:
        volume_avg = float(data['Volume'].mean())
        current_volume = float(data['Volume'].iloc[-1])
    else:
        volume_avg = 0.0
        current_volume = 0.0
    
    # عرض المؤشرات الرئيسية
    st.subheader("📊 مستويات السهم الحالية - بيانات تجريبية 🔰")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "السعر الحالي 💰",
            f"${current_price:.2f}",
            delta=f"{price_change:.2f} ({price_change_pct:.2f}%)",
            delta_color="inverse"
        )
    
    with col2:
        st.metric("أعلى سعر 📈", f"${high_price:.2f}")
    
    with col3:
        st.metric("أقل سعر 📉", f"${low_price:.2f}")
    
    with col4:
        # تحقق قبل استخدام عمود Open
        if 'Open' in data.columns and not data['Open'].dropna().empty:
            st.metric("الفتح 🔓", f"${float(data['Open'].iloc[-1]):.2f}")
        else:
            st.metric("الفتح 🔓", "N/A")
    
    with col5:
        st.metric("الحجم الحالي 📦", f"{int(current_volume):,.0f}")
    
    st.markdown("---")
    
    # معلومات إضافية من السوق
    st.subheader("📋 معلومات السوق الإضافية")
    
    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    
    with col_info1:
        st.metric("متوسط الحجم 📊", f"{int(volume_avg):,.0f}")
    
    with col_info2:
        if volume_avg > 0:
            volume_ratio = (current_volume / volume_avg * 100)
        else:
            volume_ratio = 0
        st.metric("نسبة الحجم %", f"{volume_ratio:.1f}%")
    
    with col_info3:
        daily_range = high_price - low_price
        st.metric("نطاق الفترة 🔄", f"${daily_range:.2f}")
    
    with col_info4:
        if current_price > 0:
            volatility = (daily_range / current_price * 100)
        else:
            volatility = 0
        st.metric("التقلب % 📈", f"{volatility:.2f}%")
    
    st.markdown("---")
    
    # رسم بياني تفاعلي
    st.subheader(f"📈 الرسم البياني التفاعلي - {selected_period_label}")
    
    fig = go.Figure()
    
    # إضافة خط السعر
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Close'],
        mode='lines',
        name='السعر الإغلاق',
        line=dict(color='#00d4ff', width=2),
        hovertemplate='<b>%{x}</b><br>السعر: $%{y:.2f}<extra></extra>'
    ))
    
    # إضافة منطقة الملء
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['High'],
        fill=None,
        mode='lines',
        line_color='rgba(0,0,0,0)',
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Low'],
        fill='tonexty',
        mode='lines',
        line_color='rgba(0,0,0,0)',
        name='نطاق التقلب',
        fillcolor='rgba(0, 212, 255, 0.1)',
        hoverinfo='skip'
    ))
    
    # إضافة المتوسط المتحرك
    ma_20 = data['Close'].rolling(window=min(20, len(data))).mean()
    fig.add_trace(go.Scatter(
        x=data.index,
        y=ma_20,
        mode='lines',
        name='المتوسط المتحرك 20',
        line=dict(color='#ffa500', width=1, dash='dash'),
        hovertemplate='<b>%{x}</b><br>MA20: $%{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"تحليل السهم: {selected_stock} - {selected_period_label} | بيانات تجريبية 🔰",
        xaxis_title="التاريخ والوقت ⏰",
        yaxis_title="السعر ($) 💵",
        hovermode='x unified',
        template='plotly_dark',
        height=500,
        margin=dict(l=50, r=50, t=50, b=50),
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # رسم بياني لحجم التداول
    st.subheader("📊 حجم التداول والنشاط")
    
    fig_volume = go.Figure()
    
    colors = ['#00d4ff' if data['Close'].iloc[i] >= data['Open'].iloc[i] else '#ff6b6b' 
              for i in range(len(data))]
    
    fig_volume.add_trace(go.Bar(
        x=data.index,
        y=data['Volume'],
        name='الحجم',
        marker=dict(color=colors),
        hovertemplate='<b>%{x}</b><br>الحجم: %{y:,.0f}<extra></extra>'
    ))
    
    # إضافة خط المتوسط
    fig_volume.add_trace(go.Scatter(
        x=data.index,
        y=data['Volume'].rolling(window=min(20, len(data))).mean(),
        mode='lines',
        name='متوسط الحجم',
        line=dict(color='#ffa500', width=2),
        hovertemplate='<b>%{x}</b><br>المتوسط: %{y:,.0f}<extra></extra>'
    ))
    
    fig_volume.update_layout(
        title=f"حجم التداول خلال {selected_period_label}",
        xaxis_title="التاريخ والوقت ⏰",
        yaxis_title="الحجم 📦",
        template='plotly_dark',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig_volume, use_container_width=True)
    
    st.markdown("---")
    
    # إحصائيات متقدمة وأهداف التداول
    st.subheader("📊 الإحصائيات المتقدمة والأهداف")
    
    # حسابات الأهداف
    close_prices = data['Close'].values
    
    # المتوسطات
    ma_5 = float(data['Close'].rolling(window=min(5, len(data))).mean().iloc[-1])
    ma_20 = float(data['Close'].rolling(window=min(20, len(data))).mean().iloc[-1])
    ma_50 = float(data['Close'].rolling(window=min(50, len(data))).mean().iloc[-1])
    
    # المقاومة والدعم (استخدام الأعلى والأقل)
    resistance_1 = high_price
    support_1 = low_price
    pivot = (high_price + low_price + current_price) / 3
    
    # الأهداف بناءً على التقلب
    daily_range = high_price - low_price
    atr_value = daily_range * 1.5  # تقريب ATR
    target_1 = current_price + atr_value
    target_2 = current_price + (atr_value * 1.5)
    target_3 = current_price + (atr_value * 2)
    
    stop_loss = current_price - atr_value
    
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        st.metric("المتوسط 5 📊", f"${ma_5:.2f}")
    
    with col_stat2:
        st.metric("المتوسط 20 📈", f"${ma_20:.2f}")
    
    with col_stat3:
        st.metric("المتوسط 50 📉", f"${ma_50:.2f}")
    
    with col_stat4:
        std_dev = float(data['Close'].std())
        st.metric("الانحراف المعياري", f"${std_dev:.2f}")
    
    st.markdown("---")
    
    # جدول الأهداف والمستويات
    st.subheader("🎯 مستويات الأهداف والدعم/المقاومة")
    
    targets_df = pd.DataFrame({
        "المستوى": [
            "🛑 وقف الخسارة (Stop Loss)",
            "🔴 الدعم (Support 1)",
            "⚫ نقطة المحور (Pivot)",
            "🟢 المقاومة (Resistance 1)",
            "📍 الهدف الأول (Target 1)",
            "📍 الهدف الثاني (Target 2)",
            "📍 الهدف الثالث (Target 3)"
        ],
        "السعر": [
            f"${stop_loss:.2f}",
            f"${support_1:.2f}",
            f"${pivot:.2f}",
            f"${resistance_1:.2f}",
            f"${target_1:.2f}",
            f"${target_2:.2f}",
            f"${target_3:.2f}"
        ],
        "المسافة من السعر الحالي": [
            f"{((stop_loss - current_price) / current_price * 100):.2f}%",
            f"{((support_1 - current_price) / current_price * 100):.2f}%",
            f"{((pivot - current_price) / current_price * 100):.2f}%",
            f"{((resistance_1 - current_price) / current_price * 100):.2f}%",
            f"{((target_1 - current_price) / current_price * 100):.2f}%",
            f"{((target_2 - current_price) / current_price * 100):.2f}%",
            f"{((target_3 - current_price) / current_price * 100):.2f}%"
        ]
    })
    
    st.dataframe(
        targets_df.style.format(),
        use_container_width=True,
        height=300
    )
    
    st.markdown("---")
    
    # جدول البيانات التفصيلية
    st.subheader("📋 البيانات التفصيلية (آخر 20 شمعة/فترة)")
    
    display_data = data.tail(20).copy()
    display_data.columns = ['الفتح', 'الأعلى', 'الأقل', 'الإغلاق', 'الحجم', 'القيمة المعدلة']
    
    st.dataframe(
        display_data.style.format({
            'الفتح': '${:.2f}',
            'الأعلى': '${:.2f}',
            'الأقل': '${:.2f}',
            'الإغلاق': '${:.2f}',
            'الحجم': '{:,.0f}',
            'القيمة المعدلة': '${:.2f}'
        }),
        use_container_width=True,
        height=300
    )
    
    # خيار التنزيل
    csv = display_data.to_csv(index=True)
    st.download_button(
        label="📥 تحميل البيانات (CSV)",
        data=csv,
        file_name=f"{stock_symbol}_{selected_period_label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # ملاحظات هامة
    st.info("""
    📌 **ملاحظات هامة (توضيحية):**
    - 🔰 هذه الواجهة مخصصة لأغراض تجريبية وتعلُّم التنفيذ الورقي فقط.
    - ⛔ لا تعتبر هذه منصة للتداول الفعلي — لا تُنفّذ أوامر حقيقية عبرها.
    - 📊 البيانات قد تكون مأخوذة من مصادر عامة لأغراض العرض والتجربة ولا تعني وجود اتصال مباشر بالتداول الحي.
    - 🎯 استخدم المستويات كمرجع تعليمي فقط، وقم بعمل تحليلات إضافية قبل أي قرار واقعي.
    - 🔄 التحديث التلقائي مخصص للتجربة ولا يضمن تزامناً مع أسواق حقيقية.
    """)
    
else:
    st.error("❌ لم يتمكن من تحميل البيانات. يرجى المحاولة مرة أخرى أو اختيار سهم آخر.")

# تفعيل التحديث التلقائي
if auto_refresh:
    st.markdown(f"🔄 **سيتم تحديث البيانات تلقائياً كل {refresh_interval} ثانية**")
    time.sleep(2)  # تأخير صغير قبل إعادة التشغيل
