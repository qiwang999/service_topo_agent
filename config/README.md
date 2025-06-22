# 配置管理系统

本项目使用统一的配置管理系统，支持从环境变量、.env文件和默认值加载配置。

## 配置结构

配置按功能模块分为以下几个部分：

### 1. OpenAI 配置
- `api_key`: OpenAI API密钥（必需）
- `model`: 使用的模型名称
- `temperature`: 生成温度
- `max_tokens`: 最大token数

### 2. Neo4j 配置
- `uri`: Neo4j数据库连接URI
- `username`: 用户名
- `password`: 密码（必需）
- `max_connection_lifetime`: 连接最大生命周期
- `max_connection_pool_size`: 连接池大小

### 3. 应用配置
- `host`: 应用监听地址
- `port`: 应用端口
- `debug`: 调试模式
- `secret_key`: 应用密钥

### 4. 运行模式配置
- `default_run_mode`: 默认运行模式
- `summarizer_type`: 摘要器类型
- `max_retries`: 最大重试次数

### 5. 功能开关配置
- `enable_interaction_logging`: 启用交互日志
- `enable_embeddings`: 启用Embedding功能
- `enable_cache`: 启用缓存功能
- `enable_validation`: 启用验证功能

### 6. 缓存配置
- `use_redis`: 使用Redis缓存
- `redis_host`: Redis主机地址
- `redis_port`: Redis端口
- `redis_db`: Redis数据库编号
- `redis_password`: Redis密码
- `redis_ttl`: Redis缓存TTL
- `sqlite_db_path`: SQLite数据库路径

### 7. 数据库配置
- `feedback_db_path`: 反馈数据库路径
- `vector_db_path`: 向量数据库路径
- `max_feedback_examples`: 最大反馈示例数
- `min_feedback_rating`: 最小反馈评分

### 8. Embedding 配置
- `model`: Embedding模型
- `dimensions`: 向量维度
- `similarity_threshold`: 相似度阈值
- `max_examples`: 最大示例数
- `max_feedback`: 最大反馈数

### 9. 日志配置
- `level`: 日志级别
- `format`: 日志格式
- `file`: 日志文件路径
- `max_size`: 日志文件最大大小
- `backup_count`: 日志备份数量

### 10. Gunicorn 配置
- `bind`: 绑定地址和端口
- `workers`: 工作进程数
- `worker_class`: 工作进程类
- `timeout`: 超时时间
- `keepalive`: 保持连接时间
- `max_requests`: 最大请求数
- `max_requests_jitter`: 最大请求抖动
- `accesslog`: 访问日志
- `errorlog`: 错误日志
- `loglevel`: 日志级别
- `proc_name`: 进程名称

## 使用方法

### 1. 基本使用

```python
from config.config_manager import config

# 获取单个配置值
api_key = config.get('openai', 'api_key')
port = config.get('app', 'port', 5000)  # 带默认值

# 获取整个配置节
neo4j_config = config.get_section('neo4j')
```

### 2. 配置工具

使用命令行工具管理配置：

```bash
# 查看所有配置
python config/config_tool.py show

# 查看特定配置节
python config/config_tool.py show --section openai

# 验证配置
python config/config_tool.py validate

# 导出环境变量模板
python config/config_tool.py export --output .env.example

# 检查配置状态
python config/config_tool.py check
```

### 3. 环境变量设置

创建 `.env` 文件：

```bash
# 复制模板
cp .env.example .env

# 编辑配置
vim .env
```

或者直接设置环境变量：

```bash
export OPENAI_API_KEY="your_api_key"
export NEO4J_PASSWORD="your_password"
```

## 配置优先级

配置加载优先级（从高到低）：

1. 环境变量
2. .env文件
3. 默认值

## 配置验证

配置管理器会自动验证：

- 必需的环境变量是否设置
- 端口号是否在有效范围内
- 温度值是否在有效范围内
- 其他数值类型配置的有效性

## 安全注意事项

- 敏感信息（如API密钥、密码）在打印时会自动隐藏
- 建议使用环境变量而不是硬编码敏感信息
- 生产环境中应使用安全的密钥管理服务

## 扩展配置

如需添加新的配置项：

1. 在 `ConfigManager._load_configs()` 方法中添加新的配置节
2. 在环境变量模板中添加对应的变量
3. 在配置验证中添加相应的验证逻辑
4. 更新此文档

## 示例配置

### 开发环境
```bash
APP_DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_INTERACTION_LOGGING=true
```

### 生产环境
```bash
APP_DEBUG=false
LOG_LEVEL=WARNING
ENABLE_INTERACTION_LOGGING=false
USE_REDIS=true
```

### 测试环境
```bash
APP_DEBUG=true
LOG_LEVEL=INFO
ENABLE_CACHE=false
ENABLE_VALIDATION=false
``` 