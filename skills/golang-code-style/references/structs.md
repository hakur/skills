# 结构体定义规范

## receiver 命名

结构体方法 receiver 必须使用小写字母 `t`：

```go
// ✅ 正确
func (t *UserService) CreateUser(ctx context.Context, req *CreateUserReq) error {}

// ❌ 错误
func (s *UserService) CreateUser(ctx context.Context, req *CreateUserReq) error {}
func (self *UserService) CreateUser(ctx context.Context, req *CreateUserReq) error {}
```

## 默认值：default tag + DefaultValue

使用 `default` tag 和 `github.com/hakur/util` 的 `DefaultValue` 函数初始化默认值：

- 有非零默认值的字段：加 `default` tag
- 零值即可的字段：不加 `default` tag

```go
type ClaudeChatModelOpts struct {
    // APIKey 有非零值默认，加 default tag
    APIKey string `default:"mykey" yaml:"apiKey" json:"apiKey"`
    // TimeoutSecond 零值即可，不加 default tag
    TimeoutSecond int `yaml:"timeoutSecond" json:"timeoutSecond"`
}
```

## json/yaml tag 使用驼峰风格

```go
// ✅ 正确
type Config struct {
    APIKey        string `yaml:"apiKey" json:"apiKey"`
    TimeoutSecond int    `yaml:"timeoutSecond" json:"timeoutSecond"`
}

// ❌ 错误
type Config struct {
    APIKey        string `yaml:"api_key" json:"api_key"`
    TimeoutSecond int    `yaml:"TimeoutSecond" json:"TimeoutSecond"`
}
```

## 构造函数规则

- **DTO 和 gorm 数据表结构体**：不需要构造函数
- **有内部初始化逻辑的结构体**：才需要构造函数

```go
// NewClaudeChatModel 仅在有内部初始化逻辑时才编写
func NewClaudeChatModel(opts *ClaudeChatModelOpts) *ClaudeChatModel {
    hutil.DefaultValue(opts)
    t := new(ClaudeChatModel)
    t.Opts = opts
    t.SystemPrompts = append(t.SystemPrompts, "hello") // 内部初始化逻辑
    return t
}
```

## 禁止在业务逻辑里临时定义 gorm 数据表结构体

gorm 数据表结构体必须在专门的 model/data 层文件中定义，不能在业务逻辑代码中临时定义。

## 字段排列顺序

公开字段在前，小写字段（私有字段、锁）在后：

```go
type ClaudeChatModel struct {
    Opts         *ClaudeChatModelOpts
    TokenCount   int
    SystemPrompts []string
    userPrompts  []string        // 小写：需要 getter/setter
    lock         deadlock.RWMutex // 小写：锁排最后
}
```

## getter/setter 规则

- 内部计算的字段：不需要 getter/setter
- 构造函数初始化后只读的字段：不需要 getter/setter
- 被多线程外部操作的字段：需要 getter/setter 并加锁

```go
// TokenCount 不需要 getter/setter，计算在结构体内部
func (t *ClaudeChatModel) Chat(ctx context.Context, input string) (output string) {
    t.TokenCount += len(input)
}

// userPrompts 需要线程安全的 getter/setter
func (t *ClaudeChatModel) AddUserPrompts(ctx context.Context, input string) {
    t.lock.Lock()
    defer t.lock.Unlock()
    t.userPrompts = append(t.userPrompts, input)
}
```