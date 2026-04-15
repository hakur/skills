# 设计哲学

## 1. 符合人类思维

代码应该读起来像自然语言。使用有意义的命名，使用卫语句（早期返回），而不是深度嵌套。

```go
// ❌ 反面：需要脑内反向推理
func HandleOrder(o *Order) error {
    if o != nil {
        if o.Status == "paid" {
            if o.Amount > 0 {
                // 主逻辑全在嵌套里
            } else {
                return errors.New("invalid amount")
            }
        } else {
            return errors.New("not paid")
        }
    } else {
        return errors.New("nil order")
    }
    return nil
}

// ✅ 正面：卫语句，主干逻辑在顶层
func (t *OrderService) HandleOrder(order *Order) error {
    if order == nil {
        return ErrNilOrder
    }
    if order.Status != OrderStatusPaid {
        return ErrOrderNotPaid
    }
    if order.Amount <= 0 {
        return ErrInvalidAmount
    }
    return t.processPaidOrder(order)
}
```

## 2. 代码复用

公共操作提取泛型或基类实现，不重复代码：

```go
// ❌ 反面：三处重复的 CRUD 代码
func (t *UserService) Create(ctx context.Context, req *CreateUserReq) error {
    return t.db.WithContext(ctx).Create(&User{Name: req.Name}).Error
}
func (t *UserService) Update(ctx context.Context, id uint, updates map[string]any) error {
    return t.db.WithContext(ctx).Model(&User{}).Where("id = ?", id).Updates(updates).Error
}

// ✅ 正面：通用 Repo 泛型实现
type Repo[T any] struct { db *gorm.DB }
func (t *Repo[T]) Create(ctx context.Context, entity *T) error {
    return t.db.WithContext(ctx).Create(entity).Error
}
```

## 3. 代码封装

内部细节（锁、缓存、重试）隐藏在方法签名后：

```go
// ✅ 业务层只表达意图，锁和查询细节封装在 WithLock 中
func (t *OrderService) Checkout(ctx context.Context, orderID uint) error {
    return t.orderRepo.WithLock(ctx, orderID, func(order *Order) error {
        if order.Status != OrderStatusPending {
            return ErrOrderCannotCheckout
        }
        order.Status = OrderStatusPaid
        return nil
    })
}
```

## 4. 解耦合

模块通过接口通信，不依赖具体实现：

```go
// ✅ 依赖接口，用户选择实现
type INotifier interface {
    Send(ctx context.Context, userID uint, msg string) error
}

type NotificationService struct {
    notifiers []INotifier // 不关心具体实现
}

func (t *NotificationService) Notify(ctx context.Context, userID uint, msg string) error {
    for _, n := range t.notifiers {
        n.Send(ctx, userID, msg) // 新增渠道只需注册
    }
    return nil
}
```

## 5. 第三方库优先 / 禁止造轮子

有成熟三方库就不要手写：

```go
// ❌ 手写重试逻辑
func DoWithRetry(fn func() error, maxRetries int) error {
    for i := 0; i < maxRetries; i++ {
        if err := fn(); err == nil { return nil }
        time.Sleep(time.Second * time.Duration(i+1)) // 没有抖动
    }
    return fmt.Errorf("max retries exceeded")
}

// ✅ 用 retry-go 库
func (t *Service) CallAPI(ctx context.Context) error {
    return retry.Do(func() error {
        return t.client.Call(ctx)
    }, retry.Attempts(3), retry.Context(ctx))
}
```

## 6. 禁止暴力堆砌

函数超过 200 行（不含空行和注释）必须拆分。每个步骤提取为独立函数：

```go
// ❌ 反面：一个函数堆所有逻辑
func (t *Handler) CreateUser(w http.ResponseWriter, r *http.Request) {
    // 解析请求 20行
    // 校验 30行
    // 入库 40行
    // 发通知 20行
    // 写响应 10行
}

// ✅ 正面：主函数只编排，每个步骤一个方法
func (t *Handler) CreateUser(w http.ResponseWriter, r *http.Request) {
    req, err := t.parseCreateUserReq(r)
    if err != nil { t.writeError(w, err); return }
    user, err := t.userService.CreateUser(r.Context(), req)
    if err != nil { t.writeError(w, err); return }
    t.writeJSON(w, http.StatusCreated, user)
}
```

## 7. 适度设计

- **简单功能**：直接写，不加设计模式
- **复杂多模块系统**：定义接口让用户选择策略

```go
// 简单 CRUD → 不需要接口
type UserRepo struct { db *gorm.DB }
func (t *UserRepo) Create(ctx context.Context, user *User) error { /* ... */ }

// 多种通知渠道 → 需要接口让用户选择
type INotifier interface { Send(ctx context.Context, msg string) error }
```

## 8. 职责单一

每个结构体一个职责。3+ 个职责时必须拆分：

```go
// ❌ 一个结构体干了三件事
type OrderService struct {
    db    *gorm.DB
    cache *ristretto.Cache
    lock  *redsync.RsMutex
}

// ✅ 每个职责独立接口
type OrderService struct {
    repo   IOrderRepo       // 只管持久化
    cache  IOrderCache      // 只管缓存
    events IEventPublisher  // 只管事件
}
```