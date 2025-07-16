# data_utils.py
import pandas as pd
from datetime import datetime, timedelta

def search_dataframe(df: pd.DataFrame, search_term: str, search_column: str) -> pd.DataFrame:
    """
    Tìm kiếm một từ khóa trong một cột cụ thể của DataFrame.

    Args:
        df (pd.DataFrame): DataFrame nguồn để tìm kiếm.
        search_term (str): Từ khóa cần tìm.
        search_column (str): Tên của cột sẽ được tìm kiếm.

    Returns:
        pd.DataFrame: Một DataFrame mới chứa các dòng khớp với kết quả.
                      Trả về DataFrame rỗng nếu không có kết quả hoặc đầu vào không hợp lệ.
    """
    # --- Kiểm tra đầu vào ---
    # Nếu dataframe rỗng, từ khóa trống, hoặc tên cột không tồn tại, trả về dataframe rỗng
    if df.empty or not search_term.strip() or search_column not in df.columns:
        return pd.DataFrame(columns=df.columns)

    # --- Thực hiện tìm kiếm ---
    # Chuyển cột tìm kiếm sang kiểu string để đảm bảo hàm .str hoạt động
    # case=False: không phân biệt hoa thường
    # na=False: coi các giá trị NaN là không khớp
    mask = df[search_column].astype(str).str.contains(search_term, case=False, na=False)

    return df[mask]


def process_deadline_tasks(df: pd.DataFrame):
    """
    Phân loại và sắp xếp các task dựa trên deadline, trừ những task đã hoàn thành.
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # --- THÊM BỘ LỌC TRẠNG THÁI ---
    df_filtered = df[df['task_status'] != 'Đã hoàn thành'].copy()

    # Các bước sau thực hiện trên dataframe đã được lọc
    df_filtered['deadline_dt'] = pd.to_datetime(df_filtered['task_deadline'], format='%d/%m/%Y', errors='coerce')

    today = pd.Timestamp.now().normalize()

    df_valid = df_filtered.dropna(subset=['deadline_dt']).copy()
    df_valid = df_valid[df_valid['deadline_dt'] >= today]

    if df_valid.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Hết hạn hôm nay
    due_today_df = df_valid[df_valid['deadline_dt'] == today]
    # Hết hạn trong 2-3 ngày tới
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)
    due_soon_df = df_valid[(df_valid['deadline_dt'] >= tomorrow) & (df_valid['deadline_dt'] <= day_after_tomorrow)]
    # Các task còn lại
    three_days_later = today + timedelta(days=3)
    due_later_df = df_valid[df_valid['deadline_dt'] >= three_days_later]

    # Sắp xếp kết quả
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

    # --- THÊM BỘ LỌC TRẠNG THÁI ---
    df_filtered = df[df['task_status'] != 'Đã hoàn thành'].copy()

    # Các bước sau thực hiện trên dataframe đã được lọc
    df_filtered['deadline_dt'] = pd.to_datetime(df_filtered['task_deadline'], format='%d/%m/%Y', errors='coerce')

    today = pd.Timestamp.now().normalize()

    df_valid = df_filtered.dropna(subset=['deadline_dt']).copy()
    df_overdue = df_valid[df_valid['deadline_dt'] < today].copy()

    if df_overdue.empty:
        return pd.DataFrame()

    df_overdue['days_overdue'] = (today - df_overdue['deadline_dt']).dt.days
    df_overdue = df_overdue.sort_values(by='deadline_dt', ascending=True)

    return df_overdue


def filter_latest_tasks_by_name(df: pd.DataFrame):
    """
    Lọc DataFrame để chỉ giữ lại task có add_time mới nhất cho mỗi task_name.
    """
    if df.empty or 'add_time' not in df.columns or 'task_name' not in df.columns:
        return df

    df_copy = df.copy()

    # --- SỬA LỖI Ở ĐÂY ---
    # Chỉ định rõ ràng định dạng thời gian để đảm bảo chuyển đổi chính xác
    df_copy['add_time_dt'] = pd.to_datetime(
        df_copy['add_time'],
        format='%Y-%m-%d %H:%M:%S', # Khớp với định dạng code tạo ra
        errors='coerce'
    )

    # Loại bỏ các hàng không thể chuyển đổi thời gian để tránh lỗi so sánh
    df_copy.dropna(subset=['add_time_dt'], inplace=True)
    if df_copy.empty:
        return df_copy # Trả về df rỗng nếu không có hàng nào hợp lệ

    # Sắp xếp theo tên và thời gian giảm dần
    df_sorted = df_copy.sort_values(by=['task_name', 'add_time_dt'], ascending=[True, False])

    # Loại bỏ các bản sao, chỉ giữ lại bản ghi đầu tiên (mới nhất)
    df_latest = df_sorted.drop_duplicates(subset='task_name', keep='first')

    # Bỏ cột datetime tạm thời trước khi trả về
    return df_latest.drop(columns=['add_time_dt'])


