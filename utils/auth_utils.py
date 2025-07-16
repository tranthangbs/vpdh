# auth_utils.py
import streamlit as st
from functools import wraps
from utils.permissions_config import PERMISSIONS  # <-- 1. Import cấu hình


def is_authorized(feature_key: str) -> bool:
    """
    Hàm kiểm tra quyền dựa trên file cấu hình permissions_config.py.
    Đây là hàm chính để kiểm tra quyền cho các thành phần UI.

    Args:
        feature_key (str): Tên của tính năng được định nghĩa trong PERMISSIONS.

    Returns:
        bool: True nếu người dùng có quyền, False nếu không.
    """
    # Lấy danh sách các vai trò được phép từ file cấu hình
    allowed_roles = PERMISSIONS.get(feature_key)

    # Nếu tính năng không được định nghĩa trong file config, mặc định là từ chối
    if allowed_roles is None:
        st.warning(f"Lỗi cấu hình: Quyền cho '{feature_key}' chưa được định nghĩa.")
        return False

    # Lấy vai trò hiện tại của người dùng từ session state
    user_role = st.session_state.get('role', None)

    # Kiểm tra xem vai trò của người dùng có trong danh sách được phép không
    return user_role in allowed_roles


# Decorator require_role có thể giữ nguyên hoặc sửa đổi để dùng hàm is_authorized
# Dưới đây là phiên bản cập nhật để đồng bộ
def require_role(feature_key: str):
    """
    Decorator để giới hạn quyền truy cập vào một trang hoặc hàm,
    dựa trên file cấu hình.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not is_authorized(feature_key):
                st.error("⚠️ Truy cập bị từ chối. Bạn không có quyền thực hiện chức năng này.")
                st.stop()

            return func(*args, **kwargs)

        return wrapper

    return decorator