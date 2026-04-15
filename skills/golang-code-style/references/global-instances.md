# 全局实例定义规范

## 模式：init() + DefaultValue + godotenv

全局配置实例使用 `init()` 函数初始化，结合 `DefaultValue` 和 `godotenv`：

```go
package config

import (
    "github.com/joho/godotenv"
    hutil "github.com/hakur/util"
)

var AppConfig *Config

func init() {
    AppConfig = new(Config)
    hutil.DefaultValue(AppConfig)
    godotenv.Load(".env")
    hutil.ParseStructWithEnv(AppConfig)
}

type Config struct {
    Port    int    `default:"8080" yaml:"port" json:"port"`
    DBUrl   string `default:"localhost:3306" yaml:"dbUrl" json:"dbUrl"`
}
```

## 初始化顺序

```
1. new(Config)           → 零值结构体
2. DefaultValue(Config)   → 填充 default tag 的默认值
3. godotenv.Load(".env") → 加载环境变量文件
4. ParseStructWithEnv    → 环境变量覆盖配置值
```

## 注意事项

- 全局实例变量名用大写开头（如 `AppConfig`）
- `init()` 函数中不要做耗时的网络操作
- 如果配置依赖外部服务，放到显式的初始化函数而非 `init()`
- `default` tag 只用于有非零默认值的字段