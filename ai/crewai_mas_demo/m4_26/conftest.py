import sys
from pathlib import Path

# 确保 m4l26/ 在 sys.path 中，tools/ 包可被导入
sys.path.insert(0, str(Path(__file__).resolve().parent))