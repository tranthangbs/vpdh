# utils/data_utils.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz


def search_dataframe(df: pd.DataFrame, search_term: str, search_column: str) -> pd.DataFrame:
    """
    Tìm kiếm một từ khóa trong một cột cụ thể của DataFrame.
    """
    if df.empty or not search_term.strip() or search_column not in df.columns:
        return pd.DataFrame(columns=df.columns)

    mask = df[search_column].astype(str).str.contains(search_term, case=False, na=False)
    return df[mask]


def filter_latest_tasks_by_name(df: pd.DataFrame):
    """
    Lọc DataFrame để chỉ giữ lại task có add_time mới nhất cho mỗi task_name.
    """
    if df.empty or 'add_time' not in df.columns or 'task_name' not in df.columns:
        return df

    df_copy = df.copy()
    df_copy['add_time_str'] = df_copy['add_time'].astype(str)
    df_copy['add_time_dt'] = pd.to_datetime(
        df_copy['add_time_str'],
        format='%d/%m/%Y %H:%M:%S',
        errors='coerce'
    )

    df_copy.dropna(subset=['add_time_dt'], inplace=True)
    if df_copy.empty:
        return df_copy.drop(columns=['add_time_str', 'add_time_dt'], errors='ignore')

    df_sorted = df_copy.sort_values(by=['task_name', 'add_time_dt'], ascending=[True, False])
    df_latest = df_sorted.drop_duplicates(subset='task_name', keep='first')

    return df_latest.drop(columns=['add_time_str', 'add_time_dt'], errors='ignore')


def process_deadline_tasks(df: pd.DataFrame):
    """
    Phân loại và sắp xếp các task sắp đến hạn, trừ những task đã hoàn thành.
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_filtered = df[df['task_status'] != 'Đã hoàn thành'].copy()
    df_filtered['deadline_dt'] = pd.to_datetime(df_filtered['task_deadline'], format='%Y-%m-%d', errors='coerce')

    today = pd.Timestamp.now().normalize()
    df_valid = df_filtered.dropna(subset=['deadline_dt']).copy()
    df_valid = df_valid[df_valid['deadline_dt'] >= today]

    if df_valid.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    due_today_df = df_valid[df_valid['deadline_dt'] == today]
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)
    due_soon_df = df_valid[(df_valid['deadline_dt'] >= tomorrow) & (df_valid['deadline_dt'] <= day_after_tomorrow)]
    three_days_later = today + timedelta(days=3)
    due_later_df = df_valid[df_valid['deadline_dt'] >= three_days_later]

    due_today_df = due_today_df.sort_values(by='deadline_dt')
    due_soon_df = due_soon_df.sort_values(by='deadline_dt')
    due_later_df = due_later_df.sort_values(by='deadline_dt')

    return due_today_df, due_soon_df, due_later_df


def get_overdue_tasks(df: pd.DataFrame):
    """
    Lọc và xử lý các task đã quá deadline, trừ những task đã hoàn thành.
    """
    if df.empty:
        return pd.DataFrame()

    df_filtered = df[df['task_status'] != 'Đã hoàn thành'].copy()
    df_filtered['deadline_dt'] = pd.to_datetime(df_filtered['task_deadline'], format='%Y-%m-%d', errors='coerce')

    today = pd.Timestamp.now().normalize()
    df_valid = df_filtered.dropna(subset=['deadline_dt']).copy()
    df_overdue = df_valid[df_valid['deadline_dt'] < today].copy()

    if df_overdue.empty:
        return pd.DataFrame()

    df_overdue['days_overdue'] = (today - df_overdue['deadline_dt']).dt.days
    df_overdue = df_overdue.sort_values(by='deadline_dt', ascending=True)

    return df_overdue


def get_current_hcm_time_str() -> str:
    """
    Lấy thời gian hiện tại theo múi giờ GMT+7 (Asia/Ho_Chi_Minh)
    và trả về dưới dạng chuỗi đã được định dạng dd/mm/yyyy HH:MM:SS.
    """
    hcm_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    current_time_aware = datetime.now(hcm_tz)
    return current_time_aware.strftime('%d/%m/%Y %H:%M:%S')


def get_id_from_url(url_string):
    try:
        # Bước 1: Tách chuỗi bởi ký tự '/', phần chứa ID sẽ nằm ở cuối cùng
        id_part = url_string.split('/')[-1]

        # Bước 2: Tách tiếp phần đó bởi ký tự '?' và lấy phần đầu tiên
        task_id = id_part.split('?')[0]

        return task_id
    except IndexError:
        # Trả về None nếu URL không đúng định dạng
        return None


def backfill_data(df: pd.DataFrame):
    """
    Tự động điền các giá trị bị thiếu cho một số cột được chỉ định,
    bằng cách lấy giá trị gần nhất của cùng một task trong quá khứ.
    """
    if df.empty or 'task_name' not in df.columns:
        return df

    df_copy = df.copy()

    # --- BƯỚC MỚI: CHUẨN HÓA DỮ LIỆU RỖNG ---
    # Chuyển đổi tất cả các ô có chuỗi rỗng thành giá trị NaN (Not a Number)
    # để hàm ffill() có thể hoạt động chính xác.
    df_copy.replace('', np.nan, inplace=True)

    # Chuyển đổi cột thời gian để sắp xếp chính xác
    df_copy['add_time_dt'] = pd.to_datetime(df_copy['add_time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

    # Sắp xếp theo tên và thời gian tăng dần (từ cũ đến mới)
    df_copy.sort_values(by=['task_name', 'add_time_dt'], ascending=True, inplace=True)

    # Danh sách các cột an toàn để tự động điền
    cols_to_fill = [
        'task_deadline',
        'task_link',
        'task_des',
        'task_report_to',
        'task_po'
    ]

    # Chỉ áp dụng ffill cho các cột đã chọn trong mỗi nhóm task_name
    df_copy[cols_to_fill] = df_copy.groupby('task_name')[cols_to_fill].ffill()

    # Bỏ cột tạm thời
    return df_copy.drop(columns=['add_time_dt'], errors='ignore')
