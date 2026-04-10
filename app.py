import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Nail Space Soari", page_icon="💅", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; }
.stApp { background-color: #f7f7f7; }
h1 { color: #1a1a1a !important; font-weight: 700 !important; letter-spacing: 3px; font-size: 1.8rem !important; }
h2, h3 { color: #333 !important; font-weight: 500 !important; letter-spacing: 1px; }
.stTabs [data-baseweb="tab-list"] { background: #fff; border-radius: 4px; padding: 4px; gap: 4px; border: 1px solid #e0e0e0; }
.stTabs [data-baseweb="tab"] { border-radius: 2px; font-weight: 500; color: #888; letter-spacing: 1px; font-size: 0.85rem; }
.stTabs [aria-selected="true"] { background: #1a1a1a !important; color: white !important; }
.stForm { background: white; border-radius: 4px; padding: 24px; border: 1px solid #e0e0e0; }
.stButton > button, .stFormSubmitButton > button {
    background: #1a1a1a !important; color: white !important; border: none !important;
    border-radius: 4px !important; font-size: 14px !important; font-weight: 500 !important;
    letter-spacing: 2px !important; padding: 12px 0 !important; transition: all 0.2s !important;
}
.stButton > button:hover, .stFormSubmitButton > button:hover { background: #444 !important; }
.stSelectbox > div > div, .stNumberInput > div > div { border-radius: 4px !important; border-color: #e0e0e0 !important; }
[data-testid="metric-container"] { background: white; border-radius: 4px; padding: 16px; border: 1px solid #e0e0e0; }
.stAlert { border-radius: 4px !important; }
hr { border-color: #e0e0e0; }
</style>
""", unsafe_allow_html=True)

SPREADSHEET_ID = "1g40jis2r9PU1A7SqflLKWrJUQMQdpYCqqHjBFazs7Ps"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

MENUS = ["ジェル", "ケア", "オフ", "耳つぼ", "店販"]
MENUS2 = ["ハンド", "フット", "同時施術", "お買い物", "耳つぼ", "お直し"]
PAYMENTS = ["現金", "QR", "クレジット", "スマート"]
CUSTOMER_TYPES = ["再来", "新規"]

def get_client():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=60)
def load_data():
    gc = get_client()
    ws = gc.open_by_key(SPREADSHEET_ID).sheet1
    data = ws.get_all_records()
    df = pd.DataFrame(data)
    if df.empty:
        return df
    df["日付"] = pd.to_datetime(df["日付"], errors="coerce")
    df["年"] = pd.to_numeric(df["年"], errors="coerce")
    df["月"] = pd.to_numeric(df["月"], errors="coerce")
    df["最終売上"] = pd.to_numeric(df["最終売上"], errors="coerce").fillna(0)
    df["金額"] = pd.to_numeric(df["金額"], errors="coerce").fillna(0)
    return df

def save_row(row_data):
    gc = get_client()
    ws = gc.open_by_key(SPREADSHEET_ID).sheet1
    d = row_data["日付"]
    hpb = row_data["HPB"] or 0
    discount = row_data["割引"] or 0
    headers = ws.row_values(1)
    new_row = {h: "" for h in headers}
    new_row["日付"] = str(d)
    new_row["年月"] = f"{d.year}-{d.month:02d}-01"
    new_row["年度"] = d.year
    new_row["年"] = d.year
    new_row["月"] = d.month
    new_row["新規・再来"] = row_data["新規・再来"]
    new_row["担当"] = "西"
    new_row["メニュー"] = row_data["メニュー"]
    new_row["メニュー2"] = row_data["メニュー2"]
    new_row["支払い方法"] = row_data["支払い方法"]
    new_row["金額"] = row_data["金額"]
    new_row["HPB"] = hpb if hpb > 0 else ""
    new_row["割引"] = discount if discount > 0 else ""
    new_row["請求額"] = row_data["金額"] - hpb - discount
    new_row["最終売上"] = row_data["金額"]
    new_row["備考"] = row_data["備考"] or ""
    ws.append_row([new_row.get(h, "") for h in headers])
    st.cache_data.clear()

# ---- タイトル ----
st.markdown("# Nail Space Soari")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["✍️  売上入力", "📊  月別グラフ", "🌸  メニュー別集計"])

# =====================
# TAB1: 売上入力
# =====================
with tab1:
    st.markdown("### ✍️ 売上入力")

    col1, col2 = st.columns(2)
    with col1:
        input_date = st.date_input("📅 日付", value=date.today())
    with col2:
        customer_type = st.selectbox("👤 新規・再来", CUSTOMER_TYPES)

    col3, col4 = st.columns(2)
    with col3:
        menu = st.selectbox("💅 メニュー", MENUS)
    with col4:
        menu2 = st.selectbox("＋ メニュー2", MENUS2)

    payment = st.selectbox("💳 支払い方法", PAYMENTS)
    amount = st.number_input("💴 金額（円）", min_value=0, step=100, value=None, placeholder="金額を入力")
    hpb = st.number_input("🎟️ HPBポイント使用", min_value=0, step=100, value=None, placeholder="0")

    st.markdown("**🏷️ 割引**")
    st.caption("ボタンで選ぶか、金額を直接入力")
    discount_type = st.radio("割引率", ["なし", "5%", "10%", "30%", "手入力"], horizontal=True, label_visibility="collapsed")
    manual_discount = st.number_input("割引金額（手入力）", min_value=0, step=100, value=None, placeholder="0", disabled=(discount_type != "手入力"))

    amount = amount or 0
    hpb = hpb or 0
    manual_discount = manual_discount or 0

    if discount_type == "5%":      discount = int(amount * 0.05)
    elif discount_type == "10%":   discount = int(amount * 0.10)
    elif discount_type == "30%":   discount = int(amount * 0.30)
    elif discount_type == "手入力": discount = manual_discount
    else:                          discount = 0

    note = st.text_input("📝 備考（任意）")
    seikyu = amount - hpb - discount

    if amount > 0:
        if discount > 0:
            st.info(f"割引額: **¥{discount:,}**　→　請求額: **¥{seikyu:,}**")
        else:
            st.info(f"請求額: **¥{seikyu:,}**　／　金額: ¥{amount:,}")

    if st.button("💾  保存する", use_container_width=True, type="primary"):
        if amount == 0:
            st.warning("金額を入力してください")
        else:
            try:
                save_row({"日付": input_date, "新規・再来": customer_type, "メニュー": menu,
                          "メニュー2": menu2, "支払い方法": payment, "金額": amount,
                          "HPB": hpb, "割引": discount, "備考": note})
                st.success("✅ 保存しました！")
                st.balloons()
            except Exception as e:
                st.error(f"保存エラー: {e}")

# =====================
# TAB2: 月別グラフ
# =====================
with tab2:
    st.markdown("### 📊 月別売上グラフ")
    try:
        df = load_data()
        years = sorted(df["年"].dropna().astype(int).unique().tolist(), reverse=True)
        selected_year = st.selectbox("年を選択", years, key="year_select")
        df_year = df[df["年"] == selected_year].copy()
        monthly = df_year.groupby("月")["最終売上"].sum().reset_index()
        monthly.columns = ["月", "売上"]
        monthly["月"] = monthly["月"].astype(int)
        all_months = pd.DataFrame({"月": range(1, 13)})
        monthly = all_months.merge(monthly, on="月", how="left").fillna(0)
        monthly["月ラベル"] = monthly["月"].astype(str) + "月"

        def bar_color(v):
            if v < 100000:   return "#e0e0e0"
            elif v < 200000: return "#b0b0b0"
            elif v < 300000: return "#808080"
            elif v < 400000: return "#505050"
            else:            return "#1a1a1a"
        monthly["color"] = monthly["売上"].apply(bar_color)

        fig = px.bar(monthly, x="月ラベル", y="売上", title=f"{selected_year}年 月別売上", text="売上")
        fig.update_traces(texttemplate="¥%{text:,.0f}", textposition="outside", marker_color=monthly["color"])
        fig.update_layout(yaxis_title="売上（円）", xaxis_title="", showlegend=False, height=420,
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="Noto Sans JP"), title_font_size=16)
        fig.update_yaxes(gridcolor="rgba(0,0,0,0.06)")
        st.plotly_chart(fig, use_container_width=True)

        total = monthly["売上"].sum()
        nonzero = monthly[monthly["売上"] > 0]["売上"]
        avg = nonzero.mean() if len(nonzero) > 0 else 0
        c1, c2 = st.columns(2)
        c1.metric("💰 年間合計", f"¥{total:,.0f}")
        c2.metric("📈 月平均", f"¥{avg:,.0f}")
        if selected_year - 1 in years:
            prev_total = df[df["年"] == selected_year - 1]["最終売上"].sum()
            diff_pct = ((total - prev_total) / prev_total * 100) if prev_total > 0 else 0
            st.metric("🔄 前年比", f"{diff_pct:+.1f}%", delta=f"¥{total - prev_total:+,.0f}")
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")

# =====================
# TAB3: メニュー別集計
# =====================
with tab3:
    st.markdown("### 🌸 メニュー別集計")
    try:
        df = load_data()
        years2 = sorted(df["年"].dropna().astype(int).unique().tolist(), reverse=True)
        col_a, col_b = st.columns(2)
        with col_a:
            sel_year2 = st.selectbox("年", years2, key="year2")
        with col_b:
            months_avail = sorted(df[df["年"] == sel_year2]["月"].dropna().astype(int).unique().tolist())
            month_options = ["全月"] + [f"{m}月" for m in months_avail]
            sel_month = st.selectbox("月", month_options, key="month2")

        df_f = df[df["年"] == sel_year2].copy()
        if sel_month != "全月":
            df_f = df_f[df_f["月"] == int(sel_month.replace("月", ""))]

        menu_agg = df_f.groupby("メニュー")["最終売上"].agg(["sum", "count"]).reset_index()
        menu_agg.columns = ["メニュー", "売上合計", "件数"]
        menu_agg = menu_agg.sort_values("売上合計", ascending=False)
        menu_agg["売上合計"] = menu_agg["売上合計"].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(menu_agg, use_container_width=True, hide_index=True)

        menu_plot = df_f.groupby("メニュー")["最終売上"].sum().reset_index()
        menu_plot = menu_plot[menu_plot["最終売上"] > 0]
        fig2 = px.pie(menu_plot, names="メニュー", values="最終売上", title="メニュー別売上構成",
                      color_discrete_sequence=["#1a1a1a", "#555", "#888", "#aaa", "#ccc", "#e0e0e0"], hole=0.4)
        fig2.update_layout(height=380, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Noto Sans JP"))
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("### 👥 新規・再来")
        nc_agg = df_f[df_f["新規・再来"].isin(["新規", "再来"])].groupby("新規・再来")["最終売上"].agg(["sum", "count"]).reset_index()
        nc_agg.columns = ["種別", "売上合計", "件数"]
        nc_agg["売上合計"] = nc_agg["売上合計"].apply(lambda x: f"¥{x:,.0f}")
        st.dataframe(nc_agg, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
