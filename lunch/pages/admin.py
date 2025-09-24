import streamlit as st
import pandas as pd
from datetime import time
from utils import (
    load_store_config, save_store_config, load_cutoff_time, save_cutoff_time, 
    load_orders_from_db, update_orders_in_db, clear_all_orders_in_db,
    delete_orders_from_db, load_menus_from_db, update_menus_in_db
)
import os

st.title("👨‍💼 管理者後台")
st.markdown("---")

# 使用 session_state 來管理登入狀態
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 檢查登入狀態
if not st.session_state.logged_in:
    password = st.text_input("請輸入管理者密碼", type="password", key="login_password")
    if password == "admin603":
        st.session_state.logged_in = True
        st.experimental_rerun()
    elif password:
        st.error("密碼錯誤，請重新輸入。")
else:
    # 登入成功後顯示的內容
    if st.button("登出"):
        st.session_state.logged_in = False
        st.experimental_rerun()
        
    st.header("📋 菜單管理")
    
    menus_df = load_menus_from_db()
    if not menus_df.empty:
        menus_df['店家名稱'] = menus_df['店家名稱'].fillna('')
    
    all_store_names = sorted(menus_df['店家名稱'].unique().tolist()) if not menus_df.empty else []
    all_store_names = [name for name in all_store_names if name]

    st.subheader("新增店家")
    new_store_name = st.text_input("請輸入新店家名稱", key="new_store_name_input")
    
    if st.button("新增店家"):
        if new_store_name and new_store_name not in all_store_names:
            new_row = pd.DataFrame([{'店家名稱': new_store_name, '便當品項': '', '價格': 0}])
            updated_menus_df = pd.concat([menus_df, new_row], ignore_index=True)
            update_menus_in_db(updated_menus_df)
            st.success(f"✅ 已成功新增店家：**{new_store_name}**")
            st.experimental_rerun()
        else:
            st.warning("⚠️ 請輸入有效的店家名稱，且店家名稱不能重複。")
    
    st.markdown("---")
    
    st.subheader("編輯店家菜單")
    if all_store_names:
        selected_menu_store = st.selectbox(
            "請選擇要編輯菜單的店家",
            options=all_store_names
        )
    else:
        st.info("請先新增一個店家。")
        selected_menu_store = None

    if selected_menu_store:
        selected_menu_df = menus_df[menus_df['店家名稱'] == selected_menu_store].copy()
        edited_menus_df = st.data_editor(
            selected_menu_df,
            column_config={
                "id": None,
                "店家名稱": None,
                "便當品項": st.column_config.TextColumn("便當品項", help="輸入便當品項"),
                "價格": st.column_config.NumberColumn("價格", help="輸入價格", format="NT$%d", step=1)
            },
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="menu_data_editor"
        )
        
        if st.button(f"儲存「{selected_menu_store}」的菜單變更"):
            edited_menus_df['店家名稱'] = edited_menus_df['店家名稱'].apply(
                lambda x: selected_menu_store if pd.isna(x) or x == '' else x
            )
            edited_menus_df = edited_menus_df[edited_menus_df['便當品項'] != '']
            
            menus_df = menus_df[menus_df['店家名稱'] != selected_menu_store]
            updated_menus_df = pd.concat([menus_df, edited_menus_df], ignore_index=True)
            
            update_menus_in_db(updated_menus_df)
            st.success("✅ 菜單變動已成功儲存！")
            st.experimental_rerun()

    st.markdown("---")
    
    st.header("⚙️ 今日訂餐設定")
    
    selected_store_by_admin = load_store_config()
    current_cutoff_time = load_cutoff_time()
    
    st.subheader("設定今日便當店家")
    
    if all_store_names:
        try:
            current_index = all_store_names.index(selected_store_by_admin) if selected_store_by_admin in all_store_names else 0
        except (ValueError, TypeError):
            current_index = 0
        selected_store = st.selectbox(
            "請選擇今日店家",
            options=all_store_names,
            index=current_index
        )
        if st.button("確認店家設定"):
            save_store_config(selected_store)
            st.success(f"✅ 已成功設定今日店家為：**{selected_store}**")
            st.experimental_rerun()
    else:
        st.info("請先在「菜單管理」區塊新增店家。")

    st.markdown("---")

    st.subheader("設定訂餐截止時間")
    
    time_options = {
        "上午 8:50": time(8, 50),
        "下午 4:00": time(16, 0)
    }
    current_time_str = "上午 8:50" if current_cutoff_time == time(8, 50) else "下午 4:00"
    
    new_cutoff_time_str = st.selectbox(
            "選擇截止時間",
            options=list(time_options.keys()),
            index=list(time_options.keys()).index(current_time_str) if current_time_str in time_options else 0
    )
    
    if st.button("確認時間設定"):
        selected_time_obj = time_options[new_cutoff_time_str]
        save_cutoff_time(selected_time_obj)
        st.success(f"✅ 已成功設定訂餐截止時間為：**{new_cutoff_time_str}**")
        st.experimental_rerun()
        
    st.markdown("---")

    st.header("📊 訂單總覽")
    orders_df = load
