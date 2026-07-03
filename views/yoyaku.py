import calendar
import uuid
from datetime import date, datetime

import pandas as pd
import streamlit as st

from common import (apply_style, check_login, load_df, append_row, update_row,
                    active_menu_names, menu_durations, CUSTOMER_HEADERS, RESERVE_HEADERS,
                    OPEN_HOUR, CLOSE_HOUR, DEFAULT_DURATION)

st.markdown("""
<style>
table.cal { width:100%; border-collapse:collapse; background:#fff; border:1px solid #e0e0e0; table-layout:fixed; }
table.cal th { background:#1a1a1a; color:#fff; font-size:.7rem; padding:6px 0; font-weight:500; letter-spacing:1px; }
table.cal td { border:1px solid #eee; vertical-align:top; height:74px; padding:3px 4px; font-size:.7rem; }
table.cal td .d { font-weight:700; color:#555; }
table.cal td.today { background:#fdf3ec; }
table.cal td.othermonth { background:#fafafa; color:#ccc; }
table.cal .rsv { display:block; background:#c9a896; color:#fff; border-radius:3px; padding:1px 3px; margin-top:2px;
                 font-size:.62rem; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; }
table.cal td.sun .d { color:#c0392b; } table.cal td.sat .d { color:#2980b9; }
</style>
""", unsafe_allow_html=True)


TIMES = [f"{h}:{m:02d}" for h in range(OPEN_HOUR, CLOSE_HOUR + 1) for m in (0, 30)]
STATUS = ["予約中", "来店済", "キャンセル"]
MENUS = active_menu_names()
DURATIONS = menu_durations()


def to_min(t):
    """'10:30' → 630 分"""
    try:
        h, m = str(t).split(":")
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError):
        return 0


def rsv_duration(r):
    try:
        d = int(float(r.get("所要時間", 0) or 0))
    except (TypeError, ValueError):
        d = 0
    return d if d > 0 else DURATIONS.get(str(r.get("メニュー", "")), DEFAULT_DURATION)

st.markdown("# 予約とカルテ")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📅  予約カレンダー", "➕  予約追加", "👤  顧客カルテ", "📖  カルテ検索"])

# =====================
# TAB1: 予約カレンダー
# =====================
with tab1:
    if "cal_ym" not in st.session_state:
        t = date.today()
        st.session_state.cal_ym = (t.year, t.month)

    y, m = st.session_state.cal_ym
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("← 前月"):
            y, m = (y - 1, 12) if m == 1 else (y, m - 1)
            st.session_state.cal_ym = (y, m)
            st.rerun()
    with c2:
        st.markdown(f"<h3 style='text-align:center;margin:0;'>{y}年 {m}月</h3>", unsafe_allow_html=True)
    with c3:
        if st.button("翌月 →"):
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
            st.session_state.cal_ym = (y, m)
            st.rerun()

    rsv = load_df("予約", RESERVE_HEADERS)
    rsv_active = rsv[rsv["ステータス"] != "キャンセル"] if not rsv.empty else rsv

    def day_reservations(d):
        if rsv_active.empty:
            return []
        rows = rsv_active[rsv_active["日付"] == str(d)]
        return sorted(rows.to_dict("records"), key=lambda r: r.get("時間", ""))

    cal = calendar.Calendar(firstweekday=6)  # 日曜はじまり
    weeks = cal.monthdatescalendar(y, m)
    today = date.today()

    html = "<table class='cal'><tr>" + "".join(f"<th>{w}</th>" for w in ["日", "月", "火", "水", "木", "金", "土"]) + "</tr>"
    for week in weeks:
        html += "<tr>"
        for i, d in enumerate(week):
            cls = []
            if d.month != m: cls.append("othermonth")
            if d == today: cls.append("today")
            if i == 0: cls.append("sun")
            if i == 6: cls.append("sat")
            cell = f"<span class='d'>{d.day}</span>"
            if d.month == m:
                for r in day_reservations(d):
                    cell += f"<span class='rsv'>{r['時間']} {r['名前']}</span>"
            html += f"<td class='{' '.join(cls)}'>{cell}</td>"
        html += "</tr>"
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

    st.markdown("#### 📋 日別の予約")
    sel_day = st.date_input("日付を選択", value=today if (today.year, today.month) == (y, m) else date(y, m, 1))
    day_list = day_reservations(sel_day)

    # ---- 1日のタイムライン（営業時間ぶんの縦軸に予約ブロックを配置）----
    open_min, close_min = OPEN_HOUR * 60, CLOSE_HOUR * 60
    total = close_min - open_min
    hours_html = ""
    for h in range(OPEN_HOUR, CLOSE_HOUR + 1):
        top = (h * 60 - open_min)
        hours_html += (f"<div style='position:absolute;top:{top}px;left:0;width:100%;"
                       f"border-top:1px solid #eee;'></div>"
                       f"<div style='position:absolute;top:{top - 7}px;left:2px;"
                       f"font-size:.62rem;color:#aaa;'>{h}:00</div>")
    blocks_html = ""
    for r in day_list:
        start = to_min(r["時間"])
        dur = rsv_duration(r)
        top = max(start - open_min, 0)
        height = max(min(dur, close_min - start), 24)
        done = str(r.get("ステータス")) == "来店済"
        bg = "#b9c4b1" if done else "#c9a896"
        end_h, end_m = divmod(start + dur, 60)
        blocks_html += (
            f"<div style='position:absolute;top:{top}px;left:44px;right:6px;height:{height}px;"
            f"background:{bg};border-radius:5px;padding:3px 8px;color:#fff;overflow:hidden;"
            f"box-shadow:0 1px 2px rgba(0,0,0,.12);'>"
            f"<span style='font-size:.68rem;font-weight:700;'>{r['時間']}〜{end_h}:{end_m:02d}"
            f"　{r['名前']} さん</span><br>"
            f"<span style='font-size:.62rem;'>💅 {r['メニュー']}（{dur}分）</span></div>")
    st.markdown(
        f"<div style='position:relative;height:{total + 16}px;background:#fff;"
        f"border:1px solid #e0e0e0;border-radius:4px;margin-bottom:12px;'>"
        f"{hours_html}{blocks_html}</div>",
        unsafe_allow_html=True)
    st.caption(f"営業時間 {OPEN_HOUR}:00〜{CLOSE_HOUR}:00 ｜ 🟤 予約中　🟢 来店済　空白＝空き時間")

    if not day_list:
        st.info("この日の予約はありません")
    for r in day_list:
        with st.container(border=True):
            cA, cB = st.columns([3, 1])
            with cA:
                st.markdown(f"**{r['時間']}　{r['名前']} さん**　💅 {r['メニュー']}")
                if r.get("備考"):
                    st.caption(f"📝 {r['備考']}")
            with cB:
                new_status = st.selectbox("状態", STATUS, index=STATUS.index(r["ステータス"]) if r["ステータス"] in STATUS else 0,
                                          key=f"stat_{r['予約ID']}", label_visibility="collapsed")
                if new_status != r["ステータス"]:
                    r["ステータス"] = new_status
                    update_row("予約", RESERVE_HEADERS, "予約ID", r["予約ID"], r)
                    st.rerun()

# =====================
# TAB2: 予約追加
# =====================
with tab2:
    st.markdown("### ➕ 予約を入れる")
    customers = load_df("顧客", CUSTOMER_HEADERS)
    name_options = ["（新しいお客様・直接入力）"] + customers["名前"].tolist() if not customers.empty else ["（新しいお客様・直接入力）"]

    if "rsv_key" not in st.session_state:
        st.session_state.rsv_key = 0
    rk = st.session_state.rsv_key

    c1, c2 = st.columns(2)
    with c1:
        r_date = st.date_input("📅 日付", value=date.today(), key=f"rdate_{rk}")
    with c2:
        r_time = st.selectbox("🕐 時間", TIMES, index=TIMES.index("10:00"), key=f"rtime_{rk}")

    sel_name = st.selectbox("👤 お客様", name_options, key=f"rname_{rk}")
    manual_name = ""
    if sel_name == "（新しいお客様・直接入力）":
        manual_name = st.text_input("お名前（呼び名でOK）", key=f"rmanual_{rk}")

    r_menu = st.selectbox("💅 メニュー", MENUS, key=f"rmenu_{rk}")

    dur_options = [30, 45, 60, 75, 90, 105, 120, 150, 180, 210, 240]
    menu_default = DURATIONS.get(r_menu, DEFAULT_DURATION)
    default_idx = dur_options.index(menu_default) if menu_default in dur_options else dur_options.index(90)
    r_dur = st.selectbox("⏱ 所要時間（この方に合わせて変更OK）", dur_options, index=default_idx,
                         format_func=lambda v: f"{v}分（{v // 60}時間{v % 60}分）" if v >= 60 else f"{v}分",
                         key=f"rdur_{rk}")
    st.caption(f"メニュー「{r_menu}」の標準：{menu_default}分（メニュー管理で変更できます）")

    r_note = st.text_input("📝 備考（任意）", key=f"rnote_{rk}")

    final_name = manual_name.strip() if sel_name == "（新しいお客様・直接入力）" else sel_name
    if final_name:
        rsv = load_df("予約", RESERVE_HEADERS)
        # 時間帯のかぶりチェック（開始〜終了が重なる予約を探す）
        new_start = to_min(r_time)
        new_end = new_start + r_dur
        overlap = pd.DataFrame()
        if not rsv.empty:
            same_day = rsv[(rsv["日付"] == str(r_date)) & (rsv["ステータス"] != "キャンセル")]
            mask = same_day.apply(
                lambda x: to_min(x["時間"]) < new_end and new_start < to_min(x["時間"]) + rsv_duration(x), axis=1
            ) if not same_day.empty else pd.Series(dtype=bool)
            overlap = same_day[mask] if not same_day.empty else overlap
        if not overlap.empty:
            o = overlap.iloc[0]
            o_end = to_min(o["時間"]) + rsv_duration(o)
            st.warning(f"⚠️ 時間がかぶっています：{o['名前']}さん（{o['時間']}〜{o_end // 60}:{o_end % 60:02d}）")
        end_h, end_m = divmod(new_end, 60)
        if new_end > CLOSE_HOUR * 60:
            st.warning(f"⚠️ 終了予定 {end_h}:{end_m:02d} が営業時間（{CLOSE_HOUR}:00まで）を超えます")
        st.info(f"📅 {r_date}（{'月火水木金土日'[r_date.weekday()]}）{r_time}〜{end_h}:{end_m:02d}"
                f"　**{final_name} さん**　{r_menu}（{r_dur}分）")
        if st.button("この内容で予約を保存", use_container_width=True):
            append_row("予約", RESERVE_HEADERS, {
                "予約ID": uuid.uuid4().hex[:8],
                "日付": str(r_date), "時間": r_time, "所要時間": r_dur, "名前": final_name,
                "メニュー": r_menu, "備考": r_note, "ステータス": "予約中",
            })
            st.session_state.rsv_key += 1
            st.success("✅ 予約を保存しました")
            st.rerun()

# =====================
# TAB3: 顧客カルテ（新規登録）
# =====================
with tab3:
    st.markdown("### 👤 新しいお客様のカルテを作る")
    st.caption("連絡先は保存しません（連絡はLINE公式アカウントで）。呼び名＋目印で管理します。")

    if "cst_key" not in st.session_state:
        st.session_state.cst_key = 0
    ck = st.session_state.cst_key

    c_name = st.text_input("お名前（呼び名でOK）*", key=f"cname_{ck}", placeholder="例：みほさん")
    c_mark = st.text_input("目印メモ（あなただけが分かる特徴）", key=f"cmark_{ck}", placeholder="例：火曜常連・赤い眼鏡")
    c1, c2 = st.columns(2)
    with c1:
        c_nail = st.text_input("爪質", key=f"cnail_{ck}", placeholder="例：薄め・二枚爪になりやすい")
    with c2:
        c_allergy = st.text_input("アレルギー・注意", key=f"callergy_{ck}", placeholder="例：なし")
    c_taste = st.text_input("好み", key=f"ctaste_{ck}", placeholder="例：ベージュ系・シンプル・短め")
    c_memo = st.text_area("施術メモ", key=f"cmemo_{ck}", placeholder="例：フィルイン◎ 右小指割れやすい")
    c_next = st.text_input("次回の提案", key=f"cnext_{ck}", placeholder="例：次回はフットも提案してみる")

    if c_name.strip():
        if st.button("カルテを保存", use_container_width=True):
            append_row("顧客", CUSTOMER_HEADERS, {
                "顧客ID": uuid.uuid4().hex[:8],
                "名前": c_name.strip(), "目印メモ": c_mark, "爪質": c_nail,
                "アレルギー": c_allergy, "好み": c_taste, "施術メモ": c_memo,
                "次回提案": c_next, "登録日": str(date.today()),
            })
            st.session_state.cst_key += 1
            st.success(f"✅ {c_name.strip()} さんのカルテを作成しました")
            st.rerun()

# =====================
# TAB4: カルテ検索・編集
# =====================
with tab4:
    st.markdown("### 📖 カルテを見る・直す")
    customers = load_df("顧客", CUSTOMER_HEADERS)
    if customers.empty:
        st.info("まだカルテがありません。「👤 顧客カルテ」タブから登録してください。")
    else:
        q = st.text_input("🔍 検索（名前・目印・好みなど）", placeholder="例：みほ / 火曜 / ベージュ")
        view = customers
        if q.strip():
            mask = customers.apply(lambda r: q.strip() in " ".join(map(str, r.values)), axis=1)
            view = customers[mask]
        st.caption(f"{len(view)} 件")

        rsv = load_df("予約", RESERVE_HEADERS)
        for _, row in view.iterrows():
            label = f"👤 {row['名前']}" + (f"（{row['目印メモ']}）" if row["目印メモ"] else "")
            with st.expander(label):
                with st.form(key=f"edit_{row['顧客ID']}"):
                    e_name = st.text_input("お名前", value=row["名前"])
                    e_mark = st.text_input("目印メモ", value=row["目印メモ"])
                    e_nail = st.text_input("爪質", value=row["爪質"])
                    e_allergy = st.text_input("アレルギー・注意", value=row["アレルギー"])
                    e_taste = st.text_input("好み", value=row["好み"])
                    e_memo = st.text_area("施術メモ", value=row["施術メモ"])
                    e_next = st.text_input("次回の提案", value=row["次回提案"])
                    if st.form_submit_button("更新を保存"):
                        update_row("顧客", CUSTOMER_HEADERS, "顧客ID", row["顧客ID"], {
                            "顧客ID": row["顧客ID"], "名前": e_name, "目印メモ": e_mark,
                            "爪質": e_nail, "アレルギー": e_allergy, "好み": e_taste,
                            "施術メモ": e_memo, "次回提案": e_next, "登録日": row["登録日"],
                        })
                        st.success("✅ 更新しました")
                        st.rerun()

                if not rsv.empty:
                    visits = rsv[(rsv["名前"] == row["名前"]) & (rsv["ステータス"] == "来店済")].sort_values("日付", ascending=False)
                    if not visits.empty:
                        last = visits.iloc[0]["日付"]
                        days_ago = (date.today() - datetime.strptime(last, "%Y-%m-%d").date()).days
                        st.markdown(f"**🗓 来店履歴**（最終来店：{last}・{days_ago}日前）")
                        st.dataframe(visits[["日付", "時間", "メニュー", "備考"]], hide_index=True, use_container_width=True)
                        if days_ago >= 21:
                            st.warning(f"💡 前回来店から {days_ago} 日。そろそろご案内のタイミングかも")
