#!/usr/bin/env python3
"""
测试站点创建接口的脚本
用于调试 422 错误
"""

import sys
import json
from app.routers.sites import SiteCreateRequest
from pydantic import ValidationError

def test_payload(payload_dict):
    """测试给定的 payload 是否能通过验证"""
    print(f"\n{'='*60}")
    print("测试 Payload:")
    print(json.dumps(payload_dict, indent=2, ensure_ascii=False))
    print(f"{'='*60}")

    try:
        result = SiteCreateRequest(**payload_dict)
        print("✓ 验证成功!")
        print("\n解析后的数据:")
        print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
        return True
    except ValidationError as e:
        print("✗ 验证失败!")
        print("\n错误详情:")
        for error in e.errors():
            print(f"  - 字段: {error['loc']}")
            print(f"    类型: {error['type']}")
            print(f"    消息: {error['msg']}")
            if 'input' in error:
                print(f"    输入: {error['input']}")
        return False

# 测试用例
test_cases = [
    {
        "name": "测试用例 1: 完整数据",
        "payload": {
            "name": "Test Site",
            "url": "https://example.com",
            "logo": "https://example.com/logo.png",
            "description": "Test description",
            "tags": ["tag1", "tag2"],
            "is_public": True,
            "sort_order": 10
        }
    },
    {
        "name": "测试用例 2: 空 tags 数组",
        "payload": {
            "name": "Test Site",
            "url": "https://example.com",
            "logo": None,
            "description": None,
            "tags": [],
            "is_public": True,
            "sort_order": 9999
        }
    },
    {
        "name": "测试用例 3: tags 为 None",
        "payload": {
            "name": "Test Site",
            "url": "https://example.com",
            "logo": None,
            "description": None,
            "tags": None,
            "is_public": True,
            "sort_order": 9999
        }
    },
    {
        "name": "测试用例 4: 缺少 tags 字段",
        "payload": {
            "name": "Test Site",
            "url": "https://example.com",
            "logo": None,
            "description": None,
            "is_public": True,
            "sort_order": 9999
        }
    },
    {
        "name": "测试用例 5: 空字符串字段",
        "payload": {
            "name": "Test Site",
            "url": "https://example.com",
            "logo": "",
            "description": "",
            "tags": [],
            "is_public": True,
            "sort_order": 9999
        }
    },
    {
        "name": "测试用例 6: 无效 URL",
        "payload": {
            "name": "Test Site",
            "url": "not-a-url",
            "logo": None,
            "description": None,
            "tags": [],
            "is_public": True,
            "sort_order": 9999
        }
    },
    {
        "name": "测试用例 7: 缺少必填字段 name",
        "payload": {
            "url": "https://example.com",
            "logo": None,
            "description": None,
            "tags": [],
            "is_public": True,
            "sort_order": 9999
        }
    },
    {
        "name": "测试用例 8: 缺少必填字段 url",
        "payload": {
            "name": "Test Site",
            "logo": None,
            "description": None,
            "tags": [],
            "is_public": True,
            "sort_order": 9999
        }
    }
]

if __name__ == "__main__":
    print("站点创建接口验证测试")
    print("="*60)

    passed = 0
    failed = 0

    for test_case in test_cases:
        print(f"\n\n{test_case['name']}")
        if test_payload(test_case['payload']):
            passed += 1
        else:
            failed += 1

    print(f"\n\n{'='*60}")
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print(f"{'='*60}")
