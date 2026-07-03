import pandas as pd
import streamlit as st

from common import apply_style, check_login, load_df, overwrite_sheet, MENU_HEADERS, DEFAULT_MENUS



st.markdown("# メニュー管理")
st.caption("メニュー・商品の追加や料金変更はここで。保存すると予約画面のメニュー一覧にも反映されます。")
st.markdown("---")

menus = load_df("メニュー", MENU_HEADERS)

# 初回はデフォルトメニューを流し込む
if menus.empty:
    menus = pd.DataFrame([
        {"メニュー名": n, "カテゴリ": "施術", "料金": "", "所要時間": 90, "説明": "", "有効": "TRUE"}
        for n in DEFAULT_MENUS
    ])
if "所要時間" not in menus.columns:
    menus["所要時間"] = 90

menus["有効"] = menus["有効"].astype(str).str.upper() != "FALSE"

edited = st.data_editor(
    menus,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    column_config={
        "メニュー名": st.column_config.TextColumn("メニュー名", required=True),
        "カテゴリ": st.column_config.SelectboxColumn("カテゴリ", options=["施術", "オプション", "商品", "スクール", "その他"]),
        "料金": st.column_config.NumberColumn("料金（円）", min_value=0, step=100, format="¥%d"),
        "所要時間": st.column_config.NumberColumn("所要時間（分）", min_value=0, step=15,
                                              help="予約を入れるときの標準時間。人によって変える場合は予約時に調整できます"),
        "説明": st.column_config.TextColumn("説明"),
        "有効": st.column_config.CheckboxColumn("有効", help="オフにすると予約画面に出なくなります（削除せず残せます）"),
    },
)

st.caption("行の追加は表の一番下、削除は行を選んでゴミ箱アイコンで。")

if st.button("💾 保存する", use_container_width=True):
    out = edited.copy()
    out = out[out["メニュー名"].astype(str).str.strip() != ""]
    out["有効"] = out["有効"].map(lambda v: "TRUE" if v else "FALSE")
    overwrite_sheet("メニュー", MENU_HEADERS, out)
    st.success("✅ メニューを保存しました")

st.markdown("---")
active = edited[edited["有効"] == True] if not edited.empty else edited
st.markdown(f"**現在の有効メニュー：{len(active)} 件**")
for cat in active["カテゴリ"].dropna().unique():
    rows = active[active["カテゴリ"] == cat]
    items = "、".join(rows["メニュー名"].astype(str).tolist())
    st.markdown(f"- **{cat}**：{items}")
