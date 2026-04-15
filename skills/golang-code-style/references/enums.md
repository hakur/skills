# 枚举定义规范

## 核心规则：使用枚举替代基础类型

函数参数使用类型别名（枚举），而不是 `string` `int` 等基础类型：

```go
// ✅ 正确：使用枚举类型
const (
    ChatTypeText  ChatType = "text"
    ChatTypeImage ChatType = "image"
)
type ChatType = string

func SendChatMsg(chatType ChatType, msg []byte) (err error)

// ❌ 错误：使用基础类型
func SendChatMsg(chatType string, msg []byte) (err error)
```

## 枚举值定义模式

```go
// 使用 const iota 模式定义枚举值
const (
    StatusPending  Status = 0
    StatusActive   Status = 1
    StatusInactive Status = 2
)
type Status = int

// 字符串枚举
const (
    OrderCreated  OrderStatus = "created"
    OrderPaid     OrderStatus = "paid"
    OrderShipped  OrderStatus = "shipped"
    OrderComplete OrderStatus = "complete"
)
type OrderStatus = string
```

## 枚举作为函数参数、结构体字段

```go
// ✅ 正确：枚举类型作为参数
func CreateOrder(status OrderStatus) (*Order, error)

// ❌ 错误：基础类型作为参数
func CreateOrder(status string) (*Order, error)

// ✅ 正确：枚举类型作为字段
type Order struct {
    Status OrderStatus `json:"status" yaml:"status"`
}

// ❌ 错误：基础类型作为字段
type Order struct {
    Status string `json:"status" yaml:"status"`
}
```