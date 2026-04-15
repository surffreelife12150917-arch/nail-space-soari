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

@st.cache_data(ttl=10)
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

tab1, tab2, tab3, tab4 = st.tabs(["✍️  売上入力", "📊  月別グラフ", "🌸  メニュー別集計", "✏️  編集"])

# =====================
# TAB1: 売上入力
# =====================
with tab1:
    st.markdown("### ✍️ 売上入力")

    # フォームリセット用キー
    if "form_key" not in st.session_state:
        st.session_state.form_key = 0
    fk = st.session_state.form_key

    col1, col2 = st.columns(2)
    with col1:
        input_date = st.date_input("📅 日付", value=date.today(), key=f"date_{fk}")
    with col2:
        customer_type = st.selectbox("👤 新規・再来", CUSTOMER_TYPES, key=f"ctype_{fk}")

    col3, col4 = st.columns(2)
    with col3:
        menu = st.selectbox("💅 メニュー", MENUS, key=f"menu_{fk}")
    with col4:
        menu2 = st.selectbox("＋ メニュー2", MENUS2, key=f"menu2_{fk}")

    payment = st.selectbox("💳 支払い方法", PAYMENTS, key=f"payment_{fk}")
    amount = st.number_input("💴 金額（円）", min_value=0, step=100, value=None, placeholder="金額を入力", key=f"amount_{fk}")
    hpb = st.number_input("🎟️ HPBポイント使用", min_value=0, step=100, value=None, placeholder="0", key=f"hpb_{fk}")

    st.markdown("**🏷️ 割引**")
    st.caption("ボタンで選ぶか、金額を直接入力")
    discount_type = st.radio("割引率", ["なし", "5%", "10%", "30%", "手入力"], horizontal=True, label_visibility="collapsed", key=f"dtype_{fk}")
    manual_discount = st.number_input("割引金額（手入力）", min_value=0, step=100, value=None, placeholder="0", disabled=(discount_type != "手入力"), key=f"mdisc_{fk}")

    amount = amount or 0
    hpb = hpb or 0
    manual_discount = manual_discount or 0

    if discount_type == "5%":      discount = int(amount * 0.05)
    elif discount_type == "10%":   discount = int(amount * 0.10)
    elif discount_type == "30%":   discount = int(amount * 0.30)
    elif discount_type == "手入力": discount = manual_discount
    else:                          discount = 0

    note = st.text_input("📝 備考（任意）", key=f"note_{fk}")
    seikyu = amount - hpb - discount

    # 保存前の確認ボックス
    if amount > 0:
        st.markdown(f"""
<div style="background:#fff;border:1px solid #e0e0e0;border-radius:4px;padding:16px;margin:12px 0;">
<div style="font-size:0.8rem;color:#888;margin-bottom:8px;">── 保存内容の確認 ──</div>
<div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span>金額</span><strong>¥{amount:,}</strong></div>
{"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'><span>割引（" + discount_type + "）</span><strong style='color:#c00'>－¥" + f"{discount:,}" + "</strong></div>" if discount > 0 else ""}
{"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'><span>HPB</span><strong style='color:#c00'>－¥" + f"{hpb:,}" + "</strong></div>" if hpb > 0 else ""}
<hr style="border-color:#e0e0e0;margin:8px 0;">
<div style="display:flex;justify-content:space-between;font-size:1.1rem;"><span><strong>請求額</strong></span><strong>¥{seikyu:,}</strong></div>
</div>
""", unsafe_allow_html=True)

    if st.button("💾  保存する", use_container_width=True, type="primary"):
        if amount == 0:
            st.warning("金額を入力してください")
        else:
            try:
                save_row({"日付": input_date, "新規・再来": customer_type, "メニュー": menu,
                          "メニュー2": menu2, "支払い方法": payment, "金額": amount,
                          "HPB": hpb, "割引": discount, "備考": note})
                st.session_state.save_success = True
                st.session_state.form_key += 1  # フォームリセット
                st.rerun()
            except Exception as e:
                st.error(f"保存エラー: {e}")

    # 保存完了メッセージ＋キラキラ（ボタンの下）
    if st.session_state.get("save_success"):
        st.success("✅ 保存しました！")
        st.markdown("""
<div style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;">
<style>
@keyframes sparkle {
  0%   { transform: scale(0) rotate(0deg);   opacity: 1; }
  50%  { transform: scale(1.2) rotate(180deg); opacity: 1; }
  100% { transform: scale(0) rotate(360deg); opacity: 0; }
}
.spark { position:absolute; font-size:2rem; animation: sparkle 1.2s ease-out forwards; }
</style>
<span class="spark" style="left:10%;top:20%;animation-delay:0s;">✦</span>
<span class="spark" style="left:25%;top:10%;animation-delay:0.1s;">✧</span>
<span class="spark" style="left:50%;top:5%;animation-delay:0.2s;">✦</span>
<span class="spark" style="left:70%;top:15%;animation-delay:0.15s;">✧</span>
<span class="spark" style="left:85%;top:25%;animation-delay:0.05s;">✦</span>
<span class="spark" style="left:15%;top:50%;animation-delay:0.25s;">✧</span>
<span class="spark" style="left:40%;top:40%;animation-delay:0.1s;">✦</span>
<span class="spark" style="left:60%;top:35%;animation-delay:0.3s;">✧</span>
<span class="spark" style="left:80%;top:55%;animation-delay:0.2s;">✦</span>
<span class="spark" style="left:30%;top:70%;animation-delay:0.15s;">✧</span>
<span class="spark" style="left:55%;top:65%;animation-delay:0.05s;">✦</span>
<span class="spark" style="left:75%;top:75%;animation-delay:0.2s;">✧</span>
</div>
""", unsafe_allow_html=True)
        st.session_state.save_success = False

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

        # 12ヶ月分のデータ準備
        monthly_all = df_year.groupby("月")["最終売上"].sum().reset_index()
        monthly_all.columns = ["月", "売上"]
        monthly_all["月"] = monthly_all["月"].astype(int)
        all_months = pd.DataFrame({"月": range(1, 13)})
        monthly_all = all_months.merge(monthly_all, on="月", how="left").fillna(0)

        # 月スライダー
        sel_month = st.slider("月を選択", min_value=1, max_value=12,
                              value=date.today().month, format="%d月", key="month_slider")

        # 選択月の売上
        m_val = monthly_all[monthly_all["月"] == sel_month]["売上"].values[0]
        prev_m_val = monthly_all[monthly_all["月"] == sel_month - 1]["売上"].values[0] if sel_month > 1 else 0

        def bar_color(v):
            if v < 100000:   return "#e0e0e0"
            elif v < 200000: return "#b0b0b0"
            elif v < 300000: return "#808080"
            elif v < 400000: return "#505050"
            else:            return "#1a1a1a"

        # 選択月カード
        diff = int(m_val - prev_m_val)
        diff_str = f"前月比 ¥{diff:+,}" if sel_month > 1 else ""
        st.markdown(f"""
<div style="background:#fff;border:1px solid #e0e0e0;border-radius:4px;padding:24px;text-align:center;margin:8px 0;">
  <div style="font-size:1rem;color:#888;margin-bottom:4px;">{selected_year}年 {sel_month}月</div>
  <div style="font-size:2.2rem;font-weight:700;color:{bar_color(m_val) if m_val > 0 else '#ccc'};">¥{int(m_val):,}</div>
  <div style="font-size:0.85rem;color:{'#555' if diff >= 0 else '#c00'};margin-top:6px;">{diff_str}</div>
</div>
""", unsafe_allow_html=True)

        # 12ヶ月バー（静的・タッチ不可）
        st.markdown("#### 年間推移")
        bar_html = '<div style="display:flex;align-items:flex-end;gap:3px;height:120px;padding:0 4px;">'
        max_val = monthly_all["売上"].max() or 1
        for _, r in monthly_all.iterrows():
            h = int((r["売上"] / max_val) * 100)
            color = bar_color(r["売上"])
            border = "2px solid #1a1a1a" if r["月"] == sel_month else "none"
            bar_html += f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;">'
            bar_html += f'<div style="width:100%;height:{h}px;background:{color};border-radius:2px 2px 0 0;outline:{border};"></div>'
            bar_html += f'<div style="font-size:0.6rem;color:{"#1a1a1a" if r["月"]==sel_month else "#aaa"};font-weight:{"700" if r["月"]==sel_month else "400"};">{int(r["月"])}月</div>'
            bar_html += '</div>'
        bar_html += '</div>'
        st.markdown(bar_html, unsafe_allow_html=True)

        # 年間サマリー
        st.markdown("---")
        total = monthly_all["売上"].sum()
        nonzero = monthly_all[monthly_all["売上"] > 0]["売上"]
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

        df_f["割引"] = pd.to_numeric(df_f["割引"], errors="coerce").fillna(0)
        menu_agg = df_f.groupby("メニュー").agg(
            売上合計=("最終売上", "sum"),
            件数=("最終売上", "count"),
            割引合計=("割引", "sum")
        ).reset_index()
        menu_agg = menu_agg.sort_values("売上合計", ascending=False)
        menu_agg["売上合計"] = menu_agg["売上合計"].apply(lambda x: f"¥{x:,.0f}")
        menu_agg["割引合計"] = menu_agg["割引合計"].apply(lambda x: f"¥{x:,.0f}" if x > 0 else "-")
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

# =====================
# TAB4: 編集
# =====================
with tab4:
    st.markdown("### ✏️ 過去データの編集")

    # 更新・削除完了メッセージ
    if st.session_state.get("edit_success"):
        st.success(st.session_state.edit_success)
        st.session_state.edit_success = None

    try:
        df = load_data()
        if df.empty:
            st.info("データがありません")
        else:
            df_edit = df.copy()
            df_edit["日付str"] = df_edit["日付"].dt.strftime("%Y-%m-%d")

            # ── STEP1: 年・月で絞り込み ──
            years_e = sorted(df_edit["年"].dropna().astype(int).unique().tolist(), reverse=True)
            months_all = sorted(df_edit["月"].dropna().astype(int).unique().tolist(), reverse=True)

            fc1, fc2 = st.columns(2)
            with fc1:
                sel_ey = st.selectbox("📅 年", years_e, key="edit_year")
            with fc2:
                months_in_year = sorted(df_edit[df_edit["年"] == sel_ey]["月"].dropna().astype(int).unique().tolist(), reverse=True)
                sel_em = st.selectbox("📅 月", [f"{m}月" for m in months_in_year], key="edit_month")
            sel_em_int = int(sel_em.replace("月", ""))

            df_filtered = df_edit[(df_edit["年"] == sel_ey) & (df_edit["月"] == sel_em_int)].copy()
            df_filtered = df_filtered.iloc[::-1]  # 新しい順

            if df_filtered.empty:
                st.info("該当データなし")
            else:
                # ── STEP2: 件数一覧から選ぶ ──
                st.markdown(f"**{sel_ey}年{sel_em_int}月 — {len(df_filtered)}件**")

                choices = []
                for _, r in df_filtered.iterrows():
                    d = r["日付str"]
                    m1 = r["メニュー"] or ""
                    m2 = r["メニュー2"] or ""
                    amt = int(r["金額"] or 0)
                    choices.append(f"{d}　{m1}／{m2}　¥{amt:,}")

                sel_label = st.radio("編集する記録を選んでください", choices, key="edit_radio", label_visibility="collapsed")
                sel_pos = choices.index(sel_label)
                idx = df_filtered.index[sel_pos]
                row = df.iloc[idx]

                st.markdown("---")
                st.markdown("**✏️ 編集フォーム**")

                with st.form("edit_form"):
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        e_date = st.date_input("📅 日付", value=pd.to_datetime(row["日付"]).date())
                    with e_col2:
                        e_customer = st.selectbox("👤 新規・再来", CUSTOMER_TYPES,
                                                  index=CUSTOMER_TYPES.index(row["新規・再来"]) if row["新規・再来"] in CUSTOMER_TYPES else 0)
                    e_col3, e_col4 = st.columns(2)
                    with e_col3:
                        e_menu = st.selectbox("💅 メニュー", MENUS,
                                              index=MENUS.index(row["メニュー"]) if row["メニュー"] in MENUS else 0)
                    with e_col4:
                        e_menu2 = st.selectbox("＋ メニュー2", MENUS2,
                                               index=MENUS2.index(row["メニュー2"]) if row["メニュー2"] in MENUS2 else 0)
                    e_payment = st.selectbox("💳 支払い方法", PAYMENTS,
                                             index=PAYMENTS.index(row["支払い方法"]) if row["支払い方法"] in PAYMENTS else 0)
                    e_amount = st.number_input("💴 金額（円）", min_value=0, step=100, value=int(row["金額"] or 0))
                    e_hpb    = st.number_input("🎟️ HPB", min_value=0, step=100, value=int(float(row["HPB"])) if str(row["HPB"]) not in ["", "nan"] else 0)

                    st.markdown("**🏷️ 割引**")
                    st.caption("ボタンで選ぶか、金額を直接入力")
                    e_discount_type = st.radio("割引率", ["なし", "5%", "10%", "30%", "手入力"],
                                               horizontal=True, label_visibility="collapsed", key=f"e_disc_type_{idx}",
                                               index=4)  # デフォルト：手入力
                    existing_disc = int(float(row["割引"])) if str(row["割引"]) not in ["", "nan"] else 0
                    e_manual_discount = st.number_input("割引金額（手入力）", min_value=0, step=100,
                                                        value=existing_disc, key=f"e_manual_disc_{idx}")

                    e_note = st.text_input("📝 備考", value=str(row["備考"]) if row["備考"] else "")

                    # 割引計算（フォーム内なのでサブミット時に確定）
                    _amt = int(row["金額"] or 0)
                    _ed  = existing_disc
                    st.info(f"現在の請求額: **¥{_amt - (int(float(row['HPB'])) if str(row['HPB']) not in ['', 'nan'] else 0) - _ed:,}**　※更新後に反映")

                    update_btn = st.form_submit_button("✅ 更新する", use_container_width=True, type="primary")

                if update_btn:
                    try:
                        gc = get_client()
                        ws = gc.open_by_key(SPREADSHEET_ID).sheet1
                        sheet_row = idx + 2
                        headers = ws.row_values(1)
                        hpb_v  = e_hpb or 0
                        # 割引計算（パーセント or 手入力）
                        if e_discount_type == "5%":       disc_v = int(e_amount * 0.05)
                        elif e_discount_type == "10%":    disc_v = int(e_amount * 0.10)
                        elif e_discount_type == "30%":    disc_v = int(e_amount * 0.30)
                        elif e_discount_type == "手入力": disc_v = e_manual_discount or 0
                        else:                             disc_v = 0
                        updates = {
                            "日付": str(e_date), "年月": f"{e_date.year}-{e_date.month:02d}-01",
                            "年度": e_date.year, "年": e_date.year, "月": e_date.month,
                            "新規・再来": e_customer, "メニュー": e_menu, "メニュー2": e_menu2,
                            "支払い方法": e_payment, "金額": e_amount,
                            "HPB": hpb_v if hpb_v > 0 else "",
                            "割引": disc_v if disc_v > 0 else "",
                            "請求額": e_amount - hpb_v - disc_v,
                            "最終売上": e_amount, "備考": e_note,
                        }
                        for col_name, val in updates.items():
                            if col_name in headers:
                                col_idx = headers.index(col_name) + 1
                                ws.update_cell(sheet_row, col_idx, val)
                        st.cache_data.clear()
                        st.session_state["edit_success"] = "✅ 更新しました！"
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新エラー: {e}")

                # ── 削除 ──
                st.markdown("---")
                if "delete_confirm" not in st.session_state:
                    st.session_state.delete_confirm = False

                if not st.session_state.delete_confirm:
                    if st.button("🗑️ この記録を削除する", use_container_width=True):
                        st.session_state.delete_confirm = True
                        st.rerun()
                else:
                    st.warning("本当に削除しますか？この操作は元に戻せません。")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ はい、削除する", use_container_width=True, type="primary"):
                            try:
                                gc = get_client()
                                ws = gc.open_by_key(SPREADSHEET_ID).sheet1
                                ws.delete_rows(idx + 2)
                                st.cache_data.clear()
                                st.session_state.delete_confirm = False
                                st.session_state["edit_success"] = "🗑️ 削除しました！"
                                st.rerun()
                            except Exception as e:
                                st.error(f"削除エラー: {e}")
                    with c2:
                        if st.button("キャンセル", use_container_width=True):
                            st.session_state.delete_confirm = False
                            st.rerun()
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
