import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 設定檔案路徑，用來儲存訂單資料和店家設定
ORDERS_FILE = "orders.csv"
STORE_CONFIG_FILE = "store_config.txt"

# 設定時間控制：你可以自行調整截止時間
cutoff_time = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)

# 模擬不同的店家及菜單資料
menu_data = {
    "家鄉排骨便當": {
        "招牌排骨飯": 80,
        "香酥雞腿飯": 90,
        "紅燒蹄膀飯": 100
    },
    "悟饕池上飯包": {
        "經典池上飯包": 85,
        "燒肉飯": 95,
        "懷舊排骨飯": 90
    },
    "天天自助餐": {
        "三菜一主食": 75,
        "四菜一主食": 85,
        "五菜一主食": 95
    }
}

# 輔助函數：儲存訂單到 CSV 檔案
def save_orders(df):
    df.to_csv(ORDERS_FILE, index=False, encoding='utf-8')

# 輔助函數：儲存店家設定到檔案
def save_store_config(store_name):
    with open(STORE_CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(store_name)

# 輔助函數：從檔案讀取店家設定
def load_store_config():
    if os.path.exists(STORE_CONFIG_FILE):
        with open(STORE_CONFIG_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

# 初始化 Session State 並從檔案載入資料（如果存在的話）
if "orders" not in st.session_state:
    if os.path.exists(ORDERS_FILE):
        st.session_state.orders = pd.read_csv(ORDERS_FILE)
    else:
        st.session_state.orders = pd.DataFrame(columns=["姓名", "店家", "便當品項", "價格"])

# 從檔案讀取管理者設定的店家
selected_store_by_admin = load_store_config()

st.title("🍱 團體訂便當系統")
st.markdown("---")

# 檢查是否已超過訂餐截止時間
if datetime.now() > cutoff_time:
    st.error(f"⚠️ **訂餐已截止**。截止時間為：{cutoff_time.strftime('%H:%M')}")
    st.info("若有緊急需求，請直接聯繫管理者。")
elif selected_store_by_admin is None:
    st.info("請等待管理者設定今日便當店家。")
else:
    # 訂餐表單
    st.header("1️⃣ 訂餐區")
    st.write(f"今日店家：**{selected_store_by_admin}**")
    st.write(f"今天的訂餐截止時間為：**{cutoff_time.strftime('%H:%M')}**")
    
    with st.form("order_form"):
        name = st.text_input("請輸入你的姓名", key="name_input")
        menu = menu_data[selected_store_by_admin]
        selected_item = st.selectbox("請選擇便當品項", options=list(menu.keys()))
        price = menu[selected_item]
        st.write(f"您選擇的 **{selected_item}** 價格為：**NT$ {price}**")
        
        submitted = st.form_submit_button("送出訂單")
        
        if submitted:
            if not name:
                st.warning("請輸入你的姓名後再送出！")
            else:
                new_order = pd.DataFrame([{"姓名": name, "店家": selected_store_by_admin, "便當品項": selected_item, "價格": price}])
                st.session_state.orders = pd.concat([st.session_state.orders, new_order], ignore_index=True)
                save_orders(st.session_state.orders)
                st.success(f"✅ **{name}**，您已成功訂購 **{selected_item}**！總金額為 **NT$ {price}**。")

# ---
st.markdown("---")

# 管理者區塊
st.header("2️⃣ 管理者後台 (訂單總覽)")
password = st.text_input("請輸入管理者密碼", type="password")

if password == "admin123":
    st.subheader("設定今日便當店家")
    
    # 判斷當前店家索引
    try:
        current_index = list(menu_data.keys()).index(selected_store_by_admin)
    except ValueError:
        current_index = 0
        
    selected_store = st.selectbox(
        "請選擇今日店家",
        options=list(menu_data.keys()),
        index=current_index
    )
    if st.button("確認店家設定"):
        save_store_config(selected_store)
        st.success(f"已成功設定今日店家為：**{selected_store}**")
        st.experimental_rerun() # 重新執行應用程式，讓所有使用者同步

    st.markdown("---")

    if not st.session_state.orders.empty:
        st.subheader("📊 所有已送出訂單")
        st.dataframe(st.session_state.orders, use_container_width=True)
        total_price = st.session_state.orders["價格"].sum()
        st.markdown(f"#### **總訂單數**：{len(st.session_state.orders)} 筆")
        st.markdown(f"#### **總金額**：NT$ {total_price}")

        csv_export = st.session_state.orders.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 下載所有訂單 (CSV)",
            data=csv_export,
            file_name='lunch_orders.csv',
            mime='text/csv',
        )
    else:
        st.info("目前還沒有人訂餐。")
elif password:
    st.error("密碼錯誤，請重新輸入。")