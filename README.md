# FinRAG 金融智能研究 Agent

FinRAG 是一个面向金融研究场景的本地 RAG 演示项目。它不是通用聊天机器人，而是围绕金融 PDF/研报/财报资料完成知识库管理、文档导入、混合检索、重排、表格事实问答、引用追踪和 SSE 流式回答的端到端 Demo。

当前项目包含：

- `backend/`：FastAPI 后端，负责文档管理、语料导入、索引构建、RAG 检索、重排、问答和 SSE 输出。
- `frontend/`：React + Vite 前端，包含对话页面和知识库管理页面。
- `pdf2md/`：PDF 文本层/表格抽取工具，用于把 PDF 处理成 FinRAG 可导入的 Markdown、表格 JSON/CSV 和 manifest。
- `backend/app/data/`：本地数据目录，保存 raw 文档、processed JSON、索引和表格 facts。

## 核心能力

- 金融文档知识库管理：上传、导入、重建索引、查看文档和 chunk。
- 混合检索：BM25 + 向量检索 + RRF 融合。
- 重排：支持 mock provider 和阿里云百炼 rerank API。
- 文本生成：支持 mock provider 和阿里云百炼千问模型。
- 表格问答：PDF 表格会被抽取为 table/table_row chunk，并生成 `table_facts.json`；营收、净利润、EPS 等数值问题可以优先使用结构化表格事实回答。
- 引用追踪：回答中的 citation 可追踪到文档、页码、chunk、表格 ID 和表格事实元数据。

## 技术栈

- 后端：Python 3.9+、FastAPI、Uvicorn、Pydantic、FAISS/本地向量索引、BM25、jieba。
- 前端：Node.js、React、Vite、TypeScript。
- PDF 处理：PyMuPDF、pdfplumber。
- 模型服务：默认 mock provider；生产/演示可切换到阿里云百炼 API。

## 目录结构

```text
finRAG/
  backend/
    app/
      api/                 # FastAPI API 路由
      core/                # 检索、导入、模型 provider、Agent workflow
      data/                # 本地数据目录，生产部署时建议挂载持久化卷
    scripts/               # 导入语料、构建索引、seed 等脚本
    requirements.txt
    .env.example
  frontend/
    src/                   # React 前端
    package.json
    vite.config.ts
  pdf2md/                  # PDF 抽取工具
  docs/                    # PRD、接口清单、设计文档等
```

## 环境变量

后端配置文件示例在 `backend/.env.example`。部署前建议复制一份：

```bash
cp backend/.env.example backend/.env
```

常用配置：

```env
FINRAG_MODEL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
FINRAG_MODEL_API_KEY=你的阿里云百炼 API Key
FINRAG_MODEL_API_KEY_SILICON=你的硅基流动 API Key
FINRAG_SILICON_BASE_URL=https://api.siliconflow.cn/v1
FINRAG_EMBEDDING_MODEL=text-embedding-v4
FINRAG_RERANK_MODEL=qwen3-rerank
FINRAG_TEXT_MODEL=qwen-plus

# 本地开发可用 mock；正式演示/服务器部署建议改成 bailian
FINRAG_EMBEDDING_PROVIDER=mock
FINRAG_RERANK_PROVIDER=mock
FINRAG_TEXT_PROVIDER=mock

FINRAG_RETRIEVAL_TOP_K=20
FINRAG_RERANK_TOP_K=5
FINRAG_RRF_K=60
FINRAG_INDEX_DIR=backend/app/data/index
```

如果要使用阿里云百炼模型，把 provider 改成：

```env
FINRAG_EMBEDDING_PROVIDER=bailian
FINRAG_RERANK_PROVIDER=bailian
FINRAG_TEXT_PROVIDER=bailian
```

如果 embedding/rerank 使用硅基流动、文本生成继续使用百炼千问，可配置：

```env
FINRAG_MODEL_API_KEY=你的阿里云百炼 API Key
FINRAG_MODEL_API_KEY_SILICON=你的硅基流动 API Key
FINRAG_EMBEDDING_MODEL=BAAI/bge-m3
FINRAG_RERANK_MODEL=BAAI/bge-reranker-v2-m3
FINRAG_TEXT_MODEL=qwen-plus
FINRAG_EMBEDDING_PROVIDER=silicon
FINRAG_RERANK_PROVIDER=silicon
FINRAG_TEXT_PROVIDER=bailian
```

注意：

- `.env` 不要提交到 Git。
- 测试和本地无模型演示可以继续使用 `mock`。
- 如果切换了 embedding provider 或 embedding model，必须重建向量索引，否则可能出现向量维度不匹配。

## 本地开发启动

### 1. 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```bash
curl http://localhost:8000/health
```

### 2. 启动前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

默认前端地址：

```text
http://localhost:3000
```

开发模式下，`frontend/vite.config.ts` 已配置 `/api` 代理到 `http://localhost:8000`，因此前端可以直接请求 `/api/query`、`/api/kb/*` 等接口。

### 3. 常用接口

- `GET /health`：后端健康检查。
- `GET /api/documents`：文档列表。
- `POST /api/query`：RAG 问答 SSE 接口。
- `POST /api/debug/retrieval`：调试检索结果。
- `GET /api/kb/overview`：知识库概览。
- `GET /api/kb/documents`：知识库文档列表。
- `POST /api/kb/upload`：上传文档。
- `POST /api/kb/import`：触发导入。
- `POST /api/kb/reindex`：重建索引。

## 文档导入与索引构建

FinRAG 的标准数据流是：

```text
PDF / Markdown / TXT
  -> backend/app/data/raw/
  -> backend/app/data/processed/documents.json + chunks.json + table_facts.json
  -> backend/app/data/index/
  -> RAG 查询
```

### 1. PDF 抽取

把 PDF 放在一个源目录，例如：

```text
/your/data/source_documents/
```

然后执行：

```bash
cd pdf2md
python3 -m elite_daily_pdf_to_md.cli \
  --profile finrag \
  --source-dir "/your/data/source_documents" \
  --raw-root "/path/to/finRAG/backend/app/data/raw" \
  --collection-name "finrag-user-source" \
  --extractor pymupdf
```

抽取后会生成：

```text
backend/app/data/raw/extracted/<collection-name>/*.md
backend/app/data/raw/tables/<collection-name>/**/*.json
backend/app/data/raw/tables/<collection-name>/**/*.csv
backend/app/data/raw/_meta/*manifest*.json
```

也可以把人工补充的 Markdown/TXT 放到：

```text
backend/app/data/raw/manual/<collection-name>/
```

### 2. 导入 processed JSON 并重建索引

```bash
cd backend
python3 scripts/import_corpus.py \
  --raw-root app/data/raw \
  --collection-name finrag-user-source \
  --processed-dir app/data/processed \
  --index-dir app/data/index \
  --rebuild-index
```

导入结果包括：

```text
backend/app/data/processed/documents.json
backend/app/data/processed/chunks.json
backend/app/data/processed/table_facts.json
backend/app/data/index/*
```

如果只想重建索引：

```bash
cd backend
python3 scripts/build_index.py
```

## 测试

后端测试：

```bash
cd backend
python3 -m pytest
```

前端类型检查和构建：

```bash
cd frontend
npm run lint
npm run build
```

## 服务器部署建议

### 推荐方案：直接部署后端 + 前端静态文件 + Nginx 反向代理

当前仓库还没有维护好的 Dockerfile / docker-compose，因此短期部署建议使用“直接运行”的方式，更容易排查数据目录、模型 API Key、索引文件和 PDF 导入问题。

推荐服务器结构：

```text
/opt/finrag/
  repo/                 # Git 仓库代码
  data/                 # 持久化数据目录，可软链或挂载到 backend/app/data
  logs/                 # 日志
```

### 1. 安装系统依赖

Ubuntu/Debian 示例：

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm nginx git
```

建议 Node.js 使用 20+。如果系统源版本太低，可使用 NodeSource 或 nvm 安装。

### 2. 拉取代码并安装依赖

```bash
sudo mkdir -p /opt/finrag
sudo chown -R $USER:$USER /opt/finrag
cd /opt/finrag
git clone <你的仓库地址> repo
cd repo

cd backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

cd ../frontend
npm install
npm run build
```

### 3. 配置后端环境变量

```bash
cd /opt/finrag/repo
cp backend/.env.example backend/.env
nano backend/.env
```

生产/演示建议：

```env
FINRAG_EMBEDDING_PROVIDER=silicon
FINRAG_RERANK_PROVIDER=silicon
FINRAG_TEXT_PROVIDER=bailian
FINRAG_MODEL_API_KEY=你的阿里云百炼 API Key
FINRAG_MODEL_API_KEY_SILICON=你的硅基流动 API Key
FINRAG_INDEX_DIR=backend/app/data/index
```

如果只是无模型演示，可以继续保持：

```env
FINRAG_EMBEDDING_PROVIDER=mock
FINRAG_RERANK_PROVIDER=mock
FINRAG_TEXT_PROVIDER=mock
```

### 4. 准备数据和索引

把已抽取/导入好的数据放在：

```text
/opt/finrag/repo/backend/app/data/
```

如果服务器上重新导入：

```bash
cd /opt/finrag/repo/backend
source .venv/bin/activate
python3 scripts/import_corpus.py \
  --raw-root app/data/raw \
  --collection-name finrag-user-source-40 \
  --processed-dir app/data/processed \
  --index-dir app/data/index \
  --rebuild-index
```

重要：如果 `.env` 中使用 `bailian` 或 `silicon` embedding provider，索引也必须用同样 provider 和同一个 embedding model 重建。不要用 mock 索引搭配真实 embedding 查询，也不要用旧模型索引搭配新模型查询。

### 5. 使用 systemd 运行后端

创建服务文件：

```bash
sudo nano /etc/systemd/system/finrag-backend.service
```

示例内容：

```ini
[Unit]
Description=FinRAG FastAPI Backend
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/finrag/repo/backend
EnvironmentFile=/opt/finrag/repo/backend/.env
ExecStart=/opt/finrag/repo/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable finrag-backend
sudo systemctl start finrag-backend
sudo systemctl status finrag-backend
```

查看日志：

```bash
journalctl -u finrag-backend -f
```

### 6. 使用 Nginx 托管前端并反向代理 API

前端构建目录：

```text
/opt/finrag/repo/frontend/dist
```

创建 Nginx 配置：

```bash
sudo nano /etc/nginx/sites-available/finrag
```

示例：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /opt/finrag/repo/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/finrag /etc/nginx/sites-enabled/finrag
sudo nginx -t
sudo systemctl reload nginx
```

如果使用 HTTPS，建议再用 Certbot 配置证书：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 是否建议 Docker 部署？

短期建议：**优先直接部署，不强制 Docker**。

原因：

- 当前项目没有正式维护的 `Dockerfile` / `docker-compose.yml`。
- 本项目包含较多本地数据、索引、PDF 抽取产物和模型 provider 配置，直接部署更容易定位路径和权限问题。
- 如果使用阿里云百炼 embedding，索引构建和运行时 provider 必须一致；直接部署时更容易确认环境变量。

什么时候适合 Docker：

- 你需要多服务器复制部署。
- 你希望把 Python/Node/Nginx 运行环境完全固化。
- 你已经明确数据卷挂载路径，例如 `/data/finrag/backend/app/data`。

如果要 Docker 化，建议拆成至少两个镜像/服务：

```text
finrag-backend   # FastAPI + Uvicorn
finrag-frontend  # Nginx 静态托管 frontend/dist，并反代 /api 到 backend
```

并把数据目录作为 volume 挂载：

```text
backend/app/data/raw
backend/app/data/processed
backend/app/data/index
```

目前 README 以直接部署为主；如果后续需要，我可以再为项目补充生产可用的 `Dockerfile` 和 `docker-compose.yml`。

## 生产运维注意事项

- 数据目录必须持久化，尤其是 `backend/app/data/processed` 和 `backend/app/data/index`。
- 切换 embedding provider 后必须重建索引。
- `.env` 中的 API Key 不要提交到 Git，也不要写进前端代码。
- SSE 接口需要 Nginx 关闭 buffering：`proxy_buffering off;`。
- 文档导入和索引重建会消耗 CPU/内存，建议在低峰期执行。
- 如果知识库导入后问答结果异常，优先检查：`documents.json`、`chunks.json`、`table_facts.json`、索引 provider 是否一致。

## 常见问题

### 1. 查询时报向量维度不匹配

通常是索引用 mock embedding 构建，但运行时改成了百炼 embedding，或反过来。解决方式：使用当前 `.env` 的 provider 重新执行：

```bash
cd backend
source .venv/bin/activate
python3 scripts/import_corpus.py \
  --raw-root app/data/raw \
  --collection-name finrag-user-source-40 \
  --processed-dir app/data/processed \
  --index-dir app/data/index \
  --rebuild-index
```

### 2. 前端能打开但问答失败

检查：

```bash
curl http://127.0.0.1:8000/health
journalctl -u finrag-backend -f
sudo nginx -t
```

确认 Nginx `/api/` 已正确反向代理到后端。

### 3. 表格问题答不准

检查 `backend/app/data/processed/table_facts.json` 是否存在，并确认目标公司/指标是否生成了 facts。当前系统对“公司 + 指标 + 年份/季度”的数值问题会优先使用结构化表格事实；如果 PDF 表格没有成功抽取成 facts，需要先改善 PDF 表格抽取或重新导入。

## 版本状态

当前项目已完成：

- 文档导入 pipeline。
- 知识库管理页面与后端联调。
- PDF 表格抽取。
- table/table_row chunk 和 `table_facts.json` 生成。
- 表格事实优先的数值问答与 citation metadata。

下一步建议：完成 milestone review，随后根据演示需要决定是否补 Docker 部署文件、生产日志、权限控制和更完整的运维脚本。
