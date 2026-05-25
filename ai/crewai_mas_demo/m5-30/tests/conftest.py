import sys
from pathlib import Path

_M5L30_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_M5L30_DIR))

from dotenv import load_dotenv
load_dotenv(_M5L30_DIR / ".env", override=True)