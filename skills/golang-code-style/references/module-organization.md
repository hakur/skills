# 模块组织规范

本文档提供 Go 项目的模块组织指导，帮助避免文件堆积和职责混杂。

## 核心原则

### 1. 文件夹深度限制

**最多 4 层目录深度**（生成的代码除外）。

```
✅ internal/domain/user/model.go       # 第 4 层，OK
❌ internal/domain/user/entity/types/user.go  # 第 6 层，太深
```

### 2. 文件数量指导原则

**目标 5-8 个 Go 文件，上限 15 个**（不含测试和 mock）。

| 情况 | 文件数 | 说明 |
|------|--------|------|
| 最佳 | 5-8 | 同一实体的不同方面（如 `user.go` + `user_errors.go` + `user_events.go`） |
| 可接受 | 9-12 | 复杂领域（如 Order 含订单项、定价、折扣等） |
| 必须拆分 | >15 | 职责混杂或堆积过多 |

**保留 vs 拆分判断标准**：

| 保留在一起 | 必须拆分 |
|---|---|
| 同一实体的不同方面（实体、错误、事件、验证） | 不同实体（user 和 order 放一起） |
| 高内聚：修改一个通常需要同时修改其他 | 低耦合：可以独立理解和维护 |

### 3. DDD 分层 vs 技术角色平铺

**本质区别**：
- **技术平铺** = 横向切割：全局按技术角色分，跨领域聚合 ❌
- **DDD 分层** = 纵向切割：先按领域分，内部再分层 ✓

| 坏（技术平铺） | 好（DDD 分层） |
|---|---|
| `internal/repo/user_repo.go` | `internal/domain/user/model.go` |
| `internal/repo/order_repo.go` | `internal/domain/order/model.go` |
| `internal/service/user_service.go` | `internal/application/user/service.go` |
| `internal/service/order_service.go` | `internal/application/order/service.go` |

**问题**：技术平铺时，修改 User 功能需要跨 3 个目录，无法独立查看领域代码，容易产生循环依赖。

### 4. 包组织方式

#### 方式 A：按职责分层（推荐）

适合中大型项目：

```
internal/
├── domain/              # 领域层
│   ├── user/           # model.go, errors.go, events.go
│   └── order/          # model.go, errors.go, events.go
├── application/         # 应用层
│   ├── user/service.go
│   └── order/service.go
├── infrastructure/      # 基础设施
│   ├── repository/user_repo.go
│   └── cache/redis/
└── interfaces/          # 接口适配层
    ├── http/user_handler.go
    └── grpc/
```

#### 方式 B：按功能模块

适合小型项目，每个模块内部仍分层：

```
internal/
└── modules/
    ├── user/          # domain/, application/, infrastructure/
    └── order/
```

### 5. 包命名规范

**原则**：
- 领域包用**业务名词**：`user`, `order`, `payment`
- 技术包用**技术名词**：`repository`, `cache`, `handler`
- **避免动词**：不用 `manage`, `handle`, `process`
- **避免模糊词**：不用 `utils`, `common`, `base`

### 6. 领域包内的文件组织

**允许的文件**（同一实体的不同方面）：
- `user.go` — 主实体
- `user_errors.go` — 领域错误
- `user_events.go` — 领域事件
- `user_validation.go` — 验证逻辑
- `user_types.go` — 相关类型
- `user_service.go` — 领域服务

**不允许的文件**（不同抽象层次）：
- `user_repo.go` → 移到 `infrastructure/repository/`
- `user_handler.go` → 移到 `interfaces/http/`
- `user_cache.go` → 移到 `infrastructure/cache/`

### 7. 共享代码处理

**真正共享的代码才放 `pkg/`，禁止 `common/` 垃圾堆**。`

**标准**：至少被 3+ 个包使用、稳定、通用无业务逻辑。

```
✅ internal/pkg/validator/email.go    # 通用验证器
❌ internal/common/utils.go          # 什么都往里放
```

领域特定的代码放在领域包内：
```
internal/domain/user/validation.go   # User 的验证规则
```

## 常见反模式

### 反模式 1：技术角色平铺

```
❌ internal/repo/*.go      # 所有 repo 混在一起
❌ internal/service/*.go   # 所有 service 混在一起
❌ internal/handler/*.go   # 所有 handler 混在一起
```

### 反模式 2：过度分包

```
❌ internal/user/entity/user.go          # 4 个文件分了 4 个包
❌ internal/user/valueobject/email.go
❌ internal/user/factory/user_factory.go
❌ internal/user/repository/user_repo.go
```

### 反模式 3：循环依赖

```go
// ❌ 包 A 依赖包 B，包 B 又依赖包 A
package user
import "project/order"

package order
import "project/user"  // 循环依赖！

// ✅ 通过接口解耦
package order
type UserGetter interface { ... }
```

## 决策流程

```
开始组织代码
    ↓
这是领域模型吗？     → 是 → domain/<name>/
    ↓ 否
这是技术实现吗？     → 是 → infrastructure/<tech>/
    ↓ 否
这是接口适配吗？     → 是 → interfaces/<protocol>/
    ↓ 否
                  → application/
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
