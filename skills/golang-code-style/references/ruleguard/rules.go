//go:build ruleguard
// +build ruleguard

// Package gorules 定义了 golang-code-style 的代码规范检查规则
// 这些规则通过 ruleguard 执行，基于 AST 进行精确匹配，避免正则误报
package gorules

import (
	"github.com/quasilyte/go-ruleguard/dsl"
)

// ============================================================================
// 并发相关规则
// ============================================================================

// forbidSyncMutex 禁止直接使用 sync.Mutex 和 sync.RWMutex
// 应使用 deadlock.Mutex 和 deadlock.RWMutex 以支持死锁检测
func forbidSyncMutex(m dsl.Matcher) {
	m.Import("sync")

	// 匹配 var mu sync.Mutex 或 var mu sync.RWMutex
	m.Match(`var $mu sync.Mutex`, `var $mu sync.RWMutex`).
		Report("禁止使用 sync.Mutex/sync.RWMutex, 请使用 deadlock.Mutex/deadlock.RWMutex")

	// 匹配 &sync.Mutex{} 或 &sync.RWMutex{}
	m.Match(`$mu := &sync.Mutex{}`, `$mu := &sync.RWMutex{}`).
		Report("禁止使用 sync.Mutex/sync.RWMutex, 请使用 deadlock.Mutex/deadlock.RWMutex")

	// 匹配 new(sync.Mutex) 或 new(sync.RWMutex)
	m.Match(`$mu := new(sync.Mutex)`, `$mu := new(sync.RWMutex)`).
		Report("禁止使用 sync.Mutex/sync.RWMutex, 请使用 deadlock.Mutex/deadlock.RWMutex")
}

// forbidExportedSyncMutex 禁止在导出结构体中嵌入 sync.Mutex
func forbidExportedSyncMutex(m dsl.Matcher) {
	isExported := func(v dsl.Var) bool {
		return v.Text.Matches(`^\p{Lu}`)
	}

	m.Match(`type $name struct { $*_; sync.Mutex; $*_ }`).
		Where(isExported(m["name"])).
		Report("不要在导出结构体中嵌入 sync.Mutex，应使用 deadlock.Mutex")

	m.Match(`type $name struct { $*_; sync.RWMutex; $*_ }`).
		Where(isExported(m["name"])).
		Report("不要在导出结构体中嵌入 sync.RWMutex，应使用 deadlock.RWMutex")
}

// ============================================================================
// 日志相关规则
// ============================================================================

// forbidNewLogger 禁止创建日志库新实例
// 应使用全局实例，如 logrus.Info() 或 zap.L()
func forbidNewLogger(m dsl.Matcher) {
	// logrus
	m.Match(`logrus.New()`).
		Report("禁止创建 logrus 新实例，请使用全局方法如 logrus.Info()")

	m.Match(`logrus.NewLogger($*_)`).
		Report("禁止创建 logrus 新实例，请使用全局方法如 logrus.Info()")

	// zap
	m.Match(`zap.New($*_)`).
		Report("禁止创建 zap 新实例，请使用全局方法如 zap.L()")

	m.Match(`zap.NewLogger($*_)`).
		Report("禁止创建 zap 新实例，请使用全局方法如 zap.L()")

	m.Match(`zap.NewDevelopmentConfig()`, `zap.NewProductionConfig()`).
		Report("禁止创建 zap 新配置，请使用全局 logger")

	// zerolog
	m.Match(`zerolog.New($*_)`).
		Report("禁止创建 zerolog 新实例，请使用全局实例")
}

// forbidLogrusRegister 禁止调用 logrus.Register()
func forbidLogrusRegister(m dsl.Matcher) {
	m.Match(`logrus.Register($*_)`).
		Report("禁止调用 logrus.Register()")
}

// ============================================================================
// 测试相关规则
// ============================================================================

// forbidNestedTestRun 禁止在测试中使用 t.Run 嵌套
func forbidNestedTestRun(m dsl.Matcher) {
	// 匹配在外层 t.Run 回调中再次调用 t.Run
	m.Match(`
		func $Test($t *testing.T) {
			$t.Run($_, func($_ *testing.T) {
				$*_
				$t.Run($_, func($_ *testing.T) {
					$*_
				})
				$*_
			})
		}
	`).
		Report("禁止在测试中使用 t.Run 嵌套，请使用扁平化的测试函数")
}

// forbidTSkip 禁止在测试中使用 t.Skip
func forbidTSkip(m dsl.Matcher) {
	m.Match(`$t.Skip($*_)`, `$t.Skipf($*_)`, `$t.SkipNow()`).
		Where(m["t"].Type.Is(`*testing.T`)).
		Report("禁止使用 t.Skip/t.Skipf/t.SkipNow，请补充测试条件或修复测试")
}

// ============================================================================
// 网络/WebSocket 相关规则
// ============================================================================

// forbidGorillaWebsocket 禁止导入和使用 gorilla/websocket
func forbidGorillaWebsocket(m dsl.Matcher) {
	// 匹配 import 语句
	m.Match(`"github.com/gorilla/websocket"`).
		Report("禁止使用 gorilla/websocket，请使用 github.com/coder/websocket")
}

// ============================================================================
// 命名规范规则（WARN 级别）
// ============================================================================

// warnInterfaceNaming 建议接口命名规范（Go 社区惯例：能力描述命名）
func warnInterfaceNaming(m dsl.Matcher) {
	// 建议接口名以 er 结尾（Go 惯例，如 Reader/Writer）或使用能力描述
	m.Match(`type $name interface { ... }`).
		Where(
			m["name"].Text.Matches(`^[A-Z]`) && // 是导出接口
				!m["name"].Text.Matches(`.*er$`), // 不以 er 结尾
		).
		Report("接口命名建议以 er 结尾（Go 惯例，如 Reader/Writer）或使用能力描述命名")
}

// warnMeaninglessInterfaceName 警告无意义的接口命名
func warnMeaninglessInterfaceName(m dsl.Matcher) {
	patterns := []string{
		`^Default`,
		`^Basic`,
		`^Standard`,
		`^Normal`,
		`^Plain`,
		`^Generic`,
		`^Impl\d*$`,
		`^.*Implementation$`,
	}

	for _, pattern := range patterns {
		m.Match(`type $name interface { ... }`).
			Where(m["name"].Text.Matches(pattern)).
			Report("接口命名应避免使用无意义前缀如 Default/Basic/Standard，请使用语义化命名")
	}
}

// warnMeaninglessStructName 警告无意义的结构体命名
func warnMeaninglessStructName(m dsl.Matcher) {
	patterns := []string{
		`^Default`,
		`^Basic`,
		`^Standard`,
		`^Normal`,
		`^Plain`,
		`^Generic`,
		`^Impl\d*$`,
		`^.*Implementation$`,
	}

	for _, pattern := range patterns {
		m.Match(`type $name struct { ... }`).
			Where(m["name"].Text.Matches(pattern)).
			Report("结构体命名应避免使用无意义后缀如 Default/Basic/Standard，请使用语义化命名如 JsonPacket")
	}
}

// warnReceiverNaming 建议 receiver 变量名使用小写 t
func warnReceiverNaming(m dsl.Matcher) {
	m.Match(`func ($recv $*_) $Method($*_) $*_ { ... }`).
		Where(
			m["recv"].Text.Matches(`^[A-Z]`) || // 大写开头
				m["recv"].Text.Matches(`^\w{2,}`), // 多个字符
		).
		Report("建议 receiver 变量名使用单个小写字母，如 func (t *Type) Method()")
}

// ============================================================================
// 消息队列相关规则
// ============================================================================

// forbidNonNatsMQ 禁止使用非 nats 消息队列
func forbidNonNatsMQ(m dsl.Matcher) {
	// kafka
	m.Match(`"github.com/segmentio/kafka-go"`).
		Report("禁止使用 kafka，请使用 nats / nats-jetstream")

	// rabbitmq
	m.Match(`"github.com/streadway/amqp"`).
		Report("禁止使用 rabbitmq，请使用 nats / nats-jetstream")

	// rocketmq
	m.Match(`"github.com/apache/rocketmq-client-go"`).
		Report("禁止使用 rocketmq，请使用 nats / nats-jetstream")
}
