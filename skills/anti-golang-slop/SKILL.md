---
name: anti-golang-slop
description: >
  检测 AI 生成的 Go 代码中的通用"屎山"模式。
  冗余抽象、手写轮子、结构膨胀、可读性债务、网络一致性、测试反模式、代码压缩、生命周期反模式。
  每条规则包含模式特征、检测方法和抽象伪代码，不绑定任何特定项目。
  触发词：反屎山 anti-slop 去AI味 清理Go 重构Go 代码瘦身 Go审查 remove-slop debloat。
  流程：扫描→报告→确认→修复。审查模式，不自动修改代码。
trigger: 反屎山, anti-slop, 去AI味, 清理Go, 重构Go, 代码瘦身, Go审查, remove-slop, debloat
---

# Anti Golang Slop — Go 代码反屎山审查

检测并清除 AI 生成 Go 代码中的典型"屎山"模式。所有规则与具体项目无关，适用于任意 Go 代码库。

## 核心原则

每次修改只问一个问题：**一个人写这段代码，会怎么写？**

AI 的默认行为是：定义类型 → 定义常量 → 写长函数 → 加自译注释 → 返回。人类不会这么写。**人类会删掉不需要的东西，而不是添加。** 删除不要的东西，比添加更难，也更正确。

## 工作模式：审查，不自动修改

```mermaid
flowchart LR
    A[扫描<br/>按 8 大类逐项检测] --> B[报告<br/>列出命中规则+位置+理由]
    B --> C[确认<br/>等用户逐项确认删改]
    C --> D[修复<br/>仅执行已确认项]
```

- **禁止**未报告直接改代码
- **禁止**报告后未获确认就修复
- 报告格式：`[规则编号] 文件:行号 — 命中模式 — 建议动作`
- 每增加一个功能前先问"真的需要吗"，不需要就删

---

## C1 冗余抽象 — 为不存在的变体做抽象

### R1.1 单一场景的枚举 / 类型别名 / 常量组
- **特征**：类型别名 + 一组常量，但全代码库只有一种取值；为"未来可能扩展"预留的抽象
- **检测**：搜索常量组，检查每个常量是否只有一处使用；枚举类型是否只有一个实际值
- **伪代码**：
```go
// ❌ 工具只有一种输出模式，不需要枚举
type OutputMode string
const ( ModeJSON OutputMode = "json"; ModeText OutputMode = "text"; ModeRaw OutputMode = "raw" )

// ✅ 直接返回唯一支持的结果
```

### R1.2 永远返回 nil error 的构造函数
- **特征**：构造函数签名带 `error` 返回值，但函数体内没有任何失败路径
- **检测**：`grep "func New.*error"`，逐个检查函数体是否可能返回非 nil error
- **伪代码**：
```go
// ❌ 永远返回 nil error
func NewThing() (t *Thing, err error) { t = new(Thing); return }

// ✅ 除非构造函数真的会失败，否则不要加 error
func NewThing() *Thing { return new(Thing) }
func NewThing() (t *Thing) { t = new(Thing);return }
```

### R1.3 只做 dispatch 的公开函数
- **特征**：公开函数的唯一功能是 if/else 选择后端然后转发，与内部实现完全重复
- **检测**：函数体只有条件分支 + 转发调用，无任何自有逻辑
- **伪代码**：
```go
// ❌ 薄包装，只做 dispatch
func DoWork(ctx, cfg, input) (Output, error) {
    if cfg.BackendURL != "" { return backendADoWork(...) }
    return backendBDoWork(...)
}

// ✅ 删除，调用方直接选用后端函数
BackendADoWork(ctx, cfg, input)
BackendBDoWork(ctx, cfg, input)
```

### R1.4 重复的后处理 / 注入层
- **特征**：结果已经通过返回值完整传递，却又在请求/响应钩子里缓存上次结果、检查调用名、二次注入内容；或添加调用方自己能判断的分类逻辑（如文本/二进制探测）
- **检测**：存在 `lastResult` 类字段 + 后处理钩子读缓存注入；存在 `detectMIME`/`isText` 类分支但上下游均未消费该分类
- **伪代码**：
```go
// ❌ 缓存结果 → 钩子里二次注入
func (t *Tool) ProcessRequest(ctx, req) error {
    injectText(req, t.lastResult)  // 返回值已包含结果，注入多余
}

// ✅ 钩子只做声明注册
func (t *Tool) ProcessRequest(ctx, req) error {
    registerDecl(req, t, t.Declaration())
    return nil
}
```

### R1.5 为简单 API 引入重型 SDK
- **特征**：API 只有一个端点、返回二进制或简单 JSON，却引入官方 SDK，附带 `option`/`param` 包、N 行 `ConvertXxxToYyy` 转换函数、枚举类型。层层抽象的价值为零
- **检测**：SDK import 数量 ≥3，且为 SDK 类型写了转换辅助函数；数一下用 SDK 调了几个端点 —— 只有 1 个即是命中
- **伪代码**：
```go
// ❌ SDK：3+ 个 import，20 行转换函数
import ( sdk "vendor/sdk"; "vendor/sdk/option"; "vendor/sdk/param" )
func ConvertConfigToSDKParams(cfg Config, in Input) sdk.RequestParams { ... }
resp, _ := client.Resource.Action.New(ctx, params)

// ✅ 通用 HTTP 客户端：1 个 import，0 行辅助函数
resp, _ := httpClient.R().SetContext(ctx).SetBody(body).Post("/v1/endpoint")
data := resp.Bytes()
```

### R1.6 跨层重复校验
- **特征**：参数解析层已用 tag/框架校验（`validate:"required"`），业务层又对同一字段手写 `if x == ""` 报错
- **检测**：同一字段在两层以上出现非空/格式校验
- **伪代码**：
```go
// ❌ 上游已 validate:"required"，下游又校验一遍
func BackendDo(in Input) {
    if in.Text == "" { return fmt.Errorf("text is required") }
}

// ✅ 谁的责任谁承担：解析层校验 → 业务层信任它
func BackendDo(in Input) {
    // in.Text 一定非空，直接使用
}
```

---

## C2 手写轮子 — 重新发明成熟库已有的东西

### R2.1 手写参数解码 → mapstructure
- **特征**：对 `map[string]any` 逐 key 手写 `m["key"].(string)` 类型断言
- **检测**：`grep '\.\(string\)'` / `grep '\.\(int\)'` 在参数解析处出现 ≥2 次
- **伪代码**：
```go
// ❌ 类型断言 × N 次
pattern := m["pattern"].(string); path := m["path"].(string)

// ✅ mapstructure 一次解码。注意开 WeaklyTypedInput，
//    否则 JSON 反序列化出的 float64(5) 转 int 会报错
decoder, _ := mapstructure.NewDecoder(&mapstructure.DecoderConfig{
    WeaklyTypedInput: true,
    Result:           &input,
})
decoder.Decode(args)  // args 直接传 any，无需先断言 map
```

### R2.2 手写校验 → validator tag
- **特征**：`if input.X == "" { return err }` 逐字段手写
- **检测**：构造函数/入口函数内连续 ≥2 个非空判断
- **伪代码**：
```go
// ❌ 手动判断
if input.Pattern == "" { return nil, fmt.Errorf("pattern required") }

// ✅ tag 定义 + 一次 Struct 校验
type Params struct {
    // Pattern 正则表达式
    Pattern string `mapstructure:"pattern" validate:"required"`
}
validator.New().Struct(input)
```

### R2.3 手写三元 / 默认值 → lo
- **特征**：`if x == "" { x = default }` 三行模式反复出现
- **检测**：`grep -B1 -A1 '= default'` 类赋值分支
- **伪代码**：
```go
// ❌ 3 行
if path == "" { path = defaultPath }

// ✅ 1 行
path = lo.Ternary(path != "", path, defaultPath)

// 查表 + fallback 用 Coalesce
ext, _ := lo.Coalesce(extByMime[mimeType], "bin")
```

### R2.4 手写递归遍历 → 标准库直达
- **特征**：自写 `WalkDir` + 模式匹配递归找文件，而 `filepath.Glob` 一次调用就够
- **检测**：`grep "WalkDir"` 且目的是按 glob 模式收集文件

---

## C3 结构膨胀 — 长函数、重复构造、映射散落

### R3.1 编排函数做实现 → 抽私有方法
- **特征**：入口函数（Run/Handle/Execute）既做参数解码、又做核心逻辑、又做结果聚合，超过一屏
- **检测**：入口函数 >50 行且包含 ≥3 个职责阶段
- **伪代码**：
```go
// ✅ 入口只做编排，不做实现
func (t *Tool) Run(ctx, args) (result Result, err error) {
    input, err := t.parseParams(args)   // ← 参数解码+校验
    items, err := t.collect(input)      // ← 收集
    for _, it := range items {
        r, err := t.processOne(it)      // ← 单项处理
        // ... 聚合 ...
    }
    result = Result{...}
    return
}
```

### R3.2 重复构造函数 → 公共构造器 + 薄包装
- **特征**：多个构造函数只有一两个参数不同，校验/初始化逻辑完全复制
- **检测**：`grep "func New"` 结果中函数体相似度极高
- **伪代码**：
```go
// ❌ 两个构造函数，完全重复的校验逻辑
func NewBackendAThing(cfg Config) (Thing, error) {
    if cfg.Key == "" { return nil, fmt.Errorf(...) }
    return &thing{cfg: cfg, backend: "a"}, nil
}
func NewBackendBThing(cfg Config) (Thing, error) { /* 一模一样 */ }

// ✅ 公共构造器 + 薄包装，校验只写一次
func NewThing(cfg Config, backend string) (Thing, error) {
    if cfg.Key == "" { return nil, fmt.Errorf("pkg: Key is required") }
    return &thing{cfg: cfg, backend: backend}, nil
}
func NewBackendAThing(cfg Config) (Thing, error) { return NewThing(cfg, "a") }
func NewBackendBThing(cfg Config) (Thing, error) { return NewThing(cfg, "b") }
```

### R3.3 同一映射散落多处 → 单一收口
- **特征**：同一类映射（如 format↔MIME↔扩展名）在多个文件各自维护，互相重叠但又不完全一样：有的多一项、有的大小写不一致、有的 fallback 值不同。这是屎山种子
- **检测**：`grep -r "map\[string\]string"` 跨文件比对 key 集合；同一语义出现 map / switch / inline 多种形态
- **伪代码**：
```go
// ❌ 按转换方向拆三个函数，调用方要先判断"我手里是什么"
helper.FormatToMime(format)
helper.MimeToExt(mimeType)
helper.ExtToMime(ext)

// ✅ 合并为一个归一化入口，兼容 format / MIME / 扩展名任意输入
//    "mp3"、"audio/mpeg"、".mp3" 进来都解析出同一份完整信息

// 写法一：多值返回，适合字段固定、调用点少的场景
format, mime, ext := helper.ResolveMediaType(s)
_, _, _ = format, mime, ext

// 写法二：结构体返回，适合字段会扩展、跨包传递的场景
// （两种签名二选一实现，按项目场景取舍）

// MediaType 一种媒体类型的完整描述
type MediaType struct {
    // Format 短格式名，如 "mp3"
    Format string
    // Mime 标准 MIME 类型，如 "audio/mpeg"
    Mime string
    // Ext 带点扩展名，如 ".mp3"
    Ext string
}

mt := helper.ResolveMediaType(s)  // 返回 MediaType，加字段不破坏调用方
_ = mt.Mime

// 内部一张映射表 + 输入归一化（去点、小写、按 "/" 判别），
// 所有包引用同一份映射，以后加格式只改一处
```

### R3.4 三胞胎代码 → 闭包
- **特征**：同一模式在不同字段名上重复 ≥3 遍，每遍只换字段名/常量
- **检测**：连续 if 块结构同构，仅标识符不同
- **伪代码**：
```go
// ❌ 28 行，同一模式抄三遍
if params.FieldA != "" {
    v, err := resolve(ctx, params.FieldA)
    if err != nil { v = params.FieldA }
    out = append(out, Item{Type: "a", Value: v})
}
if params.FieldB != "" { /* 一模一样，只换字段名 */ }
if params.FieldC != "" { /* 一模一样，只换字段名 */ }

// ✅ 闭包捕获 out，三行调用清零
appendIfSet := func(itemType, raw string) {
    if raw == "" { return }
    v, err := resolve(ctx, raw)
    if err != nil { v = raw }
    out = append(out, Item{Type: itemType, Value: v})
}
appendIfSet("a", params.FieldA)
appendIfSet("b", params.FieldB)
appendIfSet("c", params.FieldC)
```
- **边界**：如果每个分支逻辑差异大，继续用 if。真的是只换参数名才用闭包

### R3.5 只服务单个 struct 的私有自由函数 → 收编为方法
- **特征**：包内私有函数的核心参数总是同一个 struct（指针），全代码库的调用点全部来自这个 struct 的方法。它本质上是该 struct 的行为，却写成自由函数，每次调用都要显式传一遍 self
- **检测**：私有函数签名形如 `func doXxx(t *Thing, ...)`，反查调用点全部位于 `Thing` 的方法内
- **伪代码**：
```go
// ❌ 自由函数，但只为 Thing 服务，调用时还得把 t 传来传去
func processThing(t *Thing, item Item) error {
    t.count++
    return t.validate(item)
}

func (t *Thing) Run(items []Item) error {
    for _, it := range items {
        if err := processThing(t, it); err != nil {
            return err
        }
    }
    return nil
}

// ✅ 收编为私有方法，self 参数消失，归属一目了然
func (t *Thing) process(item Item) error {
    t.count++
    return t.validate(item)
}

func (t *Thing) Run(items []Item) error {
    for _, it := range items {
        if err := t.process(it); err != nil {
            return err
        }
    }
    return nil
}
```
- **边界**：函数同时操作多个平级 struct、或刻意不挂方法以保持 struct 的不可变性/精简公开面时，自由函数是合理选择。判断标准只有一个：**调用点是否全部属于同一个 struct**

---

## C4 可读性债务 — 命名与注释

### R4.1 行尾注释 → 字段前独立注释
- **特征**：结构体字段注释写在行尾，tag 和注释挤在一行
- **检测**：结构体定义内 `field Type \`tag\` // comment` 形态
- **伪代码**：
```go
// ❌ 行尾注释，godoc 不生成独立段落
type Params struct {
    Pattern string `tag:"pattern"` // 正则
}

// ✅ 字段前独立注释，go doc 为每个字段生成段落
type Params struct {
    // Pattern 正则表达式
    Pattern string `tag:"pattern"`
    // Path 搜索目录，默认当前工作目录
    Path string `tag:"path"`
}
```

### R4.2 命名不表意
- **特征**：名字需要看注释才知道是什么（`Input`/`Result`/`data2`），或名不副实（`lastResult` 其实每次调用都覆盖，不存在 "last"）
- **原则**：名字让读代码的人一眼就知道是什么，不需要看注释。`XxxInput → XxxToolParams`、`XxxMatch → XxxMatchResult`

### R4.3 Kubernetes 全词命名法则
- **规则**：函数名里出现的每个名词，都必须是代码里存在的类型名
- **伪代码**：
```go
// ❌ 缩写：cfg 是什么？
cfgToSpeechParams(cfg, input)
// ❌ 泛化：什么 config？
configToSpeechParams(cfg, input)
// ❌ 省略输出类型名
TTSConfigToParams(cfg, input)

// ✅ 全词：输入类型 + 转换动词 + 输出类型
ConvertTTSConfigToAudioSpeechParams(cfg, input)
// 读函数名就能画数据流图：TTSConfig → Convert → AudioSpeechParams
```

### R4.4 同类类型命名一半有一半没有
- **特征**：一组平行结构体，部分带领域前缀部分不带（`imageRequest`/`input`/`message`/`imageResponse`），读的人困惑"这个 Input 是什么的 Input"
- **检测**：同包内服务于同一流程的类型并排列出，检查命名一致性
- **原则**：私有类型只在包内可见，但命名不一致照样制造困惑。同组类型全带或全不带

### R4.5 魔法数字 → 命名常量
- **特征**：`64*1024`、`2000`、`1024*1024` 裸字面量散在逻辑里
- **检测**：逻辑代码中出现非 0/1 字面量且无明示含义
- **伪代码**：
```go
// ❌
scanner.Buffer(make([]byte, 64*1024), 1024*1024)
limit = lo.Ternary(limit > 0, limit, 2000)

// ✅
const (
    defaultLimit   = 2000
    maxScanBuffer  = 1024 * 1024
    initScanBuffer = 64 * 1024
)
scanner.Buffer(make([]byte, initScanBuffer), maxScanBuffer)
limit = lo.Ternary(limit > 0, limit, defaultLimit)
```

### R4.6 魔法字符串 → 命名常量
- **特征**：具有"协议值"性质的字符串字面量散在逻辑里 — 状态值、模式名、后端标识、map key、外部 API 的枚举字段。同一字面量出现 ≥2 处，或被 `==`/`switch` 比较。改一处忘改另一处就是 bug，且拼写错误编译器抓不到
- **检测**：`grep -o '"[a-z_]\{3,\}"'` 统计重复出现的字面量；搜索 `== "` 比较表达式
- **伪代码**：
```go
// ❌ 同一协议值散落多处，拼错一个字母编译不报错、运行才炸
if backend == "openai" { ... }
return &Tool{backend: "openai"}
switch status { case "completed": ... }

// ✅ 命名常量，编译器帮你查拼写，改值只改一处
const (
    BackendOpenAI    = "openai"
    BackendDashScope = "dashscope"
    StatusCompleted  = "completed"
)
if backend == BackendOpenAI { ... }
return &Tool{backend: BackendOpenAI}
```
- **边界**：日志消息、错误消息、`fmt.Errorf` 的格式串是**一次性文本**，不需要常量化。判定标准是"这个字符串是否会被比较/分支/当 key"——参与逻辑的才收编，只展示给人的不收

---

## C5 网络一致性 — HTTP 客户端与 IO 错误

### R5.1 HTTP 客户端创建收口到单一工厂
- **特征**：各处自行 `&http.Client{}` / `http.DefaultClient` / 分支判断"有代理走代理、没代理走默认"，代理/超时/鉴权逻辑散落
- **检测**：`grep "http.DefaultClient"` / `grep "&http.Client{"` 出现在业务代码
- **伪代码**：
```go
// ❌ 分支判断，没代理时绕过工厂
var client *http.Client
if cfg.ProxyAddr != "" {
    client, err = factory.NewProxyClient(cfg.ProxyAddr)
} else {
    client = http.DefaultClient  // ← 绕过统一规约
}

// ✅ 统一调用，空地址返回等效直连 client
client, err := factory.NewProxyClient(cfg.ProxyAddr)
if err != nil {
    return fmt.Errorf("...: proxy: %w", err)
}
```

### R5.2 同包多后端统一 HTTP 调用方式
- **特征**：一个包两个后端，一个手写 net/http、一个用 SDK，认知负担翻倍
- **检测**：同包内 import 两种 HTTP 调用方式
- **原则**：统一为同一种客户端后，代理处理、鉴权、序列化、错误检测完全一致，新人不用学两套 API

### R5.3 静默跳过 → 显式暴露，按契约决定能不能跳
- **特征**：循环里下载/请求失败打 Warn 后 `continue`，跳过只进了日志，调用方完全不知情
- **检测**：网络 IO 循环体内出现 `continue` + 日志的组合
- **判定标准：返回值是否承诺了与输入对应的完整性**
  - **承诺了 → 禁止跳**：调用方给 N 个输入期望 N 个结果（如批量下载 N 个 URL，返回 Count=N），跳过会制造不一致状态（Count 和 len 对不上），必须失败即报错
  - **没承诺 → 可以跳，但必须显式可见**：best-effort 收集场景（遍历目录某文件无权限、批量探测某项失败），"跳过坏项"是语义本身。但跳过清单必须进返回值，不能只进日志——日志是旁观者，不是错误通道
- **伪代码**：
```go
// ❌ 契约承诺 N 个结果却偷偷跳过，调用方不知道丢了数据
for _, u := range urls {
    resp, err := client.Get(u)
    if err != nil {
        log.Warn("download failed")
        continue  // ← output.Count 和 len(output.Items) 对不上
    }
}

// ✅ 情形 A：承诺完整性（输入 N 个 → 期望 N 个）——失败即报错
for _, u := range urls {
    resp, err := client.R().SetContext(ctx).Get(u)
    if err != nil {
        return fmt.Errorf("pkg: download %s: %w", u, err)
    }
}

// ✅ 情形 B：best-effort 收集——可以跳，但跳过清单显式进返回值
for _, path := range files {
    content, err := os.ReadFile(path)
    if err != nil {
        skipped = append(skipped, SkippedItem{Path: path, Err: err})
        continue
    }
}
return Result{Items: items, Skipped: skipped}, nil
```

### R5.4 重复计算 → 提局部变量
- **特征**：同一函数调用/表达式在相邻几行算两次
- **伪代码**：
```go
// ❌ 同一表达式计算两次
return Output{ Mime: f(b, mimeFor(format)), Duration: f(b, mimeFor(format)) }

// ✅ 算一次，复用
mime := mimeFor(format)
dur := f(b, mime)
return Output{ Mime: mime, Duration: dur }
```

---

## C6 测试反模式

### R6.1 测薄构造函数的测试 → 删
- **特征**：为一行的透传构造函数写 3 个测试（空参数/有效参数/默认值）。测它等于测 Go 的 struct 赋值语法
- **判定**：构造函数有业务逻辑（参数变换、校验、默认值注入）才值得测；纯透传不测
- **伪代码**：
```go
// ❌ 3 个测试，测的是一个一行函数
func TestNewBackendA_EmptyKey(t *testing.T) { ... }
func TestNewBackendA_Valid(t *testing.T) { ... }
// 本体：func NewBackendA(cfg Config) (T, error) { return NewThing(cfg, "a") }
```

### R6.2 测常量 map 的测试 → 删
- **特征**：表格驱动测试逐条断言常量映射的每个 entry。改了 map 就要改测试，不改就过不了 CI —— 负生产力
- **判定**：常量映射没有逻辑，不需要测试。有 fallback 分支逻辑时可只测 fallback

### R6.3 skip 守卫必须带注释防 AI 误删
- **特征**：集成测试用 `t.Skip`/`t.Skipf` + 环境变量守卫，但没有任何注释说明。大模型看到 `t.Skip` 第一反应是"被跳过的死代码，删"
- **伪代码**：
```go
// ❌ 裸 skip，下次 AI 直接判为废弃代码删掉
t.Skip("set XXX_TEST=1 to enable")

// ✅ 文件头注释 + t.Skipf + 写明原因（如调用外部 API 烧钱）
// 测试策略说明：
// 集成测试涉及外部 API 调用，会消耗真实配额，
// 因此通过环境变量守卫 — 仅在人工设置对应 ENV 后才运行。
// 请勿删除 t.Skipf 守卫，这不是"废弃测试"，而是"人工触发测试"。
t.Skipf("设置 XXX_TEST=1 以启用集成测试（需消耗 API 配额）")
```

### R6.4 集成测试日志 = 收据
- **特征**：调了付费外部 API，测试只 log 一个 size/类型。烧了钱得看到东西
- **原则**：把花钱买到的所有信息全打出来 — 模型、参数、时长、大小、URL。集成测试的输出就是你的收据
```go
// ❌
t.Logf("MIME: %s, size: %d", out.MimeType, len(out.Data))

// ✅
t.Logf("model=%s voice=%s duration=%s size=%d mime=%s url=%s",
    cfg.Model, cfg.Voice, out.Duration, len(out.Data), out.MimeType, out.URL)
```

### R6.5 覆盖被吞并的测试 → 删
- **特征**：小函数的专属单元测试，其断言内容已完全被一个大生命周期测试 / 上层集成测试 / 嵌套测试覆盖。小函数只是被测链路中的一环，单独测它不产生任何新增断言价值，只是重复维护成本
- **判定标准：以下 4 条全部满足才可删，缺一保留**
  1. **真覆盖**：上层测试不是"路过调用"该函数，而是其行为差异会直接导致上层断言失败（改了它会炸上层测试）
  2. **CI 必跑**：上层测试在 CI 中无条件运行。若上层是 `t.Skipf` 环境变量守卫的人工触发测试（见 R6.3），删了单测 = CI 零覆盖，**禁止删**
  3. **可定位**：上层测试失败时能从报错定位到该函数（调用链短、错误信息含上下文），删除后不丧失故障定位能力
  4. **无独有输入**：该函数不存在只有单测才能喂进去的输入组合（错误路径、边界值、异常参数）
- **伪代码**：
```go
// ❌ 冗余：TestFormatName 的每条断言，TestFullPipeline 已经走了一遍
func TestFormatName(t *testing.T) {
    assert.Equal(t, "mp3", FormatName("audio/mpeg"))
}
func TestFullPipeline(t *testing.T) {
    out := RunPipeline(in) // 内部必经 FormatName，它错了这里立刻炸
    assert.Equal(t, "mp3", out.Format)
}

// ✅ 删 TestFormatName，只留 TestFullPipeline
```
- **边界**：反向不成立——上层测试替代不了下层独有的边界/错误路径测试。删除前用 `go test -coverprofile` 验证：删掉后对应文件的覆盖率不掉，才说明是真吞并

---

## C7 代码压缩 — 行数洁癖与惯用简写

### R7.1 命名返回值 + bare return，不要重复自己
```go
// ❌ 返回值已经有名字，还要再写一遍
func (t *Tool) Run(...) (result Result, err error) {
    return Result{...}, nil
}

// ✅ 赋值后 bare return；错误路径同理，零值已就位直接 return
func (t *Tool) Run(...) (result Result, err error) {
    result = Result{...}
    return
}
```

### R7.2 switch → map 查找
```go
// ❌ switch 10 行
ext := "mp3"
switch mime {
case "audio/wav": ext = "wav"
case "audio/opus": ext = "opus"
}

// ✅ map 查找 + fallback
ext, _ := lo.Coalesce(
    map[string]string{"audio/wav": "wav", "audio/opus": "opus"}[mime],
    "mp3",
)
```

### R7.3 条件字段写入 → lo.PickBy + for-range
```go
// ❌ 每个可选字段一句 if，加字段要加三行
w.WriteField("model", model)
if in.Language != "" { w.WriteField("language", in.Language) }
if in.Prompt != "" { w.WriteField("prompt", in.Prompt) }

// ✅ PickBy 过滤空值，一把梭。加字段只改 map entry
for k, v := range lo.PickBy(map[string]string{
    "model": model, "language": in.Language, "prompt": in.Prompt,
}, func(_ string, v string) bool { return v != "" }) {
    w.WriteField(k, v)
}
```

---

## C8 生命周期反模式 — 状态、超时与零值契约

### R8.1 无状态组件缓存"上一次结果"
- **特征**：组件持有 `lastResult` 类字段，每次调用都覆盖。动态调用场景下不存在"上一次"，缓存它只会制造陈旧的隐式依赖
- **检测**：struct 字段在 Run/Handle 内被赋值、在另一个方法内被读取
- **原则**：每次调用都是新结果。需要传递就显式放返回值，不要藏字段

### R8.2 超时所有权错位
- **特征**：库/组件内部 `context.WithTimeout` 自定超时，而调用方（agent/框架）本就在控制生命周期。内建超时与调用方 deadline 互相打架
- **检测**：组件内部出现 `context.WithTimeout`，而上游调用链已有 deadline
- **原则**：超时归调用方管。组件透传 ctx，不私自加时

### R8.3 nil slice vs 空 slice 的 JSON 契约
- **特征**：重构时丢掉显式空 slice 初始化，`nil` slice 序列化成 `null` 而不是 `[]`，调用方 JSON 解析可能炸
- **检测**：返回值 struct 的 slice 字段，对比重构前后是否保留 `[]T{}` 初始化
- **伪代码**：
```go
// ❌ 重写时漏掉 — JSON 输出 null 而不是 []
return Output{ Items: items, Count: len(items) }

// ✅ 原版契约：空也要是 []
return Output{ Items: items, URLs: []string{}, Count: len(items) }
```

---

## 元规则

### M1 镜像包的 slop 会成对出现
同一项目里结构对称的包（如 audiogen / imagegen / videogen 这类"tool 接口 + A 后端 + B 后端 + 测试"四件套），犯的 slop 一模一样。**反完一个直接反另一个** — 不需要重新探索，照搬清单逐项核对即可。

### M2 重构前后对照表
每个包修完后输出对照表，量化收益：
```
            行数      依赖库     日志侵入   反模式命中
重构前       N        0          M 处      K 处
重构后       N×0.7    成熟库     0 处      0 处
```

---

## 审查报告模板

```markdown
## Anti-Slop 扫描报告 — <包名/目录>

| 规则 | 位置 | 命中模式 | 建议动作 |
|------|------|----------|----------|
| R1.2 | foo.go:42 | NewFoo 永远返回 nil error | 去掉 error 返回值 |
| R6.3 | foo_test.go:15 | 裸 t.Skip 无注释 | 补守卫说明注释 |

合计：N 处命中，预计可减少 X 行（-Y%）
待确认：请逐项确认后我再动手修复。
```

**再次强调：审查模式。扫描 → 报告 → 等用户确认 → 修复。不自动修改代码。**
