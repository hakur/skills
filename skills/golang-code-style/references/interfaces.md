# 接口设计规范

本文档提供 Go 接口设计指南，包括决策框架、命名规范、文件组织和接口组合模式。

## 核心原则

### 1. YAGNI（You Aren't Gonna Need It）

**不要提前定义接口，等到真正需要时再定义。**

### 2. 多实现才抽象

仅在需要实现多种差异化结构体时才设计接口。只有 1 种实现时不需要接口。

---

## 什么时候需要接口？

### ✅ 需要接口的情况

#### 1. 有 2+ 种实现

```go
// 多种通知渠道需要统一接口
type Notifier interface {
    Send(ctx context.Context, userID uint64, msg string) error
}

type EmailNotifier struct{}  // 实现 Notifier
type SMSNotifier struct{}    // 实现 Notifier
type PushNotifier struct{}   // 实现 Notifier
```

#### 2. 需要 Mock 测试外部依赖

```go
// 支付网关接口 - 便于测试时 Mock
type Gateway interface {
    Charge(ctx context.Context, amount decimal.Decimal, cardToken string) (*ChargeResult, error)
    Refund(ctx context.Context, chargeID string, amount decimal.Decimal) error
}

type StripeGateway struct{}    // 真实实现
type MockGateway struct{}      // Mock 实现（测试用）
```

#### 3. 需要运行时动态替换

```go
// 定价策略接口 - 运行时动态切换
type PricingStrategy interface {
    CalculatePrice(ctx context.Context, basePrice decimal.Decimal, user User) decimal.Decimal
}

type RegularPricing struct{}    // 原价
type VipPricing struct{}        // VIP 折扣
type PromotionPricing struct{}  // 促销折扣
```

### ❌ 不需要接口的情况

#### 1. 只有 1 种实现

```go
// ❌ 不需要：只有一种实现，提前定义接口
type UserRepository interface { ... }
type userRepository struct { ... }

// ✅ 正确：直接使用具体类型
type Repository struct { ... }  // 不需要 I 前缀
```

#### 2. 简单的 CRUD 服务

```go
// ❌ 不需要：简单的 CRUD，只有一种实现
type UserService interface { ... }

// ✅ 正确：直接用结构体
type Service struct { ... }
```

---

## 接口命名规范

### 单方法接口：使用 "er" 后缀

```go
type Reader interface { Read(p []byte) (n int, err error) }
type Writer interface { Write(p []byte) (n int, err error) }
type Closer interface { Close() error }
type Notifier interface { Send(ctx context.Context, msg string) error }
```

### 多方法接口：使用能力描述

```go
// ✅ 好的命名：描述能力
type Repository interface {
    Find(ctx context.Context, id uint64) (Entity, error)
    Save(ctx context.Context, entity Entity) error
    Delete(ctx context.Context, id uint64) error
}

type UserGetter interface {
    GetUser(ctx context.Context, id uint64) (*User, error)
    GetUserByEmail(ctx context.Context, email string) (*User, error)
}

// ✅ Go 社区惯例：接口名描述能力，不使用 I 前缀
// type IUserRepository interface {}  // 仅在命名冲突时使用
```

### 仅用于解决命名冲突时使用 I 前缀

```go
// ✅ 正确：解决命名冲突
type Packet struct{}                    // 已有具体类型
type IPacket interface { ... }          // 接口用 I 前缀区分
```

### ❌ 禁止的无意义命名

| 错误 | 正确 | 说明 |
|------|------|------|
| DefaultPacket | JsonPacket / RawPacket | Default 毫无语义 |
| BasicPacket | TinyPacket / MiniPacket | 暗示有"高级"版本 |
| PacketImpl | JsonPacket / XmlPacket | Impl 是最糟糕的命名 |
| PacketImpl1/Impl2 | PacketV1 / PacketV2 | 数字编号可读性差 |

---

## 接口定义位置

### 原则：由调用方定义接口

```go
// ✅ 好的示范：调用方定义需要什么

// order 包（调用方）定义自己需要什么
package order

type UserGetter interface {
    GetUser(ctx context.Context, id uint64) (*user.User, error)
}

type OrderService struct {
    userGetter UserGetter  // 依赖接口而非具体类型
}

// user 包（被调用方）实现接口
package user

type Repository struct { ... }

func (r *Repository) GetUser(ctx context.Context, id uint64) (*User, error) { ... }

// main.go 中组装
func main() {
    userRepo := &user.Repository{db: db}
    orderService := order.NewOrderService(userRepo) // 隐式实现
}
```

---

## 接口与实现文件组织

### 决策指南

| 场景 | 推荐做法 | 示例 |
|------|----------|------|
| **internal 包** | 接口和实现可以同文件 | `internal/cache/cache.go` |
| **单一实现，紧耦合** | 可以同文件 | `io.LimitedReader` |
| **小工具类型 (<100行)** | 可以同文件 | `bytes.Buffer` |
| **公共 API 接口** | 接口单独定义 | `http.ResponseWriter` 定义在 `net/http` |
| **多种实现 (mock+real)** | 接口单独定义，实现分文件 | `payment/gateway.go` + `payment/stripe.go` |
| **跨包调用的依赖** | 接口由调用方定义 | `order.UserGetter` 接口在 order 包 |

### 同文件场景示例

```go
// internal/cache/cache.go - internal 包可以同文件
type Cache interface {
    Get(ctx context.Context, key string) (string, error)
    Set(ctx context.Context, key string, value string, ttl time.Duration) error
}

type memoryCache struct { ... }  // 实现 Cache
```

### 分文件场景示例

```go
// payment/gateway.go - 公共 API 接口定义
type Gateway interface {
    Charge(ctx context.Context, amount decimal.Decimal, cardToken string) (*ChargeResult, error)
    Refund(ctx context.Context, chargeID string, amount decimal.Decimal) error
}

// payment/stripe.go - Stripe 实现
type StripeGateway struct { ... }

// payment/alipay.go - 支付宝实现
type AlipayGateway struct { ... }
```

### 标准库参考

- **同文件示例**：`io` 包中 `Reader` 接口与 `LimitedReader` 实现同文件（紧耦合）
- **分文件示例**：`http.ResponseWriter` 接口定义在 `net/http`，实现在 `net/http/response.go`

---

## 接口组合

### 基础组合模式

```go
// 小接口定义单一职责
type Reader interface { Read(p []byte) (n int, err error) }
type Writer interface { Write(p []byte) (n int, err error) }
type Closer interface { Close() error }

// 通过组合构建大接口
type ReadWriter interface { Reader; Writer }
type ReadCloser interface { Reader; Closer }
type WriteCloser interface { Writer; Closer }
type ReadWriteCloser interface { Reader; Writer; Closer }
```

### 职责分离原则

```go
// 好的设计：小接口职责单一
func Copy(dst Writer, src Reader) (written int64, err error) { ... }
func ReadFull(r Reader, buf []byte) (n int, err error) { ... }

// 使用者只实现需要的接口，不需要实现完整的 ReadWriteCloser
```

### 垂直组合模式

`http.ResponseWriter` 是垂直组合的典范：

```go
type ResponseWriter interface {
    Write([]byte) (int, error)
    Header() Header
    WriteHeader(statusCode int)
}

// 额外的可选能力通过独立接口定义
type Flusher interface { Flush() }
type Hijacker interface { Hijack() (net.Conn, *bufio.ReadWriter, error) }
type Pusher interface { Push(target string, opts *PushOptions) error }

// 实现可以同时实现多个接口
// response 实现了 ResponseWriter + Flusher + Hijacker
```

### 类型断言检查额外能力

```go
// 检查 ResponseWriter 是否支持 Flusher
if flusher, ok := w.(http.Flusher); ok {
    flusher.Flush()
}

// 检查多个可选能力
func handleUpgrade(w http.ResponseWriter) {
    if hijacker, ok := w.(http.Hijacker); !ok {
        http.Error(w, "不支持", http.StatusUpgradeRequired)
        return
    }
    // ...
}
```

### 实际应用示例

```go
// 存储接口组合设计
package storage

// 基础能力接口
type Reader interface { Read(ctx context.Context, key string) (io.ReadCloser, error) }
type Writer interface { Write(ctx context.Context, key string, r io.Reader) error }
type Deleter interface { Delete(ctx context.Context, key string) error }
type Lister interface { List(ctx context.Context, prefix string) ([]string, error) }

// 组合接口
type Storage interface { Reader; Writer; Deleter }
type FullStorage interface { Reader; Writer; Deleter; Lister }

// 使用示例：只需要读能力
func LoadConfig(s storage.Reader, key string) (*Config, error) { ... }

// 需要完整能力
func BackupStorage(src storage.FullStorage, dst storage.Storage) error { ... }
```

---

## 接口大小与组织

### 按功能职责组织

```go
// 不要硬性限制方法数量，而是按职责组织

// ✅ 按读写职责拆分
type UserReader interface {
    Find(ctx context.Context, id uint64) (*User, error)
    List(ctx context.Context, query Query) ([]User, error)
}

type UserWriter interface {
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id uint64) error
}

type UserRepository interface { UserReader; UserWriter }

// ✅ 大接口也合理：数据库驱动
type Conn interface {
    Prepare(query string) (Stmt, error)
    Close() error
    Begin() (Tx, error)
    Ping(ctx context.Context) error
    ExecContext(ctx context.Context, query string, args ...any) (Result, error)
    QueryContext(ctx context.Context, query string, args ...any) (Rows, error)
}
// 8 个方法是合理的，因为数据库连接确实需要这些操作
```

### 组合优于单一接口

```go
// ❌ 避免：大接口包含所有方法
type BigStorage interface {
    Create(), Read(), Update(), Delete(), Search(), Index(), ...
}

// ✅ 推荐：拆分为小接口 + 组合
type CRUD interface { Create(...); Read(...); Update(...); Delete(...) }
type Searchable interface { Search(ctx context.Context, query string) ([]any, error) }
type Indexable interface { Index(...); Reindex(...) }

// 按需组合
type BasicStorage interface { CRUD }
type SearchableStorage interface { CRUD; Searchable }
type FullStorage interface { CRUD; Searchable; Indexable }
```

---

## 常见反模式

### 反模式 1：所有结构体都配接口

```go
// ❌ 错误：为每个结构体定义接口（Java 风格）
type IUserService interface { ... }
type IUserRepository interface { ... }

// ✅ Go 风格：需要时再定义
// 1. 先写具体类型
// 2. 发现需要多种实现时再抽象
// 3. 由调用方定义接口
```

### 反模式 2：盲目分离接口和实现

```go
// ❌ 错误：机械地将接口和实现分开，即使不合理
// 只有 1 种实现，却非要分成两个文件
type Storage interface { ... }
type storageImpl struct { ... }

// ✅ 正确：根据场景决定
// 如果 internal 包、单一实现、小工具类型，可以同文件
// 如果公共 API、多实现、跨包调用，则分开
```

### 反模式 3：接口过大

```go
// ❌ 错误：大接口（12 个方法）
type Storage interface {
    Create(), Read(), Update(), Delete(),
    BatchCreate(), BatchRead(), ..., Search(), Index(), ...
}

// ✅ 正确：拆分为小接口 + 组合
// 参见"组合优于单一接口"章节
```

### 反模式 4：提前定义接口

```go
// ❌ 错误：先定义接口，再写实现
type UserService interface { ... }
type userService struct { ... }

// ✅ 正确：先写具体类型，需要时再抽象
type UserService struct { ... }

// 当发现需要 Mock 或多实现时，再提取接口
// 调用方定义：type UserCreator interface { Create(...) }
```

### 反模式 5：使用 I 前缀

```go
// ❌ 错误：Go 中不需要 I 前缀
type IUserRepository interface {}
type ICache interface {}

// ✅ 正确：Go 惯例，接口名描述能力
type Repository interface {}
type Cache interface {}

// 只有在解决命名冲突时才使用 I 前缀
```

---

## 决策流程

```
需要定义接口吗？
    ↓
有 2+ 种实现？
    ├─ 是 → 定义接口 ✅
    └─ 否
          ↓
    需要 Mock 测试？
          ├─ 是 → 定义接口 ✅
          └─ 否
                ↓
          需要运行时替换（策略模式）？
                ├─ 是 → 定义接口 ✅
                └─ 否 → 不需要接口 ❌
                      直接使用具体类型
```

---

## 快速检查清单

- [ ] 2+ 种实现才定义接口
- [ ] 接口由调用方定义
- [ ] 单方法接口用 "er" 后缀（Reader, Writer）
- [ ] 多方法接口用能力描述（Repository, Cache）
- [ ] 不使用 I 前缀（IRepository → Repository）
- [ ] 接口按功能职责组织，不硬性限制方法数量
- [ ] 优先使用小接口组合，避免单一接口膨胀
- [ ] 文件组织根据场景决定（internal/单一实现可同文件，公共 API/多实现应分开）
- [ ] 需要可选能力时，使用独立小接口 + 类型断言检查
