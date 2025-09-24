import pandas as pd
import os
from datetime import time
import sqlite3
import streamlit as st

# 資料庫檔案
DB_FILE = "lunch.db"
# 其他檔案路徑
STORE_CONFIG_FILE = "store_config.txt"
CUTOFF_TIME_FILE = "cutoff_time.txt"

# 輔助函數：初始化資料庫
def _initialize_database(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            姓名 TEXT NOT NULL,
            店家 TEXT NOT NULL,
            便當品項 TEXT NOT NULL,
            價格 INTEGER NOT NULL,
            已付款 BOOLEAN DEFAULT FALSE,
            選取 BOOLEAN DEFAULT FALSE,
            刪除 BOOLEAN DEFAULT FALSE,
            備註 TEXT DEFAULT ''
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS menus (
            id INTEGER PRIMARY KEY,
            店家名稱 TEXT NOT NULL,
            店家地址 TEXT,
            店家電話 TEXT,
            便當品項 TEXT NOT NULL,
            價格 INTEGER NOT NULL,
            UNIQUE(店家名稱, 便當品項) ON CONFLICT REPLACE
        )
    """)
    conn.commit()

# 輔助函數：連接資料庫 (使用 Streamlit 的單例模式)
@st.cache_resource
def get_db_connection():
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        _initialize_database(conn) # 在這裡呼叫初始化
        return conn
    except Exception as e:
        st.error(f"無法連線到資料庫: {e}")
        return None

# 輔助函數：從資料庫讀取所有訂單
@st.cache_data(ttl=60)
def load_orders_from_db():
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    df = pd.read_sql_query("SELECT * FROM orders", conn)
    if '已付款' in df.columns:
        df['已付款'] = df['已付款'].astype(bool)
    if '選取' in df.columns:
        df['選取'] = df['選取'].astype(bool)
    if '刪除' in df.columns:
        df['刪除'] = df['刪除'].astype(bool)
    return df

# 輔助函數：從資料庫讀取所有菜單
@st.cache_data(ttl=60)
def load_menus_from_db():
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    df = pd.read_sql_query("SELECT * FROM menus", conn)
    return df

# 輔助函數：儲存新的訂單到資料庫
def save_new_order_to_db(name, store, item, price):
    conn = get_db_connection()
    if conn is None: return
    c = conn.cursor()
    c.execute("INSERT INTO orders (姓名, 店家, 便當品項, 價格) VALUES (?, ?, ?, ?)",
              (name, store, item, price))
    conn.commit()
    load_orders_from_db.clear()

# 輔助函數：更新資料庫中的訂單
def update_orders_in_db(df):
    conn = get_db_connection()
    if conn is None: return
    df.to_sql('orders', conn, if_exists='replace', index=False)
    conn.commit()
    load_orders_from_db.clear()

# 輔助函數：從資料庫中刪除訂單
def delete_orders_from_db(order_ids):
    conn = get_db_connection()
    if conn is None: return
    c = conn.cursor()
    c.execute("DELETE FROM orders WHERE id IN ({})".format(','.join('?'*len(order_ids))), order_ids)
    conn.commit()
    load_orders_from_db.clear()

# 輔助函數：更新資料庫中的菜單
def update_menus_in_db(df):
    conn = get_db_connection()
    if conn is None: return
    df.to_sql('menus', conn, if_exists='replace', index=False)
    conn.commit()
    # 這裡直接呼叫清空函式來強制快取失效
    load_menus_from_db.clear()

# 輔助函數：清除所有訂單
def clear_all_orders_in_db():
    conn = get_db_connection()
    if conn is None: return
    c = conn.cursor()
    c.execute("DELETE FROM orders")
    conn.commit()
    load_orders_from_db.clear()
    
# 輔助函數：儲存店家設定到檔案
def save_store_config(store_name):
    with open(STORE_CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(store_name)

# 輔助函數：從檔案讀取店家設定
@st.cache_data(ttl=3600)
def load_store_config():
    if os.path.exists(STORE_CONFIG_FILE):
        with open(STORE_CONFIG_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

# 輔助函數：儲存截止時間到檔案
def save_cutoff_time(time_obj):
    with open(CUTOFF_TIME_FILE, "w", encoding="utf-8") as f:
        f.write(time_obj.strftime("%H:%M:%S"))

# 輔助函數：從檔案讀取截止時間
@st.cache_data(ttl=3600)
def load_cutoff_time():
    if os.path.exists(CUTOFF_TIME_FILE):
        with open(CUTOFF_TIME_FILE, "r", encoding="utf-8") as f:
            time_str = f.read().strip()
            try:
                return time.fromisoformat(time_str)
            except ValueError:
                return time(12, 0)
    return time(12, 0)
