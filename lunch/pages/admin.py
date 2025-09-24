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

password = st.text_input("請輸入管理者密碼", type="password")

if password == "admin603":
    
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
            # 確保新增的行有正確的店家名稱
            edited_menus_df['店家名稱'] = edited_menus_df['店家名稱'].apply(
                lambda x: selected_menu_store if pd.isna(x) or x == '' else x
            )
            # 過濾掉空的便當品項
            edited_menus_df = edited_menus_df[edited_menus_df['便當品項'] != '']
            
            # 從原始資料中刪除舊的店家菜單
            menus_df = menus_df[menus_df['店家名稱'] != selected_menu_store]
            
            # 合併更新後的資料
            updated_menus_df = pd.concat([menus_df, edited_menus_df], ignore_index=True)
            
            # 儲存至資料庫
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
    orders_df = load_orders_from_db()

    if not orders_df.empty:
        st.subheader("所有已送出訂單")
        edited_df = st.data_editor(
            orders_df,
            column_config={
                "id": None,
                "已付款": st.column_config.CheckboxColumn(
                    "已付款",
                    help="勾選此欄位表示此筆訂單已完成付款",
                    default=False,
                    width="small"
                ),
                "選取": st.column_config.CheckboxColumn(
                    "選取",
                    help="勾選此欄位可計算總金額",
                    default=False,
                    width="small"
                ),
                "刪除": st.column_config.CheckboxColumn(
                    "刪除",
                    help="勾選此欄位可刪除訂單",
                    default=False,
                    width="small"
                ),
                "備註": st.column_config.TextColumn(
                    "備註",
                    help="可用於記錄找零等事項",
                    default="",
                    width="medium"
                )
            },
            hide_index=True,
            key="admin_data_editor"
        )
        
        if not edited_df.equals(orders_df):
            update_orders_in_db(edited_df)
            st.info("訂單變動已自動儲存。")
            
        orders_to_delete = edited_df[edited_df["刪除"] == True]
        if not orders_to_delete.empty:
            if st.button("刪除已選取訂單"):
                order_ids_to_delete = orders_to_delete["id"].tolist()
                delete_orders_from_db(order_ids_to_delete)
                st.success("✅ 已成功刪除選取的訂單。")
                st.experimental_rerun()
                
        selected_orders = edited_df[edited_df["選取"] == True]
        selected_total = selected_orders["價格"].sum()

        st.markdown(f"#### **總訂單數**：{len(orders_df)} 筆")
        st.markdown(f"#### **所有訂單總金額**：NT$ {orders_df['價格'].sum()}")
        st.markdown(f"### **已選取訂單總金額**：<font color='green'>NT$ {selected_total}</font>", unsafe_allow_html=True)

        csv_export = orders_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 下載所有訂單 (CSV)",
            data=csv_export,
            file_name='lunch_orders.csv',
            mime='text/csv',
        )
    else:
        st.info("目前還沒有人訂餐。")

    st.markdown("---")
    
    st.header("🗑️ 清除所有訂單")
    st.warning("⚠️ 此操作會永久刪除所有訂單資料，請謹慎使用。")
    confirm_clear = st.checkbox("我確定要清除所有訂單")
    if st.button("清除所有訂單", disabled=not confirm_clear):
        clear_all_orders_in_db()
        st.success("✅ 所有訂單已成功清除！")
        st.experimental_rerun()
        
elif password:
    st.error("密碼錯誤，請重新輸入。")