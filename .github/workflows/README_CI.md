# GitHub Actions CI/CD 配置说明

## 📋 概述

本项目使用 GitHub Actions 实现自动化的代码质量检查，确保所有 Pull Request 都符合质量标准。

## 🔍 检查工作流

当有以下操作时，会自动触发检查：
- 创建 Pull Request 到 main 分支
- 推送代码到 main 分支

### 检查项目

#### 1. **代码风格检查 (Flake8)** ✅
**目的**: 检查 Python 代码风格和语法错误

**检查内容**:
- 语法错误（阻塞性）
- 未定义的名称（阻塞性）
- 代码复杂度
- 行长度限制（127 字符）

**配置文件**: `setup.cfg`

**通过条件**: 
- ❌ 严重错误（E9, F63, F7, F82）会阻止合并
- ⚠️ 其他警告仅作为提示，不阻止合并

#### 2. **类型检查 (Mypy)** 🔍
**目的**: 检查 Python 类型注解的正确性

**检查内容**:
- 类型一致性
- 函数返回类型
- 参数类型匹配

**配置**:
```bash
mypy source/ --ignore-missing-imports --no-strict-optional
```

**通过条件**: ⚠️ 仅警告，不阻止合并

#### 3. **安全扫描 (Bandit)** 🛡️
**目的**: 检测常见的安全问题

**检查内容**:
- 硬编码密码
- SQL 注入风险
- 不安全的随机数
- 命令注入风险
- 其他常见漏洞

**级别**: 
- `-ll` 低级别问题
- `-ii` 包含信息性问题

**通过条件**: ⚠️ 仅报告，不阻止合并

#### 4. **测试运行 (Pytest)** 🧪
**目的**: 运行自动化测试

**当前状态**: 📝 预留位置，等待添加测试

**未来计划**:
```bash
pytest tests/
```

#### 5. **构建验证 (PyInstaller)** 📦
**目的**: 验证代码能否成功打包为可执行文件

**检查内容**:
- 依赖完整性
- 导入正确性
- 打包配置有效性

**通过条件**: ⚠️ 仅验证，不阻止合并

#### 6. **总结报告** 📊
**目的**: 汇总所有检查结果

**输出内容**:
```markdown
## PR Check Summary

### Job Status
- Lint: success/failure
- Type Check: success/failure
- Security: success/failure
- Test: success/skipped
- Build: success/failure

✅ All critical checks passed
或
❌ Some checks failed
```

## ⚙️ 配置文件

### setup.cfg

```ini
[flake8]
max-line-length = 127      # 最大行长度
max-complexity = 10        # 最大圈复杂度
exclude =                  # 排除的目录
    .git,
    __pycache__,
    build,
    dist,
    .venv,
    *.pyc
ignore =                   # 忽略的规则
    E203,                  # 冒号前的空格
    W503,                  # 二元运算符前的换行
    E501                   # 行太长（由 max-line-length 处理）

[mypy]
python_version = 3.10
warn_return_any = False
warn_unused_configs = True
ignore_missing_imports = True
no_strict_optional = True
```

## 🚀 工作流程

### 触发条件
```yaml
on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]
```

### 执行顺序

```mermaid
graph TB
    Start[PR/Push 触发] --> Lint[代码风格检查]
    Start --> TypeCheck[类型检查]
    Start --> Security[安全扫描]
    Start --> Test[测试运行]
    
    Lint --> Build{构建验证}
    TypeCheck --> Build
    Security --> Build
    
    Build --> Summary[总结报告]
    Test --> Summary
    
    Summary --> Pass{检查通过？}
    Pass -->|是 | Merge✅[允许合并]
    Pass -->|否 | Fix[需要修复]
```

## 📊 检查结果

### 查看检查结果

1. 访问 Pull Request 页面
2. 查看底部的 "Checks" 标签
3. 点击具体任务查看详细日志

### 检查失败怎么办？

#### Flake8 错误
```bash
# 本地运行检查
pip install flake8
flake8 source/
```

**常见问题**:
- `F401`: 未使用的导入 → 删除不必要的 import
- `E302`: 缺少空行 → 在函数/类前加空行
- `F821`: 未定义的名称 → 检查变量名拼写

#### Mypy 类型错误
```bash
# 本地运行检查
pip install mypy
mypy source/ --ignore-missing-imports
```

**修复示例**:
```python
# 修改前
def greet(name):
    return f"Hello {name}"

# 修改后
def greet(name: str) -> str:
    return f"Hello {name}"
```

#### Bandit 安全问题
```bash
# 本地运行检查
pip install bandit
bandit -r source/ -ll -ii
```

**常见问题**:
- `B101`: 断言语句 → 避免在生产代码中使用 assert
- `B301`: 不安全的 pickle → 使用 JSON 替代
- `B310`: URLLib 使用 → 使用 requests 库

## 🔧 本地开发建议

### 安装开发工具
```bash
# 安装所有检查工具
pip install flake8 mypy bandit pytest

# 或使用预提交钩子
pip install pre-commit
pre-commit install
```

### 推荐工作流
1. 编写代码
2. 本地运行检查
3. 修复所有错误
4. 提交代码
5. 创建 Pull Request

## 📈 持续改进

### 未来计划

1. **增加单元测试覆盖率**
   - 为核心模块添加测试
   - 目标覆盖率 > 80%

2. **集成代码覆盖率检查**
   ```yaml
   - name: Upload coverage
     uses: codecov/codecov-action@v3
   ```

3. **添加性能测试**
   - 启动时间基准测试
   - 内存使用监控

4. **自动化发布**
   - 版本标签自动创建
   - 自动打包上传到 PyPI

## 🎯 最佳实践

### ✅ 推荐做法
- 小步提交，频繁推送
- 提交前本地运行检查
- 保持代码简洁清晰
- 添加适当的类型注解
- 编写有意义的注释

### ❌ 避免做法
- 忽略所有警告
- 过度复杂的代码
- 硬编码敏感信息
- 过长的函数和文件
- 重复代码

## 📚 相关资源

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Flake8 文档](https://flake8.pycqa.org/)
- [Mypy 文档](https://mypy.readthedocs.io/)
- [Bandit 文档](https://bandit.readthedocs.io/)
- [Pytest 文档](https://docs.pytest.org/)

---

**提示**: 如果检查配置需要调整，请修改 `.github/workflows/pr_check.yml` 和 `setup.cfg`
