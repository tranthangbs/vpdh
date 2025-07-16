# utils/google_sheet_utils.py
import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from utils.config import SHEET_IDS, TASK_SHEET_NAME

@st.cache_resource(ttl=600)
def connect_to_google_sheet():
    """Tạo kết nối tới Google Sheets bằng thông tin từ st.secrets."""
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        return gc
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets: {e}")
        return None

@st.cache_data(ttl=3600)
def get_sheet_headers(sheet_id: str) -> list:
    """Lấy danh sách tên các cột từ hàng đầu tiên của sheet được chỉ định."""
    try:
        gc = connect_to_google_sheet()
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(TASK_SHEET_NAME)
        return worksheet.row_values(1)
    except Exception as e:
        st.error(f"Không thể đọc header từ sheet ID '{sheet_id}': {e}")
        return []

def add_row_from_dict(sheet_id: str, data_dict: dict):
    """
    Tự động sắp xếp và thêm một hàng mới từ một dictionary,
    đồng thời yêu cầu Google Sheet tự diễn giải kiểu dữ liệu.
    """
    gc = connect_to_google_sheet()
    if gc is None:
        return False
    try:
        headers = get_sheet_headers(sheet_id)
        if not headers:
            st.error("Không có header, không thể thêm dữ liệu.")
            return False

        # Sắp xếp lại dữ liệu theo đúng thứ tự của header
        ordered_row = [data_dict.get(header, '') for header in headers]
        
        # Làm sạch giá trị 'nan' trước khi ghi
        sanitized_row = ['' if pd.isna(item) else item for item in ordered_row]
        
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(TASK_SHEET_NAME)
        
        # Ghi dữ liệu và yêu cầu Google Sheet tự nhận diện kiểu (ngày tháng, số,...)
        worksheet.append_row(sanitized_row, value_input_option='USER_ENTERED')
        
        # Xóa cache để đảm bảo dữ liệu được làm mới
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Lỗi khi thêm dữ liệu vào Google Sheet: {e}")
        return False

@st.cache_data(ttl=600)
def get_data_from_sheet(sheet_id: str):
    """Lấy toàn bộ dữ liệu từ sheet được chỉ định và trả về dưới dạng DataFrame."""
    if not sheet_id:
        st.error("Sheet ID không được cung cấp.")
        return pd.DataFrame()
    gc = connect_to_google_sheet()
    if gc is None:
        return pd.DataFrame()
    try:
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(TASK_SHEET_NAME)
        df = get_as_dataframe(worksheet, evaluate_formulas=True)
        df.dropna(how='all', inplace=True)
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Lỗi: Không tìm thấy trang tính (worksheet) có tên '{TASK_SHEET_NAME}'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi không xác định khi lấy dữ liệu từ sheet ID '{sheet_id}': {e}")
        return pd.DataFrame()
