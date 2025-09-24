import streamlit as st
import pandas as pd
from datetime import datetime
from utils import load_store_config, load_cutoff_datetime, load_menus_from_db, save_new_order_to_db

st.set_page_config(
    page_title="訂便當",
    page_icon="🍱"
)

selected_store_by_admin = load_store_config()
cutoff_datetime = load_cutoff_datetime()

menus_df = load_menus_from_db()

st.title("🍱 訂便當")
st.markdown("---")

# 這裡改用完整的 datetime 物件進行比對
if datetime.now() > cutoff_datetime:
    st.error(f"⚠️ **訂餐已截止**。截止時間為：{cutoff_datetime.strftime('%Y-%m-%d %H:%M')}")
    st.info("若有緊急需求，請直接聯繫管理者。")
elif selected_store_by_admin is None:
    st.info("請等待管理者設定今日便當店家。")
elif menus_df.empty:
    st.info("目前沒有可訂餐的店家及菜單。請聯繫管理者新增。")
else:
    st.header("訂餐區")
    
    store_info = menus_df[menus_df['店家名稱'] == selected_store_by_admin].iloc[0]
    
    st.write(f"今日店家：**{selected_store_by_admin}**")
    st.write(f"地址：**{store_info.get('店家地址', '未提供')}**")
    st.write(f"電話：**{store_info.get('店家電話', '未提供')}**")
    st.write(f"今天的訂餐截止時間為：**{cutoff_datetime.strftime('%Y-%m-%d %H:%M')}**")
    
    menu_items = menus_df[menus_df['店家名稱'] == selected_store_by_admin]
    
    if not menu_items.empty:
        item_price_dict = dict(zip(menu_items['便當品項'], menu_items['價格']))
        selected_item = st.selectbox("請選擇便當品項", options=list(item_price_dict.keys()))
        price = item_price_dict.get(selected_item, 0)
        
        st.write(f"您選擇的 **{selected_item}** 價格為：**NT$ {int(price)}**")
    else:
        selected_item = None
        price = 0
        st.warning("此店家目前沒有菜單品項，請聯繫管理者新增。")

    with st.form("order_form"):
        name = st.text_input("請輸入你的姓名", key="name_input")
        submitted = st.form_submit_button("送出訂單")
        
        if submitted:
            if not name:
                st.warning("請輸入你的姓名後再送出！")
            elif not selected_item:
                st.warning("請選擇便當品項後再送出！")
            else:
                save_new_order_to_db(name, selected_store_by_admin, selected_item, price)
                st.success(f"✅ **{name}**，您已成功訂購 **{selected_item}**！總金額為 **NT$ {int(price)}**。")


