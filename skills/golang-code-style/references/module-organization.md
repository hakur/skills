# 模块组织规范

本文档提供 Go 项目的模块组织指导，帮助避免文件堆积和职责混杂。

## 核心原则

### 1. 文件夹深度限制

**限制：最多 4 层目录深度**

```
✅ 好的结构（4 层）
project/
├── cmd/
│   └── server/           # 第 2 层
│       └── main.go
├── internal/
│   ├── domain/           # 第 2 层
│   │   └── user/         # 第 3 层
│   │       └── model.go  # 第 4 层 ✓
│   └── infrastructure/   # 第 2 层
│       └── repository/   # 第 3 层
│           └── user.go   # 第 4 层 ✓

❌ 坏的结构（超过 4 层）
project/
└── internal/
    └── domain/
        └── user/
            └── entity/
                └── types/
                    └── user.go  # 第 6 层 ✗
```

**例外情况**：生成的代码（`generated/`, `vendor/`）可以更深，但手写代码必须遵守限制。

### 2. 文件数量指导原则

**目标：单个文件夹 5-8 个 Go 文件（最佳实践）**
**上限：不超过 15 个 Go 文件**

计数不包括：
- `*_test.go` 测试文件
- `*_mock.go` mock 文件

```
✅ 好的结构（5-8 个文件，最佳）
internal/domain/user/
├── user.go              # 主实体
├── user_errors.go       # 领域错误
├── user_events.go       # 领域事件
├── user_validation.go   # 验证逻辑
└── user_types.go        # 相关类型
（共 5 个文件，同一领域的不同方面）

⚠️  可接受（9-12 个文件，复杂领域）
internal/domain/order/
├── order.go             # 主实体
├── order_item.go        # 订单项
├── order_status.go      # 订单状态
├── order_errors.go      # 领域错误
├── order_events.go      # 领域事件
├── pricing.go           # 定价逻辑
├── discount.go          # 折扣规则
└── shipping.go          # 物流信息
（共 8 个文件，紧密相关的领域对象）

❌ 坏的结构（> 15 个文件 或 职责混杂）
internal/user/
├── user.go, user_repo.go, user_service.go ...     # 用户相关
├── order.go, order_repo.go, order_service.go ...  # 订单相关 ✗ 不同领域
├── product.go ...                                 # 产品相关 ✗ 不同领域
└── ...
（职责混杂，文件堆积）
```

**何时保留，何时拆分？**

**保留在一起**（9-15 个文件可接受）：
- 文件是**同一实体的不同方面**（实体、错误、事件、验证等）
- 文件之间**高内聚**，修改一个通常需要同时修改其他
- 示例：order.go + order_item.go + order_errors.go + order_events.go

**必须拆分**（即使只有 6-8 个文件）：
- 文件是**不同实体**（user.go 和 order.go）
- 文件之间**低耦合**，可以独立理解和维护
- 示例：user/ 包和 order/ 包应该分开

```
❌ 拆分前（职责混杂，12 个文件）
internal/domain/
├── user.go, user_repo.go, user_service.go ...  # 用户领域
├── order.go, order_repo.go, order_service.go ...  # 订单领域 ✗ 混杂
└── product.go, product_repo.go ...  # 产品领域 ✗ 混杂

✅ 拆分后（每个包 3-6 个文件）
internal/domain/
├── user/                    # 用户领域包
│   ├── user.go             # 主实体
│   ├── user_errors.go      # 领域错误
│   └── user_events.go      # 领域事件
├── order/                   # 订单领域包
│   ├── order.go            # 主实体
│   ├── order_item.go       # 订单项
│   ├── order_errors.go     # 领域错误
│   └── order_events.go     # 领域事件
└── product/                 # 产品领域包
    ├── product.go          # 主实体
    └── product_errors.go   # 领域错误
```

### 3. DDD 分层 vs 技术角色平铺

**本质区别**：
- **技术角色平铺**（坏）：全局按技术角色分，跨领域聚合
- **DDD 分层**（好）：先按领域分，内部再按层分

```
❌ 技术角色平铺（坏）
internal/
├── repo/                      # 所有实体的 repo 混在一起
│   ├── user_repo.go          # 用户 repo
│   ├── order_repo.go         # 订单 repo  ✗ 跨领域
│   └── product_repo.go       # 产品 repo  ✗ 跨领域
├── service/                   # 所有 service 混在一起
│   ├── user_service.go       # 用户 service
│   ├── order_service.go      # 订单 service  ✗ 跨领域
│   └── product_service.go    # 产品 service  ✗ 跨领域
└── handler/
    ├── user_handler.go
    ├── order_handler.go      # ✗ 跨领域
    └── product_handler.go    # ✗ 跨领域

问题：
- 修改 User 功能需要跨 3 个目录
- 无法独立查看 User 领域的全部代码
- 容易产生循环依赖

✅ DDD 分层（好）
internal/
├── domain/                    # 领域层
│   ├── user/                 # 用户领域（包含 user 的所有领域逻辑）
│   │   ├── user.go          # 实体
│   │   ├── user_errors.go   # 错误
│   │   └── user_events.go   # 事件
│   └── order/                # 订单领域（包含 order 的所有领域逻辑）
│       ├── order.go         # 实体
│       ├── order_errors.go  # 错误
│       └── order_events.go  # 事件
├── application/              # 应用层
│   ├── user/                # 用户应用服务
│   │   └── user_service.go
│   └── order/               # 订单应用服务
│       └── order_service.go
└── infrastructure/          # 基础设施层
    ├── repository/         # 存储实现
    │   ├── user_repo.go   # 用户 repo 实现
    │   └── order_repo.go  # 订单 repo 实现

优势：
- User 领域的全部代码在同一个父目录下
- 可以独立理解、测试、修改 User 领域
- 清晰的领域边界
```

**记忆口诀**：
- 技术平铺 = 横向切割（所有领域的同一技术层放一起）✗
- DDD 分层 = 纵向切割（每个领域内部再分层）✓

### 4. 包组织方式

#### 方式 A：按职责分层（推荐）

适合：中大型项目，团队熟悉 DDD

```
internal/
├── domain/              # 领域层：业务核心，无技术依赖
│   ├── user/           # 用户领域
│   │   ├── model.go    # User 结构体
│   │   ├── errors.go   # 领域错误
│   │   └── events.go   # 领域事件
│   └── order/          # 订单领域
│       ├── model.go
│       └── errors.go
│
├── application/         # 应用层：编排领域逻辑
│   ├── user/           
│   │   ├── service.go  # 用户应用服务
│   │   └── dto.go      # DTO
│   └── order/
│       ├── service.go
│       └── dto.go
│
├── infrastructure/      # 基础设施层：技术实现
│   ├── repository/     # 存储实现
│   │   ├── user_repo.go
│   │   └── order_repo.go
│   ├── cache/          # 缓存实现
│   │   └── redis/
│   └── messaging/      # 消息队列实现
│       └── nats/
│
└── interfaces/          # 接口适配层：对外暴露
    ├── http/           # HTTP 处理器
    │   ├── user_handler.go
    │   └── order_handler.go
    └── grpc/           # gRPC 服务
        └── user_service.go
```

#### 方式 B：按功能模块（替代方案）

适合：小型项目，或功能高度内聚的模块

```
internal/
└── modules/            # 功能模块
    ├── user/          # 用户模块
    │   ├── domain/    # 内部仍分层
    │   │   └── model.go
    │   ├── application/
    │   │   └── service.go
    │   └── infrastructure/
    │       └── repo.go
    └── order/         # 订单模块
        ├── domain/
        ├── application/
        └── infrastructure/
```

**注意**：即使在方式 B 中，每个模块内部仍应保持分层。

### 4. 包命名规范

```
✅ 好的命名
├── user/              # 领域概念（名词）
├── order/             # 领域概念
├── repository/        # 技术概念（存储）
├── cache/             # 技术概念（缓存）
└── handler/           # 技术概念（处理器）

❌ 坏的命名
├── manage/            # 动词，太宽泛
├── handle/            # 动词
├── utils/             # 模糊，容易变成垃圾堆
├── common/            # 同样容易堆积
└── base/              # 抽象，不清晰
```

**命名原则**：
- 领域包：使用业务名词（user, order, payment）
- 技术包：使用技术名词（repository, cache, client）
- 避免动词：不使用 manage, handle, process

### 5. 领域包内的文件组织

**领域包内可以包含同一实体的不同方面，这不是混合职责**

```
✅ 领域包内允许的文件（同一实体的不同方面）
internal/domain/user/
├── user.go              # 主实体（必须）
├── user_errors.go       # 领域错误 ✅ 允许
├── user_events.go       # 领域事件 ✅ 允许
├── user_validation.go   # 验证逻辑 ✅ 允许
├── user_types.go        # 相关类型/值对象 ✅ 允许
└── user_service.go      # 领域服务 ✅ 允许

这些都是 User 领域的不同方面，不是混合职责。
```

**判断标准**：
- **同一实体**：所有文件都围绕 User 实体
- **高内聚**：修改 user.go 通常需要同时查看 user_errors.go
- **同一抽象层次**：都是领域逻辑，不涉及技术实现

**不允许的文件（真正的混合职责）**：
```
❌ 坏的示范：混合了技术实现
internal/domain/user/
├── user.go              # 领域模型 ✅
├── user_repo.go         # 数据库查询 ✗ 属于 infrastructure/
├── user_handler.go      # HTTP 处理器 ✗ 属于 interfaces/
├── user_cache.go        # 缓存逻辑 ✗ 属于 infrastructure/
└── user_client.go       # RPC 客户端 ✗ 属于 infrastructure/
```

**关键区别**：
- `user_errors.go`：定义 User 相关的领域错误 → **属于领域**
- `user_repo.go`：实现数据库查询 → **属于基础设施**
- `user_events.go`：定义 User 领域事件 → **属于领域**
- `user_handler.go`：处理 HTTP 请求 → **属于接口层**

### 6. 职责分离

**禁止在同一包内混合不同职责的代码**

**不同职责 = 不同抽象层次或不同技术领域**

```
❌ 坏的示范：混合了不同抽象层次
internal/user/
├── model.go           # 领域模型（业务逻辑）
├── repo.go            # 数据库查询（技术实现）✗ 不同层次
├── handler.go         # HTTP 处理器（接口层）✗ 不同层次
├── cache.go           # 缓存逻辑（技术实现）✗ 不同层次
└── grpc_client.go     # RPC 调用（技术实现）✗ 不同层次

问题：
- 修改数据库会影响 HTTP 接口
- 无法独立测试
- 依赖关系混乱

✅ 好的示范：按抽象层次分离
internal/
├── domain/user/                # 领域层：业务逻辑
│   ├── user.go                # 实体
│   ├── user_errors.go         # 领域错误
│   └── user_events.go         # 领域事件
├── application/user/           # 应用层：用例编排
│   └── user_service.go        # 应用服务
├── infrastructure/repository/  # 基础设施：存储实现
│   └── user_repo.go           # 数据库查询
├── infrastructure/cache/       # 基础设施：缓存实现
│   └── user_cache.go          # 缓存逻辑
└── interfaces/http/            # 接口层：HTTP 处理
    └── user_handler.go        # HTTP 处理器
```

### 6. 共享代码处理

**真正共享的代码才放在 common/pkg**

```
❌ 过早抽象
internal/
└── common/
    ├── utils.go      # 什么都往里放
    ├── helpers.go    # 模糊
    └── constants.go  # 常量也分开放

✅ 按需组织
internal/
├── pkg/
│   └── validator/    # 只有通用的验证器
│       └── email.go
└── domain/
    └── user/
        └── validation.go  # 领域特定的验证在这里
```

**共享代码标准**：
- 至少被 3+ 个包使用
- 稳定，不频繁修改
- 通用，无业务逻辑

### 7. 具体示例：保留 vs 拆分

**示例 1：保留在一起（9-12 个文件，同一领域）**

```
✅ 保留：Order 领域的多个方面（8 个文件）
internal/domain/order/
├── order.go              # 主实体
├── order_item.go         # 订单项（与 Order 紧密相关）
├── order_status.go       # 订单状态
├── order_errors.go       # 领域错误
├── order_events.go       # 领域事件
├── pricing.go            # 定价逻辑（Order 的一部分）
├── discount.go           # 折扣规则（Order 的一部分）
└── shipping.go           # 物流信息（Order 的一部分）

理由：
- 都是 Order 领域的不同方面
- 高内聚：修改订单通常需要同时查看订单项、定价、折扣
- 可以一起理解，不需要拆分
```

**示例 2：必须拆分（6-8 个文件，不同领域）**

```
❌ 拆分前（职责混杂，8 个文件）
internal/domain/
├── user.go               # 用户实体
├── user_errors.go        # 用户错误
├── order.go              # 订单实体 ✗ 不同领域
├── order_errors.go       # 订单错误 ✗ 不同领域
├── product.go            # 产品实体 ✗ 不同领域
├── product_errors.go     # 产品错误 ✗ 不同领域
├── payment.go            # 支付实体 ✗ 不同领域
└── payment_errors.go     # 支付错误 ✗ 不同领域

✅ 拆分后（每个包 2-3 个文件）
internal/domain/
├── user/                 # 用户领域
│   ├── user.go
│   └── user_errors.go
├── order/                # 订单领域
│   ├── order.go
│   └── order_errors.go
├── product/              # 产品领域
│   ├── product.go
│   └── product_errors.go
└── payment/              # 支付领域
    ├── payment.go
    └── payment_errors.go

理由：
- User、Order、Product、Payment 是独立的领域实体
- 低耦合：修改 User 不需要了解 Order
- 应该独立分包
```

**示例 3：边界情况（需要判断）**

```
⚠️  情况：User 领域有 12 个文件

internal/domain/user/
├── user.go
├── user_profile.go       # 用户资料（与 User 紧密相关）✅ 保留
├── user_setting.go       # 用户设置（与 User 紧密相关）✅ 保留
├── user_errors.go        # 领域错误 ✅ 保留
├── user_events.go        # 领域事件 ✅ 保留
├── user_validation.go    # 验证逻辑 ✅ 保留
├── user_types.go         # 相关类型 ✅ 保留
├── permission.go         # 权限（可能独立？）⚠️  判断
├── role.go               # 角色（可能独立？）⚠️  判断
├── user_repo.go          # ✗ 移动到 infrastructure/
├── user_cache.go         # ✗ 移动到 infrastructure/
└── user_handler.go       # ✗ 移动到 interfaces/

判断：
- user_profile, user_setting：与 User 紧密相关，保留
- permission, role：如果权限系统复杂，可拆分为独立 domain/permission/
- user_repo, user_cache, user_handler：不同抽象层次，必须移出
```

## 常见反模式

### 反模式 1：技术角色平铺

```
❌ 所有 repo 放在一起，所有 service 放在一起
internal/
├── repo/
│   ├── user_repo.go
│   ├── order_repo.go
│   └── product_repo.go
├── service/
│   ├── user_service.go
│   ├── order_service.go
│   └── product_service.go
└── handler/
    ├── user_handler.go
    ├── order_handler.go
    └── product_handler.go

问题：修改 user 功能需要跨 3 个目录
```

### 反模式 2：过度分包

```
❌ 过度拆分
internal/
└── user/
    ├── entity/
    │   └── user.go
    ├── valueobject/
    │   └── email.go
    ├── factory/
    │   └── user_factory.go
    └── repository/
        └── user_repo.go

问题：只有 4 个文件却分了 4 个包，过度设计
```

### 反模式 3：循环依赖

```
❌ 包 A 依赖包 B，包 B 又依赖包 A
package user
import "project/order"  // 依赖 order

type UserService struct {
    OrderService *order.Service
}

package order
import "project/user"  // 循环依赖！

type OrderService struct {
    UserService *user.Service
}

✅ 解决方案：通过接口解耦
package order

type UserGetter interface {
    GetUser(ctx context.Context, id uint) (*user.User, error)
}

type OrderService struct {
    userGetter UserGetter  // 依赖接口，不依赖具体包
}
```

## 决策流程

```
开始组织代码
    ↓
这是领域模型吗？
    ├─ 是 → 放入 domain/<domain-name>/
    └─ 否
          ↓
    这是技术实现吗？
          ├─ 是 → 放入 infrastructure/<tech>/
          └─ 否
                ↓
          这是接口适配吗？
                ├─ 是 → 放入 interfaces/<protocol>/
                └─ 否 → 放入 application/
```

## 快速检查清单

- [ ] 文件夹深度 ≤ 4 层
- [ ] 单个文件夹文件数：目标 5-8 个，上限 15 个
- [ ] 文件是同一实体的不同方面（保留）还是不同实体（拆分）
- [ ] 包名是名词，不是动词
- [ ] 同一包内代码职责在同一抽象层次
- [ ] 领域包内不包含基础设施代码（repo, cache, handler）
- [ ] 共享代码真的被多处使用
- [ ] 无循环依赖
