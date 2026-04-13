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
    return None


def extract_remaining(quota_data: dict, category: str | None = None) -> dict[str, float]:
    """提取模型剩余 token，{model_name: remaining}."""
    result: dict[str, float] = {}

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
            if name and rem is not None:
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
# 替换逻辑
# ══════════════════════════════════════════════

def pick_best(model_remaining: dict[str, float], current: str) -> str | None:
    """返回剩余 token 最多的模型名（若已是最好则返回 None）."""
    if not model_remaining:
        return None
    best = max(model_remaining, key=model_remaining.get)
    return None if best == current else best


def update_allowed_models(cfg: dict, quota_data: dict):
    """allowed_models：每个系列只保留剩余最多的版本."""
    allowed = cfg.get("allowed_models", [])
    if not allowed:
        return

    all_rem = extract_remaining(quota_data)

    PREFIXES = ["qwen3.5", "qwen3", "qwen-coder", "qwen-vl", "qvq", "qwen", "deepseek", "kimi"]

    def get_series(model: str) -> str:
        for p in PREFIXES:
            if model.startswith(p):
                return p
        return model.split("-")[0]

    series_best: dict[str, float] = {}
    for m, rem in all_rem.items():
        s = get_series(m)
        series_best[s] = max(series_best.get(s, 0), rem)

    new_allowed = []
    for m in allowed:
        s = get_series(m)
        rem = all_rem.get(m, 0)
        best = series_best.get(s, 0)
        # 保留：剩余 >= 系列最佳的 50%，或者是最佳本身
        if rem >= best * 0.5 or rem == best:
            new_allowed.append(m)

    cfg["allowed_models"] = new_allowed


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
    for role_path, (cat, _) in ROLE_CATEGORY_MAP.items():
        current = get_model(cfg, role_path)
        if cat:
            mrem = extract_remaining({cat: quota_data.get(cat, {})})
        else:
            mrem = extract_remaining(quota_data)

        best = pick_best(mrem, current)
        if best:
            changes.append({
                "role": ROLE_DISPLAY.get(role_path, role_path),
                "current": current,
                "current_rem": mrem.get(current),
                "best": best,
                "best_rem": mrem.get(best),
            })

    # 打印
    print("\n" + "=" * 75)
    print(f"{'Role':<40} {'Current':<20} -> {'Best':<20} {'Remain'}")
    print("=" * 75)
    if not changes:
        print(f"{'  (no replacement needed)':<40}")
    else:
        for c in sorted(changes, key=lambda x: x["best_rem"] or 0, reverse=True):
            cur = f"{c['current_rem']:.0f}" if c["current_rem"] else "?"
            print(f"{c['role']:<40} {c['current']:<20} -> {c['best']:<20} {c['best_rem']:>10.0f}  (now: {cur})")
    print("=" * 75)

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
    for role_path, (cat, _) in ROLE_CATEGORY_MAP.items():
        current = get_model(cfg, role_path)
        if cat:
            mrem = extract_remaining({cat: quota_data.get(cat, {})})
        else:
            mrem = extract_remaining(quota_data)
        best = pick_best(mrem, current)
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
