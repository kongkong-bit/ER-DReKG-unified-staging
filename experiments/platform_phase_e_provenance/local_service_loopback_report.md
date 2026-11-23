# 本机数据库端口与 IPv6 连接修复

日期：2026-11-14

## 发现与修复

- Docker 原来将 PostgreSQL `5432`、Neo4j `7474/7687` 发布到 `0.0.0.0` 和 `::`，扩大了本机开发数据库的网络可达范围。Compose 改为仅绑定 `127.0.0.1`，保留既有命名数据卷并重建容器。
- 重建后数据库健康，但应用仍连接 `localhost`。Windows 将该名称解析为 `::1` 优先、`127.0.0.1` 次之；容器只绑定 IPv4，因此 IPv6 连接失败。已在本机忽略文件 `.env` 中将 PostgreSQL 与 Neo4j 地址固定到 `127.0.0.1`，并同步更新 `.env.example`。没有读取或输出本地密码。
- FastAPI 以新配置重启，健康端点返回 200。

## 验收

- PostgreSQL、Neo4j 均为 healthy；Docker 发布地址只显示 `127.0.0.1`。
- PostgreSQL Alembic 版本仍为 `e4f62ab7093c (head)`；正式项目 14 个 AnalysisRun、9 个 GraphBuild 及历史证据仍可查询。
- Vite/FastAPI/数据库集成验证：**PASS**；正式 GraphBuild 的 38,998 条 EvidenceRecord、疾病上下文、82 条机制路径和历史 GraphBuild 证据均能读取。
- 完整后端回归：**47 passed**，日志见 `backend_pytest_loopback_20261114.log`。

## 本轮影响

只改变 Compose 端口绑定和本机连接地址，数据库数据卷未删除，PostgreSQL/Neo4j 数据未重算或改写。使用 `localhost` 的旧开发脚本应改用 `127.0.0.1`，以匹配新的绑定方式。
