#!/usr/bin/env python3
"""根据 DashScope API 配额自动替换 llm_config.yaml 中的模型."""

import argparse
import json
import shutil
import sys
from pathlib import Path

import yaml


# ──────────────────────────────────────────────
# 模型角色 → quota JSON 中的分类映射
# ──────────────────────────────────────────────
ROLE_CATEGORY_MAP = {
    "default.text_model":          ("text",      None),
    "default.image_model":         ("image",     None),
    "default.summary_model":      ("summary",   None),
    "models.assistant.model":      ("assistant", None),
    "models.lightweight.model":    ("text",      None),
    "models.vision.model":         ("image",     None),
    "models.coder.model":          ("coder",    None),
    "models.long_context.model":   ("long",     None),
}

ROLE_DISPLAY = {
    "default.text_model":          "default.text_model (通用文本)",
    "default.image_model":         "default.image_model (图像模型)",
    "default.summary_model":        "default.summary_model (摘要模型)",
    "models.assistant.model":      "models.assistant (助手)",
    "models.lightweight.model":    "models.lightweight (轻量)",
    "models.vision.model":         "models.vision (视觉)",
    "models.coder.model":          "models.coder (编程)",
    "models.long_context.model":   "models.long_context (长上下文)",
}


# ══════════════════════════════════════════════
# Quota JSON 解析
# ══════════════════════════════════════════════

def load_quota_json(path: str) -> dict:
    """支持标准 JSON 和 JSON Lines 两种格式."""
    with open(path, encoding="utf-8") as f:
        raw = f.read().strip()

    if "\n" in raw and not raw.startswith("{"):
        merged = {}
        for line in raw.splitlines():
            if line.strip():
                _merge_obj(json.loads(line), merged)
        return merged

    obj = json.loads(raw)

    # 处理 DashScope API 返回的格式: {"data": {"DataV2": {...}}}
    if "data" in obj and isinstance(obj["data"], dict):
        data = obj["data"]
        # 如果是 {"DataV2": {"data": {"data": {"freeTierQuotas": [...]}}}}
        if "DataV2" in data and isinstance(data["DataV2"], dict):
            datav2 = data["DataV2"]
            if "data" in datav2 and isinstance(datav2["data"], dict):
                inner = datav2["data"]
                if "data" in inner and isinstance(inner["data"], dict):
                    return inner["data"]
        return data

    return obj.get("data", obj)


def _merge_obj(obj: dict, merged: dict):
    """递归合并 quota 对象，按 model 聚合 remaining."""
    if "model" in obj and "quota_usage" in obj:
        name = obj["model"]
        merged.setdefault(name, {"model": name, "remaining": 0})
        rem = _get_remaining(obj)
        if rem is not None:
            merged[name]["remaining"] = max(merged[name]["remaining"], rem)
        return
    for v in obj.values():
        if isinstance(v, dict):
            _merge_obj(v, merged)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    _merge_obj(item, merged)


def _get_remaining(obj: dict) -> float | None:
    """从单个 model 对象提取 remaining 值."""
    # 优先从 quota_usage 获取剩余配额
    quota = obj.get("quota_usage") or obj.get("stats", {})
    if isinstance(quota, dict):
        if "remaining" in quota:
            v = quota["remaining"]
            return float(v) if v is not None else None
        if "used" in quota and "limit" in quota:
            used = float(quota.get("used", 0) or 0)
            limit = float(quota.get("limit", 0) or 0)
            if limit > 0:
                return limit - used

    # 支持 freeTierQuotas 格式：quotaInitTotal 是总配额
    if "quotaInitTotal" in obj:
        return float(obj["quotaInitTotal"])

    return None


def extract_remaining(quota_data: dict, category: str | None = None) -> dict[str, float]:
    """提取模型剩余 token，{model_name: remaining}."""
    result: dict[str, float] = {}

    # 处理 freeTierQuotas 格式 (DashScope API 返回的格式)
    if "freeTierQuotas" in quota_data:
        models_list = quota_data["freeTierQuotas"]
        for m in models_list:
            if not isinstance(m, dict):
                continue
            name = m.get("model", "")
            rem = _get_remaining(m)
            if name and rem is not None and rem > 0:
                result[name] = rem
        return result

    # 处理标准格式
    if all(k in quota_data for k in ["model", "quota_usage"]):
        name = quota_data["model"]
        rem = _get_remaining(quota_data)
        if name and rem is not None:
            result[name] = rem
        return result

    for cat_key, cat_val in quota_data.items():
        if category is not None and cat_key != category:
            continue
        models_list: list = []
        if isinstance(cat_val, dict):
            models_list = cat_val.get("models", cat_val.get("data", []))
        elif isinstance(cat_val, list):
            models_list = cat_val
        else:
            continue
        for m in models_list:
            if not isinstance(m, dict):
                continue
            name = m.get("model", "")
            rem = _get_remaining(m)
            if name and rem is not None and rem > 0:
                if name not in result or rem > result[name]:
                    result[name] = rem

    return result


# ══════════════════════════════════════════════
# Config 读写
# ══════════════════════════════════════════════

def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def dump_config(cfg: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def get_model(cfg: dict, role_path: str) -> str:
    parts = role_path.split(".")
    val = cfg
    for p in parts[:-1]:
        val = val[p]
    return val.get(parts[-1], "")


def set_model(cfg: dict, role_path: str, model: str):
    parts = role_path.split(".")
    val = cfg
    for p in parts[:-1]:
        val = val[p]
    val[parts[-1]] = model


# ══════════════════════════════════════════════
# 模型类型过滤
# ══════════════════════════════════════════════

def filter_models_by_type(model_remaining: dict[str, float], role_type: str) -> dict[str, float]:
    """根据角色类型过滤合适的模型.

    Args:
        model_remaining: {模型名: 剩余配额}
        role_type: 角色类型 (text, coder, image, long, summary, assistant)

    Returns:
        过滤后的 {模型名: 剩余配额}
    """
    if role_type == "coder":
        # 编程模型：强制使用 coder 模型
        filtered = {k: v for k, v in model_remaining.items()
                    if "coder" in k.lower()}
        if filtered:
            return filtered
        print(f"  [WARNING] 未找到coder模型，将使用通用模型")
    elif role_type == "image" or role_type == "vision":
        # 视觉模型：强制使用 vl (vision-language) 或 qvq 模型
        filtered = {k: v for k, v in model_remaining.items()
                    if "vl" in k.lower() or "vision" in k.lower() or k.startswith("qvq")}
        if filtered:
            return filtered
        print(f"  [WARNING] 未找到视觉模型，将使用通用模型")
    elif role_type == "long" or role_type == "long_context":
        # 长上下文模型：强制使用 long 模型
        filtered = {k: v for k, v in model_remaining.items()
                    if "long" in k.lower()}
        if filtered:
            return filtered
        print(f"  [WARNING] 未找到长上下文模型，将使用通用模型")
    elif role_type == "summary":
        # 摘要模型：优先 turbo（快速），其次是 flash
        filtered = {k: v for k, v in model_remaining.items()
                    if "turbo" in k.lower() or "flash" in k.lower()}
        if filtered:
            return filtered

    # 默认返回所有模型
    return model_remaining


def pick_best(model_remaining: dict[str, float], current: str, role_type: str = "text") -> str | None:
    """返回剩余 token 最多的模型名（若已是最好则返回 None）.

    Args:
        model_remaining: {模型名: 剩余配额}
        current: 当前使用的模型名
        role_type: 角色类型，用于过滤合适的模型

    Returns:
        最佳模型名，如果当前已经是最佳则返回 None
    """
    # 根据角色类型过滤合适的模型
    filtered = filter_models_by_type(model_remaining, role_type)

    if not filtered:
        return None

    best = max(filtered, key=filtered.get)
    return None if best == current else best


def update_allowed_models(cfg: dict, quota_data: dict):
    """allowed_models：
    1. 只保留在quota.json中真实存在且配额>0的模型
    2. 每个系列只保留配额最多的版本
    3. 自动添加quota.json中高配额的模型
    """
    allowed = cfg.get("allowed_models", [])
    if not allowed:
        return

    # 提取所有有配额的模型
    all_rem = extract_remaining(quota_data)

    if not all_rem:
        print("[WARNING] 未找到任何有配额的模型，保留原有allowed_models")
        return

    PREFIXES = ["qwen3.5", "qwen3.6", "qwen3", "qwen-coder", "qwen-vl", "qvq", "qwen", "deepseek", "kimi", "glm", "llama"]

    def get_series(model: str) -> str:
        for p in PREFIXES:
            if model.startswith(p):
                return p
        return model.split("-")[0]

    # 按系列分组，找出每个系列配额最多的模型
    series_best: dict[str, tuple[str, float]] = {}  # {series: (best_model, quota)}
    for m, rem in all_rem.items():
        s = get_series(m)
        if s not in series_best or rem > series_best[s][1]:
            series_best[s] = (m, rem)

    # 新的allowed_models列表
    new_allowed = []

    # 1. 保留原有模型中存在的且有配额的
    for m in allowed:
        if m in all_rem and all_rem[m] > 0:
            new_allowed.append(m)

    # 2. 添加每个系列中配额最多的模型（如果还未添加）
    for series, (best_model, quota) in series_best.items():
        if quota > 0 and best_model not in new_allowed:
            new_allowed.append(best_model)

    # 3. 排序：按配额降序
    new_allowed.sort(key=lambda m: all_rem.get(m, 0), reverse=True)

    cfg["allowed_models"] = new_allowed

    # 打印统计信息
    print(f"[INFO] allowed_models 更新: {len(allowed)} -> {len(new_allowed)}")
    print(f"[INFO] 新增模型: {[m for m in new_allowed if m not in allowed]}")
    print(f"[INFO] 移除模型: {[m for m in allowed if m not in new_allowed]}")


# ══════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="根据 DashScope 配额自动替换 llm_config.yaml 模型")
    parser.add_argument("quota_file", help="配额 JSON 文件（支持标准 JSON / JSON Lines）")
    parser.add_argument("--config", "-c", default="config/llm_config.yaml",
                        help="llm_config.yaml 路径（默认: config/llm_config.yaml）")
    parser.add_argument("--output", "-o", default=None,
                        help="输出文件路径（默认: 不写入，仅 dry-run）")
    parser.add_argument("--inplace", "-i", action="store_true",
                        help="原地修改（自动备份为 .bak）")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="只打印方案，不写入")
    args = parser.parse_args()

    # 加载
    quota_data = load_quota_json(args.quota_file)
    cfg = load_config(args.config)
    print(f"[INFO] quota : {args.quota_file}")
    print(f"[INFO] config : {args.config}")

    # 分析替换方案
    changes = []
    for role_path, (role_type, _) in ROLE_CATEGORY_MAP.items():
        current = get_model(cfg, role_path)

        # 提取所有模型配额
        mrem = extract_remaining(quota_data)

        # 根据角色类型选择最佳模型
        rt = role_type or "text"
        best = pick_best(mrem, current, rt)
        if best:
            changes.append({
                "role": ROLE_DISPLAY.get(role_path, role_path),
                "role_type": rt,
                "current": current,
                "current_rem": mrem.get(current, 0),
                "best": best,
                "best_rem": mrem.get(best, 0),
            })

    # 打印
    print("\n" + "=" * 85)
    print(f"{'Role':<35} {'Type':<12} {'Current':<20} -> {'Best':<20} {'Tokens':>12}")
    print("=" * 85)
    if not changes:
        print(f"{'  (no replacement needed)':<35}")
    else:
        for c in sorted(changes, key=lambda x: x["best_rem"] or 0, reverse=True):
            cur_rem = f"{c['current_rem']:,.0f}" if c["current_rem"] else "0"
            best_rem = f"{c['best_rem']:,.0f}" if c["best_rem"] else "0"
            print(f"{c['role']:<35} {c['role_type']:<12} {c['current']:<20} -> {c['best']:<20} {best_rem:>12}  (now: {cur_rem})")
    print("=" * 85)

    if args.dry_run:
        print("[dry-run] 未写入文件.\n"
              "  inplace : python update_llm_by_quota.py quota.json --inplace\n"
              "  to file : python update_llm_by_quota.py quota.json -o config/llm_config_new.yaml")
        return

    if not (args.inplace or args.output):
        print("[INFO] 未指定 --inplace / --output，默认 dry-run.\n"
              "       加 --dry-run（默认）或 --inplace / --output 来控制行为.")
        return

    # 写入
    for role_path, (role_type, _) in ROLE_CATEGORY_MAP.items():
        current = get_model(cfg, role_path)
        mrem = extract_remaining(quota_data)
        best = pick_best(mrem, current, role_type or "text")
        if best:
            set_model(cfg, role_path, best)

    update_allowed_models(cfg, quota_data)

    if args.inplace:
        backup = args.config + ".bak"
        shutil.copy2(args.config, backup)
        dump_config(cfg, args.config)
        print(f"[DONE] inplace: {args.config}")
        print(f"       backup : {backup}")
    else:
        dump_config(cfg, args.output)
        print(f"[DONE] written: {args.output}")


if __name__ == "__main__":
    main()
