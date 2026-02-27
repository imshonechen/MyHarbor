#!/usr/bin/env python3
"""
MyHarbor CLI 管理脚本
用于管理员凭证恢复和基本运维操作
"""
from __future__ import annotations

import sys
from argparse import ArgumentParser

from sqlalchemy import select, update

from app.database import SessionLocal
from app.models import SiteConfig
from app.utils.security import hash_password


def get_config_value(key: str) -> str | None:
    """获取配置值"""
    with SessionLocal() as db:
        stmt = select(SiteConfig).where(SiteConfig.key == key)
        row = db.execute(stmt).scalar_one_or_none()
        return row.value if row else None


def set_config_value(key: str, value: str) -> None:
    """设置配置值"""
    with SessionLocal() as db:
        stmt = select(SiteConfig).where(SiteConfig.key == key)
        row = db.execute(stmt).scalar_one_or_none()

        if row:
            stmt = update(SiteConfig).where(SiteConfig.key == key).values(value=value)
            db.execute(stmt)
        else:
            db.add(SiteConfig(key=key, value=value))

        db.commit()


def reset_admin() -> None:
    """重置管理员用户名和密码为默认值"""
    try:
        set_config_value("admin_username", "admin")
        set_config_value("admin_password", hash_password("admin123"))
        print("[OK] 管理员账号已重置为默认值")
        print("  用户名: admin")
        print("  密码: admin123")
        print("\n[WARNING] 请尽快登录后台修改默认密码！")
    except Exception as e:
        print(f"[ERROR] 重置失败: {e}", file=sys.stderr)
        sys.exit(1)


def show_admin() -> None:
    """查看当前管理员用户名"""
    try:
        username = get_config_value("admin_username")
        if username:
            print(f"当前管理员用户名: {username}")
        else:
            print("[ERROR] 未找到管理员配置", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}", file=sys.stderr)
        sys.exit(1)


def show_route() -> None:
    """查看当前后台安全路由码"""
    try:
        import os

        route_code = get_config_value("admin_route_code")
        if route_code:
            # 从环境变量获取端口号，默认为 24041
            port = os.environ.get("APP_PORT", "24041")

            print(f"当前后台路由码: {route_code}")
            print(f"后台访问地址: http://localhost:{port}/{route_code}")
        else:
            print("[ERROR] 未找到路由码配置", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}", file=sys.stderr)
        sys.exit(1)


def set_admin(username: str, password: str) -> None:
    """设置管理员凭证"""
    try:
        if not username or not password:
            print("[ERROR] 用户名和密码不能为空", file=sys.stderr)
            sys.exit(1)

        if len(username) < 3:
            print("[ERROR] 用户名长度至少为 3 个字符", file=sys.stderr)
            sys.exit(1)

        if len(password) < 6:
            print("[ERROR] 密码长度至少为 6 个字符", file=sys.stderr)
            sys.exit(1)

        set_config_value("admin_username", username)
        set_config_value("admin_password", hash_password(password))
        print("[OK] 管理员凭证已更新")
        print(f"  用户名: {username}")
        print("  密码: ********")
    except Exception as e:
        print(f"[ERROR] 设置失败: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = ArgumentParser(
        description="MyHarbor CLI 管理脚本",
        epilog="示例: python manage.py reset-admin"
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # reset-admin 命令
    subparsers.add_parser(
        "reset-admin",
        help="重置管理员用户名和密码为默认值 (admin/admin123)"
    )

    # show-admin 命令
    subparsers.add_parser(
        "show-admin",
        help="查看当前管理员用户名"
    )

    # show-route 命令
    subparsers.add_parser(
        "show-route",
        help="查看当前后台安全路由码"
    )

    # set-admin 命令
    set_admin_parser = subparsers.add_parser(
        "set-admin",
        help="设置管理员凭证"
    )
    set_admin_parser.add_argument(
        "--username",
        required=True,
        help="管理员用户名 (至少 3 个字符)"
    )
    set_admin_parser.add_argument(
        "--password",
        required=True,
        help="管理员密码 (至少 6 个字符)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # 执行对应命令
    if args.command == "reset-admin":
        reset_admin()
    elif args.command == "show-admin":
        show_admin()
    elif args.command == "show-route":
        show_route()
    elif args.command == "set-admin":
        set_admin(args.username, args.password)


if __name__ == "__main__":
    main()
