---
name: golang-code-style
description: >
  Go 代码生成规范与验证技能。
  触发词：.go, Go代码, Go项目, golang, go test, go vet, go build,
  _test.go, gorm, go mod, kratos, fiber, gin, logrus, zap,
  deadlock, golangci-lint, Go单元测试, Go接口, 创建Go, 写Go,
  go.mod, GORM, Go测试, Go结构体。
  提供：FATAL/ERROR/WARN 三层代码约束、测试规范、生成后自检清单、
  脚本验证（L1/L2/L3）。
trigger: go, golang, .go, gorm, kratos, fiber, go test, go build, _test.go, Go代码, Go项目, Go接口, Go单元测试
---

# Golang Code Style

当生成或修改 Go 代码时，遵循此技能提供的规范和验证流程。

## 触发条件（加载后确认）

此技能已自动加载。请确认当前任务属于以下范畴之一：

- 创建或修改 `.go` 文件
- 创建 Go 项目（`go mod init`）
- 修改 Go 测试文件（`_test.go`）
- 用户明确要求遵守 Go 代码规范

如果当前任务不涉及 Go 代码，可以忽略此技能的详细内容，但硬约束层规则仍适用于所有 Go 代码。

---

## 🔴 硬约束 — 违反将导致代码被拒绝

以下规则无例外。生成代码时逐条核对。每条规则嵌入正确示例，无需查阅 reference。

### 测试规则

**R1: 所有测试必须真实执行**
```
正确: func TestXxx(t *testing.T) { actual := DoSomething(); assert.NotNil(t, actual) }
错误: func TestXxx(t *testing.T) { t.Skip("环境未准备好") }
```
- 禁止 t.Skip() / t.Skipf() / t.SkipNow() — AST 检查强制拦截
- 缺少环境时: TestMain + go-mysql-server / miniredis / godotenv 补充
- 参考: `references/testing.md`

**R2: 所有测试必须有真实断言**
```
正确: assert.Equal(t, 200, resp.StatusCode)  ← 期望值基于 HTTP 规范
错误: expected := "hello"; assert.Equal(t, expected, actual)  ← expected 与 actual 同源
```
- 每个 `func TestXxx` 必须包含 ≥1 个 assert/require 调用
- expected 值必须基于独立推理计算，不可从 actual 复制

**R3: 测试函数扁平化**
```
正确: func TestUserCreate(t *testing.T) {}   ← 每个场景独立函数
       func TestUserCreateWithEmail(t *testing.T) {}
错误: t.Run("sub", func(t *testing.T) { t.Run("subsub", ...) })  ← 嵌套禁止
```
- 禁止 `t.Run` 嵌套 — AST 检查强制拦截
- 公共逻辑提取为辅助函数

### 并发规则

**R4: 互斥锁类型锁定**
```
正确: import "github.com/sasha-s/go-deadlock"
       lock deadlock.RWMutex
错误: import "sync"
       lock sync.RWMutex
```
- 互斥锁只能是 `deadlock.Mutex` / `deadlock.RWMutex`
- 禁止 `sync.Mutex` / `sync.RWMutex` — AST 检查强制拦截
- 参考: `references/concurrency.md`

### 日志规则

**R5: 日志只用全局实例**
```
正确: logrus.WithFields(logrus.Fields{"user": id}).Info("created")
       zap.L().Info("started", zap.Int("port", 8080))
错误: logger := logrus.New()
       logger, _ := zap.NewProduction()
```
- 禁止 `logrus.New()` / `zap.New()` / `zerolog.New()` — AST 检查强制拦截
- 参考: `references/logging.md`

### 网络规则

**R6: WebSocket 库锁定**
```
正确: import "github.com/coder/websocket"
错误: import "github.com/gorilla/websocket"
```
- 只能使用 `github.com/coder/websocket`
- 禁止 `gorilla/websocket` — AST 检查强制拦截
- 参考: `references/libraries.md`

---

## 🟠 设计约束 — 违反会导致 CI/build 失败

以下规则在 `go vet` / `golangci-lint` / 代码审查中会产生失败。

- **函数长度**: 单个函数 ≤ 200 行（不含空行和注释）。超过必须拆分
- **代码重复**: 同一代码块出现 ≥ 3 处 → 必须提取公共函数。测试代码同样受此约束
- **目录深度**: 项目文件夹 ≤ 4 层（生成代码除外）
- **禁止目录**: 禁止 `test/`、`test/integration/` 目录和 `*_integration_test.go` 文件
- **禁止虚假断言**: 禁止 `expected` 变量使用与 `actual` 相同的硬编码值使断言永远成立
- **禁止裸字面量替代枚举**: 禁止 `x = 1 // PostStatusNormal` 模式。枚举字段必须使用命名常量，不能裸数字/字符串 + 注释伪装。缺常量时主动定义
- **测试对应**: `abc.go` → `abc_test.go`，只测试导出函数
- **Mock 测试**: `abc.go` → `abc_mock_test.go`，使用 testify/mock
- **TestMain 初始化**: 环境变量和全局实例在 `TestMain` 中通过 `godotenv.Load(".env")` 初始化

---

## 🟡 风格建议 — 可讨论，推荐遵守

- **接口**: 2+ 种实现时才定义接口，1 种实现直接用结构体。接口命名用能力描述（Reader, Repository），与结构体命名冲突时可用 I 前缀区分。Go 社区惯例是无 I 前缀
- **receiver**: 变量名用单字母 `t`，如 `func (t *Service) Method()`
- **tag 风格**: json/yaml tag 使用驼峰：`json:"apiKey"` 而非 `json:"api_key"`
- **变量命名**: 不与包名冲突，禁止数字后缀（`url2` ❌ → `targetURL` ✅）
- **锁字段**: 私有字段 + 排最后：`lock deadlock.RWMutex`
- **结构体**: 公开字段在前，锁在后。仅在有内部初始化逻辑时才写构造函数
- **枚举**: 使用类型别名替代基础类型作为函数参数/字段类型
- **日志内容**: 英文输出，使用 `WithFields` 附加结构化信息

---

## ⚡ 生成后自检 — 必须逐条执行，非可选

在向用户报告"完成"之前，执行以下检查。**这是指令，不是建议。**

### 通用检查（任何 .go 文件生成后）

逐行扫描你生成的代码:
□ 有没有 `sync.Mutex` 或 `sync.RWMutex`?
  → 有：致命。替换为 `deadlock.Mutex` / `deadlock.RWMutex` 后重新扫描。
□ 有没有 `logrus.New()` / `zap.New()` / `zerolog.New()`?
  → 有：致命。改为全局调用 `logrus.Info()` / `zap.L().Info()` 后重新扫描。
□ 有没有 `"github.com/gorilla/websocket"`?
  → 有：致命。改为 `"github.com/coder/websocket"` 后重新扫描。

### 测试专项检查（_test.go 文件生成后）

逐文件扫描:
□ 有没有 `t.Skip` / `t.Skipf` / `t.SkipNow`?
  → 发现任何一条：停止，不要报告完成。删除 Skip 语句，用 TestMain + 内存替代品补充测试环境后重新扫描。
□ 每个 `func TestXxx` 的函数体有没有 `assert.` 或 `require.` 调用？
  → 空函数体：补充真实断言后重新扫描。
□ 有没有 `expected := "某值"; assert.Equal(t, expected, actual)` 且 expected 与 actual 由同一来源计算？
  → 虚假测试：expected 必须基于独立推理。重写后重新扫描。
□ 有没有 `t.Run` 嵌套？
  → 展平为独立 `TestXxx` 函数后重新扫描。
□ 测试代码是否有 ≥3 处高度相似的代码块？
  → 提取公共辅助函数后重新扫描。

### 枚举/GORM 硬编码检测（任何 .go 文件生成后）

逐行扫描你生成的代码中的**裸数字/字符串字面量**:
□ 搜索: `= 数字 // 枚举名` 或 `: 数字, // 枚举名`
  → `c.Status = 1 // PostStatusNormal` → 违规。改为 `c.Status = PostStatusNormal`
  → `Status: 1, // PostStatusNormal` → 违规。改为 `Status: PostStatusNormal`
□ 搜索: GORM 查询参数中的裸字面量
  → `Where("col = ?", 1)`, `Where("a = ? AND b = ?", 1, ConstB)`
  → 每个参数都要问: 这个字段有没有命名常量？
  → 有 → 用常量；没有 → 在文件顶部 `const FieldName = <值>` 然后使用
  → 特别注意混合合规: `Where("a = ? AND b = ?", 裸值, 常量)` — 裸值是漏网之鱼
□ 搜索: `Updates(map[string]any{"field": 裸值})`, `Create(&Model{Field: 裸值})`
  → 同样规则: 有常量用常量，无常量定义常量
□ 搜索: 字符串字面量替代字符串枚举
  → `Type = "normal" // OrderTypeNormal` → 违规。改为 `Type = OrderTypeNormal`

**检测原则**: 枚举语义的字段 → 必须用命名常量。裸字面量 + 注释 = 欺骗。缺常量不是借口 → 主动定义。

**发现任何违规 → 立即修复 → 重新自检 → 直到全部通过 → 才能报告完成。**

---

## 📋 自动化验证

完成自检后，运行脚本进行机械性验证：

```bash
python <skill-dir>/scripts/verify.py <project_path>
```

三层检查依次执行：

| 层级 | 检查内容 | 工具 |
|------|---------|------|
| L1 | `go vet` + `golangci-lint` | `scripts/checks/l1_static.py` |
| L2 | 代码重复检测（dupl）+ AST 规则检查（ruleguard） | `scripts/checks/l2_dupl.py` + `scripts/checks/l2_ruleguard.py` |
| L3 | `go build` + `go test` | `scripts/checks/l3_compile.py` |

## 🔧 未知库学习协议 — 遇到不熟悉的 Go 三方库时执行

当需要使用一个**不在 LLM 训练数据中**或**不熟悉**的 Go 三方库时，按以下三层策略执行。此协议是**指令**，不是建议。

### Step 1: go doc — 主力工具，理解 API 意图

先查阅文档（prose），不要直接读源码。文档信息密度远高于源码，更高效。

```bash
# 查看包的完整 API 文档
go doc <pkg>
# 示例: go doc github.com/samber/lo

# 查看特定类型的文档
go doc <pkg>.<Type>
# 示例: go doc github.com/samber/lo.Map

# 查看特定方法的文档
go doc <pkg>.<Type>.<Method>
# 示例: go doc net/http.ResponseWriter.Write
```

**Token 成本**: ~100-300 tokens 即可获取完整 API 概况。
**适用**: 所有情况。这是第一步，必做。

### Step 2: lsp_find_references — 辅助工具，找真实使用示例

如果看了文档仍不确定具体写法，搜索项目中已有的调用：

```
lsp_find_references(filePath="your/file.go", line=N, character=N)
→ 返回项目中所有使用该符号的位置 → 阅读其中 1-2 个实际写法学到模式
```

**Token 成本**: ~200-500 tokens（含跳转阅读）。
**适用**: 文档不够清晰时。按需使用，不是必做。

### Step 3: lsp_diagnostics — 验证工具，检查类型正确性

写完代码后，不等 `go build`，立即验证：

```
lsp_diagnostics(filePath="your/file.go")
→ 即时返回类型错误、未定义符号等
→ 根据错误修正代码 → 重新验证 → 直到干净
```

**Token 成本**: ~50-100 tokens。
**适用**: 写完使用新库的代码后必做。

### Token 效率原则

```
go doc (文档)          → 总是先做，信息密度最高
lsp_find_references   → 按需，文档不够时
lsp_diagnostics       → 写完代码后总是做
LSP 直接读源码         → 最后手段，token 最昂贵
```

---

## 📚 深入参考（按需查阅）

核心规则已在上方完整展示。以下文件提供详细示例和解释：

| 场景 | Reference 文件 |
|--------|---------------|
| 选择三方库 | `references/libraries.md` |
| 详细测试示例（TestMain/内存DB/Mock） | `references/testing.md` |
| 接口设计详解 | `references/interfaces.md` |
| 并发/锁详解 | `references/concurrency.md` |
| 结构体定义 | `references/structs.md` |
| 枚举定义 | `references/enums.md` |
| 命名规范 | `references/naming.md` |
| 文件组织 | `references/file-organization.md` |
| 模块组织 | `references/module-organization.md` |
| 全局实例 | `references/global-instances.md` |
| 日志详解 | `references/logging.md` |
| 设计哲学 | `references/code-philosophy.md` |

## 工具说明

- **ruleguard 规则**: `references/ruleguard/rules.go` — 基于 AST 精确检查，通过 golangci-lint 集成
- **dupl 阈值**: 通过 `DUPL_THRESHOLD` 环境变量设置（默认 15）
- **语义自检**: 脚本只检查机械性规则。接口必要性、设计模式适度性等语义规则已在上方约束层中覆盖
- **protobuf**: 每次修改 protobuf 文件后都要运行命令行重新生成代码
