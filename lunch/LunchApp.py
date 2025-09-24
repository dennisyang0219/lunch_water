import streamlit as st
import pandas as pd
from datetime import time, datetime
from utils import (
    load_store_config, load_cutoff_time, load_menus_from_db, save_new_order_to_db,
    initialize_database
)

# 確保資料庫在應用程式啟動時只初始化一次
if 'db_initialized' not in st.session_state:
    initialize_database()
    st.session_state.db_initialized = True

st.set_page_config(
    page_title="便當點餐系統",
    page_icon="🍱",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("🍱 便當點餐系統")
st.markdown("---")

# 載入所有店家和菜單資訊
menus_df = load_menus_from_db()
all_stores = sorted(menus_df['店家名稱'].unique().tolist()) if not menus_df.empty else []
all_stores = [s for s in all_stores if s] # 移除空字串

# 載入今日店家和截止時間
today_store_name = load_store_config()
cutoff_time = load_cutoff_time()

if not today_store_name or not menus_df.empty:
    st.warning("⚠️ 管理員尚未設定今日店家，請稍候。")
    st.info("請聯絡管理員登入後台進行設定。")
else:
    st.header(f"今日便當店家：{today_store_name}")
    st.markdown(f"**訂餐截止時間**：`{cutoff_time.strftime('%H:%M')}`")
    
    current_time = datetime.now().time()
    
    if current_time > cutoff_time:
        st.error("⏳ 訂餐時間已過，無法再新增訂單。")
    else:
        store_menu = menus_df[menus_df['店家名稱'] == today_store_name]
        
        if store_menu.empty or (len(store_menu) == 1 and store_menu.iloc[0]['便當品項'] == '無'):
            st.warning("⚠️ 此店家菜單尚未設定，請通知管理員。")
        else:
            st.subheader("點餐")
            with st.form("lunch_order_form"):
                name = st.text_input("您的姓名", key="order_name")
                
                # 準備菜單選項
                menu_options = store_menu.apply(
                    lambda row: f"{row['便當品項']} (NT$ {row['價格']})",
                    axis=1
                ).tolist()
                
                selected_item_str = st.selectbox("選擇便當品項", options=menu_options, key="order_item")
                
                # 提交按鈕
                submitted = st.form_submit_button("送出訂單")
                
                if submitted:
                    if not name:
                        st.error("請輸入您的姓名。")
                    else:
                        selected_item_name = selected_item_str.split(' (NT$')[0]
                        selected_item_price = int(selected_item_str.split('NT$ ')[-1].split(')')[0])
                        
                        try:
                            save_new_order_to_db(name, today_store_name, selected_item_name, selected_item_price)
                            st.success(f"🎉 訂單已送出！**{name}**，您點了 **{selected_item_name}**，價格 **NT$ {selected_item_price}**。")
                        except Exception as e:
                            st.error(f"送出訂單時發生錯誤: {e}")
