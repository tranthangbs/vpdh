# utils/view_utils.py
import streamlit as st
import pandas as pd
from datetime import datetime

# Import các hàm tiện ích cần thiết
from utils.google_sheet_utils import add_row_from_dict
from utils.data_utils import get_current_hcm_time_str


def set_active_view(view_name: str):
    """
    Hàm helper chung để thiết lập chế độ xem hiện tại cho bất kỳ trang nào.
    """
    if st.session_state.get('active_view') == view_name:
        st.session_state.active_view = 'none'
    else:
        st.session_state.active_view = view_name
    st.rerun()


def render_task_card(task_data: pd.Series, sheet_id: str, unique_key_part: int):
    """
    Hiển thị thông tin của một task dưới dạng một card có thể mở rộng để chỉnh sửa.

    Args:
        task_data (pd.Series): Dữ liệu của một hàng task.
        sheet_id (str): ID của Google Sheet để thực hiện lưu thay đổi.
        unique_key_part (int): Một số nguyên duy nhất (như index) để tạo key không trùng lặp.
    """
    with st.container(border=True):
        # Kiểm tra xem có thông tin về ngày trễ không để thay đổi cách hiển thị
        if 'days_overdue' in task_data and pd.notna(task_data['days_overdue']):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Công việc:** `{task_data.get('task_name', 'N/A')}`")
                st.markdown(f"**Giao cho:** `{task_data.get('task_po', 'N/A')}`")
            with col2:
                st.error(f"Đã trễ {int(task_data['days_overdue'])} ngày")
                st.write(f"Deadline: {task_data.get('task_deadline', 'N/A')}")
        else:
            # Giao diện mặc định nếu không phải task quá hạn
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Công việc:**\n\n`{task_data.get('task_name', 'N/A')}`")
            with col2:
                st.markdown(f"**Giao cho:**\n\n`{task_data.get('task_po', 'N/A')}`")
            with col3:
                st.metric("Trạng thái", value=task_data.get('task_status', 'N/A'))

        # Expander chứa form chỉnh sửa
        with st.expander("Xem chi tiết & Chỉnh sửa"):
            form_key = f"edit_form_{task_data.get('task_id', '')}_{unique_key_part}"

            with st.form(key=form_key, clear_on_submit=True):
                st.markdown("#### Chỉnh sửa thông tin công việc")

                new_task_name = st.text_input("Tên công việc", value=task_data.get('task_name', ''))
                new_task_po = st.text_input("Giao cho", value=task_data.get('task_po', ''))
                new_task_des = st.text_area("Mô tả", value=task_data.get('task_des', ''))

                status_options = ["Mới tạo", "Đang làm", "Hoàn thành", "Tạm dừng", "Đã hủy"]
                current_status_index = status_options.index(task_data.get('task_status')) if task_data.get(
                    'task_status') in status_options else 0
                new_status = st.selectbox("Trạng thái", options=status_options, index=current_status_index)

                new_comment = st.text_input("Bình luận / Ghi chú mới", value=task_data.get('task_comment', ''))

                submitted = st.form_submit_button("Lưu thay đổi")
                if submitted:
                    updated_row_data = {
                        'task_name': new_task_name,
                        'add_time': get_current_hcm_time_str(),  # <-- Dùng hàm lấy thời gian tập trung
                        'task_deadline': task_data.get('task_deadline', ''),
                        'task_link': task_data.get('task_link', ''),
                        'task_id': f"TASK-{int(datetime.now().timestamp())}",  # ID mới cho bản ghi cập nhật
                        'task_des': new_task_des,
                        'task_report_to': task_data.get('task_report_to', ''),
                        'task_po': new_task_po,
                        'task_status': new_status,
                        'task_comment': new_comment
                    }

                    with st.spinner("Đang lưu thay đổi..."):
                        success = add_row_from_dict(sheet_id, updated_row_data)

                    if success:
                        st.success(f"Đã cập nhật công việc '{new_task_name}' thành công!")
                    else:
                        st.error("Có lỗi xảy ra khi lưu thay đổi.")
