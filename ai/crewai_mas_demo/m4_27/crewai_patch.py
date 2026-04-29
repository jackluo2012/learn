"""
CrewAI MCP Client Cleanup Bug 补丁

修复 CrewAI 1.9.3 在已有事件循环环境中调用 asyncio.run() 的问题
"""

import asyncio
import warnings

# 保存原始的 cleanup 方法
_original_cleanup = None


def patched_cleanup(self):
    """修复后的 cleanup 方法，处理已有事件循环的情况"""
    if not self._mcp_clients:
        return

    async def _disconnect_all() -> None:
        for client in self._mcp_clients:
            if client and hasattr(client, "connected") and client.connected:
                try:
                    await client.disconnect()
                except Exception as e:
                    # 静默处理单个客户端断开连接的错误
                    pass

    try:
        # 检查是否已有事件循环在运行
        try:
            loop = asyncio.get_running_loop()
            # 如果已有事件循环，创建 task
            asyncio.create_task(_disconnect_all())
        except RuntimeError:
            # 没有运行中的事件循环，使用 asyncio.run
            asyncio.run(_disconnect_all())
    except Exception as e:
        # 静默处理所有清理错误，避免干扰正常流程
        pass
    finally:
        self._mcp_clients.clear()


def apply_patch():
    """应用补丁到 CrewAI Agent 类"""
    global _original_cleanup

    try:
        from crewai.agent import Agent

        # 保存原始方法（只保存一次）
        if _original_cleanup is None:
            _original_cleanup = Agent._cleanup_mcp_clients

        # 应用补丁
        Agent._cleanup_mcp_clients = patched_cleanup
        print("✅ CrewAI MCP cleanup patch applied successfully")

    except ImportError as e:
        print(f"⚠️  Failed to import CrewAI: {e}")
    except Exception as e:
        print(f"⚠️  Failed to apply patch: {e}")


def remove_patch():
    """移除补丁，恢复原始方法"""
    global _original_cleanup

    if _original_cleanup is not None:
        try:
            from crewai.agent import Agent
            Agent._cleanup_mcp_clients = _original_cleanup
            print("✅ CrewAI MCP cleanup patch removed")
        except Exception as e:
            print(f"⚠️  Failed to remove patch: {e}")


if __name__ == "__main__":
    # 测试补丁
    apply_patch()
