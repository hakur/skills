# 接口设计规范

## 核心规则：多实现才抽象

仅在需要实现多种差异化结构体时才设计接口。只有 1 种实现时不需要接口。

## 接口命名规则

### 命名优先级

| 优先级 | 条件 | 命名示例 |
|--------|------|----------|
| 1 | 有多种实现，需暴露策略选择 | `Packet` (接口) + `JsonPacket`/`XmlPacket` (实现) |
| 2 | 语义化动词/名词更清晰 | `Unmarshaler`, `Decoder`, `Serializer` |
| 3 | 与已有类型冲突 | `IPacket` (仅用于解决冲突) |

### 何时使用 IPacket

```go
// ✅ 正确：解决命名冲突
type Packet struct{}                    // 已有
type IPacket interface {                 // 新增接口
    Unmarshal(v any) error
}

// ✅ 正确：多实现时接口用无前缀命名
type Packet interface { ... }            // 接口
type JsonPacket struct {}               // 实现
type XmlPacket struct {}                // 实现

// ✅ 正确：单一职责的语义化命名
type Unmarshaler interface { ... }
type Encoder interface { ... }
type Connection interface { ... }
```

### ❌ 错误示范：无意义命名

禁止使用以下无意义命名的接口和结构体：

```go
// ❌ 错误：Default - 毫无语义
type DefaultPacket struct{}
func (t *DefaultPacket) Unmarshal(v any) error { ... }

// ❌ 错误：Basic - 暗示有"高级"版本，但可能永远不会有
type BasicPacket struct{}
func (t *BasicPacket) Unmarshal(v any) error { ... }

// ❌ 错误：Standard - 暗示有"非标准"版本
type StandardPacket struct{}
func (t *StandardPacket) Unmarshal(v any) error { ... }

// ❌ 错误：Normal - 暗示有"异常"版本
type NormalPacket struct{}
func (t *NormalPacket) Unmarshal(v any) error { ... }

// ❌ 错误：Plain - 相比什么？Rich？Fancy？
type PlainPacket struct{}
func (t *PlainPacket) Unmarshal(v any) error { ... }

// ❌ 错误：Impl - 最糟糕的命名之一
type PacketImpl struct{}
type PacketImplementation struct{}   // 太长，且毫无语义

// ❌ 错误：Impl1/Impl2 - 数字编号让代码可读性极差
type PacketImpl1 struct{}
type PacketImpl2 struct{}
```

### 正确 vs 错误对比

| 错误 | 正确 |
|------|------|
| DefaultPacket | JsonPacket / RawPacket |
| BasicPacket | TinyPacket / MiniPacket |
| StandardPacket | CommonPacket / CorePacket |
| NormalPacket | StandardPacket (如果真是标准) |
| PlainPacket | SimplePacket / CleanPacket |
| PacketImpl | JsonPacket / XmlPacket |
| PacketImpl1/Impl2 | PacketV1 / PacketV2 |

## 何时定义接口

```
┌──────────────────────────────────────────────────────────┐
│  有 2+ 种实现 → 定义接口，使用语义化命名                    │
│                                                          │
│  只有 1 种实现 → 不需要接口，直接写结构体                  │
│                                                          │
│  需要 mock 测试 → 定义接口方便 mock                       │
│                                                          │
│  需要让用户选择策略 → 定义接口让用户选择实现               │
│                                                          │
│  已有同名类型冲突 → 使用 IPacket 解围                     │
└──────────────────────────────────────────────────────────┘
```

## 已有 I 前缀接口保持兼容

对于由工具自动生成的 `I{Entity}Do` 模式接口（如 gorm.io/gen 生成的 DAO 层接口），保持现有命名不变，不强制迁移。

```go
// ✅ 兼容：gorm.io/gen 生成的代码保持原样
type IActActivityDo interface {
    FindOne(ctx context.Context, id int64) (*ActActivity, error)
}

type actActivityDo struct {
    DOBase
}
```

## 示例

```go
// ✅ 正确：多种差异化实现
type Packet interface { ... }            // 接口
type JsonPacket struct {}               // JSON 实现
type XmlPacket struct {}                // XML 实现
type ProtobufPacket struct {}           // Protobuf 实现

// ✅ 正确：语义化命名
type Unmarshaler interface {
    Unmarshal(v any) (err error)
}

type Encoder interface {
    Encode(v any) (data []byte, err error)
}

// ✅ 正确：解决冲突
type Packet struct{}                    // 已有
type IPacket interface {                 // 新增
    Unmarshal(v any) error
}

// 只有 1 种实现 → 不需要接口，直接写结构体
type OrderRepo struct {
    db *gorm.DB
}
func (t *OrderRepo) Create(ctx context.Context, order *Order) error { /* ... */ }
```
