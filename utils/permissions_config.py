"""
Đây là file cấu hình trung tâm cho việc phân quyền.
Mỗi key trong dictionary đại diện cho một tính năng hoặc một thành phần UI.
Value tương ứng là một list các vai trò (role) được phép truy cập.
"""

PERMISSIONS = {
    # Key (Tên tính năng) : Value (Danh sách vai trò được phép)

    # --- Quyền cho các nút/tính năng chung ---
    'view_all_tasks': ['admin'],
    'add_new_task': ['admin',],
    'edit_own_task': ['admin', 'manager', 'employee'],
    'delete_task': ['admin'],
    'search_task': ['admin', 'manager', 'employee'],
    'process_deadline_tasks': ['admin', 'manager', 'employee'],
    'get_overdue_tasks': ['admin', 'manager', 'employee'],

    # --- Quyền truy cập trang ---
    'access_admin_dashboard': ['admin'],
    'access_reports_page': ['admin', 'manager'],
}
