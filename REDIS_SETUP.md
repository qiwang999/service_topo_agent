# Redis 缓存配置指南

## 为什么使用 Redis？

Redis 相比 SQLite 在缓存场景下有以下优势：

### 性能优势
- **内存存储**：数据存储在内存中，读写速度极快
- **单线程模型**：避免了锁竞争，性能稳定
- **原子操作**：支持原子性的复杂操作

### 缓存特性
- **TTL 支持**：内置过期时间功能
- **淘汰策略**：支持 LRU、LFU、Random 等淘汰策略
- **数据结构丰富**：String、Hash、List、Set、ZSet

### 扩展性
- **分布式支持**：支持集群模式
- **持久化**：支持 RDB 和 AOF 持久化
- **高可用**：支持主从复制和哨兵模式

## 安装 Redis

### macOS
```bash
# 使用 Homebrew
brew install redis

# 启动 Redis
brew services start redis
```

### Ubuntu/Debian
```bash
# 安装 Redis
sudo apt update
sudo apt install redis-server

# 启动 Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Docker
```bash
# 运行 Redis 容器
docker run -d --name redis-cache -p 6379:6379 redis:latest

# 或者使用 docker-compose
docker-compose up -d redis
```

## 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# Redis Configuration
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_DB="0"
REDIS_PASSWORD=""  # 如果设置了密码
REDIS_TTL="3600"   # 缓存过期时间（秒）
```

## 系统架构

### 混合缓存管理器

系统使用 `HybridCacheManager` 类，支持自动回退：

1. **优先使用 Redis**：如果 Redis 可用，优先使用 Redis 缓存
2. **自动回退**：如果 Redis 不可用，自动回退到 SQLite
3. **透明切换**：对上层应用透明，无需修改业务代码

### 缓存策略

```python
# 初始化缓存管理器
cache_manager = HybridCacheManager(
    use_redis=True,  # 尝试使用 Redis
    redis_config={
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'password': None,
        'default_ttl': 3600
    }
)
```

## 性能对比

| 特性 | SQLite | Redis |
|------|--------|-------|
| 存储方式 | 磁盘 | 内存 |
| 读写速度 | 慢 | 快 |
| TTL 支持 | 无 | 有 |
| 淘汰策略 | 无 | 丰富 |
| 分布式 | 不支持 | 支持 |
| 内存占用 | 低 | 高 |
| 持久化 | 自动 | 可选 |

## 使用建议

### 开发环境
- 使用 SQLite：简单部署，无需额外服务
- 适合：快速原型、单机测试

### 生产环境
- 使用 Redis：高性能、可扩展
- 适合：高并发、多实例部署

### 混合模式
- 优先 Redis，回退 SQLite
- 适合：渐进式迁移、容错需求

## 监控和维护

### Redis 监控
```bash
# 查看 Redis 信息
redis-cli info

# 查看内存使用
redis-cli info memory

# 查看连接数
redis-cli info clients
```

### 缓存统计
```bash
# 通过 API 获取缓存统计
curl -X GET http://localhost:5001/enhanced/cache-stats
```

### 清理缓存
```bash
# 清理所有缓存
redis-cli flushdb

# 清理特定模式的缓存
redis-cli --scan --pattern "query_cache:*" | xargs redis-cli del
```

## 故障排除

### 常见问题

1. **Redis 连接失败**
   - 检查 Redis 服务是否启动
   - 检查端口和密码配置
   - 查看防火墙设置

2. **内存不足**
   - 调整 Redis 内存限制
   - 配置合适的淘汰策略
   - 监控内存使用情况

3. **性能问题**
   - 检查网络延迟
   - 优化 Redis 配置
   - 考虑使用 Redis 集群

### 日志查看
```bash
# 查看 Redis 日志
tail -f /var/log/redis/redis-server.log

# 查看应用日志
tail -f /var/log/your-app.log
```

## 最佳实践

1. **合理设置 TTL**：根据数据更新频率设置合适的过期时间
2. **监控内存使用**：定期检查 Redis 内存使用情况
3. **备份策略**：配置 Redis 持久化和备份
4. **安全配置**：设置密码和访问控制
5. **性能调优**：根据实际负载调整 Redis 配置 