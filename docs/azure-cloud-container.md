# Azure Cloud Container 배포 가이드

## 1. 개요

LLM MCP Hub를 Azure 클라우드 컨테이너 서비스에서 운영하기 위한 가이드 문서입니다.

### 1.1 지원 서비스

| 서비스 | 권장도 | 설명 |
|--------|--------|------|
| **Azure Container Apps** | ⭐⭐⭐ | 권장 - 서버리스 컨테이너, 자동 스케일링 |
| Azure Container Instance | ⭐⭐ | 단순 컨테이너 실행, 장기 실행 시 비용 증가 |

### 1.2 핵심 제약사항

> **API Key 사용 금지** - CLI 기반 OAuth 인증만 사용

- Anthropic API Key, Google AI API Key 사용 불가
- Claude CLI OAuth, Gemini CLI OAuth로 기존 구독 플랜 활용
- OAuth 토큰은 Azure Files에 영속화하여 관리

---

## 2. 아키텍처

### 2.1 전체 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                         Azure Cloud                              │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  Azure Key Vault │    │  Azure Files     │                   │
│  │  (Secrets)       │    │  (Auth Tokens)   │                   │
│  │  - Storage Key   │    │  ├─ claude/      │                   │
│  │  - Redis Conn    │    │  │  └─ auth.json │                   │
│  └────────┬─────────┘    │  └─ gemini/      │                   │
│           │              │     └─ creds.json│                   │
│           │              └─────────┬────────┘                   │
│           │                        │                            │
│           │    ┌───────────────────┼───────────────────┐        │
│           │    │                   │                   │        │
│           ▼    ▼                   ▼                   │        │
│  ┌─────────────────────────────────────────────────────┴──┐     │
│  │              Azure Container Apps Environment           │     │
│  │  ┌───────────────────────────────────────────────────┐ │     │
│  │  │              LLM MCP Hub Container                 │ │     │
│  │  │                                                    │ │     │
│  │  │  ┌─────────────┐  ┌─────────────┐                 │ │     │
│  │  │  │ Claude CLI  │  │ Gemini CLI  │                 │ │     │
│  │  │  │ (subprocess)│  │ (subprocess)│                 │ │     │
│  │  │  └─────────────┘  └─────────────┘                 │ │     │
│  │  │                                                    │ │     │
│  │  │  Volume Mounts:                                    │ │     │
│  │  │  /mnt/auth/claude/auth.json                       │ │     │
│  │  │  /mnt/auth/gemini/creds.json                      │ │     │
│  │  └───────────────────────────────────────────────────┘ │     │
│  └────────────────────────────┬───────────────────────────┘     │
│                               │                                  │
│                               ▼                                  │
│                    ┌─────────────────────┐                      │
│                    │  Azure Redis Cache  │                      │
│                    │  (Session Store)    │                      │
│                    └─────────────────────┘                      │
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

### 2.2 서비스 비교

| 항목 | Azure Container Apps | Azure Container Instance |
|------|---------------------|-------------------------|
| **영속 스토리지** | Azure Files (SMB/NFS) | Azure Files (Linux만) |
| **Secret 관리** | 앱 레벨 Secret + 볼륨 마운트 | Secret Volume (tmpfs) |
| **자동 스케일링** | O | X |
| **장기 실행** | O (항상 실행 가능) | O (비용 계속 발생) |
| **비용 모델** | 사용량 기반 | 초 단위 과금 |
| **Ingress** | 내장 (HTTPS) | 별도 설정 필요 |
| **MCP 서버 적합도** | ⭐⭐⭐ | ⭐⭐ |

---

## 3. OAuth 토큰 관리

### 3.1 토큰 유효 기간

| CLI | Access Token | Refresh Token | 재인증 주기 권장 |
|-----|--------------|---------------|-----------------|
| Claude CLI | 1시간 (3600초) | 수일~수주 | **1~2주** |
| Gemini CLI | 1시간 (60분) | 수개월 | **2~4주** |

### 3.2 토큰 저장 구조

```
Azure Files (auth-files share)
├── claude/
│   └── auth.json          # Claude OAuth credentials
│       {
│         "accessToken": "...",
│         "refreshToken": "...",
│         "expiresAt": 1234567890,
│         "scopes": ["user:inference", "user:profile"]
│       }
└── gemini/
    └── creds.json         # Gemini OAuth credentials
        {
          "access_token": "...",
          "refresh_token": "...",
          "token_uri": "...",
          "expiry": "..."
        }
```

### 3.3 토큰 갱신 프로세스

```
┌─────────────────────────────────────────────────────────┐
│                   토큰 갱신 워크플로우                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Day 1: 초기 인증                                       │
│    ├─ 로컬에서 claude /login 실행                       │
│    ├─ 로컬에서 gemini login 실행                        │
│    └─ Azure Files에 토큰 파일 업로드                    │
│                                                         │
│  Day 1~14: 정상 운영                                    │
│    ├─ Access Token: CLI가 자동 갱신                     │
│    └─ Refresh Token: 유효                               │
│                                                         │
│  Day 14: 헬스체크                                       │
│    ├─ 토큰 만료 임박 감지                               │
│    └─ 알림 발송 (Slack/Email)                          │
│                                                         │
│  Day 14~15: 재인증                                      │
│    ├─ 관리자 로컬에서 재인증                            │
│    ├─ Azure Files에 토큰 업데이트                       │
│    └─ (필요시) Container App 재시작                     │
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
- 로컬에서 Claude/Gemini CLI 인증 완료

### 4.2 Step 1: Azure 리소스 생성

```bash
# 변수 설정
RESOURCE_GROUP="llm-mcp-hub-rg"
LOCATION="koreacentral"
STORAGE_ACCOUNT="llmmcphubstorage"
CONTAINER_ENV="llm-mcp-hub-env"
CONTAINER_APP="llm-mcp-hub"
REDIS_NAME="llm-mcp-hub-redis"

# 리소스 그룹 생성
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Storage Account 생성
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

```bash
# Claude 인증 파일 업로드
az storage file upload \
  --share-name auth-files \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --source ~/.claude/.credentials.json \
  --path claude/auth.json

# Gemini 인증 파일 업로드
az storage file upload \
  --share-name auth-files \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --source ~/.gemini/oauth_creds.json \
  --path gemini/creds.json
```

### 4.4 Step 3: Container Apps 환경 생성

```bash
# Container Apps 환경 생성
az containerapp env create \
  --name $CONTAINER_ENV \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Storage 연결
az containerapp env storage set \
  --name $CONTAINER_ENV \
  --resource-group $RESOURCE_GROUP \
  --storage-name authstorage \
  --azure-file-account-name $STORAGE_ACCOUNT \
  --azure-file-account-key $STORAGE_KEY \
  --azure-file-share-name auth-files \
  --access-mode ReadWrite
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
      - name: redis-connection-string
        value: "{redis-connection-string}"
  template:
    containers:
      - name: llm-mcp-hub
        image: myregistry.azurecr.io/llm-mcp-hub:latest
        resources:
          cpu: 1.0
          memory: 2Gi
        env:
          - name: CLAUDE_AUTH_PATH
            value: /mnt/auth/claude/auth.json
          - name: GEMINI_AUTH_PATH
            value: /mnt/auth/gemini/creds.json
          - name: REDIS_URL
            secretRef: redis-connection-string
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
```

**배포 실행:**

```bash
az containerapp create \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --yaml container-app.yaml
```

### 4.6 Step 5: 배포 확인

```bash
# Container App URL 조회
az containerapp show \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv

# 헬스체크
curl https://<app-url>/health
```

---

## 5. 운영 가이드

### 5.1 토큰 갱신 스크립트

**refresh-tokens.sh:**

```bash
#!/bin/bash
# OAuth 토큰 갱신 스크립트

STORAGE_ACCOUNT="llmmcphubstorage"
RESOURCE_GROUP="llm-mcp-hub-rg"
CONTAINER_APP="llm-mcp-hub"

# Storage Key 조회
STORAGE_KEY=$(az storage account keys list \
  --account-name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query '[0].value' -o tsv)

echo "=== OAuth 토큰 갱신 시작 ==="

# 1. 로컬에서 재인증 (수동)
echo "1. Claude 재인증..."
claude /login

echo "2. Gemini 재인증..."
gemini login

# 2. Azure Files에 업로드
echo "3. Claude 토큰 업로드..."
az storage file upload \
  --share-name auth-files \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --source ~/.claude/.credentials.json \
  --path claude/auth.json \
  --overwrite

echo "4. Gemini 토큰 업로드..."
az storage file upload \
  --share-name auth-files \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --source ~/.gemini/oauth_creds.json \
  --path gemini/creds.json \
  --overwrite

# 3. Container App 재시작 (선택)
echo "5. Container App 재시작..."
az containerapp revision restart \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP

echo "=== 토큰 갱신 완료 ==="
```

### 5.2 헬스체크 모니터링

**토큰 상태 확인 API (구현 권장):**

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
  --action-group "ops-team-action-group"
```

---

## 6. 비용 예상

### 6.1 월간 비용 (예상)

| 서비스 | 사양 | 예상 비용 (USD) |
|--------|------|----------------|
| Azure Container Apps | 1 vCPU, 2GB RAM, 항상 실행 | $50-70 |
| Azure Files | Standard, 1GB | $0.06 |
| Azure Redis Cache | Basic C0 (250MB) | $16 |
| Azure Container Registry | Basic | $5 |
| 네트워크 (Egress) | ~10GB/월 | $1 |
| **총계** | | **~$72-92/월** |

### 6.2 비용 최적화 방안

| 방안 | 절감 효과 | 트레이드오프 |
|------|----------|-------------|
| 최소 레플리카 0 설정 | -30% | Cold start 지연 (수 초) |
| Spot Instance 사용 | -60% | 가용성 감소 |
| Redis 대신 인메모리 | -$16 | 세션 영속성 없음 |

---

## 7. 제약사항 및 주의점

### 7.1 기술적 제약

| 항목 | 제약 | 해결 방안 |
|------|------|----------|
| Azure Files SMB | Linux 컨테이너만 지원 | Linux 베이스 이미지 사용 |
| 볼륨 이름 | 특수문자(`.`) 사용 불가 | `auth-json` 형태로 명명 |
| Identity 기반 접근 | Azure Files 미지원 | Storage Key 사용 |
| Cold Start | 스케일 0→1 시 지연 | minReplicas: 1 설정 |

### 7.2 운영 제약

| 항목 | 제약 | 해결 방안 |
|------|------|----------|
| 토큰 자동 갱신 | 완전 자동화 불가 | 2주 주기 수동 갱신 + 알림 |
| OAuth 브라우저 인증 | 컨테이너 내 불가 | 로컬에서 인증 후 업로드 |
| Refresh Token 만료 | 예측 어려움 | 보수적 갱신 주기 (1~2주) |

---

## 8. 트러블슈팅

### 8.1 일반적인 문제

**문제: 토큰 만료로 401 에러 발생**

```bash
# 로그 확인
az containerapp logs show \
  --name $CONTAINER_APP \
  --resource-group $RESOURCE_GROUP

# 해결: 토큰 갱신 스크립트 실행
./refresh-tokens.sh
```

**문제: Azure Files 마운트 실패**

```bash
# Storage 연결 상태 확인
az containerapp env storage show \
  --name $CONTAINER_ENV \
  --resource-group $RESOURCE_GROUP \
  --storage-name authstorage

# 해결: Storage Key 재설정
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

### 8.2 디버깅 명령어

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
```

---

## 9. 참고 자료

- [Azure Container Apps 문서](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure Container Apps Storage Mounts](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts)
- [Azure Files Volume Mount Tutorial](https://learn.microsoft.com/en-us/azure/container-apps/storage-mounts-azure-files)
- [Azure Container Apps Secrets Management](https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets)
- [Claude Code Docker Docs](https://docs.docker.com/ai/sandboxes/claude-code/)
- [Gemini CLI Headless Mode](https://google-gemini.github.io/gemini-cli/docs/cli/headless.html)

---

## 10. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| 0.1 | 2026-01-08 | - | 초안 작성 |
