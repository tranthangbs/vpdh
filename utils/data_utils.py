# utils/data_utils.py
import pandas as pd
from datetime import datetime, timedelta


# --- hàm search_dataframe không đổi ---
def search_dataframe(df: pd.DataFrame, search_term: str, search_column: str) -> pd.DataFrame:
    if df.empty or not search_term.strip() or search_column not in df.columns:
        return pd.DataFrame(columns=df.columns)
    mask = df[search_column].astype(str).str.contains(search_term, case=False, na=False)
    return df[mask]


# --- hàm filter_latest_tasks_by_name không đổi ---
def filter_latest_tasks_by_name(df: pd.DataFrame):
    """
    Lọc DataFrame để chỉ giữ lại task có add_time mới nhất cho mỗi task_name.
    """
    if df.empty or 'add_time' not in df.columns or 'task_name' not in df.columns:
        return df

    df_copy = df.copy()

    # --- THAY ĐỔI Ở ĐÂY ---
    # Cập nhật định dạng cho cột 'add_time' để khớp với định dạng mới
    df_copy['add_time_dt'] = pd.to_datetime(
        df_copy['add_time'],
        format='%d/%m/%Y %H:%M:%S', # <-- Sửa định dạng ở đây
        errors='coerce'
    )

    df_copy.dropna(subset=['add_time_dt'], inplace=True)
    if df_copy.empty:
        return df_copy.drop(columns=['add_time_dt'], errors='ignore')

    df_sorted = df_copy.sort_values(by=['task_name', 'add_time_dt'], ascending=[True, False])
    df_latest = df_sorted.drop_duplicates(subset='task_name', keep='first')

    return df_latest.drop(columns=['add_time_dt'], errors='ignore')


# --- CẬP NHẬT HÀM process_deadline_tasks ---
def process_deadline_tasks(df: pd.DataFrame):
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    df_filtered = df[df['task_status'] != 'Đã hoàn thành'].copy()

    # THAY ĐỔI Ở ĐÂY: Cập nhật định dạng ngày tháng mới
    df_filtered['deadline_dt'] = pd.to_datetime(df_filtered['task_deadline'], format='%d/%m/%Y %H:%M:%S',
                                                errors='coerce')

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


# --- CẬP NHẬT HÀM get_overdue_tasks ---
def get_overdue_tasks(df: pd.DataFrame):
    if df.empty:
        return pd.DataFrame()
    df_filtered = df[df['task_status'] != 'Đã hoàn thành'].copy()

    # THAY ĐỔI Ở ĐÂY: Cập nhật định dạng ngày tháng mới
    df_filtered['deadline_dt'] = pd.to_datetime(df_filtered['task_deadline'], format='%d/%m/%Y %H:%M:%S',
                                                errors='coerce')

    today = pd.Timestamp.now().normalize()
    df_valid = df_filtered.dropna(subset=['deadline_dt']).copy()
    df_overdue = df_valid[df_valid['deadline_dt'] < today].copy()
    if df_overdue.empty:
        return pd.DataFrame()
    df_overdue['days_overdue'] = (today - df_overdue['deadline_dt']).dt.days
    df_overdue = df_overdue.sort_values(by='deadline_dt', ascending=True)
    return df_overdue
