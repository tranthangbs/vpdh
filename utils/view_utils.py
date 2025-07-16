# utils/view_utils.py
import streamlit as st
import pandas as pd
from datetime import datetime
from .google_sheet_utils import add_row_from_dict
from .data_utils import get_current_hcm_time_str, get_id_from_url


def set_active_view(view_name: str):
    """
    Hàm helper chung để thiết lập chế độ xem chính cho trang (view_all, search,...).
    """
    # Khi chuyển view chính, luôn thoát khỏi chế độ chỉnh sửa của card
    st.session_state.editing_task_key = None

    if st.session_state.get('active_view') == view_name:
        st.session_state.active_view = 'none'
    else:
        st.session_state.active_view = view_name
    st.rerun()


def render_task_card(task_data: pd.Series, sheet_id: str, unique_key_part: int):
    """
    Hiển thị một card duy nhất cho task, có thể chuyển đổi giữa chế độ xem và chỉnh sửa.
    """
    card_key = f"card_{unique_key_part}"
    is_editing = (st.session_state.get('editing_task_key') == card_key)

    with st.container(border=True):
        if is_editing:
            with st.form(key=f"edit_form_{card_key}"):
                st.subheader(f"**{task_data.get('task_name', 'N/A')}**")
                st.markdown("---")
                sub_cols = st.columns(5)
                with sub_cols[0]:
                    st.markdown(f"**Thư ký phụ trách:**");
                    new_task_po = st.text_input("", f"{task_data.get('task_po', 'N/A')}")
                with sub_cols[1]:
                    st.markdown(f"**Báo cáo cho:**");
                    new_task_report_to = st.text_input("", f"{task_data.get('task_report_to', 'N/A')}")
                with sub_cols[2]:
                    st.markdown("**Deadline**")
                    deadline_str = task_data.get('task_deadline')
                    deadline_dt = pd.to_datetime(deadline_str, format='%Y-%m-%d', errors='coerce')
                    if pd.isna(deadline_dt):
                        st.caption("(chưa có)")
                    else:
                        today = pd.Timestamp.now().normalize()
                        delta = (deadline_dt - today).days
                        task_status = task_data.get('task_status')
                        if delta < 0:
                            st.error(f"{deadline_dt.strftime('%d/%m/%Y')}")
                            if task_status not in ['Đã hoàn thành', 'Đã hủy']: st.caption(f"Trễ {-delta} ngày")
                        elif delta == 0:
                            st.warning(f"{deadline_dt.strftime('%d/%m/%Y')}")
                        else:
                            st.success(f"{deadline_dt.strftime('%d/%m/%Y')}")
                with sub_cols[3]:
                    st.markdown(f"**Trạng thái:**")
                    st.info(f"{task_data.get('task_status', 'N/A')}")
                with sub_cols[4]:
                    link = task_data.get('task_link', '')
                    if link:
                        task_id = get_id_from_url(link)
                        st.link_button("FWS", url=f'https://workingspace.familyhospital.vn/task/show/{task_id}',
                                       use_container_width=True)
                form_cols = st.columns(2)
                with form_cols[0]:
                    if st.form_submit_button("Lưu thay đổi", use_container_width=True, type="primary"):
                        updated_row_data = {
                            'add_time': get_current_hcm_time_str(),
                            'task_deadline': task_data.get('task_deadline', ''),
                            'task_link': task_data.get('task_link', ''),
                            'task_id': f"TASK-{int(datetime.now().timestamp())}", 'task_des': task_data.get('task_des', ''),
                            'task_report_to': new_task_report_to, 'task_po': new_task_po,
                            'task_status': task_data.get('task_status', ''), 'task_comment': task_data.get('task_status', '')
                        }
                        with st.spinner("Đang lưu..."):
                            add_row_from_dict(sheet_id, updated_row_data)
                        st.session_state.editing_task_key = None
                        st.rerun()
                with form_cols[1]:
                    if st.form_submit_button("Hủy", use_container_width=True):
                        st.session_state.editing_task_key = None
                        st.rerun()
        else:
            st.subheader(f"**{task_data.get('task_name', 'N/A')}**")
            st.markdown("---")
            sub_cols = st.columns(5)
            with sub_cols[0]:
                st.markdown(f"**Thư ký phụ trách:**");
                st.info(f"{task_data.get('task_po', 'N/A')}")
            with sub_cols[1]:
                st.markdown(f"**Báo cáo cho:**");
                st.info(f"{task_data.get('task_report_to', 'N/A')}")
            with sub_cols[2]:
                st.markdown("**Deadline**")
                deadline_str = task_data.get('task_deadline')
                deadline_dt = pd.to_datetime(deadline_str, format='%Y-%m-%d', errors='coerce')
                if pd.isna(deadline_dt):
                    st.caption("(chưa có)")
                else:
                    today = pd.Timestamp.now().normalize()
                    delta = (deadline_dt - today).days
                    task_status = task_data.get('task_status')
                    if delta < 0:
                        st.error(f"{deadline_dt.strftime('%d/%m/%Y')}")
                        if task_status not in ['Đã hoàn thành', 'Đã hủy']: st.caption(f"Trễ {-delta} ngày")
                    elif delta == 0:
                        st.warning(f"{deadline_dt.strftime('%d/%m/%Y')}")
                    else:
                        st.success(f"{deadline_dt.strftime('%d/%m/%Y')}")
            with sub_cols[3]:
                st.markdown(f"**Trạng thái:**")
                st.info(f"{task_data.get('task_status', 'N/A')}")
            with sub_cols[4]:
                link = task_data.get('task_link', '')
                if link:
                    task_id = get_id_from_url(link)
                    st.link_button("FWS", url=f'https://workingspace.familyhospital.vn/task/show/{task_id}',
                                   use_container_width=True)
                if st.button("Chỉnh sửa", key=f"edit_btn_{card_key}", use_container_width=True):
                    st.session_state.editing_task_key = card_key
                    st.rerun()
