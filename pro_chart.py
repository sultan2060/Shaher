import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
import time

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="📈 منصة تجريبية للتحليل والتنبؤ الورقي",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS مخصص للواجهة والتنبيهات
st.markdown("""
    <style>
    .main { background-color: #0f1419; color: #ffffff; }
    .legal-warning {
        background-color: #3b1818;
        border: 2px solid #ff4b4b;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        color: #ffffff;
    }
    .strategy-info {
        background-color: #1a2332;
        border-right: 5px solid #00d4ff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .plan-card {
        background-color: #16212e;
        border: 1px solid #2e3e50;
        padding: 15px;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. إخلاء المسؤولية القانونية التنبيهي في بداية الصفحة
# ---------------------------------------------------------
st.markdown("""
<div class="legal-warning">
    <h3 style="margin-top:0; color:#ff6b6b;">⚠️ إشعار وتعهد قانوني: منصة تجريبية للتعلم فقط</h3>
    <p><b>تنبيه هام جداً:</b> هذه المنصة مخصصة لأغراض <b>التعليم والتداول الورقي التجريبي (Paper Trading) وتجربة البرمجة فقط</b>. 
    البيانات والإشارات والمستويات الظاهرة هي نتائج معادلات برمجية رياضية خاضعة للخطأ والصواب ولا تعتبر بأي شكل من الأشكال توصية استثمارية أو مالية أو دعوة للشراء أو البيع. 
    <b>المطور والمنصة يخليان مسؤوليتهما القانونية الكاملة عن أي قرارات تداول حقيقية أو خسائر مالية قد تنتج عن استخدام هذه البيانات.</b></p>
</div>
""", unsafe_allow_html=True)

st.title("🧪 منصة التحليل والتنبؤ التجريبي (استراتيجية Tshren)")

# ---------------------------------------------------------
# 3. الشريط الجانبي: الإقرار والتعديل على الشروط والأسهم
# ---------------------------------------------------------
st.sidebar.header("⚖️ الإقرار القانوني")
agreed = st.sidebar.checkbox("أقر بوعيي التام بأن هذه المنصة تجريبية وليست توصية مالية", value=False)

if not agreed:
    st.warning("👈 يرجى الموافقة على مربع الإقرار في الشريط الجانبي لتفعيل التحكم والاطلاع على الشارت والتنبؤات.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ الأسهم والفترات الزمنية")

# قائمة الأسهم العشرة
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

period_options = {
    "1 دقيقة": ("1m", 1),
    "5 دقائق": ("5m", 5),
    "15 دقيقة": ("15m", 14),
    "30 دقيقة": ("30m", 30),
    "60 دقيقة": ("60m", 60),
    "1 ساعة": ("1h", 60),
    "24 ساعة (يوم)": ("1d", 365),
    "أسبوع واحد": ("1wk", 1000)
}

selected_period_label = st.sidebar.selectbox("⏰ اختر الفترة الزمنية", list(period_options.keys()))
interval, days = period_options[selected_period_label]

st.sidebar.markdown("---")
st.sidebar.header("🛠️ التعديل على شروط ومحددات الاستراتيجية")

# ممتلكات قابلة للتعديل من قبل المستخدم
rr_ratio = st.sidebar.slider("نسبة العائد إلى المخاطرة (Target R:R)", 1.0, 4.0, 1.5, step=0.1)
ext_target_mult = st.sidebar.slider("مضاعف الهدف الممتد (Extended Target)", 1.5, 5.0, 2.5, step=0.1)
lookback_bars = st.sidebar.slider("عدد الشموع السابقة لفحص القمم والقيعان", 2, 10, 3)

auto_refresh = st.sidebar.checkbox("🔄 تحديث تلقائي حقيقي للبيانات", value=True)
refresh_interval = st.sidebar.slider("سرعة التحديث (ثواني)", 10, 120, 20, step=5)

# ---------------------------------------------------------
# 4. عرض الشروط والقواعد البرمجية المعتمدة للمستخدم
# ---------------------------------------------------------
with st.expander("📖 اضغط هنا لقراءة شروط ومعادلات الاستراتيجية الحالية (وكيفية حساب الخطة)"):
    st.markdown(f"""
    **كيف تعمل الاستراتيجية البرمجية الحالية؟**
    
    1. **إشارة الشراء (CALL 🚀):**
       * يتم البحث عن كسر قاع سابق خلال آخر `{lookback_bars}` شمعة.
       * تليها شمعة اختراق صاعدة (خضراء).
       * تليها شمعة إعادة اختبار (حمراء).
       * **نقطة الدخول:** سعر إغلاق الشمعة الحالية.
       * **وقف الخسارة:** أدنئ قاع تم تسجيله في نموذج الكسر.
       * **الهدف الأول:** `سعر الدخول + (المخاطرة × {rr_ratio})`.
       * **الهدف الممتد:** `سعر الدخول + (المخاطرة × {ext_target_mult})`.

    2. **إشارة البيع (PUT 🔻):**
       * يتم البحث عن اختراق قمة سابقة خلال آخر `{lookback_bars}` شمعة.
       * تليها شمعة هبوط مفردة (حمراء).
       * تليها شمعة إعادة اختبار (خضراء).
       * **نقطة الدخول:** سعر إغلاق الشمعة الحالية.
       * **وقف الخسارة:** أعلى قمة تم تسجيلها في نموذج الاختراق.
       * **الهدف الأول:** `سعر الدخول - (المخاطرة × {rr_ratio})`.
       * **الهدف الممتد:** `سعر الدخول - (المخاطرة × {ext_target_mult})`.
    """)

# ---------------------------------------------------------
# 5. خوارزمية حساب الإشارات بناءً على الشروط المعدلة
# ---------------------------------------------------------
def detect_tshren_signals(df, rr_mult, ext_mult, lookback):
    df = df.copy()
    df['Signal'] = None
    df['Entry'] = np.nan
    df['StopLoss'] = np.nan
    df['Target1'] = np.nan
    df['TargetExt'] = np.nan

    open_p = df['Open'].values
    high_p = df['High'].values
    low_p = df['Low'].values
    close_p = df['Close'].values

    for i in range(lookback + 1, len(df)):
        # شرط CALL
        min_prev_low = min(low_p[i-lookback:i-1])
        is_call = (
            (low_p[i-1] < min_prev_low) and 
            (close_p[i-1] > open_p[i-1]) and 
            (close_p[i] < open_p[i])
        )

        # شرط PUT
        max_prev_high = max(high_p[i-lookback:i-1])
        is_put = (
            (high_p[i-1] > max_prev_high) and 
            (close_p[i-1] < open_p[i-1]) and 
            (close_p[i] > open_p[i])
        )

        if is_call:
            entry = close_p[i]
            sl = min(low_p[i-lookback:i+1])
            risk = entry - sl
            if risk > 0:
                df.iloc[i, df.columns.get_loc('Signal')] = 'CALL'
                df.iloc[i, df.columns.get_loc('Entry')] = entry
                df.iloc[i, df.columns.get_loc('StopLoss')] = sl
                df.iloc[i, df.columns.get_loc('Target1')] = entry + (risk * rr_mult)
                df.iloc[i, df.columns.get_loc('TargetExt')] = entry + (risk * ext_mult)

        elif is_put:
            entry = close_p[i]
            sl = max(high_p[i-lookback:i+1])
            risk = sl - entry
            if risk > 0:
                df.iloc[i, df.columns.get_loc('Signal')] = 'PUT'
                df.iloc[i, df.columns.get_loc('Entry')] = entry
                df.iloc[i, df.columns.get_loc('StopLoss')] = sl
                df.iloc[i, df.columns.get_loc('Target1')] = entry - (risk * rr_mult)
                df.iloc[i, df.columns.get_loc('TargetExt')] = entry - (risk * ext_mult)

    return df

# جلب البيانات الحية
def load_data(symbol, interval, days):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        data = yf.download(symbol, start=start_date, end=end_date, interval=interval, progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception:
        return None

data = load_data(stock_symbol, interval, days)

if data is not None and not data.empty:
    df_signals = detect_tshren_signals(data, rr_ratio, ext_target_mult, lookback_bars)
    recent_signals = df_signals[df_signals['Signal'].notnull()].tail(5)

    close_series = data['Close'].dropna()
    current_price = float(close_series.iloc[-1])
    
    # ---------------------------------------------------------
    # 6. عرض خطة التداول المباشرة (Trade Plan)
    # ---------------------------------------------------------
    st.subheader("📋 خطة التنبؤ المستقبلي التجريبية (Trade Plan)")
    
    if not recent_signals.empty:
        latest = recent_signals.iloc[-1]
        sig_type = latest['Signal']
        badge = "🟢 توصية دخول تجريبية (CALL - صعود)" if sig_type == 'CALL' else "🔴 توصية دخول تجريبية (PUT - هبوط)"
        
        st.markdown(f"#### {badge}")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("نقطة الدخول المقترحة", f"${latest['Entry']:.2f}")
        col2.metric("الهدف الأول (Target 1)", f"${latest['Target1']:.2f}")
        col3.metric("الهدف الممتد (Target Ext)", f"${latest['TargetExt']:.2f}")
        col4.metric("وقف الخسارة (Stop Loss)", f"${latest['StopLoss']:.2f}")
        
        risk_val = abs(latest['Entry'] - latest['StopLoss'])
        col5.metric("مقدار المخاطرة للشمعة", f"${risk_val:.2f}")
    else:
        st.info("ℹ️ لم تعثر الخوارزمية على نماذج مكتملة الشروط في الشموع الأخيرة لهذه الفترة. يمكنك تعديل الحساسية من الشريط الجانبي.")

    st.markdown("---")

    # ---------------------------------------------------------
    # 7. الرسم البياني والتنبؤات
    # ---------------------------------------------------------
    st.subheader(f"📈 الشارت التفاعلي لـ {selected_stock} ({selected_period_label})")
    
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=df_signals.index,
        open=df_signals['Open'],
        high=df_signals['High'],
        low=df_signals['Low'],
        close=df_signals['Close'],
        name="السعر"
    ))

    # إضافة إشارات التنبؤ على الرسم
    for idx, row in recent_signals.iterrows():
        color_bg = "#1b5e20" if row['Signal'] == 'CALL' else "#b71c1c"
        color_arrow = "#00e676" if row['Signal'] == 'CALL' else "#ff5252"
        y_pos = row['Low'] if row['Signal'] == 'CALL' else row['High']
        y_shift = -20 if row['Signal'] == 'CALL' else 20
        
        fig.add_annotation(
            x=idx, y=y_pos,
            text=f"<b>{row['Signal']}</b><br>دخول: {row['Entry']:.2f}<br>هدف: {row['Target1']:.2f}<br>وقف: {row['StopLoss']:.2f}",
            showarrow=True, arrowhead=2, arrowcolor=color_arrow,
            bgcolor=color_bg, font=dict(color="white", size=9), yshift=y_shift
        )

    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------
    # 8. جدول الإشارات الأخيرة
    # ---------------------------------------------------------
    st.subheader("📜 سجل النماذج السابقة التي تم كشفها تلقائياً")
    display_table = recent_signals[['Signal', 'Entry', 'Target1', 'TargetExt', 'StopLoss']].copy()
    display_table.columns = ['النوع', 'سعر الدخول', 'الهدف الأول', 'الهدف الممتد', 'وقف الخسارة']
    st.dataframe(display_table.sort_index(ascending=False), use_container_width=True)

else:
    st.error("❌ تعذر جلب البيانات الحية حالياً. يرجى المحاولة لاحقاً أو تغيير الفريم الزمني.")

# التحديث التلقائي
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
