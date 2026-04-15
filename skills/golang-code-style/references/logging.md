# 日志库使用规范

## 核心规则：必须使用全局实例

日志库（logrus / zap / zerolog）必须使用全局实例调用，禁止创建新实例和二次包装。

## 正确用法

```go
import "github.com/sirupsen/logrus"

// ✅ 正确：直接使用全局方法
logrus.Info("server started")
logrus.WithFields(logrus.Fields{
    "port": 8080,
}).Info("server listening")
```

```go
import "go.uber.org/zap"

// ✅ 正确：使用 zap 的全局 logger
zap.L().Info("server started", zap.Int("port", 8080))
```

## 禁止用法

```go
// ❌ 禁止：创建新实例
logger := logrus.New()

// ❌ 禁止：二次包装
type MyLogger struct {
    inner *logrus.Logger
}
func NewMyLogger() *MyLogger { /* ... */ }

// ❌ 禁止：logrus.Register()
logrus.Register()
```

## 日志级别使用

| 级别 | 场景 |
|------|------|
| Panic | 不可恢复的错误，程序即将退出 |
| Fatal | 严重错误，程序会退出 |
| Error | 操作失败但程序继续运行 |
| Warn | 潜在问题，不影响主流程 |
| Info | 关键业务事件 |
| Debug | 调试信息，生产环境通常关闭 |
| Trace | 最详细的跟踪信息 |

## 日志内容规范

- 日志内容使用英文
- 使用 WithFields 附加结构化信息而不是拼接字符串

```go
// ✅ 正确
logrus.WithFields(logrus.Fields{
    "userId": userId,
    "action": "login",
}).Info("user logged in")

// ❌ 错误
logrus.Info(fmt.Sprintf("user %d logged in", userId))
```