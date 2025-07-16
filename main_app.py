import streamlit as st
from utils.users import USERS

# Cấu hình trang
st.set_page_config(
    page_title="Trang chủ | App Quản lý",
    page_icon="🏠",
    layout="centered"
)

# --- QUẢN LÝ TRẠNG THÁI ĐĂNG NHẬP ---
# Khởi tạo session state nếu chưa có
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""


# --- HÀM ĐĂNG XUẤT ---
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.toast("Bạn đã đăng xuất!", icon="👋")


# --- GIAO DIỆN ---
if not st.session_state.logged_in:
    # --- TRANG ĐĂNG NHẬP ---
    st.title("Chào mừng đến với App Quản Lý 🚀")
    st.write("Vui lòng đăng nhập để sử dụng các chức năng.")

    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập").lower()
        password = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập")

        if submitted:
            user_data = USERS.get(username)
            if user_data and user_data["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = user_data["role"]
                st.rerun()
            else:
                st.error("Tên đăng nhập hoặc mật khẩu không chính xác.")
else:
    # --- TRANG CHỦ SAU KHI ĐĂNG NHẬP ---
    st.title(f"Xin chào, {st.session_state.username.capitalize()}!")
    st.subheader("Bạn đã đăng nhập thành công.")
    st.markdown("---")
    st.info("Sử dụng thanh điều hướng bên trái để truy cập các trang chức năng.", icon="👈")

    if st.button("Đăng xuất"):
        logout()
        st.rerun()