# 配置迁移指南

本指南帮助您从现有的硬编码配置迁移到新的统一配置管理系统。

## 迁移前准备

1. 备份现有配置文件
2. 记录当前使用的配置值
3. 确保了解新配置系统的结构

## 迁移步骤

### 1. 导出当前配置

首先，使用配置工具导出环境变量模板：

```bash
python config/config_tool.py export --output .env.template
```

### 2. 创建 .env 文件

复制模板并填入您的实际配置值：

```bash
cp .env.template .env
```

### 3. 更新代码中的配置引用

#### 旧方式（需要替换）：

```python
# 直接使用环境变量
import os
api_key = os.getenv("OPENAI_API_KEY")
port = int(os.getenv("APP_PORT", "5000"))

# 硬编码配置
NEO4J_URI = "bolt://localhost:7687"
ENABLE_CACHE = True
```

#### 新方式（推荐）：

```python
# 使用配置管理器
from config.config_manager import config

api_key = config.get('openai', 'api_key')
port = config.get('app', 'port', 5000)

# 获取整个配置节
neo4j_config = config.get_section('neo4j')
enable_cache = config.get('feature', 'enable_cache')
```

### 4. 具体迁移示例

#### 迁移 app.py

**旧代码：**
```python
ENABLE_LOGGING = os.environ.get("ENABLE_INTERACTION_LOGGING", "false").lower() == "true"
DEFAULT_RUN_MODE = os.environ.get("DEFAULT_RUN_MODE", "standard")
summarizer_choice = os.environ.get("SUMMARIZER_TYPE", "llm")
```

**新代码：**
```python
from config.config_manager import config

ENABLE_LOGGING = config.get('feature', 'enable_interaction_logging')
DEFAULT_RUN_MODE = config.get('run', 'default_run_mode')
summarizer_choice = config.get('run', 'summarizer_type')
```

#### 迁移 enhanced_app.py

**旧代码：**
```python
ENABLE_LOGGING = os.environ.get("ENABLE_INTERACTION_LOGGING", "false").lower() == "true"
DEFAULT_RUN_MODE = os.environ.get("DEFAULT_RUN_MODE", "standard")
ENABLE_EMBEDDINGS = os.environ.get("ENABLE_EMBEDDINGS", "true").lower() == "true"
ENABLE_CACHE = os.environ.get("ENABLE_CACHE", "true").lower() == "true"
```

**新代码：**
```python
from config.config_manager import config

ENABLE_LOGGING = config.get('feature', 'enable_interaction_logging')
DEFAULT_RUN_MODE = config.get('run', 'default_run_mode')
ENABLE_EMBEDDINGS = config.get('feature', 'enable_embeddings')
ENABLE_CACHE = config.get('feature', 'enable_cache')
```

#### 迁移工具类

**旧代码：**
```python
# tools/llm_client.py
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("FATAL: OPENAI_API_KEY environment variable not set.")
return ChatOpenAI(model=model_name, openai_api_key=api_key, temperature=0)
```

**新代码：**
```python
# tools/llm_client.py
from config.config_manager import config

api_key = config.get('openai', 'api_key')
model = config.get('openai', 'model')
temperature = config.get('openai', 'temperature')

return ChatOpenAI(
    model=model, 
    openai_api_key=api_key, 
    temperature=temperature
)
```

**旧代码：**
```python
# tools/neo4j_client.py
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
```

**新代码：**
```python
# tools/neo4j_client.py
from config.config_manager import config

neo4j_config = config.get_section('neo4j')
uri = neo4j_config['uri']
username = neo4j_config['username']
password = neo4j_config['password']
```

### 5. 更新 Gunicorn 配置

**旧方式：**
```python
# gunicorn_config.py
bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
```

**新方式：**
```python
# 使用 config/gunicorn_config.py
# 配置会自动从配置管理器加载
```

### 6. 验证迁移

运行配置验证工具：

```bash
python config/config_tool.py validate
```

检查配置状态：

```bash
python config/config_tool.py check
```

运行配置示例：

```bash
python config/usage_example.py
```

## 迁移检查清单

- [ ] 备份了现有配置文件
- [ ] 创建了 .env 文件并填入正确值
- [ ] 更新了所有硬编码的配置引用
- [ ] 更新了工具类中的配置获取方式
- [ ] 更新了 Gunicorn 配置文件
- [ ] 验证了配置的正确性
- [ ] 测试了应用功能

## 常见问题

### Q: 如何保持向后兼容性？

A: 可以在配置管理器中添加兼容性方法：

```python
def get_env_compat(self, key: str, default: str = None):
    """向后兼容的环境变量获取方法"""
    return self._get_env(key, default)
```

### Q: 如何处理敏感信息？

A: 配置管理器会自动隐藏敏感信息：

```python
# 打印配置时会自动隐藏密码和密钥
config.print_config('openai')
```

### Q: 如何在不同环境中使用不同配置？

A: 可以创建多个 .env 文件：

```bash
.env.development
.env.production
.env.test
```

然后在启动时指定：

```bash
python -c "from config.config_manager import ConfigManager; ConfigManager('.env.production')"
```

## 迁移后的优势

1. **统一管理**：所有配置集中在一个地方
2. **类型安全**：配置值自动转换为正确的类型
3. **验证机制**：自动验证配置的有效性
4. **安全保护**：敏感信息自动隐藏
5. **易于维护**：配置结构清晰，易于扩展
6. **工具支持**：提供配置查看、验证、导出工具

## 下一步

迁移完成后，您可以：

1. 使用配置工具管理配置
2. 添加新的配置项
3. 实现配置热重载
4. 集成配置监控
5. 实现配置版本控制 