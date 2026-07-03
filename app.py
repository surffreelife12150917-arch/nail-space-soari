"""エントリーポイント：ログイン＋ページ切り替え（メニュー名はここで日本語指定）"""
import streamlit as st

from common import apply_style, check_login

st.set_page_config(page_title="Nail Space Soari", page_icon="💅", layout="centered")
apply_style()

if not check_login():
    st.stop()

pages = [
    st.Page("views/home.py", title="今日", icon="🏠", default=True),
    st.Page("views/yoyaku.py", title="予約とカルテ", icon="📅"),
    st.Page("views/menu_kanri.py", title="メニュー管理", icon="💅"),
    st.Page("views/summary.py", title="月次サマリー", icon="📈"),
    st.Page("views/sales.py", title="売上（フル機能）", icon="✍️"),
]
st.navigation(pages).run()
