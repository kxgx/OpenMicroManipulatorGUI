"""
多语言功能测试脚本
"""

import sys
from i18n import get_translator, tr


def test_translation():
    """测试翻译功能"""
    translator = get_translator()
    
    print("=" * 60)
    print("多语言翻译测试")
    print("=" * 60)
    
    # 测试中文
    print("\n【简体中文】")
    translator.set_language('zh_CN')
    print(f"窗口标题：{tr('window_title')}")
    print(f"连接按钮：{tr('connect_btn')}")
    print(f"移动按钮：{tr('move_btn')}")
    print(f"状态就绪：{tr('status_ready')}")
    print(f"连接成功：{tr('msg_connect_success')}")
    
    # 测试英文
    print("\n【English】")
    translator.set_language('en_US')
    print(f"Window Title: {tr('window_title')}")
    print(f"Connect Button: {tr('connect_btn')}")
    print(f"Move Button: {tr('move_btn')}")
    print(f"Status Ready: {tr('status_ready')}")
    print(f"Connect Success: {tr('msg_connect_success')}")
    
    # 测试可用语言
    print("\n【可用语言】")
    languages = translator.get_available_languages()
    for code, name in languages.items():
        print(f"  {code}: {name}")
    
    print("\n" + "=" * 60)
    print("✅ 翻译测试完成")
    print("=" * 60)


if __name__ == '__main__':
    test_translation()
