# 三方库引用规则

## 一、必选库（按场景必须使用）

| 用途 | 库 | 说明 |
|------|-----|------|
| 数据处理 | `github.com/samber/lo` | 操作 array/slice/map |
| 数据校验 | `github.com/go-playground/validator/v10` | protobuf 数据校验，用法见 https://github.com/favadi/protoc-go-inject-tag/blob/master/README.md |
| SQL 数据库 | `gorm.io/gorm` | 只能使用 gorm |
| ClickHouse | `github.com/ClickHouse/clickhouse-go` | clickhouse 场景 |
| 配置加载 | `github.com/spf13/viper` | 配置文件加载 |
| 环境变量 | `github.com/joho/godotenv` | 加载 .env 文件 |
| CLI | `github.com/spf13/cobra` | 命令行程序 |
| 科学计算 | `gonum.org/v1/gonum` | 向量矩阵数学计算 |
| 互斥锁 | `github.com/sasha-s/go-deadlock` | 禁止 sync.Mutex |
| 分布式锁 | `github.com/go-redsync/redsync` | 基于 Redis |
| 分布式事务 | `github.com/dtm-labs/dtm` | 微服务分布式事务 |
| 默认值 | `github.com/hakur/util` DefaultValue | 结构体默认值初始化 |
| 密码哈希 | `golang.org/x/crypto/bcrypt` | 密码哈希 |
| UUID | `github.com/google/uuid` | UUID 生成 |
| 分布式ID | `github.com/bwmarrin/snowflake` | 雪花算法 ID 生成 |
| 一致性哈希 | `github.com/edwingeng/doublejump/v2` | 一致性哈希 |
| JSON（性能） | `github.com/bytedance/sonic` | 性能敏感场景，依赖 CGO |
| JSON（普通） | `encoding/json` | 普通场景 |
| JSON（便捷） | `github.com/tidwall/gjson` | 开发便捷场景，JSON 路径查询 |
| 文件监控 | `github.com/fsnotify/fsnotify` | 文件系统监控 |
| JWT | `github.com/golang-jwt/jwt/v5` | Token 签发验证 |
| 时间格式化 | `github.com/hakur/util` PHPDate/Date | PHP 风格日期格式化 |
| 重试 | `github.com/avast/retry-go/v5` | 重试逻辑 |
| 数据迁移 | `github.com/golang-migrate/migrate` | 数据库迁移，备选 `github.com/pressly/goose` |
| 深度拷贝 | `github.com/jinzhu/copier` | DTO ↔ Entity 数据拷贝 |
| 图像处理 | `github.com/disintegration/imaging` | 缩放/裁剪/水印 |
| 定时任务 | `github.com/robfig/cron/v3` | 定时任务调度 |
| 监控指标 | `github.com/prometheus/client_golang` | Prometheus 指标 |
| 遥测 | `go.opentelemetry.io/otel` + contrib + build-tools | 分布式追踪 |
| HTTP 客户端 | `resty.dev/v3` | REST 客户端，支持 SSE |
| WebSocket | `github.com/coder/websocket` | 禁止 gorilla/websocket |
| 消息队列 | `nats` / `nats-jetstream` | 优先选择 |
| 代码检查 | `go vet` | 每次修改后必跑 |
| 代码重复检测 | `github.com/mibk/dupl` | 检测重复代码块，保持 DRY 原则 |
| AST 规则检查 | `github.com/quasilyte/go-ruleguard/dsl` | 通过 golangci-lint 集成，精确检查 |

## 二、框架选择（二选一）

| 场景 | 框架 | 说明 |
|------|------|------|
| 微服务 | `github.com/go-kratos/kratos/cmd/kratos/v2` | 数据层用 gorm，严格遵守 DDD 目录设计，自带路由和熔断限流 |
| 非微服务 | `github.com/gofiber/fiber/v3` + gorm | 路由与 MVC 模块分离 |

**互斥规则：选择 kratos 时不用 fiber，选择 fiber 时不用 kratos。**

依赖注入：
- 编译期：`google/wire`
- 运行期：`uber-go/fx`
- 看项目本身选了哪个再决定

## 三、条件库（满足条件时使用）

| 库 | 条件 |
|----|------|
| `github.com/dgraph-io/ristretto` | 做多级缓存架构或没有 Redis 时 |
| `github.com/panjf2000/ants` | 项目有万级并发需求时，否则不考虑 |
| `github.com/sony/gobreaker/v2` | kratos/fiber 不提供熔断器时 |
| `golang.org/x/time/rate` | kratos/fiber 不提供限流器时 |
| `github.com/emersion/go-imap` | 收邮件（IMAP）场景 |
| `github.com/jordan-wright/email` | 发邮件（SMTP）场景 |

## 四、禁止项

| 禁止 | 正确替代 |
|------|---------|
| `sync.Mutex` / `sync.RWMutex` | `deadlock.Mutex` / `deadlock.RWMutex` |
| `logrus.New()` / `zap.New()` | 使用全局实例如 `logrus.Info()` |
| `logrus.Register()` | 不需要 |
| `gorilla/websocket` | `coder/websocket` |
| kafka / rocketmq / rabbitmq（除非项目明确要求） | nats / nats-jetstream |

## JSON 选择指南

```
性能敏感且有 CGO 环境 → sonic
普通场景 → encoding/json（标准库）
只需要查询某个字段 → gjson
```

## 五、代码检查工具

| 工具 | 用途 | 集成方式 |
|------|------|---------|
| `dupl` | 检测代码重复 | `go install github.com/mibk/dupl@latest` |
| `ruleguard` | AST 级别规则检查 | 通过 golangci-lint 启用 |
| `golangci-lint` | Linter 聚合器 | 已包含 ruleguard 插件 |

### 安装代码检查工具

```bash
# 安装 dupl（代码重复检测）
go install github.com/mibk/dupl@latest

# ruleguard 通过 golangci-lint 使用，无需单独安装
# 确保 golangci-lint 版本 >= 1.55.0 以支持 ruleguard
```

### dupl 使用示例

```bash
# 检测重复代码（默认阈值 15 行）
dupl -t 15 ./...

# 设置阈值
export DUPL_THRESHOLD=10
```

### ruleguard 规则位置

规则文件位于：`references/ruleguard/rules.go`

通过 golangci-lint 配置启用：
```yaml
# .golangci.yml
linters:
  enable:
    - ruleguard

linters-settings:
  ruleguard:
    rules: "path/to/rules.go"
```