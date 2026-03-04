"""
创建用例管理模块的测试数据
运行方式: cd backend && python3 scripts/create_testcase_testdata.py

注意: 枚举值必须与设计文档 docs/plans/2026-03-02-testcase-module-design.md 一致
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.services.testcase_service import TestCaseService
from app.schemas.testcase import TestCaseGroupCreate, TestCaseCreate


def create_testdata():
    db = SessionLocal()
    try:
        service = TestCaseService(db)

        # 创建根分组
        print("创建用例分组...")

        user_module = service.create_group(
            TestCaseGroupCreate(name="用户模块", order=1),
            created_by="admin"
        )
        print(f"  - 创建分组: {user_module.name}")

        order_module = service.create_group(
            TestCaseGroupCreate(name="订单模块", order=2),
            created_by="admin"
        )
        print(f"  - 创建分组: {order_module.name}")

        payment_module = service.create_group(
            TestCaseGroupCreate(name="支付模块", order=3),
            created_by="admin"
        )
        print(f"  - 创建分组: {payment_module.name}")

        # 创建子分组
        login_group = service.create_group(
            TestCaseGroupCreate(name="登录功能", parent_id=user_module.id, order=1),
            created_by="admin"
        )
        print(f"  - 创建子分组: {login_group.name}")

        register_group = service.create_group(
            TestCaseGroupCreate(name="注册功能", parent_id=user_module.id, order=2),
            created_by="admin"
        )
        print(f"  - 创建子分组: {register_group.name}")

        profile_group = service.create_group(
            TestCaseGroupCreate(name="个人中心", parent_id=user_module.id, order=3),
            created_by="admin"
        )
        print(f"  - 创建子分组: {profile_group.name}")

        # 创建用例
        # 注意: 枚举值必须使用设计文档定义的中文值
        print("\n创建测试用例...")

        test_cases = [
            # 登录用例
            {
                "group_id": login_group.id,
                "title": "用户使用手机号和密码登录",
                "case_type": "功能测试",  # 设计文档 4.2
                "platform": "Web",         # 设计文档 4.2
                "priority": "P0",          # 设计文档 4.2
                "status": "草稿",          # 设计文档 5.2
                "is_core": True,
                "owner": "admin",
                "developer": "张三",
                "page_url": "https://example.com/login",
                "preconditions": "1. 用户已注册\n2. 用户账号状态正常",
                "steps": json.dumps([
                    {"step": "打开登录页面", "expected": "页面正常显示"},
                    {"step": "输入已注册的手机号", "expected": "手机号输入框显示输入内容"},
                    {"step": "输入正确的密码", "expected": "密码输入框显示为密文"},
                    {"step": "点击登录按钮", "expected": "登录成功，跳转到首页"}
                ]),
                "remark": "这是一个核心用例，需要在每次发版前执行",
                "tags": json.dumps(["冒烟", "P0"])
            },
            {
                "group_id": login_group.id,
                "title": "用户使用错误密码登录失败",
                "case_type": "功能测试",
                "platform": "Web",
                "priority": "P2",
                "status": "草稿",
                "is_core": False,
                "owner": "admin",
                "preconditions": "用户已注册",
                "steps": json.dumps([
                    {"step": "打开登录页面", "expected": "页面正常显示"},
                    {"step": "输入已注册的手机号", "expected": "手机号输入框显示输入内容"},
                    {"step": "输入错误的密码", "expected": "密码输入框显示为密文"},
                    {"step": "点击登录按钮", "expected": "显示密码错误提示"}
                ]),
                "tags": json.dumps(["回归"])
            },
            {
                "group_id": login_group.id,
                "title": "用户使用验证码登录",
                "case_type": "功能测试",
                "platform": "RN",  # RN (Android+H5)
                "priority": "P0",
                "status": "草稿",
                "is_core": True,
                "owner": "admin",
                "preconditions": "用户已注册",
                "steps": json.dumps([
                    {"step": "打开登录页面", "expected": "页面正常显示"},
                    {"step": "切换到验证码登录方式", "expected": "显示验证码输入框"},
                    {"step": "输入手机号并获取验证码", "expected": "验证码发送成功"},
                    {"step": "输入验证码并点击登录", "expected": "登录成功，跳转到首页"}
                ]),
                "tags": json.dumps(["冒烟", "P0"])
            },
            # 注册用例
            {
                "group_id": register_group.id,
                "title": "新用户使用手机号注册",
                "case_type": "功能测试",
                "platform": "Web",
                "priority": "P0",
                "status": "草稿",
                "is_core": True,
                "owner": "admin",
                "developer": "李四",
                "preconditions": "手机号未注册过",
                "steps": json.dumps([
                    {"step": "打开注册页面", "expected": "页面正常显示"},
                    {"step": "输入未注册的手机号", "expected": "手机号输入框显示输入内容"},
                    {"step": "获取并输入验证码", "expected": "验证码输入成功"},
                    {"step": "设置密码", "expected": "密码设置成功"},
                    {"step": "点击注册按钮", "expected": "注册成功，跳转到首页"}
                ]),
                "tags": json.dumps(["冒烟", "P0"])
            },
            {
                "group_id": register_group.id,
                "title": "已注册手机号无法重复注册",
                "case_type": "功能测试",
                "platform": "H5",
                "priority": "P2",
                "status": "草稿",
                "is_core": False,
                "owner": "admin",
                "preconditions": "手机号已注册",
                "steps": json.dumps([
                    {"step": "打开注册页面", "expected": "页面正常显示"},
                    {"step": "输入已注册的手机号", "expected": "手机号输入框显示输入内容"},
                    {"step": "点击获取验证码", "expected": "提示手机号已注册"}
                ]),
                "tags": json.dumps(["回归"])
            },
            # 个人中心用例
            {
                "group_id": profile_group.id,
                "title": "用户修改昵称",
                "case_type": "功能测试",
                "platform": "小程序",
                "priority": "P3",
                "status": "草稿",
                "is_core": False,
                "owner": "admin",
                "preconditions": "用户已登录",
                "steps": json.dumps([
                    {"step": "进入个人中心", "expected": "显示个人信息"},
                    {"step": "点击编辑按钮", "expected": "进入编辑模式"},
                    {"step": "修改昵称", "expected": "昵称输入框显示新昵称"},
                    {"step": "点击保存", "expected": "保存成功，显示新昵称"}
                ]),
                "tags": json.dumps([])
            },
            {
                "group_id": profile_group.id,
                "title": "用户修改头像",
                "case_type": "功能测试",
                "platform": "服务端",
                "priority": "P3",
                "status": "草稿",
                "is_core": False,
                "owner": "admin",
                "developer": "王五",
                "preconditions": "用户已登录",
                "steps": json.dumps([
                    {"step": "进入个人中心", "expected": "显示个人信息"},
                    {"step": "点击头像", "expected": "弹出选择方式"},
                    {"step": "选择相册图片", "expected": "图片选择器打开"},
                    {"step": "裁剪图片", "expected": "裁剪完成"},
                    {"step": "确认上传", "expected": "头像更新成功"}
                ]),
                "tags": json.dumps([])
            },
            # 订单模块用例
            {
                "group_id": order_module.id,
                "title": "用户创建订单",
                "case_type": "功能测试",
                "platform": "Web",
                "priority": "P0",
                "status": "草稿",
                "is_core": True,
                "owner": "admin",
                "preconditions": "1. 用户已登录\n2. 购物车有商品",
                "steps": json.dumps([
                    {"step": "进入购物车", "expected": "显示购物车商品列表"},
                    {"step": "选择要购买的商品", "expected": "商品被选中"},
                    {"step": "点击结算", "expected": "跳转到订单确认页"},
                    {"step": "选择收货地址", "expected": "地址选择成功"},
                    {"step": "点击提交订单", "expected": "订单创建成功"}
                ]),
                "tags": json.dumps(["冒烟", "P0"])
            },
            {
                "group_id": order_module.id,
                "title": "用户取消订单",
                "case_type": "功能测试",
                "platform": "RN",
                "priority": "P2",
                "status": "草稿",
                "is_core": False,
                "owner": "admin",
                "preconditions": "1. 用户已登录\n2. 存在待支付订单",
                "steps": json.dumps([
                    {"step": "进入订单列表", "expected": "显示订单列表"},
                    {"step": "点击待支付订单的取消按钮", "expected": "弹出取消确认框"},
                    {"step": "确认取消", "expected": "订单状态变为已取消"}
                ]),
                "tags": json.dumps(["回归"])
            },
            # 支付模块用例
            {
                "group_id": payment_module.id,
                "title": "用户使用支付宝支付",
                "case_type": "功能测试",
                "platform": "Web",
                "priority": "P0",
                "status": "草稿",
                "is_core": True,
                "owner": "admin",
                "preconditions": "1. 用户已登录\n2. 订单已创建",
                "steps": json.dumps([
                    {"step": "在订单详情页点击支付", "expected": "显示支付方式选择"},
                    {"step": "选择支付宝支付", "expected": "跳转到支付宝支付页"},
                    {"step": "完成支付", "expected": "支付成功，订单状态更新"}
                ]),
                "tags": json.dumps(["冒烟", "P0"])
            },
            {
                "group_id": payment_module.id,
                "title": "用户使用微信支付",
                "case_type": "功能测试",
                "platform": "RN",
                "priority": "P0",
                "status": "草稿",
                "is_core": True,
                "owner": "admin",
                "preconditions": "1. 用户已登录\n2. 订单已创建",
                "steps": json.dumps([
                    {"step": "在订单详情页点击支付", "expected": "显示支付方式选择"},
                    {"step": "选择微信支付", "expected": "显示微信支付二维码"},
                    {"step": "扫码完成支付", "expected": "支付成功，订单状态更新"}
                ]),
                "tags": json.dumps(["冒烟", "P0"])
            },
            # 性能测试用例
            {
                "group_id": login_group.id,
                "title": "登录接口响应时间测试",
                "case_type": "性能测试",
                "platform": "服务端",
                "priority": "P1",
                "status": "草稿",
                "is_core": False,
                "owner": "admin",
                "developer": "赵六",
                "preconditions": "服务正常运行",
                "steps": json.dumps([
                    {"step": "使用压测工具发起100并发请求", "expected": "所有请求正常响应"},
                    {"step": "检查响应时间统计", "expected": "P99 < 500ms"},
                    {"step": "检查错误率", "expected": "错误率 < 0.1%"}
                ]),
                "tags": json.dumps(["性能"])
            },
            # 安全测试用例
            {
                "group_id": login_group.id,
                "title": "登录SQL注入测试",
                "case_type": "安全测试",
                "platform": "服务端",
                "priority": "P0",
                "status": "草稿",
                "is_core": True,
                "owner": "admin",
                "preconditions": "服务正常运行",
                "steps": json.dumps([
                    {"step": "在用户名输入框输入SQL注入语句", "expected": "输入被正确转义"},
                    {"step": "点击登录", "expected": "登录失败，但不报错"},
                    {"step": "检查数据库日志", "expected": "无异常SQL执行"}
                ]),
                "tags": json.dumps(["安全", "P0"])
            },
            # 兼容性测试用例
            {
                "group_id": login_group.id,
                "title": "登录页面浏览器兼容性测试",
                "case_type": "兼容性测试",
                "platform": "Web",
                "priority": "P1",
                "status": "草稿",
                "is_core": False,
                "owner": "admin",
                "preconditions": "多种浏览器环境准备就绪",
                "steps": json.dumps([
                    {"step": "在Chrome浏览器测试登录", "expected": "功能正常"},
                    {"step": "在Firefox浏览器测试登录", "expected": "功能正常"},
                    {"step": "在Safari浏览器测试登录", "expected": "功能正常"},
                    {"step": "在Edge浏览器测试登录", "expected": "功能正常"}
                ]),
                "tags": json.dumps(["兼容性"])
            },
            # 用户体验测试用例
            {
                "group_id": profile_group.id,
                "title": "个人中心页面加载体验测试",
                "case_type": "用户体验测试",
                "platform": "H5",
                "priority": "P2",
                "status": "草稿",
                "is_core": False,
                "owner": "admin",
                "preconditions": "用户已登录",
                "steps": json.dumps([
                    {"step": "清除浏览器缓存", "expected": "缓存清除成功"},
                    {"step": "访问个人中心页面", "expected": "页面在2秒内加载完成"},
                    {"step": "检查页面交互流畅度", "expected": "无明显卡顿"}
                ]),
                "tags": json.dumps(["体验"])
            },
            # 其他类型用例
            {
                "group_id": order_module.id,
                "title": "订单数据导出功能测试",
                "case_type": "其他",
                "platform": "Web",
                "priority": "P4",
                "status": "草稿",
                "is_core": False,
                "owner": "admin",
                "preconditions": "有订单数据",
                "steps": json.dumps([
                    {"step": "进入订单管理页面", "expected": "显示订单列表"},
                    {"step": "点击导出按钮", "expected": "弹出导出选项"},
                    {"step": "选择导出格式为Excel", "expected": "开始导出"},
                    {"step": "下载导出文件", "expected": "文件下载成功"}
                ]),
                "tags": json.dumps([])
            },
        ]

        for case_data in test_cases:
            case = service.create_case(
                TestCaseCreate(**case_data),
                created_by="admin"
            )
            print(f"  - 创建用例: {case.code} - {case.title}")

        print(f"\n测试数据创建完成!")
        print(f"  分组数量: 6")
        print(f"  用例数量: {len(test_cases)}")

    finally:
        db.close()


if __name__ == "__main__":
    create_testdata()
