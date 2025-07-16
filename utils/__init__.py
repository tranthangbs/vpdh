"""
File này biến package 'utils' thành một module duy nhất, cung cấp một API gọn gàng.
Thay vì import từ utils.config, utils.auth_utils, etc.,
bạn có thể import trực tiếp từ utils.
"""

# Từ config.py
from .config import SHEET_IDS

# Từ google_sheet_utils.py
from .google_sheet_utils import get_data_from_sheet, get_sheet_headers, add_row_from_dict

# Từ auth_utils.py
from .auth_utils import is_authorized, require_role

# Từ view_utils.py
from .view_utils import set_active_view, render_task_card

# Từ data_utils.py
from .data_utils import search_dataframe, process_deadline_tasks, get_overdue_tasks, filter_latest_tasks_by_name
