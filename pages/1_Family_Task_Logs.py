# pages/1_Family_Task_Log.py

import streamlit as st
import pandas as pd
from datetime import datetime

# Import mọi thứ cần thiết từ package 'utils' duy nhất
from utils import (
    is_authorized,
    set_active_view,
    search_dataframe,
    get_data_from_sheet,
    add_row_from_dict,
    SHEET_IDS,
    render_task_card,
    process_deadline_tasks,
    get_overdue_tasks,
    filter_latest_tasks_by_name,
    get_current_hcm_time_str
)

# --- CẤU HÌNH TRANG VÀ KIỂM TRA ĐĂNG NHẬP ---
st.set_page_config(page_title="Family Task Log", page_icon="📝", layout="wide")

if not st.session_state.get('logged_in'):
    st.error("Bạn cần đăng nhập để xem trang này.")
    st.stop()

# --- KHỞI TẠO STATE ---
if 'active_view' not in st.session_state:
    st.session_state.active_view = 'none'
if 'search_results_df' not in st.session_state:
    st.session_state.search_results_df = None
if 'overdue_results_df' not in st.session_state:
    st.session_state.overdue_results_df = None
if 'deadline_results' not in st.session_state:
    st.session_state.deadline_results = None

# --- GIAO DIỆN CHÍNH ---
st.title("📋 Family Task Log")
st.markdown("---")

# --- THANH CÔNG CỤ (TOOLBAR) ---
cols = st.columns(6)
with cols[0]:
    if st.button("🔄 Làm mới", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
if is_authorized('view_all_tasks'):
    with cols[5]:
        if st.button("👑 Xem tất cả", use_container_width=True):
            set_active_view('view_all')
if is_authorized('add_new_task'):
    with cols[4]:
        if st.button("➕ Thêm mới", use_container_width=True):
            set_active_view('add_new')
if is_authorized('search_task'):
    with cols[1]:
        if st.button("🔍 Tìm kiếm", use_container_width=True):
            st.session_state.search_results_df = None
            set_active_view('search')
# Giả sử bạn đã thêm các quyền này vào file config
if is_authorized('process_deadline_tasks'):
    with cols[2]:
        if st.button("🚨 Deadline", use_container_width=True):
            st.session_state.deadline_results = None
            set_active_view('deadline')
if is_authorized('get_overdue_tasks'):
    with cols[3]:
        if st.button("🔥 Quá hạn", use_container_width=True):
            st.session_state.overdue_results_df = None
            set_active_view('overdue')
st.markdown("---")

# --- LẤY VÀ LỌC DỮ LIỆU GỐC MỘT LẦN DUY NHẤT ---
# Đây là bước quan trọng để đảm bảo tất cả các chức năng đều hoạt động
# trên một bộ dữ liệu nhất quán (chỉ chứa các task mới nhất).
task_sheet_id = SHEET_IDS.get("tasks")
with st.spinner("Đang tải và xử lý dữ liệu..."):
    df_tasks_raw = get_data_from_sheet(task_sheet_id)
    latest_df = filter_latest_tasks_by_name(df_tasks_raw) if not df_tasks_raw.empty else df_tasks_raw


# --- KHU VỰC HIỂN THỊ NỘI DUNG ---
if st.session_state.active_view == 'none':
    st.info("👋 Chào mừng bạn. Vui lòng chọn một chức năng từ thanh công cụ bên trên.")

if st.session_state.active_view != 'none':
    # 1. HIỂN THỊ DANH SÁCH TASK
    if st.session_state.active_view == 'view_all':
        with st.container(border=False):
            st.markdown("##### 📝 Danh sách công việc")
            if not latest_df.empty:
                for index, row in latest_df.iterrows():
                    render_task_card(row, task_sheet_id, index)
            else:
                st.info("Không có dữ liệu công việc để hiển thị.")

    # 2. HIỂN THỊ FORM THÊM TASK MỚI
    if st.session_state.active_view == 'add_new':
        with st.container(border=True):
            st.markdown("##### ✨ Tạo một công việc mới")
            with st.form("new_task_form", clear_on_submit=True):
                task_name = st.text_input("Tên công việc (*)")
                task_po = st.text_input("Giao cho (*)")
                task_des = st.text_area("Mô tả chi tiết")
                submitted = st.form_submit_button("Lưu công việc")
                if submitted:
                    if not task_name or not task_po:
                        st.warning("Vui lòng điền đầy đủ Tên công việc và Người thực hiện.")
                    else:
                        new_row_data = {
                            'task_name': task_name,
                            'add_time': get_current_hcm_time_str(),
                            'task_id': f"TASK-{int(datetime.now().timestamp())}",
                            'task_des': task_des,
                            'task_report_to': st.session_state.username,
                            'task_po': task_po,
                            'task_status': "Mới tạo"
                        }

                        with st.spinner("Đang lưu..."):
                            success = add_row_from_dict(task_sheet_id, new_row_data)
                        if success:
                            st.success("Đã thêm công việc mới thành công!")
                            st.rerun()
                        else:
                            st.error("Đã có lỗi xảy ra.")

    # 3. HIỂN THỊ GIAO DIỆN TÌM KIẾM
    if st.session_state.active_view == 'search':
        search_controls_container = st.container(border=True)
        with search_controls_container:
            with st.form("search_form"):
                st.write("Nhập thông tin tìm kiếm:")
                c1, c2 = st.columns([3, 1])
                with c1:
                    search_term = st.text_input("Từ khóa:", label_visibility="collapsed")
                with c2:
                    search_in_col = st.selectbox("Tìm trong cột:", options=['task_name', 'task_po', 'task_des', 'task_status'], label_visibility="collapsed")
                submitted = st.form_submit_button("Thực hiện tìm kiếm")
                if submitted:
                    if search_term.strip():
                        results_df = search_dataframe(df=latest_df, search_term=search_term, search_column=search_in_col)
                        st.session_state.search_results_df = results_df
                    else:
                        st.warning("Vui lòng nhập từ khóa để tìm kiếm.")
                        st.session_state.search_results_df = None
        results_container = st.container(border=False)
        with results_container:
            if st.session_state.search_results_df is not None:
                st.markdown(f"##### 🔍 Kết quả tìm kiếm")
                results_df = st.session_state.search_results_df
                if not results_df.empty:
                    for index, row in results_df.iterrows():
                        render_task_card(row, task_sheet_id, index)
                else:
                    st.info("Không tìm thấy công việc nào phù hợp.")
                if st.button("↩️ Xóa kết quả tìm kiếm"):
                    st.session_state.search_results_df = None
                    st.rerun()
            elif not latest_df.empty:
                st.markdown("##### 📝 Toàn bộ công việc (trong chế độ tìm kiếm)")
                # for index, row in latest_df.iterrows():
                #     render_task_card(row, task_sheet_id, index)
            else:
                st.info("Không có dữ liệu.")

    # 4. HIỂN THỊ GIAO DIỆN TÌM KIẾM DEADLINE
    if st.session_state.active_view == 'deadline':
        filter_container = st.container(border=True)
        with filter_container:
            st.write("**Bộ lọc tìm kiếm deadline:**")
            po_list = latest_df['task_po'].dropna().unique().tolist()
            selected_pos = st.multiselect("Chọn người thực hiện (PO):", options=po_list)
            if st.button("Tìm kiếm Deadline"):
                filtered_df = latest_df[latest_df['task_po'].isin(selected_pos)] if selected_pos else latest_df
                due_today, due_soon, due_later = process_deadline_tasks(filtered_df)
                st.session_state.deadline_results = {"today": due_today, "soon": due_soon, "later": due_later}
        if st.session_state.deadline_results:
            results = st.session_state.deadline_results
            with st.container(border=True):
                st.error(f"🔴 Hết hạn hôm nay ({len(results['today'])} task)")
                if not results['today'].empty:
                    for index, row in results['today'].iterrows():
                        render_task_card(row, task_sheet_id, index)
                else: st.write("_Không có task nào._")
            with st.container(border=True):
                st.warning(f"🟠 Hết hạn trong 2-3 ngày tới ({len(results['soon'])} task)")
                if not results['soon'].empty:
                    for index, row in results['soon'].iterrows():
                        render_task_card(row, task_sheet_id, index)
                else: st.write("_Không có task nào._")
            with st.expander(f"🟢 Các task khác chưa tới deadline ({len(results['later'])} task)"):
                if not results['later'].empty:
                    for index, row in results['later'].iterrows():
                        render_task_card(row, task_sheet_id, index)
                else: st.write("_Không có task nào._")

    # 5. HIỂN THỊ GIAO DIỆN TASK QUÁ HẠN
    if st.session_state.active_view == 'overdue':
        filter_container = st.container(border=True)
        with filter_container:
            st.write("**Lọc các task đã quá hạn:**")
            po_list = latest_df['task_po'].dropna().unique().tolist()
            selected_pos = st.multiselect("Chọn người thực hiện (PO):", options=po_list)
            sort_cols = st.columns((2, 2, 8))
            with sort_cols[0]:
                if st.button("Tìm Task Quá Hạn"):
                    filtered_df = latest_df[latest_df['task_po'].isin(selected_pos)] if selected_pos else latest_df
                    st.session_state.overdue_results_df = get_overdue_tasks(filtered_df)
        if st.session_state.overdue_results_df is not None:
            results_df = st.session_state.overdue_results_df
            with st.container(border=True):
                st.error(f"🔥 Tìm thấy {len(results_df)} task đã quá hạn")
                if not results_df.empty:
                    with sort_cols[1]:
                        if st.button("Tăng dần 🔼"):
                            sorted_df = results_df.sort_values(by='days_overdue', ascending=True)
                            st.session_state.overdue_results_df = sorted_df
                            st.rerun()
                    with sort_cols[2]:
                        if st.button("Giảm dần 🔽"):
                            sorted_df = results_df.sort_values(by='days_overdue', ascending=False)
                            st.session_state.overdue_results_df = sorted_df
                            st.rerun()
                    st.markdown("---")
                    for index, row in results_df.iterrows():
                        render_task_card(row, task_sheet_id, index)
                else:
                    st.success("🎉 Không có task nào bị trễ trong bộ lọc này. Tuyệt vời!")
