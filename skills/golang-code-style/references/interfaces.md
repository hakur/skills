# 接口设计规范

本文档提供完整的 Go 接口设计指南，包括决策框架、命名规范、文件组织和接口组合模式。

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
// 通知渠道接口 - 多种实现需要抽象
package notification

type Notifier interface {
    Send(ctx context.Context, userID uint64, msg string) error
}

// 邮件通知实现
type EmailNotifier struct {
    smtpHost string
    smtpPort int
    username string
    password string
}

func (e *EmailNotifier) Send(ctx context.Context, userID uint64, msg string) error {
    // 通过 SMTP 发送邮件
    return nil
}

// 短信通知实现
type SMSNotifier struct {
    apiKey    string
    apiSecret string
    endpoint  string
}

func (s *SMSNotifier) Send(ctx context.Context, userID uint64, msg string) error {
    // 调用短信服务商 API
    return nil
}

// 推送通知实现
type PushNotifier struct {
    firebaseApp *firebase.App
}

func (p *PushNotifier) Send(ctx context.Context, userID uint64, msg string) error {
    // 调用 FCM 推送服务
    return nil
}

// 使用示例：可以同时发送多种通知
func NotifyAll(ctx context.Context, notifiers []Notifier, userID uint64, msg string) error {
    var errs []error
    for _, n := range notifiers {
        if err := n.Send(ctx, userID, msg); err != nil {
            errs = append(errs, err)
        }
    }
    return errors.Join(errs...)
}

// 实际调用
func main() {
    notifiers := []Notifier{
        &EmailNotifier{/* ... */},
        &SMSNotifier{/* ... */},
        &PushNotifier{/* ... */},
    }
    
    if err := NotifyAll(context.Background(), notifiers, 123, "Hello!"); err != nil {
        log.Println("通知发送失败:", err)
    }
}
```

#### 2. 需要 Mock 测试外部依赖

```go
// 支付网关接口 - 便于测试时 Mock
package payment

import (
    "context"
    "github.com/shopspring/decimal"
)

type ChargeResult struct {
    ChargeID string
    Amount   decimal.Decimal
    Status   string
}

type PaymentGateway interface {
    Charge(ctx context.Context, amount decimal.Decimal, cardToken string) (*ChargeResult, error)
    Refund(ctx context.Context, chargeID string, amount decimal.Decimal) error
}

// 真实实现：Stripe
type StripeGateway struct {
    apiKey string
    client *stripe.Client
}

func (s *StripeGateway) Charge(ctx context.Context, amount decimal.Decimal, cardToken string) (*ChargeResult, error) {
    // 调用 Stripe API
    return &ChargeResult{
        ChargeID: "ch_123",
        Amount:   amount,
        Status:   "succeeded",
    }, nil
}

func (s *StripeGateway) Refund(ctx context.Context, chargeID string, amount decimal.Decimal) error {
    // 调用 Stripe API 退款
    return nil
}

// Mock 实现（仅用于测试）
type MockPaymentGateway struct {
    mock.Mock
}

func (m *MockPaymentGateway) Charge(ctx context.Context, amount decimal.Decimal, cardToken string) (*ChargeResult, error) {
    args := m.Called(ctx, amount, cardToken)
    return args.Get(0).(*ChargeResult), args.Error(1)
}

func (m *MockPaymentGateway) Refund(ctx context.Context, chargeID string, amount decimal.Decimal) error {
    args := m.Called(ctx, chargeID, amount)
    return args.Error(0)
}

// 测试示例
func TestProcessOrder(t *testing.T) {
    mockGateway := new(MockPaymentGateway)
    mockGateway.On("Charge", mock.Anything, decimal.NewFromFloat(100.00), "tok_visa").
        Return(&ChargeResult{ChargeID: "ch_test", Status: "succeeded"}, nil)
    
    service := NewOrderService(mockGateway)
    err := service.ProcessOrder(context.Background(), Order{Amount: decimal.NewFromFloat(100.00)})
    
    assert.NoError(t, err)
    mockGateway.AssertExpectations(t)
}
```

#### 3. 需要运行时动态替换

```go
// 定价策略接口 - 运行时动态切换
package pricing

import (
    "context"
    "github.com/shopspring/decimal"
)

type User struct {
    ID      uint64
    Level   string // "regular", "vip", "svip"
    Points  int
}

type PricingStrategy interface {
    CalculatePrice(ctx context.Context, basePrice decimal.Decimal, user User) decimal.Decimal
}

// 普通用户定价
type RegularPricing struct{}

func (r *RegularPricing) CalculatePrice(ctx context.Context, basePrice decimal.Decimal, user User) decimal.Decimal {
    return basePrice // 原价
}

// VIP 用户定价
type VipPricing struct{}

func (v *VipPricing) CalculatePrice(ctx context.Context, basePrice decimal.Decimal, user User) decimal.Decimal {
    // VIP 9 折
    return basePrice.Mul(decimal.NewFromFloat(0.9))
}

// 促销活动定价
type PromotionPricing struct {
    DiscountPercent decimal.Decimal // 如 20 表示 8 折
}

func (p *PromotionPricing) CalculatePrice(ctx context.Context, basePrice decimal.Decimal, user User) decimal.Decimal {
    discount := decimal.NewFromInt(100).Sub(p.DiscountPercent).Div(decimal.NewFromInt(100))
    return basePrice.Mul(discount)
}

// 使用示例
func GetPricingStrategy(user User) PricingStrategy {
    switch user.Level {
    case "vip":
        return &VipPricing{}
    case "svip":
        return &VipPricing{} // SVIP 也使用 VIP 定价
    default:
        return &RegularPricing{}
    }
}

// 订单服务
func (s *OrderService) CalculateOrderPrice(ctx context.Context, items []Item, user User) (decimal.Decimal, error) {
    basePrice := calculateItemsTotal(items)
    
    // 根据用户等级获取定价策略
    strategy := GetPricingStrategy(user)
    
    // 应用定价策略
    finalPrice := strategy.CalculatePrice(ctx, basePrice, user)
    
    // 检查是否有促销活动
    if promo := s.getActivePromotion(); promo != nil {
        finalPrice = promo.CalculatePrice(ctx, finalPrice, user)
    }
    
    return finalPrice, nil
}
```

### ❌ 不需要接口的情况

#### 1. 只有 1 种实现

```go
// ❌ 不需要：只有一种实现，提前定义接口
type UserRepository interface {
    Find(ctx context.Context, id uint64) (*User, error)
    Save(ctx context.Context, user *User) error
    Delete(ctx context.Context, id uint64) error
}

type userRepository struct {
    db *gorm.DB
}

// ✅ 正确：直接使用具体类型
type Repository struct {
    db *gorm.DB
}

func (r *Repository) Find(ctx context.Context, id uint64) (*User, error) {
    var user User
    err := r.db.WithContext(ctx).First(&user, id).Error
    return &user, err
}

func (r *Repository) Save(ctx context.Context, user *User) error {
    return r.db.WithContext(ctx).Save(user).Error
}

func (r *Repository) Delete(ctx context.Context, id uint64) error {
    return r.db.WithContext(ctx).Delete(&User{}, id).Error
}
```

#### 2. 简单的 CRUD 服务

```go
// ❌ 不需要：简单的 CRUD，只有一种实现
type UserService interface {
    Create(ctx context.Context, req CreateUserReq) (*User, error)
    Get(ctx context.Context, id uint64) (*User, error)
    Update(ctx context.Context, id uint64, req UpdateUserReq) (*User, error)
    Delete(ctx context.Context, id uint64) error
}

// ✅ 正确：直接用结构体
type Service struct {
    repo *Repository
}

func (s *Service) Create(ctx context.Context, req CreateUserReq) (*User, error) {
    user := &User{
        Name:  req.Name,
        Email: req.Email,
    }
    if err := s.repo.Save(ctx, user); err != nil {
        return nil, err
    }
    return user, nil
}
// ... 其他方法
```

---

## 接口命名规范

### 单方法接口：使用 "er" 后缀

```go
// 单方法接口使用 "er" 后缀 - 这是 Go 的惯例
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type Closer interface {
    Close() error
}

type Notifier interface {
    Send(ctx context.Context, msg string) error
}

type Stringer interface {
    String() string
}

type Formatter interface {
    Format(f fmt.State, verb rune)
}
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

type Cache interface {
    Get(ctx context.Context, key string) (Value, error)
    Set(ctx context.Context, key string, value Value, ttl time.Duration) error
    Delete(ctx context.Context, key string) error
}

// ❌ 不需要 I 前缀（Go 社区惯例）
// type IUserRepository interface {}  // 不推荐
// type ICache interface {}          // 不推荐
```

### 仅用于解决命名冲突时使用 I 前缀

```go
// ✅ 正确：解决命名冲突
type Packet struct{}                    // 已有具体类型
type IPacket interface {                 // 接口用 I 前缀区分
    Unmarshal(v any) error
}
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

import (
    "context"
    "myapp/user"
)

// UserGetter 定义 order 包需要的能力
type UserGetter interface {
    GetUser(ctx context.Context, id uint64) (*user.User, error)
}

type OrderService struct {
    userGetter UserGetter  // 依赖接口而非具体类型
}

func NewOrderService(userGetter UserGetter) *OrderService {
    return &OrderService{userGetter: userGetter}
}

func (s *OrderService) CreateOrder(ctx context.Context, userID uint64, items []Item) (*Order, error) {
    // 通过接口获取用户信息
    u, err := s.userGetter.GetUser(ctx, userID)
    if err != nil {
        return nil, fmt.Errorf("获取用户失败: %w", err)
    }
    
    // ... 创建订单逻辑
    return &Order{UserID: userID, Items: items}, nil
}

// user 包（被调用方）实现接口
package user

import "context"

type Repository struct {
    db *gorm.DB
}

func (r *Repository) GetUser(ctx context.Context, id uint64) (*User, error) {
    var user User
    err := r.db.WithContext(ctx).First(&user, id).Error
    if err != nil {
        return nil, err
    }
    return &user, nil
}

// main.go 中组装
func main() {
    userRepo := &user.Repository{db: db}
    orderService := order.NewOrderService(userRepo) // userRepo 隐式实现了 order.UserGetter
    // ...
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
// internal/cache/cache.go
// internal 包不对外暴露，接口和实现可以放在一起
package cache

import (
    "context"
    "time"
)

// Cache 接口定义 - 与实现同文件
// 因为这是一个 internal 包，不对外暴露，且只有一种实现
type Cache interface {
    Get(ctx context.Context, key string) (string, error)
    Set(ctx context.Context, key string, value string, ttl time.Duration) error
    Delete(ctx context.Context, key string) error
}

// memoryCache 实现
type memoryCache struct {
    data map[string]item
    mu   sync.RWMutex
}

type item struct {
    value      string
    expiration time.Time
}

func NewMemoryCache() Cache {
    c := &memoryCache{
        data: make(map[string]item),
    }
    go c.cleanup()
    return c
}

func (c *memoryCache) Get(ctx context.Context, key string) (string, error) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    
    item, ok := c.data[key]
    if !ok || time.Now().After(item.expiration) {
        return "", ErrNotFound
    }
    return item.value, nil
}

func (c *memoryCache) Set(ctx context.Context, key string, value string, ttl time.Duration) error {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    c.data[key] = item{
        value:      value,
        expiration: time.Now().Add(ttl),
    }
    return nil
}

func (c *memoryCache) Delete(ctx context.Context, key string) error {
    c.mu.Lock()
    defer c.mu.Unlock()
    delete(c.data, key)
    return nil
}

func (c *memoryCache) cleanup() {
    ticker := time.NewTicker(time.Minute)
    defer ticker.Stop()
    
    for range ticker.C {
        c.mu.Lock()
        now := time.Now()
        for key, item := range c.data {
            if now.After(item.expiration) {
                delete(c.data, key)
            }
        }
        c.mu.Unlock()
    }
}
```

### 分文件场景示例

```go
// payment/gateway.go
// 公共 API 接口定义
package payment

import (
    "context"
    "github.com/shopspring/decimal"
)

type Gateway interface {
    Charge(ctx context.Context, amount decimal.Decimal, cardToken string) (*ChargeResult, error)
    Refund(ctx context.Context, chargeID string, amount decimal.Decimal) error
}

type ChargeResult struct {
    ChargeID string
    Amount   decimal.Decimal
    Status   string
}

// payment/stripe.go
// Stripe 实现
package payment

import (
    "context"
    "github.com/shopspring/decimal"
    "github.com/stripe/stripe-go/v74"
)

type StripeGateway struct {
    client *stripe.Client
}

func NewStripeGateway(apiKey string) *StripeGateway {
    return &StripeGateway{
        client: stripe.NewClient(apiKey),
    }
}

func (s *StripeGateway) Charge(ctx context.Context, amount decimal.Decimal, cardToken string) (*ChargeResult, error) {
    // Stripe 具体实现
    return &ChargeResult{
        ChargeID: "ch_stripe_123",
        Amount:   amount,
        Status:   "succeeded",
    }, nil
}

func (s *StripeGateway) Refund(ctx context.Context, chargeID string, amount decimal.Decimal) error {
    // Stripe 退款实现
    return nil
}

// payment/alipay.go
// 支付宝实现
package payment

import (
    "context"
    "github.com/shopspring/decimal"
)

type AlipayGateway struct {
    appID     string
    publicKey string
}

func NewAlipayGateway(appID, publicKey string) *AlipayGateway {
    return &AlipayGateway{
        appID:     appID,
        publicKey: publicKey,
    }
}

func (a *AlipayGateway) Charge(ctx context.Context, amount decimal.Decimal, cardToken string) (*ChargeResult, error) {
    // 支付宝具体实现
    return &ChargeResult{
        ChargeID: "alipay_456",
        Amount:   amount,
        Status:   "success",
    }, nil
}

func (a *AlipayGateway) Refund(ctx context.Context, chargeID string, amount decimal.Decimal) error {
    // 支付宝退款实现
    return nil
}
```

### 标准库参考

```go
// 同文件示例：io.LimitedReader
// 接口 Reader 与实现 LimitedReader 在同一个包中，紧耦合
package io

type Reader interface {
    Read(p []byte) (n int, err error)
}

type LimitedReader struct {
    R Reader // underlying reader
    N int64  // max bytes remaining
}

func (l *LimitedReader) Read(p []byte) (n int, err error) {
    if l.N <= 0 {
        return 0, EOF
    }
    if int64(len(p)) > l.N {
        p = p[0:l.N]
    }
    n, err = l.R.Read(p)
    l.N -= int64(n)
    return
}

// 分文件示例：http.ResponseWriter
// 接口定义在 net/http，实现在 net/http/response.go
package http

type ResponseWriter interface {
    Header() Header
    Write([]byte) (int, error)
    WriteHeader(statusCode int)
}

// 实现在 net/http/server.go 中的 response 结构体
// 但 ResponseWriter 作为公共 API 接口在 http 包定义
```

---

## 接口组合

### 基础组合模式

```go
// 小接口定义单一职责
package io

type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type Closer interface {
    Close() error
}

type Seeker interface {
    Seek(offset int64, whence int) (int64, error)
}

// 通过组合构建大接口
type ReadWriter interface {
    Reader
    Writer
}

type ReadCloser interface {
    Reader
    Closer
}

type WriteCloser interface {
    Writer
    Closer
}

type ReadWriteCloser interface {
    Reader
    Writer
    Closer
}

type ReadSeeker interface {
    Reader
    Seeker
}

type ReadWriteSeeker interface {
    Reader
    Writer
    Seeker
}
```

### 职责分离原则

```go
// 好的设计：小接口职责单一
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type Closer interface {
    Close() error
}

// 使用时按需组合
func Copy(dst Writer, src Reader) (written int64, err error) {
    // 只需要 Reader 和 Writer，不关心 Close
}

func ReadFull(r Reader, buf []byte) (n int, err error) {
    // 只需要 Reader
}

// 使用者只实现需要的接口
// 不需要实现完整的 ReadWriteCloser
```

### 垂直组合模式

```go
// http.ResponseWriter 是垂直组合的典范
package http

// ResponseWriter 嵌入基础接口
type ResponseWriter interface {
    // 基础写能力
    Write([]byte) (int, error)
    
    // HTTP 特定的能力
    Header() Header
    WriteHeader(statusCode int)
}

// 额外的可选能力通过独立接口定义
type Flusher interface {
    // Flush 将缓冲数据发送到客户端
    Flush()
}

type Hijacker interface {
    // Hijack 让调用者接管连接
    Hijack() (net.Conn, *bufio.ReadWriter, error)
}

type Pusher interface {
    // Push 发起 HTTP/2 服务器推送
    Push(target string, opts *PushOptions) error
}

// 实现可以同时实现多个接口
// response 实现了 ResponseWriter + Flusher + Hijacker
```

### 类型断言检查额外能力

```go
// 检查 ResponseWriter 是否支持 Flusher
func flushResponse(w http.ResponseWriter) {
    // 尝试转换为 Flusher 接口
    if flusher, ok := w.(http.Flusher); ok {
        flusher.Flush()
    }
    // 如果不支持，静默忽略
}

// 检查多个可选能力
func handleUpgrade(w http.ResponseWriter, r *http.Request) {
    // 检查是否支持 Hijacker
    hijacker, ok := w.(http.Hijacker)
    if !ok {
        http.Error(w, "WebSocket 不支持", http.StatusUpgradeRequired)
        return
    }
    
    // 检查是否支持 Flusher
    if flusher, ok := w.(http.Flusher); ok {
        flusher.Flush()
    }
    
    // 接管连接
    conn, bufrw, err := hijacker.Hijack()
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    defer conn.Close()
    
    // ... 处理 WebSocket 或长连接
}

// 检查自定义接口组合
type ReadWriteFlushCloser interface {
    io.ReadWriter
    http.Flusher
    io.Closer
}

func processStream(rw io.ReadWriter) error {
    // 检查是否支持 Flush
    if flusher, ok := rw.(http.Flusher); ok {
        flusher.Flush()
    }
    
    // 检查是否支持 Close
    if closer, ok := rw.(io.Closer); ok {
        defer closer.Close()
    }
    
    // ... 处理数据
    return nil
}
```

### 实际应用示例

```go
// 存储接口组合设计
package storage

import (
    "context"
    "io"
)

// 基础能力接口
type Reader interface {
    Read(ctx context.Context, key string) (io.ReadCloser, error)
}

type Writer interface {
    Write(ctx context.Context, key string, r io.Reader) error
}

type Deleter interface {
    Delete(ctx context.Context, key string) error
}

type Lister interface {
    List(ctx context.Context, prefix string) ([]string, error)
}

// 组合接口
type Storage interface {
    Reader
    Writer
    Deleter
}

type FullStorage interface {
    Reader
    Writer
    Deleter
    Lister
}

// 使用示例
// 只需要读能力
func LoadConfig(s storage.Reader, key string) (*Config, error) {
    r, err := s.Read(context.Background(), key)
    if err != nil {
        return nil, err
    }
    defer r.Close()
    
    var cfg Config
    if err := json.NewDecoder(r).Decode(&cfg); err != nil {
        return nil, err
    }
    return &cfg, nil
}

// 需要完整能力
func BackupStorage(src storage.FullStorage, dst storage.Storage) error {
    // 列出所有对象
    keys, err := src.List(context.Background(), "")
    if err != nil {
        return err
    }
    
    for _, key := range keys {
        r, err := src.Read(context.Background(), key)
        if err != nil {
            return err
        }
        
        if err := dst.Write(context.Background(), key, r); err != nil {
            r.Close()
            return err
        }
        r.Close()
    }
    
    return nil
}
```

---

## 接口大小与组织

### 按功能职责组织

```go
// 不要硬性限制方法数量，而是按职责组织

// ✅ 按读写职责拆分
type UserReader interface {
    Find(ctx context.Context, id uint64) (*User, error)
    FindByEmail(ctx context.Context, email string) (*User, error)
    List(ctx context.Context, query Query) ([]User, error)
    Count(ctx context.Context, filter Filter) (int64, error)
}

type UserWriter interface {
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id uint64) error
}

type UserRepository interface {
    UserReader
    UserWriter
}

// ✅ 大接口也合理：数据库驱动
type Conn interface {
    Prepare(query string) (Stmt, error)
    Close() error
    Begin() (Tx, error)
    
    // 驱动特定的准备方法
    PrepareContext(ctx context.Context, query string) (Stmt, error)
    
    // 上下文支持的开始事务
    BeginTx(ctx context.Context, opts TxOptions) (Tx, error)
    
    // Ping 验证连接
    Ping(ctx context.Context) error
    
    // 连接属性
    ExecContext(ctx context.Context, query string, args ...any) (Result, error)
    QueryContext(ctx context.Context, query string, args ...any) (Rows, error)
}
// 8 个方法是合理的，因为数据库连接确实需要这些操作
```

### 组合优于单一接口

```go
// ❌ 避免：大接口包含所有方法
type BigStorage interface {
    Create()
    Read()
    Update()
    Delete()
    Search()
    Index()
    Reindex()
    Stats()
    BatchCreate()
    BatchDelete()
    Export()
    Import()
}

// ✅ 推荐：拆分为小接口 + 组合
type CRUD interface {
    Create(ctx context.Context, obj any) error
    Read(ctx context.Context, id string) (any, error)
    Update(ctx context.Context, obj any) error
    Delete(ctx context.Context, id string) error
}

type Searchable interface {
    Search(ctx context.Context, query string) ([]any, error)
}

type Indexable interface {
    Index(ctx context.Context, obj any) error
    Reindex(ctx context.Context) error
}

type BatchOperable interface {
    BatchCreate(ctx context.Context, objs []any) error
    BatchDelete(ctx context.Context, ids []string) error
}

type Exportable interface {
    Export(ctx context.Context, w io.Writer) error
    Import(ctx context.Context, r io.Reader) error
}

// 按需组合
type BasicStorage interface {
    CRUD
}

type SearchableStorage interface {
    CRUD
    Searchable
}

type FullStorage interface {
    CRUD
    Searchable
    Indexable
    BatchOperable
    Exportable
}
```

---

## 常见反模式

### 反模式 1：所有结构体都配接口

```go
// ❌ 错误：为每个结构体定义接口（Java 风格）
type IUserService interface { 
    CreateUser(ctx context.Context, req CreateUserReq) (*User, error)
    GetUser(ctx context.Context, id uint64) (*User, error)
}
type UserService struct {}

type IUserRepository interface {
    Save(ctx context.Context, user *User) error
    Find(ctx context.Context, id uint64) (*User, error)
}
type UserRepository struct {}

// ✅ Go 风格：需要时再定义
// 1. 先写具体类型
// 2. 发现需要多种实现时再抽象
// 3. 由调用方定义接口
```

### 反模式 2：盲目分离接口和实现

```go
// ❌ 错误：机械地将接口和实现分开，即使不合理
// 只有 1 种实现，却非要分成两个文件

// storage/interface.go
type Storage interface {
    Get(key string) (string, error)
    Set(key string, value string) error
}

// storage/impl.go
type storageImpl struct {
    data map[string]string
}

func NewStorage() Storage {
    return &storageImpl{data: make(map[string]string)}
}

// ✅ 正确：根据场景决定
// 如果 internal 包、单一实现、小工具类型，可以同文件
// 如果公共 API、多实现、跨包调用，则分开
```

### 反模式 3：接口过大

```go
// ❌ 错误：大接口（12 个方法）
type Storage interface {
    Create(), Read(), Update(), Delete(),
    BatchCreate(), BatchRead(), BatchUpdate(), BatchDelete(),
    Search(), Index(), Reindex(), Stats()
}

// ✅ 正确：拆分为小接口 + 组合
// 参见"组合优于单一接口"章节
```

### 反模式 4：提前定义接口

```go
// ❌ 错误：先定义接口，再写实现
type UserService interface {
    Create(ctx context.Context, req CreateUserReq) (*User, error)
    Get(ctx context.Context, id uint64) (*User, error)
    Update(ctx context.Context, id uint64, req UpdateUserReq) (*User, error)
    Delete(ctx context.Context, id uint64) error
}

type userService struct {
    repo *userRepository
}

// ✅ 正确：先写具体类型，需要时再抽象
type UserService struct {
    repo *UserRepository
}

func (s *UserService) Create(ctx context.Context, req CreateUserReq) (*User, error) {
    // 实现...
}
// ...

// 当发现需要 Mock 或多实现时，再提取接口
// 调用方定义：
// type UserCreator interface {
//     Create(ctx context.Context, req CreateUserReq) (*User, error)
// }
```

### 反模式 5：使用 I 前缀

```go
// ❌ 错误：Go 中不需要 I 前缀
type IUserRepository interface {}
type ICache interface {}
type ILogger interface {}

// ✅ 正确：Go 惯例，接口名描述能力
type Repository interface {}
type Cache interface {}
type Logger interface {}

// 只有在解决命名冲突时才使用 I 前缀
// 例如已有具体类型 Packet，接口可命名为 IPacket
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
