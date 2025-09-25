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
