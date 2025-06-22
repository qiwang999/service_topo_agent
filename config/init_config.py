#!/usr/bin/env python3
"""
配置初始化脚本
帮助用户快速设置项目配置。
"""

import os
import sys
import getpass
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_manager import ConfigManager


def get_user_input(prompt: str, default: str = "", password: bool = False) -> str:
    """获取用户输入。"""
    if password:
        return getpass.getpass(prompt)
    else:
        return input(f"{prompt} [{default}]: ").strip() or default


def create_env_file():
    """创建.env文件。"""
    print("🔧 配置初始化向导")
    print("=" * 50)
    
    env_content = []
    
    # OpenAI 配置
    print("\n📝 OpenAI 配置")
    print("-" * 30)
    api_key = get_user_input("请输入 OpenAI API Key", password=True)
    if api_key:
        env_content.append(f"OPENAI_API_KEY={api_key}")
    
    model = get_user_input("OpenAI 模型", "gpt-4o")
    env_content.append(f"OPENAI_MODEL={model}")
    
    temperature = get_user_input("生成温度 (0-2)", "0")
    env_content.append(f"OPENAI_TEMPERATURE={temperature}")
    
    # Neo4j 配置
    print("\n🗄️  Neo4j 配置")
    print("-" * 30)
    uri = get_user_input("Neo4j URI", "bolt://localhost:7687")
    env_content.append(f"NEO4J_URI={uri}")
    
    username = get_user_input("Neo4j 用户名", "neo4j")
    env_content.append(f"NEO4J_USERNAME={username}")
    
    password = get_user_input("Neo4j 密码", password=True)
    if password:
        env_content.append(f"NEO4J_PASSWORD={password}")
    
    # 应用配置
    print("\n🌐 应用配置")
    print("-" * 30)
    host = get_user_input("应用监听地址", "0.0.0.0")
    env_content.append(f"APP_HOST={host}")
    
    port = get_user_input("应用端口", "5000")
    env_content.append(f"APP_PORT={port}")
    
    debug = get_user_input("调试模式 (true/false)", "false")
    env_content.append(f"APP_DEBUG={debug}")
    
    # 功能开关
    print("\n⚙️  功能开关")
    print("-" * 30)
    enable_cache = get_user_input("启用缓存 (true/false)", "true")
    env_content.append(f"ENABLE_CACHE={enable_cache}")
    
    enable_embeddings = get_user_input("启用 Embedding (true/false)", "true")
    env_content.append(f"ENABLE_EMBEDDINGS={enable_embeddings}")
    
    enable_logging = get_user_input("启用交互日志 (true/false)", "false")
    env_content.append(f"ENABLE_INTERACTION_LOGGING={enable_logging}")
    
    # 缓存配置
    if enable_cache.lower() == 'true':
        print("\n💾 缓存配置")
        print("-" * 30)
        use_redis = get_user_input("使用 Redis (true/false)", "true")
        env_content.append(f"USE_REDIS={use_redis}")
        
        if use_redis.lower() == 'true':
            redis_host = get_user_input("Redis 主机", "localhost")
            env_content.append(f"REDIS_HOST={redis_host}")
            
            redis_port = get_user_input("Redis 端口", "6379")
            env_content.append(f"REDIS_PORT={redis_port}")
            
            redis_password = get_user_input("Redis 密码 (可选)", password=True)
            if redis_password:
                env_content.append(f"REDIS_PASSWORD={redis_password}")
    
    # 日志配置
    print("\n📋 日志配置")
    print("-" * 30)
    log_level = get_user_input("日志级别 (DEBUG/INFO/WARNING/ERROR)", "INFO")
    env_content.append(f"LOG_LEVEL={log_level}")
    
    # 写入文件
    env_file = Path(".env")
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(env_content))
    
    print(f"\n✅ 配置文件已创建: {env_file}")
    print("请检查并确认配置是否正确。")
    
    return env_file


def validate_config():
    """验证配置。"""
    try:
        config = ConfigManager()
        if config.validate():
            print("✅ 配置验证通过")
            return True
        else:
            print("❌ 配置验证失败")
            return False
    except Exception as e:
        print(f"❌ 配置验证错误: {e}")
        return False


def main():
    """主函数。"""
    if len(sys.argv) > 1 and sys.argv[1] == '--validate':
        # 仅验证配置
        return 0 if validate_config() else 1
    
    # 检查是否已存在.env文件
    if Path(".env").exists():
        print("⚠️  .env 文件已存在")
        overwrite = input("是否要覆盖现有配置? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("取消操作")
            return 0
    
    # 创建配置文件
    env_file = create_env_file()
    
    # 验证配置
    print("\n🔍 验证配置...")
    if validate_config():
        print("\n🎉 配置初始化完成！")
        print("现在可以运行应用了。")
        return 0
    else:
        print("\n❌ 配置验证失败，请检查配置并重新运行。")
        return 1


if __name__ == '__main__':
    sys.exit(main()) 