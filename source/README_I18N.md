# 多语言支持 (i18n) 🌐

## 📋 **功能概述**

OpenMicroManipulator 现已支持多语言界面，目前提供：

- ✅ **简体中文** (zh_CN)
- ✅ **English** (en_US)

## 🎯 **使用方法**

### 方式一：代码中切换

```python
from i18n import get_translator

# 获取翻译器
translator = get_translator()

# 切换到英文
translator.set_language('en_US')

# 切换到中文
translator.set_language('zh_CN')

# 使用翻译
from i18n import tr
print(tr('window_title'))  # 根据当前语言输出
```

### 方式二：GUI 界面（开发中）

在菜单栏中选择：`工具 (Tools)` → `语言设置 (Language Settings)`

## 📁 **文件结构**

```
source/
├── i18n.py                          # 翻译核心模块
├── gui_components/
│   └── language_settings.py         # 语言设置对话框
└── test_i18n.py                     # 测试脚本
```

## 🔧 **添加新语言**

### 步骤 1: 在 i18n.py 中添加翻译

```python
TRANSLATIONS = {
    'zh_CN': {...},
    'en_US': {...},
    'ja_JP': {  # 日语
        'window_title': 'OpenMicroManipulator - マイクロステージ制御システム',
        'connect_btn': '接続',
        # ... 其他翻译
    },
}
```

### 步骤 2: 更新可用语言列表

```python
def get_available_languages(self):
    return {
        'zh_CN': '简体中文',
        'en_US': 'English',
        'ja_JP': '日本語',  # 新增
    }
```

## 📝 **翻译键命名规范**

- 使用小写字母和下划线：`button_text`
- 按功能分组：`menu_*`, `btn_*`, `msg_*`, `dlg_*`
- 保持语义清晰：`status_ready` 而不是 `s1`

## 🧪 **测试**

运行测试脚本验证翻译功能：

```bash
cd source
python test_i18n.py
```

## 🔄 **界面刷新**

当用户切换语言时：

1. 翻译器更新当前语言设置
2. 触发 `update_ui_language()` 信号
3. 主窗口重新加载所有文本
4. 对话框和菜单立即更新

## 💡 **最佳实践**

### ✅ 推荐做法

```python
# 使用翻译函数
label.setText(tr('connect_btn'))

# 批量更新
def update_ui_language(self):
    self.setWindowTitle(tr('window_title'))
    self.menu_file.setTitle(tr('menu_file'))
```

### ❌ 避免做法

```python
# 硬编码文本
label.setText("连接")  # ❌

# 混合使用
if lang == 'zh':
    label.setText("连接")
else:
    label.setText("Connect")  # ❌
```

## 🎨 **PySide6 国际化**

对于复杂的 Qt 应用，可以使用 Qt 的官方国际化流程：

1. 使用 `tr()` 函数标记文本
2. 使用 `lupdate` 提取 `.ts` 文件
3. 使用 Linguist 翻译
4. 使用 `lrelease` 编译 `.qm` 文件

但本项目采用简化的字典映射方式，更适合 Python 项目。

## 📊 **翻译统计**

| 语言 | 状态 | 完成度 |
|------|------|--------|
| 简体中文 | ✅ 完成 | 100% |
| English | ✅ 完成 | 100% |

## 🐛 **已知限制**

1. 部分动态生成的内容可能需要重启才能完全翻译
2. 第三方库的提示信息保持原语言
3. 日志消息暂不翻译

## 🤝 **贡献翻译**

欢迎贡献更多语言的翻译！请修改 `source/i18n.py` 并提交 Pull Request。

---

**最后更新**: 2026-03-06  
**版本**: v0.2.0
