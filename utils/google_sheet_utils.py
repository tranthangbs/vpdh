import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from datetime import datetime
from utils.config import SHEET_IDS


# Kết nối tới Google Sheets
@st.cache_resource(ttl=600)
def connect_to_google_sheet():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        return gc
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets: {e}")
        return None

@st.cache_data(ttl=3600) # Cache header trong 1 giờ
def get_sheet_headers(sheet_id: str) -> list:
    """Lấy danh sách tên các cột từ hàng đầu tiên của sheet."""
    try:
        gc = connect_to_google_sheet()
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1
        return worksheet.row_values(1)
    except Exception as e:
        st.error(f"Không thể đọc header từ sheet ID '{sheet_id}': {e}")
        return []

@st.cache_data(ttl=600)
def get_data_from_sheet(sheet_id: str):
    """
    Lấy dữ liệu từ sheet đầu tiên của một file Google Sheet bất kỳ.
    Args:
        sheet_id (str): ID của file Google Sheet cần đọc.
    Returns:
        pd.DataFrame: DataFrame chứa dữ liệu.
    """
    if not sheet_id:
        st.error("Sheet ID không được cung cấp.")
        return pd.DataFrame()

    gc = connect_to_google_sheet()
    if gc is None:
        return pd.DataFrame()

    try:
        spreadsheet = gc.open_by_key(sheet_id)
        # Lấy trang tính đầu tiên theo yêu cầu "chỉ sử dụng duy nhất 1 sheet"
        worksheet = spreadsheet.sheet1

        df = get_as_dataframe(worksheet, evaluate_formulas=True)
        df.dropna(how='all', inplace=True)
        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Lỗi: Không tìm thấy Google Sheet với ID '{sheet_id}'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi không xác định khi lấy dữ liệu từ sheet ID '{sheet_id}': {e}")
        return pd.DataFrame()


def add_row_from_dict(sheet_id: str, data_dict: dict):
    """
    Tự động sắp xếp và thêm một hàng mới từ một dictionary.
    Đây là hàm được khuyên dùng để thêm dữ liệu.
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
        # Dùng data_dict.get(header, '') để tránh lỗi nếu thiếu key và điền chuỗi rỗng
        ordered_row = [data_dict.get(header, '') for header in headers]

        # Làm sạch giá trị nan trước khi ghi
        sanitized_row = ['' if pd.isna(item) else item for item in ordered_row]

        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1
        worksheet.append_row(sanitized_row)

        # Xóa cache để đảm bảo dữ liệu được làm mới
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Lỗi khi thêm dữ liệu vào Google Sheet: {e}")
        return False

