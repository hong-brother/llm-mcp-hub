# Azure Cloud Container 배포 가이드

## 1. 개요

LLM MCP Hub를 Azure 클라우드 컨테이너 서비스에서 운영하기 위한 가이드 문서입니다.

### 1.1 지원 서비스

| 서비스 | 권장도 | 설명 |
|--------|--------|------|
| **Azure Container Apps** | 권장 | 서버리스 컨테이너, 자동 스케일링 |
| Azure Container Instance | - | 단순 컨테이너 실행, 장기 실행 시 비용 증가 |

### 1.2 핵심 제약사항

> **API Key 사용 금지** - SDK/CLI 기반 OAuth 인증만 사용

- Anthropic API Key, Google AI API Key 사용 불가
- **Claude**: Agent SDK + OAuth 토큰 (`CLAUDE_CODE_OAUTH_TOKEN` 환경변수)
- **Gemini**: CLI + PTY Wrapper (OAuth 토큰 파일 마운트)
- OAuth 토큰은 Azure Key Vault / Azure Files에서 관리

---

## 2. 아키텍처

### 2.1 전체 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                         Azure Cloud                              │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  Azure Key Vault │    │  Azure Files     │                   │
│  │  (Secrets)       │    │  (Gemini Token)  │                   │
│  │                  │    │                  │                   │
│  │  - CLAUDE_CODE_  │    │  └─ gemini/      │                   │
│  │    OAUTH_TOKEN   │    │     └─ oauth_    │                   │
│  │  - REDIS_CONN    │    │        creds.json│                   │
│  └────────┬─────────┘    └─────────┬────────┘                   │
│           │                        │                            │
│           │    ┌───────────────────┼───────────────────┐        │
│           │    │                   │                   │        │
│           ▼    ▼                   ▼                   │        │
│  ┌─────────────────────────────────────────────────────┴──┐     │
│  │              Azure Container Apps Environment           │     │
│  │  ┌───────────────────────────────────────────────────┐ │     │
│  │  │              LLM MCP Hub Container                 │ │     │
│  │  │                                                    │ │     │
│  │  │  ┌─────────────────┐  ┌─────────────────┐        │ │     │
│  │  │  │ Claude Adapter  │  │ Gemini Adapter  │        │ │     │
│  │  │  │ (Agent SDK)     │  │ (PTY + CLI)     │        │ │     │
│  │  │  │                 │  │                 │        │ │     │
│  │  │  │ Env Var 인증    │  │ File 마운트 인증│        │ │     │
│  │  │  └─────────────────┘  └─────────────────┘        │ │     │
│  │  │                                                    │ │     │
│  │  │  Volume Mounts:                                    │ │     │
│  │  │  /mnt/auth/gemini/oauth_creds.json                │ │     │
│  │  └───────────────────────────────────────────────────┘ │     │
│  └────────────────────────┬───────────────────────────────┘     │
│                           │                                      │
│                           ▼                                      │
│                ┌─────────────────────┐                          │
│                │  Azure Redis Cache  │                          │
│                │  (Session Store)    │                          │
│                └─────────────────────┘                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    External Users    │
                    │  - REST API Client   │
                    │  - MCP Client        │
                    │  - n8n Workflow      │
                    └─────────────────────┘
```

### 2.2 인증 방식 비교

| Provider | 인증 방식 | Azure 저장소 | 컨테이너 설정 |
|----------|----------|-------------|--------------|
| **Claude** | Agent SDK + OAuth | Key Vault Secret | 환경변수 참조 |
| **Gemini** | CLI + PTY | Azure Files | 볼륨 마운트 |

---

## 3. OAuth 토큰 관리

### 3.1 토큰 유효 기간

| CLI | Access Token | Refresh Token | 재인증 주기 권장 |
|-----|--------------|---------------|-----------------|
| Claude | 1시간 | 수일~수주 | **1~2주** |
| Gemini | 1시간 | 수개월 | **2~4주** |

### 3.2 토큰 저장 구조

**Claude**: Azure Key Vault Secret
```
Secret Name: claude-oauth-token
Value: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Gemini**: Azure Files
```
Azure Files (auth-files share)
└── gemini/
    └── oauth_creds.json
        {
          "access_token": "ya29.a0AfH6SMC...",
          "refresh_token": "1//0eXXXXXX...",
          "token_uri": "https://oauth2.googleapis.com/token",
          "expiry": "2026-01-10T12:00:00Z"
        }
```

### 3.3 토큰 갱신 워크플로우

```
┌─────────────────────────────────────────────────────────┐
│                   토큰 갱신 워크플로우                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Day 1: 초기 인증                                       │
│    ├─ 로컬에서 claude setup-token 실행                  │
│    ├─ 로컬에서 gemini 실행 (Google 로그인)              │
│    ├─ Claude 토큰 → Azure Key Vault에 저장             │
│    └─ Gemini 토큰 → Azure Files에 업로드               │
│                                                         │
│  Day 1~14: 정상 운영                                    │
│    ├─ Access Token: SDK/CLI가 자동 갱신                │
│    └─ Refresh Token: 유효                               │
│                                                         │
│  Day 11: 헬스체크                                       │
│    ├─ /health/tokens API로 만료 임박 감지              │
│    └─ 알림 발송 (Slack/Email)                          │
│                                                         │
│  Day 14: 재인증                                         │
│    ├─ 관리자 로컬에서 재인증                            │
│    ├─ Azure Key Vault/Files 업데이트                   │
│    └─ Container App 재시작 (필요시)                     │
│                                                         │
│  Day 15~28: 정상 운영 (반복)                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 배포 가이드

### 4.1 사전 요구사항

- Azure CLI 설치
- Azure 구독 및 리소스 그룹
- Docker 이미지 레지스트리 (Azure Container Registry 권장)
- 로컬에서 Claude/Gemini 인증 완료

### 4.2 Step 1: Azure 리소스 생성

```bash
# 변수 설정
RESOURCE_GROUP="llm-mcp-hub-rg"
LOCATION="koreacentral"
STORAGE_ACCOUNT="llmmcphubstorage"
KEY_VAULT="llm-mcp-hub-kv"
CONTAINER_ENV="llm-mcp-hub-env"
CONTAINER_APP="llm-mcp-hub"
REDIS_NAME="llm-mcp-hub-redis"
ACR_NAME="llmmcphubacr"

# 리소스 그룹 생성
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Azure Container Registry 생성
az acr create \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku Basic

# Key Vault 생성 (Claude 토큰용)
az keyvault create \
  --name $KEY_VAULT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Storage Account 생성 (Gemini 토큰용)
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Storage Account Key 조회
STORAGE_KEY=$(az storage account keys list \
  --account-name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query '[0].value' -o tsv)

# File Share 생성
az storage share create \
  --name auth-files \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY

# Azure Redis Cache 생성
az redis create \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Basic \
  --vm-size c0
```

### 4.3 Step 2: OAuth 토큰 업로드

**Claude 토큰 → Key Vault:**
```bash
# 로컬에서 토큰 생성
claude setup-token

# 토큰 추출 (Linux)
CLAUDE_TOKEN=$(cat ~/.claude/.credentials.json | jq -r '.accessToken')

# Key Vault에 저장
az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "claude-oauth-token" \
  --value "$CLAUDE_TOKEN"
```

**Gemini 토큰 → Azure Files:**
```bash
# 로컬에서 인증
gemini  # "Login with Google" 선택

# Azure Files에 업로드
az storage directory create \
  --share-name auth-files \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --name gemini

az storage file upload \
  --share-name auth-files \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --source ~/.gemini/oauth_creds.json \
  --path gemini/oauth_creds.json
```

### 4.4 Step 3: Container Apps 환경 생성

```bash
# Container Apps 환경 생성
az containerapp env create \
  --name $CONTAINER_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Storage 연결 (Gemini 토큰 파일용)
az containerapp env storage set \
  --name $CONTAINER_ENV \
  --resource-group $RESOURCE_GROUP \
  --storage-name authstorage \
  --azure-file-account-name $STORAGE_ACCOUNT \
  --azure-file-account-key $STORAGE_KEY \
  --azure-file-share-name auth-files \
  --access-mode ReadOnly
```

### 4.5 Step 4: Container App 배포

**container-app.yaml:**

```yaml
properties:
  managedEnvironmentId: /subscriptions/{subscription-id}/resourceGroups/llm-mcp-hub-rg/providers/Microsoft.App/managedEnvironments/llm-mcp-hub-env
  configuration:
    ingress:
      external: true
      targetPort: 8000
      transport: http
      allowInsecure: false
    secrets:
      - name: claude-oauth-token
        keyVaultUrl: https://llm-mcp-hub-kv.vault.azure.net/secrets/claude-oauth-token
        identity: system
      - name: redis-connection-string
        value: "{redis-connection-string}"
    registries:
      - server: llmmcphubacr.azurecr.io
        identity: system
  template:
    containers:
      - name: llm-mcp-hub
        image: llmmcphubacr.azurecr.io/llm-mcp-hub:latest
        resources:
          cpu: 1.0
          memory: 2Gi
        env:
          # Claude - Key Vault에서 토큰 로드
          - name: CLAUDE_CODE_OAUTH_TOKEN
            secretRef: claude-oauth-token
          - name: CLAUDE_MODEL
            value: claude-sonnet-4-5-20250929

          # Gemini - 파일 마운트 경로
          - name: GEMINI_AUTH_PATH
            value: /mnt/auth/gemini/oauth_creds.json
          - name: GEMINI_MODEL
            value: gemini-2.5-pro

          # Redis
          - name: REDIS_URL
            secretRef: redis-connection-string

          # 로깅
          - name: LOG_LEVEL
            value: INFO
        volumeMounts:
          - volumeName: auth-storage
            mountPath: /mnt/auth
    volumes:
      - name: auth-storage
        storageName: authstorage
        storageType: AzureFile
    scale:
      minReplicas: 1
      maxReplicas: 3
      rules:
        - name: http-rule
          http:
            metadata:
              concurrentRequests: "100"
  identity:
    type: SystemAssigned
```

**배포 실행:**

```bash
# System Assigned Identity 활성화 및 Key Vault 접근 권한 부여
az containerapp create \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --yaml container-app.yaml

# Container App의 Identity에 Key Vault 접근 권한 부여
IDENTITY_PRINCIPAL_ID=$(az containerapp show \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --query identity.principalId -o tsv)

az keyvault set-policy \
  --name $KEY_VAULT \
  --object-id $IDENTITY_PRINCIPAL_ID \
  --secret-permissions get list
```

### 4.6 Step 5: 배포 확인

```bash
# Container App URL 조회
APP_URL=$(az containerapp show \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)

echo "App URL: https://$APP_URL"

# 헬스체크
curl https://$APP_URL/health

# 토큰 상태 확인
curl https://$APP_URL/health/tokens
```

---

## 5. 운영 가이드

### 5.1 토큰 갱신 스크립트

**refresh-tokens.sh:**

```bash
#!/bin/bash
# OAuth 토큰 갱신 스크립트

RESOURCE_GROUP="llm-mcp-hub-rg"
KEY_VAULT="llm-mcp-hub-kv"
STORAGE_ACCOUNT="llmmcphubstorage"
CONTAINER_APP="llm-mcp-hub"

# Storage Key 조회
STORAGE_KEY=$(az storage account keys list \
  --account-name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query '[0].value' -o tsv)

echo "=== OAuth 토큰 갱신 시작 ==="

# 1. Claude 재인증
echo "1. Claude 재인증..."
claude setup-token

# 2. Claude 토큰 → Key Vault 업데이트
echo "2. Claude 토큰 업로드..."
CLAUDE_TOKEN=$(cat ~/.claude/.credentials.json | jq -r '.accessToken')
az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "claude-oauth-token" \
  --value "$CLAUDE_TOKEN"

# 3. Gemini 재인증
echo "3. Gemini 재인증..."
gemini  # "Login with Google" 선택

# 4. Gemini 토큰 → Azure Files 업데이트
echo "4. Gemini 토큰 업로드..."
az storage file upload \
  --share-name auth-files \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --source ~/.gemini/oauth_creds.json \
  --path gemini/oauth_creds.json \
  --overwrite

# 5. Container App 재시작
echo "5. Container App 재시작..."
az containerapp revision restart \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP

echo "=== 토큰 갱신 완료 ==="
```

### 5.2 헬스체크 모니터링

**토큰 상태 확인 API:**

```
GET /health/tokens

Response:
{
  "claude": {
    "status": "valid",
    "expires_at": "2026-01-15T12:00:00Z",
    "days_remaining": 7
  },
  "gemini": {
    "status": "valid",
    "expires_at": "2026-01-22T12:00:00Z",
    "days_remaining": 14
  }
}
```

### 5.3 알림 설정 (Azure Monitor)

```bash
# 토큰 만료 임박 알림 (Application Insights 메트릭 기반)
az monitor metrics alert create \
  --name "token-expiry-alert" \
  --resource-group $RESOURCE_GROUP \
  --scopes /subscriptions/{sub-id}/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/containerApps/$CONTAINER_APP \
  --condition "avg token_days_remaining < 3" \
  --action-group "ops-team-action-group" \
  --description "OAuth token expires in less than 3 days"
```

---

## 6. Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Node.js 설치 (Gemini CLI용)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Gemini CLI 설치
RUN npm install -g @google/gemini-cli

# Python 패키지 관리자 (uv)
RUN pip install uv

# 의존성 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# 소스 코드
COPY src/ ./src/

# 환경변수 기본값
ENV CLAUDE_CODE_OAUTH_TOKEN=""
ENV CLAUDE_MODEL="claude-sonnet-4-5-20250929"
ENV GEMINI_AUTH_PATH="/mnt/auth/gemini/oauth_creds.json"
ENV GEMINI_MODEL="gemini-2.5-pro"
ENV REDIS_URL="redis://localhost:6379"
ENV LOG_LEVEL="INFO"

# 포트 노출
EXPOSE 8000

# 실행
CMD ["uv", "run", "uvicorn", "llm_mcp_hub.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 7. 비용 예상

### 7.1 월간 비용 (예상)

| 서비스 | 사양 | 예상 비용 (USD) |
|--------|------|----------------|
| Azure Container Apps | 1 vCPU, 2GB RAM, 항상 실행 | $50-70 |
| Azure Files | Standard, 1GB | $0.06 |
| Azure Key Vault | Standard | $0.03/10K ops |
| Azure Redis Cache | Basic C0 (250MB) | $16 |
| Azure Container Registry | Basic | $5 |
| 네트워크 (Egress) | ~10GB/월 | $1 |
| **총계** | | **~$72-92/월** |

### 7.2 비용 최적화 방안

| 방안 | 절감 효과 | 트레이드오프 |
|------|----------|-------------|
| 최소 레플리카 0 설정 | -30% | Cold start 지연 (수 초) |
| Redis 대신 인메모리 | -$16 | 세션 영속성 없음, 단일 인스턴스만 |

---

## 8. 제약사항 및 주의점

### 8.1 기술적 제약

| 항목 | 제약 | 해결 방안 |
|------|------|----------|
| Azure Files SMB | Linux 컨테이너만 지원 | Linux 베이스 이미지 사용 |
| Key Vault 접근 | Managed Identity 필요 | System Assigned Identity 활성화 |
| Gemini PTY | TTY 필요 | ptyprocess 라이브러리 사용 |
| Cold Start | 스케일 0→1 시 지연 | minReplicas: 1 설정 |

### 8.2 운영 제약

| 항목 | 제약 | 해결 방안 |
|------|------|----------|
| 토큰 자동 갱신 | 완전 자동화 불가 (OAuth 브라우저 인증) | 1~2주 주기 수동 갱신 + 알림 |
| OAuth 브라우저 인증 | 컨테이너 내 불가 | 로컬에서 인증 후 업로드 |
| Refresh Token 만료 | 예측 어려움 | 보수적 갱신 주기 (1~2주) |

---

## 9. 트러블슈팅

### 9.1 일반적인 문제

**문제: Claude 토큰 인증 실패**

```bash
# 로그 확인
az containerapp logs show \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP

# Key Vault Secret 확인
az keyvault secret show \
  --vault-name $KEY_VAULT \
  --name "claude-oauth-token"

# 해결: 토큰 재생성 및 업데이트
claude setup-token
CLAUDE_TOKEN=$(cat ~/.claude/.credentials.json | jq -r '.accessToken')
az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name "claude-oauth-token" \
  --value "$CLAUDE_TOKEN"
```

**문제: Gemini 파일 마운트 실패**

```bash
# Storage 연결 상태 확인
az containerapp env storage show \
  --name $CONTAINER_ENV \
  --resource-group $RESOURCE_GROUP \
  --storage-name authstorage

# 해결: Storage Key 재설정
NEW_STORAGE_KEY=$(az storage account keys list \
  --account-name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query '[0].value' -o tsv)

az containerapp env storage set \
  --name $CONTAINER_ENV \
  --resource-group $RESOURCE_GROUP \
  --storage-name authstorage \
  --azure-file-account-key $NEW_STORAGE_KEY
```

**문제: Redis 연결 실패**

```bash
# Redis 상태 확인
az redis show \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP

# 연결 문자열 확인
az redis list-keys \
  --name $REDIS_NAME \
  --resource-group $RESOURCE_GROUP
```

### 9.2 디버깅 명령어

```bash
# Container App 로그 실시간 확인
az containerapp logs show \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --follow

# Container App 콘솔 접속
az containerapp exec \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --command /bin/bash

# 리비전 목록 확인
az containerapp revision list \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --output table

# 환경변수 확인 (콘솔 접속 후)
echo $CLAUDE_CODE_OAUTH_TOKEN
cat $GEMINI_AUTH_PATH
```

---

## 10. 참고 자료

- [Azure Container Apps 문서](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure Container Apps Storage Mounts](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts)
- [Azure Key Vault with Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets)
- [Claude Agent SDK - PyPI](https://pypi.org/project/claude-agent-sdk/)
- [Gemini CLI - GitHub](https://github.com/google-gemini/gemini-cli)
- [ptyprocess - PyPI](https://pypi.org/project/ptyprocess/)

---

## 11. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 0.1 | 2026-01-08 | - | 초안 작성 |
| 0.2 | 2026-01-09 | - | **아키텍처 변경**: subprocess → SDK 기반. Claude Agent SDK + Gemini PTY Wrapper. Key Vault/Azure Files 분리 저장. |
