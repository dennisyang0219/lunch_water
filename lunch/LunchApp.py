import streamlit as st
import pandas as pd
from datetime import time, datetime, timedelta
from utils import (
    load_store_config, load_cutoff_time, load_menus_from_db, save_new_order_to_db, load_orders_from_db
)

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
if not menus_df.empty:
    menus_df['價格'] = pd.to_numeric(menus_df['價格'], errors='coerce').fillna(0).astype(int)
    all_stores = sorted(menus_df['店家名稱'].unique().tolist())
    all_stores = [s for s in all_stores if s]
else:
    all_stores = []

# 載入今日店家和截止時間
today_store_name = load_store_config()
cutoff_time = load_cutoff_time()

if not today_store_name or not all_stores:
    st.warning("⚠️ 管理員尚未設定今日店家，請稍候。")
    st.info("請聯絡管理員登入後台進行設定。")
else:
    st.header(f"今日便當店家：{today_store_name}")
    
    if cutoff_time.hour > 12:
        cutoff_time_str = f"下午 {cutoff_time.hour - 12:02d}:{cutoff_time.minute:02d}"
    elif cutoff_time.hour == 12:
        cutoff_time_str = f"下午 12:{cutoff_time.minute:02d}"
    elif cutoff_time.hour == 0:
        cutoff_time_str = f"上午 12:{cutoff_time.minute:02d}"
    else:
        cutoff_time_str = f"上午 {cutoff_time.hour:02d}:{cutoff_time.minute:02d}"
        
    st.markdown(f"**訂餐截止時間**：`{cutoff_time_str}`")
    
    current_datetime = datetime.now()
    cutoff_datetime = datetime.combine(current_datetime.date(), cutoff_time)
    
    if current_datetime > cutoff_datetime:
        st.error("⏳ 訂餐時間已過，無法再新增訂單。")
    else:
        store_menu = menus_df[menus_df['店家名稱'] == today_store_name]
        
        if store_menu.empty or (len(store_menu) == 1 and store_menu.iloc[0]['便當品項'] == '無'):
            st.warning("⚠️ 此店家菜單尚未設定，請通知管理員。")
        else:
            st.subheader("點餐")
            with st.form("lunch_order_form"):
                name = st.text_input("您的姓名", key="order_name")
                
                menu_options = store_menu.apply(
                    lambda row: f"{row['便當品項']} (NT$ {row['價格']})",
                    axis=1
                ).tolist()
                
                selected_item_str = st.selectbox("選擇便當品項", options=menu_options, key="order_item")
                
                submitted = st.form_submit_button("送出訂單")
                
                if submitted:
                    if not name:
                        st.error("請輸入您的姓名。")
                    else:
                        selected_item_name = selected_item_str.split(' (NT$')[0]
                        selected_item_price = store_menu.loc[store_menu['便當品項'] == selected_item_name, '價格'].iloc[0]

                        try:
                            save_new_order_to_db(name, today_store_name, selected_item_name, selected_item_price)
                            st.success(f"🎉 訂單已送出！**{name}**，您點了 **{selected_item_name}**，價格 **NT$ {selected_item_price}**。")
                        except Exception as e:
                            st.error(f"送出訂單時發生錯誤: {e}")
            
    st.markdown("---")
    st.subheader("我的訂單")
    
    orders_df = load_orders_from_db()
    if not orders_df.empty:
        my_orders_df = orders_df[orders_df['姓名'] == st.session_state.get('user_name', None)]
        if not my_orders_df.empty:
            my_orders_df['價格'] = pd.to_numeric(my_orders_df['價格'], errors='coerce').fillna(0).astype(int)
            my_orders_df = my_orders_df[['便當品項', '價格', '備註']].copy()
            st.table(my_orders_df)
            st.markdown(f"#### **我的訂單總金額**：NT$ {my_orders_df['價格'].sum()}")
        else:
            st.info("您今天還沒有任何訂單。")
    else:
        st.info("您今天還沒有任何訂單。")
