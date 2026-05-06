"""
第28课·数字员工的自我进化（v6）
hooks/ — CrewAI 回调钩子

v6 只保留 l2_task_callback（L3 由 session 日志承担）。
"""

from hooks.l2_task_callback import make_l2_task_callback

__all__ = ["make_l2_task_callback"]
