"""共通処理：スプレッドシート接続・ログイン・スタイル"""
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1g40jis2r9PU1A7SqflLKWrJUQMQdpYCqqHjBFazs7Ps"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

STYLE = """
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
[data-testid="metric-container"] { background: white; border-radius: 4px; padding: 16px; border: 1px solid #e0e0e0; }
</style>
"""

DEFAULT_MENUS = ["ジェル", "ケア", "オフ", "耳つぼ", "店販", "その他"]
MENU_HEADERS = ["メニュー名", "カテゴリ", "料金", "所要時間", "説明", "有効"]
CUSTOMER_HEADERS = ["顧客ID", "名前", "目印メモ", "爪質", "アレルギー", "好み", "施術メモ", "次回提案", "登録日"]
RESERVE_HEADERS = ["予約ID", "日付", "時間", "所要時間", "名前", "メニュー", "メニュー2", "備考", "ステータス"]
MENUS2 = ["ハンド", "フット", "ハンドフット", "お買い物", "耳つぼ", "お直し"]

# 営業時間（変えたいときはここを直す）
OPEN_HOUR = 9    # 9:00 オープン
CLOSE_HOUR = 19  # 19:00 クローズ
DEFAULT_DURATION = 90  # 所要時間が未設定のときの既定値（分）


def apply_style():
    st.markdown(STYLE, unsafe_allow_html=True)


def check_login() -> bool:
    """st.secrets に app_password があればパスワードを要求"""
    pw = st.secrets.get("app_password", "")
    if not pw:
        return True
    if st.session_state.get("logged_in"):
        return True
    st.markdown("# Soari 管理")
    entered = st.text_input("🔑 パスワード", type="password")
    if entered:
        if entered == pw:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("パスワードが違います")
    return False


def get_client():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds)


def get_ws(name, headers):
    gc = get_client()
    book = gc.open_by_key(SPREADSHEET_ID)
    try:
        ws = book.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = book.add_worksheet(title=name, rows=1000, cols=max(len(headers), 10))
        ws.append_row(headers)
    return ws


@st.cache_data(ttl=10)
def load_df(name, headers):
    ws = get_ws(name, headers)
    df = pd.DataFrame(ws.get_all_records())
    if df.empty:
        df = pd.DataFrame(columns=headers)
    return df


def append_row(name, headers, row):
    ws = get_ws(name, headers)
    sheet_headers = ws.row_values(1)
    ws.append_row([str(row.get(h, "")) for h in sheet_headers])
    st.cache_data.clear()


def update_row(name, headers, key_col, key_val, row):
    ws = get_ws(name, headers)
    sheet_headers = ws.row_values(1)
    col_idx = sheet_headers.index(key_col) + 1
    cell = ws.find(str(key_val), in_column=col_idx)
    if cell:
        ws.update(f"A{cell.row}", [[str(row.get(h, "")) for h in sheet_headers]])
        st.cache_data.clear()
        return True
    return False


def overwrite_sheet(name, headers, df):
    """シート全体を df の内容で書き換える（メニュー管理用）"""
    ws = get_ws(name, headers)
    ws.clear()
    rows = [headers] + df.fillna("").astype(str)[headers].values.tolist()
    ws.update("A1", rows)
    st.cache_data.clear()


def active_menu_names():
    """メニューシートから有効なメニュー名を取得（無ければ既定リスト）"""
    try:
        menus = load_df("メニュー", MENU_HEADERS)
        names = menus[menus["有効"].astype(str) != "FALSE"]["メニュー名"].astype(str)
        names = [n for n in names.tolist() if n.strip()]
        return names or DEFAULT_MENUS
    except Exception:
        return DEFAULT_MENUS


def menu_durations():
    """メニュー名 → 所要時間(分) の辞書"""
    try:
        menus = load_df("メニュー", MENU_HEADERS)
        result = {}
        for _, r in menus.iterrows():
            try:
                mins = int(float(r.get("所要時間", 0) or 0))
            except (TypeError, ValueError):
                mins = 0
            result[str(r["メニュー名"])] = mins if mins > 0 else DEFAULT_DURATION
        return result
    except Exception:
        return {}


@st.cache_data(ttl=30)
def load_sales():
    """売上シート（sheet1）を読み込む"""
    gc = get_client()
    ws = gc.open_by_key(SPREADSHEET_ID).sheet1
    df = pd.DataFrame(ws.get_all_records())
    if df.empty:
        return df
    df["日付"] = pd.to_datetime(df["日付"], errors="coerce")
    df["年"] = pd.to_numeric(df["年"], errors="coerce")
    df["月"] = pd.to_numeric(df["月"], errors="coerce")
    df["最終売上"] = pd.to_numeric(df["最終売上"], errors="coerce").fillna(0)
    return df
