from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from common import apply_style, check_login, load_sales



st.markdown("# 月次サマリー")
st.caption("今月のお店の状態をひと目で。")
st.markdown("---")

df = load_sales()
if df.empty:
    st.info("売上データがまだありません。")
    st.stop()

# 月の選択
months = df.dropna(subset=["年", "月"]).groupby(["年", "月"]).size().reset_index()[["年", "月"]]
months = months.sort_values(["年", "月"], ascending=False)
labels = [f"{int(r.年)}年{int(r.月)}月" for r in months.itertuples()]
sel = st.selectbox("📅 月を選択", labels)
sel_y, sel_m = int(sel.split("年")[0]), int(sel.split("年")[1].replace("月", ""))

cur = df[(df["年"] == sel_y) & (df["月"] == sel_m)]
prev_y, prev_m = (sel_y - 1, 12) if sel_m == 1 else (sel_y, sel_m - 1)
prv = df[(df["年"] == prev_y) & (df["月"] == prev_m)]

def stats(d):
    total = int(d["最終売上"].sum())
    count = len(d)
    new = int((d["新規・再来"] == "新規").sum())
    rep = int((d["新規・再来"] == "再来").sum())
    unit = int(total / count) if count else 0
    rep_rate = round(rep / count * 100) if count else 0
    return total, count, new, rep, unit, rep_rate

t, c, n, r, u, rr = stats(cur)
pt, pc, pn, pr, pu, prr = stats(prv)

# ---- 指標タイル ----
c1, c2, c3 = st.columns(3)
c1.metric("💴 売上合計", f"¥{t:,}", delta=f"{t - pt:+,} 円（前月比）" if pc else None)
c2.metric("🧾 施術件数", f"{c} 件", delta=f"{c - pc:+} 件" if pc else None)
c3.metric("👛 客単価", f"¥{u:,}", delta=f"{u - pu:+,} 円" if pc else None)

c4, c5, c6 = st.columns(3)
c4.metric("✨ 新規", f"{n} 人", delta=f"{n - pn:+} 人" if pc else None)
c5.metric("🔁 再来", f"{r} 人", delta=f"{r - pr:+} 人" if pc else None)
c6.metric("📈 再来率", f"{rr} %", delta=f"{rr - prr:+} pt" if pc else None)

st.markdown("---")

ACCENT = "#a6785f"  # 単色（濃いモーヴブラウン）— 白背景で十分なコントラスト

# ---- メニュー別売上（単一色・横棒・直接ラベル）----
st.markdown("### 💅 メニュー別売上")
by_menu = cur.groupby("メニュー")["最終売上"].sum().sort_values()
if not by_menu.empty:
    fig = px.bar(by_menu, orientation="h", text=[f"¥{v:,.0f}" for v in by_menu.values])
    fig.update_traces(marker_color=ACCENT, textposition="outside", cliponaxis=False,
                      hovertemplate="%{y}：¥%{x:,.0f}<extra></extra>")
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None,
                      plot_bgcolor="white", paper_bgcolor="white",
                      margin=dict(l=0, r=10, t=10, b=10), height=60 + 40 * len(by_menu),
                      xaxis=dict(showgrid=True, gridcolor="#eee"), font=dict(family="Noto Sans JP"))
    st.plotly_chart(fig, use_container_width=True)

# ---- 決済方法別（単一色・横棒）----
st.markdown("### 💳 決済方法別")
by_pay = cur.groupby("支払い方法")["最終売上"].sum().sort_values()
if not by_pay.empty:
    fig2 = px.bar(by_pay, orientation="h", text=[f"¥{v:,.0f}" for v in by_pay.values])
    fig2.update_traces(marker_color=ACCENT, textposition="outside", cliponaxis=False,
                       hovertemplate="%{y}：¥%{x:,.0f}<extra></extra>")
    fig2.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None,
                       plot_bgcolor="white", paper_bgcolor="white",
                       margin=dict(l=0, r=10, t=10, b=10), height=60 + 40 * len(by_pay),
                       xaxis=dict(showgrid=True, gridcolor="#eee"), font=dict(family="Noto Sans JP"))
    st.plotly_chart(fig2, use_container_width=True)

# ---- 直近6ヶ月の売上推移（単一系列の縦棒）----
st.markdown("### 🗓 売上の推移（直近6ヶ月）")
trend = (df.dropna(subset=["年", "月"])
           .groupby(["年", "月"])["最終売上"].sum().reset_index()
           .sort_values(["年", "月"]).tail(6))
trend["月ラベル"] = trend.apply(lambda x: f"{int(x['年'])}/{int(x['月']):02d}", axis=1)
fig3 = px.bar(trend, x="月ラベル", y="最終売上", text=[f"¥{v:,.0f}" for v in trend["最終売上"]])
fig3.update_traces(marker_color=ACCENT, textposition="outside", cliponaxis=False,
                   hovertemplate="%{x}：¥%{y:,.0f}<extra></extra>")
fig3.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None,
                   plot_bgcolor="white", paper_bgcolor="white",
                   margin=dict(l=0, r=10, t=20, b=10), height=320,
                   yaxis=dict(showgrid=True, gridcolor="#eee"), font=dict(family="Noto Sans JP"))
st.plotly_chart(fig3, use_container_width=True)

# ---- 表でも見られるように ----
with st.expander("📋 数字の一覧（表）"):
    st.dataframe(
        pd.DataFrame({
            "項目": ["売上合計", "施術件数", "客単価", "新規", "再来", "再来率"],
            sel: [f"¥{t:,}", f"{c}件", f"¥{u:,}", f"{n}人", f"{r}人", f"{rr}%"],
            f"{prev_y}年{prev_m}月": [f"¥{pt:,}", f"{pc}件", f"¥{pu:,}", f"{pn}人", f"{pr}人", f"{prr}%"],
        }),
        hide_index=True, use_container_width=True,
    )
