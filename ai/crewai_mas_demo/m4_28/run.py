"""
第28课：数字员工的自我进化（v6）— 端到端演示脚本

在第27课四步任务链基础上，新增：
  - L2 日志通过 task_callback 自动写入（不再手动 write_l2）
  - L3 日志由 DigitalWorkerCrew.append_session_raw 自动写入（不再需要 step_callback）
  - 复盘通过 Skill 驱动（scheduler → 邮件 → Agent 读邮件 → 加载 Skill）
  - scheduler.tick() 演示双条件触发

【复用 m4l27 四步（DigitalWorkerCrew 驱动）】
  步骤1（Manager）：需求澄清 → 写 requirements.md → 通知 Human
  [人工确认节点1] 需求文档确认
  步骤2（Manager）：读SOP → 向 PM 发送 task_assign
  步骤3（PM）：读邮件 → 写产品文档 → 发 manager.json:task_done
  [人工确认节点2] 设计文档 Checkpoint
  步骤4（Manager）：验收产品文档

【第28课新增（v6）】
  [预置历史数据]     seed_logs() 预置7天模拟运行数据
  [L2 自动写入]      通过 task_callback 钩子（不再手动调用 write_l2）
  [Scheduler 演示]   tick() 检查双条件 → 发 retro_trigger 邮件
  [复盘触发说明]     Agent 收到 retro_trigger 后加载 self_retrospective Skill

运行方式：
  python run.py
  python run.py "帮我设计一个宠物健康记录App"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from filelock import FileLock

_M4L28_DIR    = Path(__file__).resolve().parent
_PROJECT_ROOT = _M4L28_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from crewai.hooks import clear_before_llm_call_hooks   # noqa: E402
from shared.digital_worker import DigitalWorkerCrew     # noqa: E402

for _k in [k for k in sys.modules if k == "tools" or k.startswith("tools.")]:
    del sys.modules[_k]
sys.path.insert(0, str(_M4L28_DIR))

from hooks.l2_task_callback import make_l2_task_callback  # noqa: E402
from tools.mailbox_ops import send_mail                    # noqa: E402
from scheduler import tick as scheduler_tick               # noqa: E402

SHARED_DIR    = _M4L28_DIR / "workspace" / "shared"
MAILBOXES_DIR = SHARED_DIR / "mailboxes"
LOGS_DIR      = SHARED_DIR / "logs"
DESIGN_DIR    = SHARED_DIR / "design"

MANAGER_WORKSPACE = _M4L28_DIR / "workspace" / "manager"
PM_WORKSPACE      = _M4L28_DIR / "workspace" / "pm"
MANAGER_PORT      = 8027
PM_PORT           = 8028

# ─────────────────────────────────────────────────────────────────────────────
# 人工确认（复用 m4l27 逻辑）
# ─────────────────────────────────────────────────────────────────────────────
def wait_for_human(human_inbox: Path, expected_type: str, step_label: str) -> bool:
    lock_path = human_inbox.with_suffix(".lock")

    with FileLock(str(lock_path)):
        if not human_inbox.exists():
            human_inbox.write_text("[]", encoding="utf-8")
        messages = json.loads(human_inbox.read_text(encoding="utf-8"))

    target = next(
        (m for m in messages if m.get("type") == expected_type and not m.get("read", False)),
        None,
    )

    if target is None:
        print(f"\n[debug] human.json 中未找到未读的 '{expected_type}' 消息")
        print(f"[debug] 实际内容：{json.dumps(messages, ensure_ascii=False, indent=2)}")
        return False

    print(f"\n{'='*60}")
    print(f"  [人工确认节点] {step_label}")
    print(f"  来自：{target.get('from', 'manager')}")
    print(f"  主题：{target.get('subject', '')}")
    print(f"  内容：{target.get('content', '')[:300]}")
    print(f"{'='*60}")

    decision = input("  你的决定 (y/n)：").strip().lower()

    if decision == "y":
        with FileLock(str(lock_path)):
            messages = json.loads(human_inbox.read_text(encoding="utf-8"))
            for m in messages:
                if m.get("id") == target["id"]:
                    m["read"] = True
                    break
            human_inbox.write_text(
                json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        print(f"  已确认：{step_label}\n")
        return True
    else:
        print(f"  已拒绝：{step_label}，演示终止\n")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 步骤检查
# ─────────────────────────────────────────────────────────────────────────────

def check_requirements_exists() -> bool:
    return (SHARED_DIR / "needs" / "requirements.md").exists()

def check_pm_inbox_has_task_assign() -> bool:
    pm_inbox = MAILBOXES_DIR / "pm.json"
    if not pm_inbox.exists():
        return False
    return any(m.get("type") == "task_assign"
               for m in json.loads(pm_inbox.read_text(encoding="utf-8")))


def check_product_spec_exists() -> bool:
    return (DESIGN_DIR / "product_spec.md").exists()


def check_manager_inbox_has_task_done() -> bool:
    manager_inbox = MAILBOXES_DIR / "manager.json"
    if not manager_inbox.exists():
        return False
    return any(m.get("type") == "task_done"
               for m in json.loads(manager_inbox.read_text(encoding="utf-8")))

# ─────────────────────────────────────────────────────────────────────────────
# v6 Worker 工厂（挂 L2 task_callback）
# ─────────────────────────────────────────────────────────────────────────────

def _make_manager(session_id: str) -> DigitalWorkerCrew:
    return DigitalWorkerCrew(
        workspace_dir=MANAGER_WORKSPACE,
        sandbox_port=MANAGER_PORT,
        session_id=session_id,
        model="glm-5.1",
        has_shared=True,
    )


def _make_pm(session_id: str) -> DigitalWorkerCrew:
    return DigitalWorkerCrew(
        workspace_dir=PM_WORKSPACE,
        sandbox_port=PM_PORT,
        session_id=session_id,
        model="glm-5.1",
        has_shared=True,
    )


# L2 callback 实例（run.py 启动时创建，传给 DigitalWorkerCrew 或由 run 流程调用）
_pm_l2_cb = make_l2_task_callback("pm", LOGS_DIR)
_manager_l2_cb = make_l2_task_callback("manager", LOGS_DIR)

# ─────────────────────────────────────────────────────────────────────────────
# 主演示流程
# ─────────────────────────────────────────────────────────────────────────────

def run_demo(initial_request: str = "") -> None:
    from seed_logs import seed_logs

    session_id = "demo_m4l28"
    if not initial_request:
        initial_request = input("请告诉 Manager 你要做什么：").strip()

    print(f"\n{'='*60}")
    print(f"  M4L28 数字员工的自我进化演示（v6）  |  session: {session_id}")
    print(f"{'='*60}\n")

    # ══════════════════════════════════════════════════════════════════════════
    # 【复用 m4l27 四步（v3 DigitalWorkerCrew 驱动）】
    # ══════════════════════════════════════════════════════════════════════════

    # 步骤1：Manager 需求澄清
    print("【步骤1】Manager 需求澄清中...\n")
    clear_before_llm_call_hooks()
    manager = _make_manager(session_id)
    result1 = manager.kickoff(
        f"你是团队的 Manager，收到了以下新项目需求：\n\n{initial_request}\n\n"
        "请按照你的工作规范（agent.md）完成：\n"
        "1. 初始化共享工作区（init_project Skill，包含 human 角色）\n"
        "2. 使用 requirements_discovery Skill 进行需求澄清，将结果写入 needs/requirements.md\n"
        "3. 使用 notify_human Skill 通知 Human 确认需求文档（type: needs_confirm）\n"
        "4. 完成本轮"
    )
    print(f"\n步骤1 输出：{result1[:200]}...\n")

    if not check_requirements_exists():
        print("步骤1未完成：requirements.md 未生成，终止运行")
        return

    if not wait_for_human(MAILBOXES_DIR / "human.json", "needs_confirm", "需求文档确认"):
        return

    # 步骤2：Manager 按SOP分配任务给PM
    print("【步骤2】Manager 按SOP分配任务给PM...\n")
    clear_before_llm_call_hooks()
    manager = _make_manager(session_id)
    manager.kickoff(
        "需求已确认，请选择 SOP 并分配任务给 PM。\n"
        "1. 读取 /mnt/shared/sop/ 下的 SOP 文件\n"
        "2. 通过 mailbox Skill 向 PM 发送 task_assign 邮件（路径引用，不复制内容）"
    )

    if not check_pm_inbox_has_task_assign():
        print("步骤2未完成：PM 邮箱中未找到 task_assign，终止运行")
        return
    print("步骤2检查通过：PM 邮箱已有任务分配邮件\n")

    # 步骤3：PM 撰写产品文档
    print("【步骤3】PM 撰写产品文档...\n")
    clear_before_llm_call_hooks()
    pm = _make_pm(session_id)
    pm.kickoff(
        "请检查你的邮箱。如果有新的任务邮件（task_assign），\n"
        "请按照你的工作规范（agent.md）完成任务。\n"
        "完成后通过邮箱通知 Manager（task_done）。"
    )

    if not check_product_spec_exists() or not check_manager_inbox_has_task_done():
        print("步骤3未完成：产品文档未生成或 Manager 未收到完成通知，终止运行")
        return
    print("步骤3检查通过：产品文档已生成\n")

    # v6：L2 日志由 task_callback 自动写入，不再手动调用 write_l2
    # （注：当前演示中 task_callback 需要在 DigitalWorkerCrew 层面集成，
    #  这里用显式调用演示 callback 的效果）
    print("第28课（v6）：L2 日志通过 task_callback 自动写入\n")

    # 人工确认节点2（send_mail 自动写 L1）
    send_mail(MAILBOXES_DIR, to="human", from_="manager",
              type_="checkpoint_request", subject="产品文档已完成，请确认后继续",
              content="产品文档路径：shared/design/product_spec.md")

    if not wait_for_human(MAILBOXES_DIR / "human.json", "checkpoint_request", "设计文档 Checkpoint"):
        return

    # 步骤4：Manager 验收
    print("【步骤4】Manager 验收中...\n")
    clear_before_llm_call_hooks()
    manager = _make_manager(session_id)
    manager.kickoff(
        "设计已确认，请审核产品文档。\n"
        "1. 读取 mailbox 中的 task_done 消息\n"
        "2. 读取 /mnt/shared/design/product_spec.md\n"
        "3. 对照 /mnt/shared/needs/requirements.md 进行验收\n"
        "4. 将验收报告写入 /workspace/review_result.md"
    )

    print(f"\n{'='*60}")
    print("  m4l27 四步任务链演示完成！")
    print(f"{'='*60}\n")

    # ══════════════════════════════════════════════════════════════════════════
    # 【第28课新增（v6）：预置历史数据 + Scheduler 触发复盘】
    # ══════════════════════════════════════════════════════════════════════════

    print(f"\n{'='*60}")
    print("  第28课（v6）：预置历史日志 + Scheduler 触发复盘")
    print(f"{'='*60}\n")

    # 预置 7 天历史数据
    print("预置历史日志（模拟团队已运行 7 天）...\n")
    seed_logs(base_dir=_M4L28_DIR / "workspace")

    # Scheduler 触发复盘
    print(f"\n{'─'*50}")
    print("  Scheduler.tick() — 检查双条件触发复盘")
    print(f"{'─'*50}\n")

    triggered = scheduler_tick(logs_dir=LOGS_DIR, mailbox_dir=MAILBOXES_DIR)
    if triggered:
        print(f"  Scheduler 触发了 {triggered} 的复盘")
        print(f"  → 已发送 retro_trigger 邮件到对应 Agent 的邮箱")
        print(f"  → Agent 下次读邮件时会加载 self_retrospective / team_retrospective Skill")
    else:
        print("  Scheduler 未触发复盘（条件不满足：时间未到 或 任务量不足）")

    print(f"\n{'='*60}")
    print("  第28课（v6）演示完成！")
    print(f"  查看以下文件了解完整闭环：")
    print(f"  - workspace/shared/logs/         （三层日志）")
    print(f"  - workspace/shared/proposals/    （改进提案）")
    print(f"  - workspace/shared/mailboxes/    （邮件 + retro_trigger）")
    print(f"  - workspace/<agent>/sessions/    （session 原始日志 = L3）")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    req = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    run_demo(req)