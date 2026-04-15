# 文件组织规范

## 核心规则：一个目录一个接口文件

如果 model 目录下的文件有 model.go、claude_chat_model.go、openai_chat_model.go 等，则：

**model.go** 放所有接口定义：

```go
// model.go
type IChatModel interface {
    Chat(input string) (output string)
}

type IStreamChatModel interface {
    StreamChat(input string) (output string)
}
```

**各实现文件**放对应的实现：

```
model/
├── model.go                    # 接口定义
├── claude_chat_model.go        # ClaudeChatModel 实现
├── claude_stream_chat_model.go # ClaudeStreamChatModel 实现
├── openai_chat_model.go         # OpenAIChatModel 实现
└── openai_stream_chat_model.go # OpenAIStreamChatModel 实现
```

## 目录结构模式

```
project/
├── cmd/                  # 入口
│   └── server/
│       └── main.go
├── internal/             # 私有代码
│   ├── model/            # 数据模型
│   │   ├── model.go      # 接口定义
│   │   └── xxx_model.go  # 各实现
│   ├── service/          # 业务逻辑
│   │   ├── service.go    # 接口定义
│   │   └── xxx_service.go
│   └── repo/             # 数据访问
│       ├── repo.go        # 接口定义
│       └── xxx_repo.go
├── configs/              # 配置文件
├── pkg/                  # 公共代码
└── api/                  # API 定义
```

## kratos 项目的 DDD 目录

使用 kratos 框架时，严格遵守 DDD 目录设计哲学：

```
project/
├── cmd/
├── configs/
├── internal/
│   ├── conf/             # 配置结构
│   ├── server/           # HTTP/gRPC 服务
│   ├── service/          # 业务入口
│   ├── biz/              # 业务逻辑
│   └── data/             # 数据访问
└── third_party/
```