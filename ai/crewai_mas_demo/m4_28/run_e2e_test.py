"""
端到端演示自动化脚本（非交互式）
自动跳过 wait_for_human 确认节点，直接执行全流程。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_M4L28_DIR    = Path(__file__).resolve().parent
_PROJECT_ROOT = _M4L28_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from crewai.hooks import clear_before_llm_call_hooks
from shared.digital_worker import DigitalWorkerCrew

for _k in [k for k in sys.modules if k == "tools" or k.startswith("tools.")]:
    del sys.modules[_k]
sys.path.insert(0, str(_M4L28_DIR))

from tools.mailbox_ops import send_mail
from scheduler import tick as scheduler_tick

SHARED_DIR    = _M4L28_DIR / "workspace" / "shared"
MAILBOXES_DIR = SHARED_DIR / "mailboxes"
LOGS_DIR      = SHARED_DIR / "logs"

MANAGER_WORKSPACE = _M4L28_DIR / "workspace" / "manager"
PM_WORKSPACE      = _M4L28_DIR / "workspace" / "pm"

results = {}
errors = []


def auto_confirm(inbox_path: Path, msg_type: str, label: str):
    if not inbox_path.exists():
        print(f"  [WARN] {label}: {inbox_path} 不存在")
        errors.append(f"{label}: inbox 不存在")
        return
    messages = json.loads(inbox_path.read_text(encoding="utf-8"))
    target = next((m for m in messages if m.get("type") == msg_type and not m.get("read")), None)
    if target:
        target["read"] = True
        inbox_path.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [AUTO] 已确认: {label} (msg_id={target.get('id', '?')})")
    else:
        print(f"  [WARN] {label}: 未找到未读 {msg_type} 消息")
        errors.append(f"{label}: 未找到 {msg_type}")


def step(name, fn):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    t0 = time.time()
    try:
        result = fn()
        elapsed = time.time() - t0
        results[name] = {"status": "OK", "elapsed": f"{elapsed:.1f}s", "output_len": len(str(result)) if result else 0}
        print(f"  [{elapsed:.1f}s] OK")
        return result
    except Exception as e:
        elapsed = time.time() - t0
        results[name] = {"status": "FAIL", "elapsed": f"{elapsed:.1f}s", "error": str(e)}
        errors.append(f"{name}: {e}")
        print(f"  [{elapsed:.1f}s] FAIL: {e}")
        return None


def run():
    session_id = "e2e_test"
    request = "帮我设计一个宠物健康记录App，支持多宠物管理和疫苗提醒"

    # 步骤1: Manager 需求澄清
    def step1():
        clear_before_llm_call_hooks()
        m = DigitalWorkerCrew(
            workspace_dir=MANAGER_WORKSPACE, sandbox_port=8027,
            session_id=session_id, model="glm-5.1", has_shared=True,
        )
        return m.kickoff(
            f"你是团队的 Manager，收到了以下新项目需求：\n\n{request}\n\n"
            "请按照你的工作规范（agent.md）完成：\n"
            "1. 初始化共享工作区（init_project Skill，包含 human 角色）\n"
            "2. 使用 requirements_discovery Skill 进行需求澄清，将结果写入 needs/requirements.md\n"
            "3. 使用 notify_human Skill 通知 Human 确认需求文档（type: needs_confirm）\n"
            "4. 完成本轮"
        )

    result1 = step("步骤1: Manager 需求澄清", step1)

    req_file = SHARED_DIR / "needs" / "requirements.md"
    if req_file.exists():
        print(f"  requirements.md: {req_file.stat().st_size} bytes")
    else:
        print("  [WARN] requirements.md 未生成")
        errors.append("requirements.md 未生成")

    # 自动确认需求
    auto_confirm(MAILBOXES_DIR / "human.json", "needs_confirm", "需求确认")

    # 步骤2: Manager 分配任务给 PM
    def step2():
        clear_before_llm_call_hooks()
        m = DigitalWorkerCrew(
            workspace_dir=MANAGER_WORKSPACE, sandbox_port=8027,
            session_id=session_id, model="glm-5.1", has_shared=True,
        )
        return m.kickoff(
            "需求已确认，请选择 SOP 并分配任务给 PM。\n"
            "1. 读取 /mnt/shared/sop/ 下的 SOP 文件\n"
            "2. 通过 mailbox Skill 向 PM 发送 task_assign 邮件（路径引用，不复制内容）"
        )

    step("步骤2: Manager 分配任务", step2)

    pm_inbox = MAILBOXES_DIR / "pm.json"
    if pm_inbox.exists():
        msgs = json.loads(pm_inbox.read_text(encoding="utf-8"))
        has_assign = any(m.get("type") == "task_assign" for m in msgs)
        print(f"  PM 邮箱: {len(msgs)} 封, task_assign: {has_assign}")
        if not has_assign:
            errors.append("PM 邮箱无 task_assign")
    else:
        errors.append("PM 邮箱不存在")

    # 步骤3: PM 撰写产品文档
    def step3():
        clear_before_llm_call_hooks()
        p = DigitalWorkerCrew(
            workspace_dir=PM_WORKSPACE, sandbox_port=8028,
            session_id=session_id, model="glm-5.1", has_shared=True,
        )
        return p.kickoff(
            "请检查你的邮箱。如果有新的任务邮件（task_assign），\n"
            "请按照你的工作规范（agent.md）完成任务。\n"
            "完成后通过邮箱通知 Manager（task_done）。"
        )

    step("步骤3: PM 撰写产品文档", step3)

    spec_file = SHARED_DIR / "design" / "product_spec.md"
    if spec_file.exists():
        print(f"  product_spec.md: {spec_file.stat().st_size} bytes")
    else:
        print("  [WARN] product_spec.md 未生成")
        errors.append("product_spec.md 未生成")

    # L1 自动写入 checkpoint
    send_mail(MAILBOXES_DIR, to="human", from_="manager",
              type_="checkpoint_request", subject="产品文档已完成，请确认后继续",
              content="产品文档路径：shared/design/product_spec.md")
    auto_confirm(MAILBOXES_DIR / "human.json", "checkpoint_request", "设计文档 Checkpoint")

    # 步骤4: Manager 验收
    def step4():
        clear_before_llm_call_hooks()
        m = DigitalWorkerCrew(
            workspace_dir=MANAGER_WORKSPACE, sandbox_port=8027,
            session_id=session_id, model="glm-5.1", has_shared=True,
        )
        return m.kickoff(
            "设计已确认，请审核产品文档。\n"
            "1. 读取 mailbox 中的 task_done 消息\n"
            "2. 读取 /mnt/shared/design/product_spec.md\n"
            "3. 对照 /mnt/shared/needs/requirements.md 进行验收\n"
            "4. 将验收报告写入 /workspace/review_result.md"
        )

    step("步骤4: Manager 验收", step4)

    review_file = MANAGER_WORKSPACE / "review_result.md"
    if review_file.exists():
        print(f"  review_result.md: {review_file.stat().st_size} bytes")
    else:
        print("  [INFO] review_result.md 未生成（Manager 可能直接输出了验收结论）")

    # 第28课新增: seed_logs + scheduler
    def step5():
        from seed_logs import seed_logs
        seed_logs(base_dir=_M4L28_DIR / "workspace")
        return "seed_logs done"

    step("步骤5: 预置历史日志 (seed_logs)", step5)

    def step6():
        return scheduler_tick(logs_dir=LOGS_DIR, mailbox_dir=MAILBOXES_DIR)

    triggered = step("步骤6: Scheduler.tick()", step6)
    if triggered:
        print(f"  触发复盘: {triggered}")
    else:
        print("  未触发（seed_logs 数据均 >24h 前，属正常行为）")

    # 打印最终报告
    print(f"\n{'='*60}")
    print("  E2E 运行报告")
    print(f"{'='*60}")
    for name, info in results.items():
        status_icon = "✅" if info["status"] == "OK" else "❌"
        print(f"  {status_icon} {name}: {info['status']} ({info['elapsed']})")

    print(f"\n  错误数: {len(errors)}")
    for e in errors:
        print(f"    ❌ {e}")

    # 检查最终文件
    print(f"\n  文件检查:")
    checks = [
        ("requirements.md", SHARED_DIR / "needs" / "requirements.md"),
        ("product_spec.md", SHARED_DIR / "design" / "product_spec.md"),
        ("L1 日志", SHARED_DIR / "logs" / "l1_human"),
        ("L2 日志", SHARED_DIR / "logs" / "l2_task"),
        ("L3 日志 (旧)", SHARED_DIR / "logs" / "l3_react"),
        ("L3 session", _M4L28_DIR / "workspace" / "pm" / "sessions"),
        ("human.json", MAILBOXES_DIR / "human.json"),
        ("pm.json", MAILBOXES_DIR / "pm.json"),
        ("manager.json", MAILBOXES_DIR / "manager.json"),
    ]
    for label, path in checks:
        if path.exists():
            if path.is_dir():
                count = len(list(path.rglob("*.json")) + list(path.rglob("*.jsonl")))
                print(f"    ✅ {label}: {count} files")
            else:
                print(f"    ✅ {label}: {path.stat().st_size} bytes")
        else:
            print(f"    ❌ {label}: 不存在")

    return results, errors


if __name__ == "__main__":
    run()