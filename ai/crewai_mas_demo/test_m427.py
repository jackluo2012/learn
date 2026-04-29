#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
# 在 crewai 导入之前设置 OPENAI_API_KEY
os.environ.setdefault("OPENAI_API_KEY", "sk-fake123456789012345678901234567890123456789012345678")

from m4_27.main import main
main()