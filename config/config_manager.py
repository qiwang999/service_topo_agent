import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigManager:
    """
    统一的配置管理器，集中管理所有配置项。
    支持从环境变量、.env文件和默认值加载配置。
    """
    
    def __init__(self, env_file: str = ".env"):
        """
        初始化配置管理器。
        
        Args:
            env_file: .env文件路径
        """
        # 加载.env文件
        load_dotenv(env_file)
        
        # 初始化所有配置
        self._load_configs()
    
    def _load_configs(self):
        """加载所有配置项。"""
        
        # === OpenAI 配置 ===
        self.openai_config = {
            'api_key': self._get_env('OPENAI_API_KEY', required=True),
            'model': self._get_env('OPENAI_MODEL', default='gpt-4o'),
            'temperature': float(self._get_env('OPENAI_TEMPERATURE', default='0')),
            'max_tokens': int(self._get_env('OPENAI_MAX_TOKENS', default='4000'))
        }
        
        # === Neo4j 配置 ===
        self.neo4j_config = {
            'uri': self._get_env('NEO4J_URI', default='bolt://localhost:7687'),
            'username': self._get_env('NEO4J_USERNAME', default='neo4j'),
            'password': self._get_env('NEO4J_PASSWORD', required=True),
            'max_connection_lifetime': int(self._get_env('NEO4J_MAX_CONNECTION_LIFETIME', default='3600')),
            'max_connection_pool_size': int(self._get_env('NEO4J_MAX_CONNECTION_POOL_SIZE', default='50'))
        }
        
        # === 应用配置 ===
        self.app_config = {
            'host': self._get_env('APP_HOST', default='0.0.0.0'),
            'port': int(self._get_env('APP_PORT', default='5000')),
            'debug': self._get_env('APP_DEBUG', default='false').lower() == 'true',
            'secret_key': self._get_env('APP_SECRET_KEY', default='your-secret-key-change-this')
        }
        
        # === 运行模式配置 ===
        self.run_config = {
            'default_run_mode': self._get_env('DEFAULT_RUN_MODE', default='standard'),
            'summarizer_type': self._get_env('SUMMARIZER_TYPE', default='llm'),
            'max_retries': int(self._get_env('MAX_RETRIES', default='3'))
        }
        
        # === 功能开关配置 ===
        self.feature_config = {
            'enable_interaction_logging': self._get_env('ENABLE_INTERACTION_LOGGING', default='false').lower() == 'true',
            'enable_embeddings': self._get_env('ENABLE_EMBEDDINGS', default='true').lower() == 'true',
            'enable_cache': self._get_env('ENABLE_CACHE', default='true').lower() == 'true',
            'enable_validation': self._get_env('ENABLE_VALIDATION', default='true').lower() == 'true'
        }
        
        # === 缓存配置 ===
        self.cache_config = {
            'use_redis': self._get_env('USE_REDIS', default='true').lower() == 'true',
            'redis_host': self._get_env('REDIS_HOST', default='localhost'),
            'redis_port': int(self._get_env('REDIS_PORT', default='6379')),
            'redis_db': int(self._get_env('REDIS_DB', default='0')),
            'redis_password': self._get_env('REDIS_PASSWORD', default=''),
            'redis_ttl': int(self._get_env('REDIS_TTL', default='3600')),
            'sqlite_db_path': self._get_env('SQLITE_DB_PATH', default='feedback.db')
        }
        
        # === 数据库配置 ===
        self.database_config = {
            'feedback_db_path': self._get_env('FEEDBACK_DB_PATH', default='feedback.db'),
            'vector_db_path': self._get_env('VECTOR_DB_PATH', default='vector.db'),
            'max_feedback_examples': int(self._get_env('MAX_FEEDBACK_EXAMPLES', default='20')),
            'min_feedback_rating': int(self._get_env('MIN_FEEDBACK_RATING', default='4'))
        }
        
        # === Embedding 配置 ===
        self.embedding_config = {
            'model': self._get_env('EMBEDDING_MODEL', default='text-embedding-3-small'),
            'dimensions': int(self._get_env('EMBEDDING_DIMENSIONS', default='1536')),
            'similarity_threshold': float(self._get_env('SIMILARITY_THRESHOLD', default='0.7')),
            'max_examples': int(self._get_env('MAX_EXAMPLES', default='5')),
            'max_feedback': int(self._get_env('MAX_FEEDBACK', default='3'))
        }
        
        # === 日志配置 ===
        self.logging_config = {
            'level': self._get_env('LOG_LEVEL', default='INFO'),
            'format': self._get_env('LOG_FORMAT', default='%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            'file': self._get_env('LOG_FILE', default=''),
            'max_size': int(self._get_env('LOG_MAX_SIZE', default='10MB')),
            'backup_count': int(self._get_env('LOG_BACKUP_COUNT', default='5'))
        }
        
        # === Gunicorn 配置 ===
        self.gunicorn_config = {
            'bind': f"{self.app_config['host']}:{self.app_config['port']}",
            'workers': int(self._get_env('GUNICORN_WORKERS', default=str(os.cpu_count() * 2 + 1))),
            'worker_class': self._get_env('GUNICORN_WORKER_CLASS', default='sync'),
            'timeout': int(self._get_env('GUNICORN_TIMEOUT', default='120')),
            'keepalive': int(self._get_env('GUNICORN_KEEPALIVE', default='2')),
            'max_requests': int(self._get_env('GUNICORN_MAX_REQUESTS', default='1000')),
            'max_requests_jitter': int(self._get_env('GUNICORN_MAX_REQUESTS_JITTER', default='100')),
            'accesslog': self._get_env('GUNICORN_ACCESS_LOG', default='-'),
            'errorlog': self._get_env('GUNICORN_ERROR_LOG', default='-'),
            'loglevel': self._get_env('GUNICORN_LOG_LEVEL', default='info'),
            'proc_name': self._get_env('GUNICORN_PROC_NAME', default='service-topology-agent')
        }
    
    def _get_env(self, key: str, default: Optional[str] = None, required: bool = False) -> str:
        """
        从环境变量获取配置值。
        
        Args:
            key: 环境变量名
            default: 默认值
            required: 是否必需
            
        Returns:
            配置值
            
        Raises:
            ValueError: 如果必需的环境变量未设置
        """
        value = os.getenv(key, default)
        
        if required and not value:
            raise ValueError(f"必需的环境变量 {key} 未设置")
        
        return value
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        获取配置值。
        
        Args:
            section: 配置节名称
            key: 配置键名
            default: 默认值
            
        Returns:
            配置值
        """
        config_section = getattr(self, f"{section}_config", {})
        return config_section.get(key, default)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取整个配置节。
        
        Args:
            section: 配置节名称
            
        Returns:
            配置节字典
        """
        return getattr(self, f"{section}_config", {})
    
    def validate(self) -> bool:
        """
        验证配置的有效性。
        
        Returns:
            配置是否有效
        """
        try:
            # 验证必需的配置
            if not self.openai_config['api_key']:
                raise ValueError("OpenAI API Key 未设置")
            
            if not self.neo4j_config['password']:
                raise ValueError("Neo4j 密码未设置")
            
            # 验证端口范围
            if not (1 <= self.app_config['port'] <= 65535):
                raise ValueError(f"端口号 {self.app_config['port']} 无效")
            
            # 验证温度值
            if not (0 <= self.openai_config['temperature'] <= 2):
                raise ValueError(f"温度值 {self.openai_config['temperature']} 无效")
            
            return True
            
        except Exception as e:
            print(f"配置验证失败: {e}")
            return False
    
    def print_config(self, section: Optional[str] = None):
        """
        打印配置信息。
        
        Args:
            section: 要打印的配置节，如果为None则打印所有配置
        """
        if section:
            config = self.get_section(section)
            print(f"\n=== {section.upper()} 配置 ===")
            for key, value in config.items():
                # 隐藏敏感信息
                if 'password' in key.lower() or 'key' in key.lower():
                    value = '*' * len(str(value)) if value else 'None'
                print(f"  {key}: {value}")
        else:
            sections = ['openai', 'neo4j', 'app', 'run', 'feature', 'cache', 
                       'database', 'embedding', 'logging', 'gunicorn']
            for section in sections:
                self.print_config(section)
    
    def export_env_file(self, filename: str = ".env.example"):
        """
        导出环境变量文件模板。
        
        Args:
            filename: 输出文件名
        """
        env_template = """# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0
OPENAI_MAX_TOKENS=4000

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password_here
NEO4J_MAX_CONNECTION_LIFETIME=3600
NEO4J_MAX_CONNECTION_POOL_SIZE=50

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=5000
APP_DEBUG=false
APP_SECRET_KEY=your-secret-key-change-this

# 运行模式配置
DEFAULT_RUN_MODE=standard
SUMMARIZER_TYPE=llm
MAX_RETRIES=3

# 功能开关配置
ENABLE_INTERACTION_LOGGING=false
ENABLE_EMBEDDINGS=true
ENABLE_CACHE=true
ENABLE_VALIDATION=true

# 缓存配置
USE_REDIS=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_TTL=3600
SQLITE_DB_PATH=feedback.db

# 数据库配置
FEEDBACK_DB_PATH=feedback.db
VECTOR_DB_PATH=vector.db
MAX_FEEDBACK_EXAMPLES=20
MIN_FEEDBACK_RATING=4

# Embedding 配置
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
SIMILARITY_THRESHOLD=0.7
MAX_EXAMPLES=5
MAX_FEEDBACK=3

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# Gunicorn 配置
GUNICORN_WORKERS=auto
GUNICORN_WORKER_CLASS=sync
GUNICORN_TIMEOUT=120
GUNICORN_KEEPALIVE=2
GUNICORN_MAX_REQUESTS=1000
GUNICORN_MAX_REQUESTS_JITTER=100
GUNICORN_ACCESS_LOG=-
GUNICORN_ERROR_LOG=-
GUNICORN_LOG_LEVEL=info
GUNICORN_PROC_NAME=service-topology-agent
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(env_template)
        
        print(f"环境变量模板已导出到 {filename}")


# 全局配置实例
config = ConfigManager() 