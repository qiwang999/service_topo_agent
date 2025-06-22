#!/usr/bin/env python3
"""
配置使用示例
展示如何在代码中使用统一的配置管理系统。
"""

from config.config_manager import config


def example_openai_config():
    """OpenAI配置使用示例。"""
    print("=== OpenAI 配置示例 ===")
    
    # 获取API密钥
    api_key = config.get('openai', 'api_key')
    print(f"API Key: {'*' * len(api_key) if api_key else 'Not set'}")
    
    # 获取模型配置
    model = config.get('openai', 'model')
    temperature = config.get('openai', 'temperature')
    max_tokens = config.get('openai', 'max_tokens')
    
    print(f"Model: {model}")
    print(f"Temperature: {temperature}")
    print(f"Max Tokens: {max_tokens}")


def example_neo4j_config():
    """Neo4j配置使用示例。"""
    print("\n=== Neo4j 配置示例 ===")
    
    # 获取整个Neo4j配置节
    neo4j_config = config.get_section('neo4j')
    
    for key, value in neo4j_config.items():
        if 'password' in key:
            value = '*' * len(str(value)) if value else 'Not set'
        print(f"{key}: {value}")


def example_app_config():
    """应用配置使用示例。"""
    print("\n=== 应用配置示例 ===")
    
    host = config.get('app', 'host')
    port = config.get('app', 'port')
    debug = config.get('app', 'debug')
    
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")


def example_feature_flags():
    """功能开关使用示例。"""
    print("\n=== 功能开关示例 ===")
    
    features = [
        ('enable_cache', '缓存功能'),
        ('enable_embeddings', 'Embedding功能'),
        ('enable_interaction_logging', '交互日志'),
        ('enable_validation', '验证功能')
    ]
    
    for feature_key, feature_name in features:
        enabled = config.get('feature', feature_key)
        status = "✅ 启用" if enabled else "❌ 禁用"
        print(f"{feature_name}: {status}")


def example_cache_config():
    """缓存配置使用示例。"""
    print("\n=== 缓存配置示例 ===")
    
    use_redis = config.get('cache', 'use_redis')
    print(f"使用Redis: {use_redis}")
    
    if use_redis:
        redis_host = config.get('cache', 'redis_host')
        redis_port = config.get('cache', 'redis_port')
        redis_ttl = config.get('cache', 'redis_ttl')
        
        print(f"Redis Host: {redis_host}")
        print(f"Redis Port: {redis_port}")
        print(f"Redis TTL: {redis_ttl}秒")
    else:
        sqlite_path = config.get('cache', 'sqlite_db_path')
        print(f"SQLite DB: {sqlite_path}")


def example_conditional_config():
    """条件配置使用示例。"""
    print("\n=== 条件配置示例 ===")
    
    # 根据功能开关决定使用哪种配置
    if config.get('feature', 'enable_cache'):
        if config.get('cache', 'use_redis'):
            print("使用Redis缓存")
            # 这里可以初始化Redis客户端
        else:
            print("使用SQLite缓存")
            # 这里可以初始化SQLite缓存
    else:
        print("缓存功能已禁用")
    
    # 根据运行模式决定行为
    run_mode = config.get('run', 'default_run_mode')
    if run_mode == 'standard':
        print("运行在标准模式")
    elif run_mode == 'enhanced':
        print("运行在增强模式")
    else:
        print(f"运行在自定义模式: {run_mode}")


def example_validation():
    """配置验证示例。"""
    print("\n=== 配置验证示例 ===")
    
    if config.validate():
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败")


def main():
    """主函数。"""
    print("🔧 配置使用示例")
    print("=" * 50)
    
    try:
        example_openai_config()
        example_neo4j_config()
        example_app_config()
        example_feature_flags()
        example_cache_config()
        example_conditional_config()
        example_validation()
        
        print("\n🎉 所有示例执行完成！")
        
    except Exception as e:
        print(f"❌ 示例执行失败: {e}")
        print("请确保已正确设置环境变量或创建 .env 文件")


if __name__ == '__main__':
    main() 