"""循环检测——状态哈希去重，连续重复时终止。"""

import hashlib
import json
import sys

from hook_framework.registry import GuardrailDeny


class LoopDetector:
    def __init__(self, threshold: int = 3):

        """
        初始化循环检测器
        
        Args:
            threshold (int): 检测循环的阈值，默认为3
        """
        self._threshold = threshold  # 循环检测的阈值
        """
        初始化循环检测器
        
        参数:
            threshold: 循环检测的阈值，默认为3，表示连续出现3次相同状态即视为循环
        """
        self._threshold = threshold  # 循环检测的阈值
        self._tool_hashes: list[str] = []
        self._turn_hashes: list[str] = []
        self._loop_detections = 0

    def _check_loop(self, hashes: list[str], state: str, ctx) -> None:
        # 计算当前状态的MD5哈希值，并取前16位作为简短哈希
        h = hashlib.md5(state.encode()).hexdigest()[:16]
        # 将当前哈希值添加到哈希列表中
        hashes.append(h)
        # 如果哈希列表长度超过阈值的2倍，则删除最早的部分，只保留最近的阈值数量的哈希
        if len(hashes) > self._threshold * 2:
            del hashes[:-self._threshold]

        # 如果哈希列表长度达到或超过阈值
        if len(hashes) >= self._threshold:
            # 获取最近的阈值数量的哈希值
            recent = hashes[-self._threshold:]
            # 检查最近的哈希值是否全部相同（即没有变化）
            if len(set(recent)) == 1:
                # 如果检测到循环，增加循环计数器
                self._loop_detections += 1
                # 发出检测信号
                self._emit_detection(ctx)
                # 抛出异常，阻止继续执行
                raise GuardrailDeny(
                    f"Loop detected: identical state repeated "
                    f"{self._threshold} consecutive times "
                    f"(turn {ctx.turn_number}, tool: {ctx.tool_name})"
                )

    def after_turn_handler(self, ctx):
        state = f"{ctx.tool_name}:{ctx.metadata.get('output', '')[:200]}"
        self._check_loop(self._turn_hashes, state, ctx)

    def after_tool_handler(self, ctx):
        """AFTER_TOOL_CALL: 检测工具调用循环（覆盖 native function calling 路径）。"""
        output = ctx.metadata.get("tool_output", ctx.metadata.get("output", ""))[:200]
        state = f"{ctx.tool_name}:{output}"
        self._check_loop(self._tool_hashes, state, ctx)

    def _emit_detection(self, ctx):
        record = {
            "level": "CRITICAL",
            "guardrail": "loop_detector",
            "message": "Loop detected — terminating",
            "turn": ctx.turn_number,
            "tool": ctx.tool_name,
            "threshold": self._threshold,
        }
        print(json.dumps(record, ensure_ascii=False), file=sys.stderr)

    def get_metrics(self) -> dict:
        all_hashes = self._tool_hashes + self._turn_hashes
        return {
            "total_turns": len(self._turn_hashes),
            "total_tool_calls": len(self._tool_hashes),
            "unique_states": len(set(all_hashes)), 
            "loop_detections": self._loop_detections,
        }