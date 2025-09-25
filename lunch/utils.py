import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import time, datetime, timedelta
import pytz

# 直接使用 pytz 獲取台灣時區
LOCAL_TZ = pytz.timezone('Asia/Taipei')

DB_PATH = 'data/lunch_orders.db'

# 確保資料庫目錄存在
os.makedirs('data', exist_ok=True)

def init_db():
    """初始化資料庫並創建表格（如果不存在）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            姓名 TEXT,
            店家名稱 TEXT,
            便當品項 TEXT,
            價格 INTEGER,
            數量 INTEGER,
            備註 TEXT,
            時間 TEXT,
            已付款 BOOLEAN,
            選取 BOOLEAN,
            刪除 BOOLEAN
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS menus (
            id INTEGER PRIMARY KEY,
            店家名稱 TEXT,
            店家地址 TEXT,
            店家電話 TEXT,
            便當品項 TEXT,
            價格 INTEGER
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# 初始化資料庫
init_db()

# --- 訂單相關函數 ---

def load_orders_from_db():
    """從資料庫讀取所有訂單"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM orders", conn)
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=['id', '姓名', '店家名稱', '便當品項', '價格', '數量', '備註', '時間', '已付款', '選取', '刪除'])
    return df

def save_orders_to_db(df):
    """將訂單 DataFrame 寫入資料庫，覆蓋舊資料"""
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('orders', conn, if_exists='replace', index=False)
    conn.close()

def save_new_order_to_db(name, store_name, item, price):
    """將單筆新訂單添加到資料庫"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 確保價格是數字，避免寫入錯誤值
    try:
        price = int(price)
    except (ValueError, TypeError):
        price = 0
        
    # 儲存為本地時區的時間
    local_time = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    
    order_data = (name, store_name, item, price, 1, '', local_time, 0, 0, 0)
    c.execute("INSERT INTO orders (姓名, 店家名稱, 便當品項, 價格, 數量, 備註, 時間, 已付款, 選取, 刪除) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", order_data)
    
    conn.commit()
    conn.close()

def update_orders_in_db(df):
    """更新整個訂單表格"""
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('orders', conn, if_exists='replace', index=False)
    conn.close()

def clear_all_orders_in_db():
    """清除所有訂單資料"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM orders")
    conn.commit()
    conn.close()

def delete_orders_from_db(order_ids):
    """根據 ID 刪除訂單"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executemany("DELETE FROM orders WHERE id = ?", [(oid,) for oid in order_ids])
    conn.commit()
    conn.close()

# --- 菜單相關函數 ---

def load_menus_from_db():
    """從資料庫讀取所有菜單"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM menus", conn)
    conn.close()
    if df.empty:
        return pd.DataFrame(columns=['id', '店家名稱', '店家地址', '店家電話', '便當品項', '價格'])
    return df

def update_menus_in_db(df):
    """更新整個菜單表格"""
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('menus', conn, if_exists='replace', index=False)
    conn.close()

def delete_store_from_db(store_name):
    """從資料庫中刪除指定的店家及其所有菜單項目"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM menus WHERE 店家名稱 = ?", (store_name,))
    conn.commit()
    conn.close()

def fetch_order_count(user_name):
    """查詢某使用者的訂單數量"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders WHERE 姓名 = ?", (user_name,))
    count = c.fetchone()[0]
    conn.close()
    return count

# --- 設定相關函數 ---

def load_store_config():
    """讀取今日店家設定"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key = 'today_store'")
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def save_store_config(store_name):
    """保存今日店家設定"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO config (key, value) VALUES ('today_store', ?)", (store_name,))
    conn.commit()
    conn.close()
    
def load_cutoff_time():
    """讀取截止時間設定"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key = 'cutoff_time'")
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        try:
            h, m = map(int, result[0].split(':'))
            return time(h, m)
        except (ValueError, IndexError):
            return time(8, 50)
    return time(8, 50)

def save_cutoff_time(cutoff_time):
    """保存截止時間設定"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    time_str = cutoff_time.strftime("%H:%M")
    c.execute("REPLACE INTO config (key, value) VALUES ('cutoff_time', ?)", (time_str,))
    conn.commit()
    conn.close()
