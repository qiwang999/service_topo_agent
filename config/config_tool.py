#!/usr/bin/env python3
"""
配置管理工具
用于查看、验证和导出项目配置。
"""

import argparse
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config_manager import ConfigManager


def main():
    parser = argparse.ArgumentParser(description='配置管理工具')
    parser.add_argument('action', choices=['show', 'validate', 'export', 'check'], 
                       help='要执行的操作')
    parser.add_argument('--section', '-s', 
                       help='要查看的配置节（仅对show操作有效）')
    parser.add_argument('--output', '-o', default='.env.example',
                       help='输出文件名（仅对export操作有效）')
    parser.add_argument('--env-file', '-e', default='.env',
                       help='环境变量文件路径')
    
    args = parser.parse_args()
    
    try:
        # 初始化配置管理器
        config = ConfigManager(args.env_file)
        
        if args.action == 'show':
            if args.section:
                config.print_config(args.section)
            else:
                config.print_config()
                
        elif args.action == 'validate':
            if config.validate():
                print("✅ 配置验证通过")
                return 0
            else:
                print("❌ 配置验证失败")
                return 1
                
        elif args.action == 'export':
            config.export_env_file(args.output)
            
        elif args.action == 'check':
            print("🔍 检查配置状态...")
            
            # 检查必需的环境变量
            required_vars = ['OPENAI_API_KEY', 'NEO4J_PASSWORD']
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
                print("请设置这些环境变量或创建 .env 文件")
                return 1
            else:
                print("✅ 所有必需的环境变量已设置")
            
            # 检查可选配置
            optional_checks = [
                ('ENABLE_CACHE', '缓存功能'),
                ('ENABLE_EMBEDDINGS', 'Embedding功能'),
                ('USE_REDIS', 'Redis缓存'),
                ('ENABLE_VALIDATION', '验证功能')
            ]
            
            for var, desc in optional_checks:
                value = os.getenv(var, 'true').lower()
                status = "✅" if value == 'true' else "⚠️"
                print(f"{status} {desc}: {value}")
            
            # 检查数据库连接
            try:
                neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
                print(f"📊 Neo4j URI: {neo4j_uri}")
            except Exception as e:
                print(f"❌ Neo4j配置错误: {e}")
            
            # 检查应用配置
            app_port = os.getenv('APP_PORT', '5000')
            print(f"🌐 应用端口: {app_port}")
            
            return 0
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main()) 