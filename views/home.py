"""🏠 今日の画面 — アプリを開くと最初に出るシンプルなトップページ"""
from datetime import date

import pandas as pd
import streamlit as st

from common import (apply_style, check_login, get_client, load_df, load_sales,
                    update_row, active_menu_names, MENUS2, SPREADSHEET_ID, RESERVE_HEADERS)



PAYMENTS = ["現金", "QR", "クレジット", "スマート"]
CUSTOMER_TYPES = ["再来", "新規"]
STATUS = ["予約中", "来店済", "キャンセル"]

today = date.today()
wd = "月火水木金土日"[today.weekday()]

st.markdown("# Nail Space Soari")
st.markdown(f"### 🏠 今日 — {today.year}年{today.month}月{today.day}日（{wd}）")
st.caption("くわしい機能は左のメニューから（予約とカルテ／メニュー管理／月次サマリー／売上）")
st.markdown("---")

# =====================
# 今日の売上サマリー
# =====================
sales = load_sales()
if not sales.empty:
    today_sales = sales[sales["日付"].dt.date == today]
    c1, c2 = st.columns(2)
    c1.metric("💴 今日の売上", f"¥{int(today_sales['最終売上'].sum()):,}")
    c2.metric("🧾 今日の件数", f"{len(today_sales)} 件")

# =====================
# 今日の予約
# =====================
st.markdown("### 📅 今日の予約")
rsv = load_df("予約", RESERVE_HEADERS)
today_rsv = rsv[(rsv["日付"] == str(today)) & (rsv["ステータス"] != "キャンセル")] if not rsv.empty else pd.DataFrame()

if today_rsv.empty:
    st.info("今日の予約はありません")
else:
    for r in sorted(today_rsv.to_dict("records"), key=lambda x: x.get("時間", "")):
        with st.container(border=True):
            cA, cB = st.columns([3, 1])
            with cA:
                st.markdown(f"**{r['時間']}　{r['名前']} さん**　💅 {r['メニュー']}")
                if r.get("備考"):
                    st.caption(f"📝 {r['備考']}")
            with cB:
                new_status = st.selectbox("状態", STATUS,
                                          index=STATUS.index(r["ステータス"]) if r["ステータス"] in STATUS else 0,
                                          key=f"tstat_{r['予約ID']}", label_visibility="collapsed")
                if new_status != r["ステータス"]:
                    r["ステータス"] = new_status
                    update_row("予約", RESERVE_HEADERS, "予約ID", r["予約ID"], r)
                    st.rerun()

st.markdown("---")

# =====================
# クイック売上入力
# =====================
st.markdown("### ✍️ クイック売上入力")
st.caption("最低限だけ。HPBポイントなど細かい入力は左メニューの「売上」からどうぞ。")

if "quick_key" not in st.session_state:
    st.session_state.quick_key = 0
qk = st.session_state.quick_key

c1, c2 = st.columns(2)
with c1:
    q_menu = st.selectbox("💅 メニュー", active_menu_names(), key=f"qmenu_{qk}")
with c2:
    q_menu2 = st.selectbox("＋ メニュー2", MENUS2, key=f"qmenu2_{qk}")

q_ctype = st.selectbox("👤 新規・再来", CUSTOMER_TYPES, key=f"qctype_{qk}")

c3, c4 = st.columns(2)
with c3:
    q_payment = st.selectbox("💳 支払い方法", PAYMENTS, key=f"qpay_{qk}")
with c4:
    q_amount = st.number_input("💴 金額（円）", min_value=0, step=100, value=None,
                               placeholder="金額を入力", key=f"qamt_{qk}")

st.markdown("**🏷️ 割引**")
q_dtype = st.radio("割引率", ["なし", "5%", "10%", "30%", "手入力"], horizontal=True,
                   label_visibility="collapsed", key=f"qdtype_{qk}")
q_manual = st.number_input("割引金額（手入力）", min_value=0, step=100, value=None, placeholder="0",
                           disabled=(q_dtype != "手入力"), key=f"qmdisc_{qk}")

q_amount = q_amount or 0
q_manual = q_manual or 0
if q_dtype == "5%":      q_discount = int(q_amount * 0.05)
elif q_dtype == "10%":   q_discount = int(q_amount * 0.10)
elif q_dtype == "30%":   q_discount = int(q_amount * 0.30)
elif q_dtype == "手入力": q_discount = q_manual
else:                    q_discount = 0

if q_amount > 0:
    q_seikyu = q_amount - q_discount
    disc_label = f" 割引 -¥{q_discount:,} → 請求 ¥{q_seikyu:,}" if q_discount else ""
    st.info(f"📅 今日 ／ {q_menu}・{q_menu2} ／ {q_payment} ／ **¥{q_amount:,}**（{q_ctype}）{disc_label}")
    if st.button("保存する", use_container_width=True):
        gc = get_client()
        ws = gc.open_by_key(SPREADSHEET_ID).sheet1
        headers = ws.row_values(1)
        new_row = {h: "" for h in headers}
        new_row["日付"] = str(today)
        new_row["年月"] = f"{today.year}-{today.month:02d}-01"
        new_row["年度"] = today.year
        new_row["年"] = today.year
        new_row["月"] = today.month
        new_row["新規・再来"] = q_ctype
        new_row["担当"] = "西"
        new_row["メニュー"] = q_menu
        new_row["メニュー2"] = q_menu2
        new_row["支払い方法"] = q_payment
        new_row["金額"] = q_amount
        new_row["割引"] = q_discount if q_discount > 0 else ""
        new_row["請求額"] = q_amount - q_discount
        new_row["最終売上"] = q_amount
        ws.append_row([new_row.get(h, "") for h in headers])
        st.cache_data.clear()
        st.session_state.quick_key += 1
        st.success("✅ 保存しました")
        st.balloons()
        st.rerun()
