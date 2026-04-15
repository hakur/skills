---
name: golang-code-style
description: Go 代码生成规范与验证技能。当生成或修改 Go 代码时自动触发，提供三方库约束、代码风格规范、测试规范和设计哲学指导，并支持脚本验证（L1/L2/L3）和语义自检。
---

# Golang Code Style

当生成或修改 Go 代码时，遵循此技能提供的规范和验证流程。

## 触发条件

- 生成新的 `.go` 文件
- 修改已有的 `.go` 文件
- 创建 Go 项目结构

## 使用步骤

### 第一步：引用 Reference 文件

根据代码上下文，读取对应的 reference 文件：

| 上下文 | Reference 文件 |
|--------|---------------|
| 选择三方库 | `references/libraries.md` |
| 编写测试 | `references/testing.md` |
| 定义结构体 | `references/structs.md` |
| 定义接口 | `references/interfaces.md` |
| 定义枚举/常量 | `references/enums.md` |
| 使用锁/并发 | `references/concurrency.md` |
| 组织文件目录 | `references/file-organization.md` |
| 模块分包规范 | `references/module-organization.md` |
| 全局配置/实例 | `references/global-instances.md` |
| 使用日志 | `references/logging.md` |
| 设计代码架构 | `references/code-philosophy.md` |

### 第二步：脚本验证（机械性检查）

完成代码修改后，运行验证脚本：

```bash
python <this skill dir>/scripts/verify.py <project_path>
```

验证三层检查依次执行：

| 层级 | 检查内容 | 工具 |
|------|---------|------|
| L1 | `go vet` + `golangci-lint` | `scripts/checks/l1_static.py` |
| L2 | 代码重复检测 + AST 规则检查 | `scripts/checks/l2_dupl.py` + `scripts/checks/l2_ruleguard.py` |
| L3 | `go build` + `go test` | `scripts/checks/l3_compile.py` |

L2 检查项包含两个独立的检查模块：

**A. 代码重复检测（dupl）**
- 检测 15 行以上的重复代码块
- 2 处重复 = WARN，3 处及以上 = ERROR
- 自动排除 vendor/ 和生成的文件

**B. AST 规则检查（ruleguard）**

基于 AST 的精确检查（避免正则误报）：

**ERROR（必须修复）：**
- 禁止使用 `sync.Mutex` / `sync.RWMutex`（AST 精确匹配）
- 禁止创建日志库新实例（`logrus.New()` / `zap.New()` 等）
- 禁止在测试中使用 `t.Run` 嵌套
- 禁止使用 `t.Skip`
- 禁止生成 `*_integration_test.go`
- 禁止使用 `gorilla/websocket`
- 禁止使用禁止的消息队列（非 nats）

**WARN（建议修复）：**
- 接口命名建议以 `I` 开头
- receiver 变量名建议使用小写 `t`

**配置文件**：
- ruleguard 规则：`references/ruleguard/rules.go`
- dupl 阈值：通过 `DUPL_THRESHOLD` 环境变量设置（默认 15）

### 第三步：语义性自检（AI 检查清单）

脚本只检查机械性规则。以下语义性规则需要 AI 自检：

- [ ] **接口必要性**：只有 2+ 种实现时才定义接口，1 种实现不需要
- [ ] **设计模式适度性**：简单功能不用设计模式，复杂多模块系统才用接口暴露策略选择
- [ ] **函数长度**：单个函数不超过 200 行
- [ ] **解耦合**：模块通过接口通信，依赖方向正确
- [ ] **三方库选择**：参考 `references/libraries.md` 的四层分层选择
- [ ] **json/yaml tag**：结构体 tag 使用驼峰风格
- [ ] **代码复用**：公共操作提取泛型/基类实现，不重复代码
- [ ] **封装**：内部细节（锁、缓存、重试）隐藏在方法签名后
- [ ] **职责单一**：一个结构体一个职责，3+ 个职责时拆分

### 第四步：使用 go doc 查阅三方库

每次使用 Go 第三方库之前，使用 `go doc` 命令查阅 import 路径内 package 的 API 文档。

## 注意事项

- 每次修改 protobuf 文件后都要运行命令行重新生成代码
- 每次修改 Go 代码后都要运行 `go vet` 检查错误
- 日志库（logrus/zap/zerolog）必须使用全局实例，禁止二次包装
- 互斥锁必须使用 `deadlock.Mutex`/`deadlock.RWMutex`，禁止 `sync.Mutex`/`sync.RWMutex`