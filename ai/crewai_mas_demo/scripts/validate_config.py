#!/usr/bin/env python3
"""
配置验证脚本

检查项目配置是否正确，特别是环境变量是否设置。
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple


class ConfigValidator:
    """配置验证器"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_env_file(self) -> bool:
        """验证.env文件是否存在"""
        env_file = Path.cwd() / ".env"
        if not env_file.exists():
            self.errors.append(
                ".env文件不存在。请参考.env.example文件创建.env文件。"
            )
            return False
        return True

    def validate_required_env_vars(self) -> bool:
        """验证必需的环境变量"""
        required_vars = {
            "QWEN_API_KEY": "阿里云API密钥",
            "OPENROUTER_API_KEY": "OpenRouter API密钥（可选）",
        }

        missing_vars = []
        for var_name, description in required_vars.items():
            value = os.getenv(var_name)
            if not value:
                missing_vars.append(f"  - {var_name}: {description}")

        if missing_vars:
            self.errors.append(
                "缺少必需的环境变量:\n" + "\n".join(missing_vars)
            )
            return False
        return True

    def validate_api_key_format(self) -> bool:
        """验证API key格式"""
        api_key = os.getenv("QWEN_API_KEY")
        if not api_key:
            return True

        if not api_key.startswith("sk-"):
            self.warnings.append(
                f"QWEN_API_KEY格式可能不正确：{api_key[:10]}..."
            )

        if len(api_key) < 20:
            self.errors.append(
                f"QWEN_API_KEY长度太短：{len(api_key)}字符"
            )
            return False

        return True

    def validate_gitignore(self) -> bool:
        """验证.gitignore配置"""
        gitignore_path = Path.cwd() / ".gitignore"
        if not gitignore_path.exists():
            self.warnings.append(".gitignore文件不存在")
            return False

        gitignore_content = gitignore_path.read_text()
        required_patterns = [
            ".env",
            "*.log",
            "*.bak",
            "*.key",
        ]

        missing_patterns = []
        for pattern in required_patterns:
            if pattern not in gitignore_content:
                missing_patterns.append(pattern)

        if missing_patterns:
            self.warnings.append(
                f".gitignore缺少以下模式: {', '.join(missing_patterns)}"
            )
            return False

        return True

    def validate_log_files(self) -> bool:
        """检查是否有包含敏感信息的日志文件"""
        log_files = [
            "m4-25/agent_dev.log",
            "m4-23/agent.log",
            "m3-21/agent_test.log",
            "m3-21/agent.log",
            "m3-21/run_output.log",
        ]

        sensitive_patterns = [
            "sk-",
            "api_key",
            "API_KEY",
            "secret",
            "password",
        ]

        found_sensitive = []
        for log_file in log_files:
            log_path = Path.cwd() / log_file
            if not log_path.exists():
                continue

            try:
                content = log_path.read_text()
                for pattern in sensitive_patterns:
                    if pattern.lower() in content.lower():
                        found_sensitive.append(log_file)
                        break
            except Exception:
                pass

        if found_sensitive:
            self.warnings.append(
                "以下日志文件可能包含敏感信息，建议删除:\n" +
                "\n".join(f"  - {log}" for log in found_sensitive)
            )
            return False

        return True

    def validate_tracked_files(self) -> bool:
        """检查是否有敏感文件被git跟踪"""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "ls-files"],
                capture_output=True,
                text=True,
                check=True,
            )
            tracked_files = result.stdout.splitlines()

            sensitive_tracked = [
                f for f in tracked_files
                if any(pattern in f for pattern in [
                    ".env",
                    "*.log",
                    "*.bak",
                    "*.key",
                    "secret",
                ])
            ]

            if sensitive_tracked:
                self.errors.append(
                    "以下敏感文件被git跟踪（应从git中移除）:\n" +
                    "\n".join(f"  - {f}" for f in sensitive_tracked)
                )
                return False

        except subprocess.CalledProcessError:
            self.warnings.append("无法检查git跟踪文件（不是git仓库）")

        return True

    def run_all_validations(self) -> Tuple[bool, bool]:
        """
        运行所有验证

        Returns:
            (has_errors, has_warnings)
        """
        print("开始配置验证...\n")

        # 加载.env文件
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)

        # 运行各项验证
        self.validate_env_file()
        self.validate_required_env_vars()
        self.validate_api_key_format()
        self.validate_gitignore()
        self.validate_log_files()
        self.validate_tracked_files()

        # 输出结果
        if self.warnings:
            print("⚠️  警告:")
            for warning in self.warnings:
                print(f"  {warning}\n")

        if self.errors:
            print("❌ 错误:")
            for error in self.errors:
                print(f"  {error}\n")
        else:
            print("✅ 所有配置验证通过！")

        return (len(self.errors) > 0, len(self.warnings) > 0)


def main():
    """主函数"""
    validator = ConfigValidator()
    has_errors, has_warnings = validator.run_all_validations()

    if has_errors:
        sys.exit(1)
    elif has_warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
