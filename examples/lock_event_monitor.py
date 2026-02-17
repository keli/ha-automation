#!/usr/bin/env python3
"""
门锁事件监听和测试脚本
用于识别门锁的各种开锁方式、位置和动作的数值映射

使用方法:
    python lock_event_monitor.py

然后按照提示进行各种开锁操作，脚本会记录所有事件详情

注意：
    不同型号的小米门锁，其事件参数的数值映射可能不同。
    建议使用此脚本测试你的具体门锁型号，以获得准确的映射关系。
    已知的一个映射示例：
    - 操作位置: 1 = 门内手动（旋钮）, 2 = 门外
    - 锁动作: 1 = 上锁, 2 = 开锁
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ha_automation.client import HAClient
from ha_automation.device_discovery import DeviceDiscovery


# 测试步骤（通用版本，适配不同门锁型号）
# 注意：操作位置的值因门锁型号而异，以下为参考值
# 已知映射（某些型号）：操作位置 1=门内手动, 2=门外, 锁动作 1=上锁, 2=开锁
TEST_STEPS = [
    {
        "step": 1,
        "description": "🏠 请在【门外】使用【指纹识别】开锁",
        "expected": "操作位置=1或2, 操作方式=1或2, 锁动作=1或2"
    },
    {
        "step": 2,
        "description": "🔑 请在【门外】使用【密码】开锁",
        "expected": "操作位置=1或2, 操作方式=2或相关值, 锁动作=1或2"
    },
    {
        "step": 3,
        "description": "📱 请在【门外】使用【NFC卡片】开锁（如果支持）",
        "expected": "操作位置=1或2, 操作方式=3或相关值, 锁动作=1或2",
        "optional": True
    },
    {
        "step": 4,
        "description": "👤 请在【门外】使用【人脸识别】开锁（小米门锁4Pro支持）",
        "expected": "操作位置=1或2, 操作方式=?, 锁动作=1或2",
        "optional": True
    },
    {
        "step": 5,
        "description": "🫱 请在【门外】使用【掌静脉识别】开锁（小米门锁4Pro支持）",
        "expected": "操作位置=1或2, 操作方式=?, 锁动作=1或2",
        "optional": True
    },
    {
        "step": 6,
        "description": "🩸 请在【门外】使用【指静脉识别】开锁（部分高端型号支持）",
        "expected": "操作位置=1或2, 操作方式=?, 锁动作=1或2",
        "optional": True
    },
    {
        "step": 7,
        "description": "🚪 请在【门内】使用【旋钮/把手】开锁",
        "expected": "操作位置=1或2或3, 操作方式=13或相关值, 锁动作=1或2"
    },
    {
        "step": 8,
        "description": "📲 请在【门外】使用【手机APP蓝牙】开锁",
        "expected": "操作位置=1或2, 操作方式=5或12, 锁动作=1或2"
    },
    {
        "step": 9,
        "description": "🔑 请使用【机械钥匙】开锁（如果可以检测到）",
        "expected": "操作位置=1或2, 操作方式=4或相关值, 锁动作=1或2",
        "optional": True
    },
    {
        "step": 10,
        "description": "🔒 请在【门外】【上提反锁】",
        "expected": "操作位置=1或2或4, 操作方式=?, 锁动作=1或2"
    },
    {
        "step": 11,
        "description": "🏠 请在【门内】【旋钮上锁】",
        "expected": "操作位置=1或2或3, 操作方式=?, 锁动作=1或2"
    },
]


class LockEventMonitor:
    def __init__(self, lock_event_entity: str = None):
        self.client = HAClient()
        self.discovery = DeviceDiscovery(self.client)
        self.lock_event_entity = lock_event_entity
        self.last_state: Dict[str, Any] = {}
        self.events_log: List[Dict[str, Any]] = []
        self.current_step = 0

    def auto_detect_lock_event(self) -> str:
        """自动检测门锁事件实体"""
        print("\n🔍 正在自动检测门锁事件实体...")

        # 获取所有实体
        all_entities = self.discovery.discover_all()

        # 查找所有门锁相关的事件实体
        lock_events = [
            e for e in all_entities
            if e.entity_id.startswith('event.')
            and '门锁' in e.friendly_name
            and ('锁事件' in e.friendly_name
                 or 'lock_event' in e.entity_id.lower())
        ]

        if not lock_events:
            print("❌ 未找到门锁事件实体")
            print("💡 提示：请确保你的门锁已接入 Home Assistant")
            return None

        if len(lock_events) == 1:
            entity_id = lock_events[0].entity_id
            name = lock_events[0].friendly_name
            print(f"✅ 自动检测到门锁事件: {name}")
            print(f"   实体ID: {entity_id}")
            return entity_id

        # 多个门锁，让用户选择
        print(f"\n找到 {len(lock_events)} 个门锁事件实体:")
        for i, lock in enumerate(lock_events, 1):
            name = lock.friendly_name
            entity_id = lock.entity_id
            print(f"  {i}. {name} ({entity_id})")

        while True:
            try:
                choice = input("\n请选择门锁编号 (1-{}): ".format(len(lock_events)))
                idx = int(choice) - 1
                if 0 <= idx < len(lock_events):
                    return lock_events[idx].entity_id
                else:
                    print("❌ 无效的选择，请重新输入")
            except (ValueError, KeyboardInterrupt):
                print("\n❌ 取消选择")
                return None

    def get_current_state(self) -> Dict[str, Any]:
        """获取门锁事件的当前状态"""
        if not self.lock_event_entity:
            return {}
        try:
            state = self.client.get_states(self.lock_event_entity)
            return state
        except Exception as e:
            print(f"❌ 获取状态失败: {e}")
            return {}

    def format_event(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """格式化事件数据"""
        attrs = state.get('attributes', {})
        return {
            'timestamp': datetime.now().isoformat(),
            'state_time': state.get('state', ''),
            'operation_location': attrs.get('操作位置'),
            'operation_method': attrs.get('操作方式'),
            'lock_action': attrs.get('锁动作'),
            'operation_id': attrs.get('操作ID'),
            'unix_timestamp': attrs.get('当前时间（unix timestamp）'),
        }

    def print_event(self, event: Dict[str, Any], step: int = None):
        """打印事件信息"""
        print("\n" + "=" * 70)
        if step:
            print(f"✅ 检测到步骤 {step} 的开锁事件")
        else:
            print(f"📋 检测到新的门锁事件")
        print("=" * 70)
        print(f"⏰ 检测时间: {event['timestamp']}")
        print(f"📍 操作位置: {event['operation_location']}")
        print(f"🔑 操作方式: {event['operation_method']}")
        print(f"🔒 锁动作:   {event['lock_action']}")
        print(f"👤 操作ID:   {event['operation_id']}")
        print(f"🕐 门锁时间: {event['unix_timestamp']}")
        print("=" * 70)

    def save_to_file(self):
        """保存所有记录到文件"""
        log_file = Path(__file__).parent / "lock_events_log.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.events_log, f, ensure_ascii=False, indent=2)
        print(f"\n💾 日志已保存到: {log_file}")

    def print_summary(self):
        """打印测试摘要"""
        print("\n\n" + "=" * 70)
        print("📊 测试摘要")
        print("=" * 70)

        if not self.events_log:
            print("❌ 没有记录到任何事件")
            return

        print(f"\n总共记录了 {len(self.events_log)} 个事件:\n")

        for i, event in enumerate(self.events_log, 1):
            step_info = event.get('step', '未标记')
            desc = event.get('description', '未说明')
            print(f"\n事件 {i}: {desc}")
            print(f"  步骤: {step_info}")
            print(f"  操作位置: {event['operation_location']}")
            print(f"  操作方式: {event['operation_method']}")
            print(f"  锁动作: {event['lock_action']}")

        # 分析映射关系
        print("\n\n" + "=" * 70)
        print("🔍 数值映射分析")
        print("=" * 70)

        # 按操作位置分组
        locations = {}
        for event in self.events_log:
            loc = event['operation_location']
            if loc not in locations:
                locations[loc] = []
            locations[loc].append(event.get('description', ''))

        print("\n【操作位置】映射:")
        for loc, descs in sorted(locations.items()):
            print(f"  {loc} → {', '.join(set(descs))}")

        # 按操作方式分组
        methods = {}
        for event in self.events_log:
            method = event['operation_method']
            if method not in methods:
                methods[method] = []
            methods[method].append(event.get('description', ''))

        print("\n【操作方式】映射:")
        for method, descs in sorted(methods.items()):
            print(f"  {method} → {', '.join(set(descs))}")

        # 按锁动作分组
        actions = {}
        for event in self.events_log:
            action = event['lock_action']
            if action not in actions:
                actions[action] = []
            actions[action].append(event.get('description', ''))

        print("\n【锁动作】映射:")
        for action, descs in sorted(actions.items()):
            print(f"  {action} → {', '.join(set(descs))}")

        print("\n" + "=" * 70)

    async def monitor_loop(self):
        """主监听循环"""
        print("\n" + "=" * 70)
        print("🔐 门锁事件监听脚本 (支持小米智能门锁4Pro及其他型号)")
        print("=" * 70)
        print("\n本脚本会监听门锁的所有操作事件，并记录详细参数。")
        print("支持的识别方式：指纹、密码、NFC、人脸、掌静脉、指静脉等")
        print("按 Ctrl+C 可以随时停止监听。\n")

        # 自动检测或使用指定的门锁实体
        if not self.lock_event_entity:
            self.lock_event_entity = self.auto_detect_lock_event()

        if not self.lock_event_entity:
            print("\n❌ 无法确定门锁事件实体，退出")
            return

        print(f"\n监听实体: {self.lock_event_entity}")

        # 获取初始状态
        print("\n📡 正在连接到 Home Assistant...")
        self.last_state = self.get_current_state()

        if not self.last_state:
            print("❌ 无法连接到 Home Assistant，请检查配置")
            return

        print("✅ 连接成功！")

        # 显示当前状态
        current_event = self.format_event(self.last_state)
        print("\n当前门锁最后一次事件:")
        self.print_event(current_event)

        print("\n\n" + "=" * 70)
        print("🧪 开始测试流程")
        print("=" * 70)
        print("\n请按照以下步骤依次操作门锁，每次操作后等待几秒让脚本记录:")
        print("(标记为可选的步骤，如果你的门锁不支持可跳过)\n")

        for step in TEST_STEPS:
            optional_mark = " [可选]" if step.get('optional') else ""
            print(f"\n步骤 {step['step']}{optional_mark}: {step['description']}")
            print(f"   预期值: {step['expected']}")

        print("\n\n⏳ 如果你不想按步骤测试，也可以随意操作门锁，")
        print("   脚本会记录所有事件，之后我们可以手动标注。\n")
        print("💡 开始监听... (每3秒检查一次)\n")

        self.current_step = 0
        check_count = 0

        try:
            while True:
                await asyncio.sleep(3)
                check_count += 1

                # 每30秒提示一次
                if check_count % 10 == 0:
                    print(f"⏱️  监听中... (已记录 {len(self.events_log)} 个事件)")

                # 获取当前状态
                current_state = self.get_current_state()

                if not current_state:
                    continue

                # 检查状态是否变化
                current_time = current_state.get('state', '')
                last_time = self.last_state.get('state', '')

                if current_time != last_time:
                    # 检测到新事件
                    event = self.format_event(current_state)

                    # 尝试匹配当前步骤
                    self.current_step += 1
                    if self.current_step <= len(TEST_STEPS):
                        step_info = TEST_STEPS[self.current_step - 1]
                        event['step'] = self.current_step
                        event['description'] = step_info['description']
                        self.print_event(event, self.current_step)

                        # 询问是否继续
                        print(f"\n✅ 步骤 {self.current_step} 已记录")
                        if self.current_step < len(TEST_STEPS):
                            print(f"\n准备好后，请继续步骤 {self.current_step + 1}")
                    else:
                        event['step'] = f'额外-{self.current_step - len(TEST_STEPS)}'
                        event['description'] = '额外测试'
                        self.print_event(event)

                    self.events_log.append(event)
                    self.last_state = current_state

                    # 所有步骤完成
                    if self.current_step == len(TEST_STEPS):
                        print("\n\n🎉 所有测试步骤已完成！")
                        print("💡 如果需要额外测试，可以继续操作门锁")
                        print("   或按 Ctrl+C 结束并查看摘要\n")

        except KeyboardInterrupt:
            print("\n\n⏹️  停止监听...")

        finally:
            # 保存日志
            if self.events_log:
                self.save_to_file()
                self.print_summary()
            else:
                print("\n⚠️  没有记录到任何新事件")

            print("\n\n👋 监听结束\n")


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='门锁事件监听和测试工具 (支持小米智能门锁4Pro等多种型号)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 自动检测门锁
  python lock_event_monitor.py

  # 指定门锁实体ID
  python lock_event_monitor.py --entity event.xiaomi_cn_1183795032_s1_lock_event_e_2_1020

支持的识别方式:
  - 指纹识别
  - 密码
  - NFC卡片
  - 人脸识别 (小米门锁4Pro)
  - 掌静脉识别 (小米门锁4Pro)
  - 指静脉识别 (部分高端型号)
  - 手机蓝牙
  - 机械钥匙
        """
    )
    parser.add_argument(
        '--entity',
        help='门锁事件实体ID（不指定则自动检测）'
    )

    args = parser.parse_args()

    monitor = LockEventMonitor(lock_event_entity=args.entity)
    await monitor.monitor_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n退出程序")
        sys.exit(0)
