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

# 密碼驗證
password = st.text_input("請輸入管理者密碼", type="password")

if password == "admin603":  # 請將 'admin123' 換成你自己的密碼
    
    # --- 菜單管理區塊 ---
    st.header("📋 菜單管理")
    st.info("在這裡新增、修改或刪除店家和菜單品項。")
    
    # 從資料庫讀取菜單資料
    menus_df = load_menus_from_db()
    
    if menus_df.empty:
        # 如果是空的，建立一個空的DataFrame來顯示
        menus_df = pd.DataFrame(columns=['店家名稱', '便當品項', '價格'])
    
    # 讓管理者編輯菜單表格
    edited_menus_df = st.data_editor(
        menus_df,
        column_config={
            "id": None, # 隱藏 id 欄位
            "店家名稱": st.column_config.TextColumn("店家名稱", help="輸入店家名稱"),
            "便當品項": st.column_config.TextColumn("便當品項", help="輸入便當品項"),
            "價格": st.column_config.NumberColumn("價格", help="輸入價格", format="NT$%d", step=1)
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="menu_data_editor"
    )
    
    if st.button("儲存菜單變更"):
        # 移除 'id' 欄位，因為它會自動生成
        if 'id' in edited_menus_df.columns:
            edited_menus_df = edited_menus_df.drop(columns=['id'])
            
        update_menus_in_db(edited_menus_df)
        st.success("✅ 菜單變動已成功儲存！")
        st.rerun()

    st.markdown("---")
    
    # --- 設定區塊 ---
    st.header("⚙️ 設定區")
    
    selected_store_by_admin = load_store_config()
    current_cutoff_time = load_cutoff_time()
    
    # 設定今日店家 (現在會從資料庫動態抓取店家列表)
    st.subheader("設定今日便當店家")
    # 從菜單表格中取得所有店家名稱
    store_names = menus_df['店家名稱'].unique().tolist()
    
    if store_names:
        try:
            current_index = store_names.index(selected_store_by_admin) if selected_store_by_admin in store_names else 0
        except (ValueError, TypeError):
            current_index = 0
            
        selected_store = st.selectbox(
            "請選擇今日店家",
            options=store_names,
            index=current_index
        )
        if st.button("確認店家設定"):
            save_store_config(selected_store)
            st.success(f"已成功設定今日店家為：**{selected_store}**")
            st.rerun()
    else:
        st.info("請先在「菜單管理」區塊新增店家。")

    st.markdown("---")

    # 設定截止時間
    st.subheader("設定訂餐截止時間")
    
    time_options = {
        "上午 8:50": time(8, 50),
        "下午 4:00": time(16, 0)
    }
    
    current_time_str = "上午 8:50" if current_cutoff_time == time(8, 50) else "下午 4:00"
    
    new_cutoff_time_str = st.selectbox(
        "選擇截止時間",
        options=list(time_options.keys()),
        index=list(time_options.keys()).index(current_time_str)
    )
    
    if st.button("確認時間設定"):
        selected_time_obj = time_options[new_cutoff_time_str]
        save_cutoff_time(selected_time_obj)
        st.success(f"已成功設定訂餐截止時間為：**{new_cutoff_time_str}**")
        st.rerun()
        
    st.markdown("---")

    # --- 訂單總覽區塊 ---
    st.header("📊 訂單總覽")
    orders_df = load_orders_from_db()

    if not orders_df.empty:
        st.subheader("所有已送出訂單")

        # 使用 st.data_editor 讓表格可編輯
        edited_df = st.data_editor(
            orders_df,
            column_config={
                "id": None, # 隱藏 id 欄位
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
        
        # 檢查表格是否有變動，如果有則儲存
        if not edited_df.equals(orders_df):
            update_orders_in_db(edited_df)
            st.info("訂單變動已自動儲存。")
            
        # 找到被勾選要刪除的訂單
        orders_to_delete = edited_df[edited_df["刪除"] == True]
        if not orders_to_delete.empty:
            if st.button("刪除已選取訂單"):
                order_ids_to_delete = orders_to_delete["id"].tolist()
                delete_orders_from_db(order_ids_to_delete)
                st.success("✅ 已成功刪除選取的訂單。")
                st.rerun()
                
        # 計算選取訂單的總金額
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
    
    # 清除所有訂單按鈕
    st.header("🗑️ 清除所有訂單")
    st.warning("⚠️ 此操作會永久刪除所有訂單資料，請謹慎使用。")
    confirm_clear = st.checkbox("我確定要清除所有訂單")
    if st.button("清除所有訂單", disabled=not confirm_clear):
        clear_all_orders_in_db()
        st.success("✅ 所有訂單已成功清除！")
        st.rerun()
        
elif password:
    st.error("密碼錯誤，請重新輸入。")
