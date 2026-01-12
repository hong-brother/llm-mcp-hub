# LLM MCP Hub Admin Dashboard - Frontend Architecture

## 1. Overview

F5(API 통계)를 제외한 관리자 대시보드 프론트엔드 아키텍처.

### 구현 범위

| 기능 | 설명 | 우선순위 |
|------|------|----------|
| F1 | 메인 대시보드 (종합 상태) | P0 |
| F2 | LLM 프로바이더 관리 | P0 |
| F3 | OAuth 토큰 상태 모니터링 | P1 |
| F4 | 활성 세션 관리 | P0 |

---

## 2. Tech Stack

| 영역 | 기술 | 버전 | 선택 이유 |
|------|------|------|-----------|
| Framework | Next.js | 15.x | App Router, Server Components |
| Language | TypeScript | 5.x | 타입 안정성 |
| State | TanStack Query | 5.x | 서버 상태 관리, 캐싱, 폴링 |
| UI | Shadcn/ui | latest | Radix 기반, 커스터마이징 용이 |
| Styling | Tailwind CSS | 3.x | Utility-first |
| HTTP | ky | 1.x | Fetch 래퍼, 간결한 API |
| Icons | Lucide React | latest | 일관된 아이콘셋 |

---

## 3. Project Structure

```
src/llm_mcp_hub_web/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # Root layout + Providers
│   ├── page.tsx                  # F1: 메인 대시보드
│   ├── providers/
│   │   └── page.tsx              # F2: 프로바이더 관리
│   ├── tokens/
│   │   └── page.tsx              # F3: 토큰 모니터링
│   └── sessions/
│       ├── page.tsx              # F4: 세션 목록
│       └── [id]/
│           └── page.tsx          # F4: 세션 상세
│
├── components/
│   ├── ui/                       # Shadcn 컴포넌트 (자동 생성)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── table.tsx
│   │   ├── badge.tsx
│   │   ├── alert.tsx
│   │   └── ...
│   │
│   ├── layout/                   # 레이아웃
│   │   ├── app-sidebar.tsx       # 좌측 네비게이션
│   │   ├── app-header.tsx        # 상단 헤더
│   │   └── page-header.tsx       # 페이지 타이틀
│   │
│   ├── dashboard/                # F1 컴포넌트
│   │   ├── system-status.tsx     # 전체 상태 배지
│   │   ├── component-cards.tsx   # 서비스별 상태 카드
│   │   ├── provider-summary.tsx  # 프로바이더 요약
│   │   └── token-alerts.tsx      # 토큰 만료 경고
│   │
│   ├── providers/                # F2 컴포넌트
│   │   ├── provider-card.tsx     # 프로바이더 카드
│   │   └── provider-grid.tsx     # 카드 그리드
│   │
│   ├── tokens/                   # F3 컴포넌트
│   │   ├── token-card.tsx        # 토큰 상태 카드
│   │   └── token-status-badge.tsx
│   │
│   └── sessions/                 # F4 컴포넌트
│       ├── session-table.tsx     # 세션 목록 테이블
│       ├── session-detail.tsx    # 세션 상세 정보
│       ├── message-list.tsx      # 대화 내역
│       └── delete-session-dialog.tsx
│
├── lib/
│   ├── api/                      # API 클라이언트
│   │   ├── client.ts             # ky 인스턴스
│   │   ├── health.ts             # /health API
│   │   ├── providers.ts          # /v1/providers API
│   │   └── sessions.ts           # /v1/sessions API
│   │
│   ├── hooks/                    # React Query 훅
│   │   ├── use-health.ts
│   │   ├── use-providers.ts
│   │   └── use-sessions.ts
│   │
│   └── utils.ts                  # 유틸리티 함수
│
├── types/                        # TypeScript 타입
│   ├── health.ts
│   ├── provider.ts
│   └── session.ts
│
├── config/
│   └── api.ts                    # API 설정 (baseURL 등)
│
├── styles/
│   └── globals.css               # Tailwind + 전역 스타일
│
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
└── components.json               # Shadcn 설정
```

---

## 4. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Components                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Dashboard    │  │ Providers    │  │ Sessions             │   │
│  │ Components   │  │ Components   │  │ Components           │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
└─────────┼─────────────────┼──────────────────────┼──────────────┘
          │                 │                      │
          ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Custom Hooks Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ useHealth()  │  │useProviders()│  │ useSessions()        │   │
│  │ useTokens()  │  │useProvider() │  │ useSession()         │   │
│  │              │  │              │  │ useDeleteSession()   │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
└─────────┼─────────────────┼──────────────────────┼──────────────┘
          │                 │                      │
          ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     TanStack Query                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ QueryClient                                                 │ │
│  │ - Caching (staleTime: 30s)                                 │ │
│  │ - Background Refetch                                        │ │
│  │ - Polling (refetchInterval: 10s for health)                │ │
│  │ - Optimistic Updates (session delete)                      │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API Client (ky)                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ - Base URL: process.env.NEXT_PUBLIC_API_URL                │ │
│  │ - Error Handling                                            │ │
│  │ - Request/Response Interceptors                            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LLM MCP Hub Backend                            │
│  ┌───────────┐  ┌────────────┐  ┌─────────────────────────────┐ │
│  │ /health/* │  │/v1/providers│  │ /v1/sessions/*             │ │
│  └───────────┘  └────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. API Endpoints Mapping

### F1: 메인 대시보드

| Hook | API | Polling | 용도 |
|------|-----|---------|------|
| `useHealth()` | `GET /health` | 10s | 기본 상태 |
| `useDetailedHealth()` | `GET /health/detailed` | 10s | 컴포넌트 상태 |
| `useTokenHealth()` | `GET /health/tokens` | 60s | 토큰 경고 |

### F2: 프로바이더 관리

| Hook | API | Polling | 용도 |
|------|-----|---------|------|
| `useProviders()` | `GET /v1/providers` | - | 목록 조회 |
| `useProvider(name)` | `GET /v1/providers/{name}` | - | 상세 조회 |
| `useProviderModels(name)` | `GET /v1/providers/{name}/models` | - | 모델 목록 |

### F3: 토큰 모니터링

| Hook | API | Polling | 용도 |
|------|-----|---------|------|
| `useTokenHealth()` | `GET /health/tokens` | 60s | 토큰 상태 |

### F4: 세션 관리

| Hook | API | Polling | 용도 |
|------|-----|---------|------|
| `useSessions()` | `GET /v1/sessions` | 30s | 목록 조회 |
| `useSession(id)` | `GET /v1/sessions/{id}` | - | 상세 조회 |
| `useDeleteSession()` | `DELETE /v1/sessions/{id}` | - | 삭제 |

---

## 6. Component Specifications

### 6.1 Layout Components

#### AppSidebar
```tsx
// 좌측 네비게이션
const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Providers', href: '/providers', icon: Server },
  { name: 'Tokens', href: '/tokens', icon: Key },
  { name: 'Sessions', href: '/sessions', icon: MessageSquare },
];
```

### 6.2 Dashboard Components (F1)

#### SystemStatus
- 전체 상태 배지 (Healthy/Degraded/Unhealthy)
- 색상: 초록/노랑/빨강

#### ComponentCards
- Redis, Claude, Gemini 상태를 개별 카드로 표시
- 각 카드: 상태 아이콘, 이름, latency, 에러 메시지

#### TokenAlerts
- 만료 14일 이내: 경고 배너 표시
- 만료됨: 에러 배너 표시

### 6.3 Provider Components (F2)

#### ProviderCard
```tsx
interface ProviderCardProps {
  name: string;
  status: 'available' | 'unavailable';
  models: string[];
  defaultModel: string;
}
```

### 6.4 Session Components (F4)

#### SessionTable
| Column | 설명 |
|--------|------|
| Session ID | 클릭 시 상세 페이지 이동 |
| Provider | Claude/Gemini 배지 |
| Created At | 상대 시간 (예: 5분 전) |
| Last Activity | 상대 시간 |
| Messages | 메시지 수 |
| Actions | 삭제 버튼 |

#### DeleteSessionDialog
- 확인 다이얼로그
- 삭제 시 Optimistic Update

---

## 7. State Management Strategy

### TanStack Query 설정

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,      // 30초
      gcTime: 5 * 60 * 1000,     // 5분
      retry: 1,
      refetchOnWindowFocus: true,
    },
  },
});
```

### 폴링 전략

| 데이터 | Interval | 이유 |
|--------|----------|------|
| Health | 10초 | 실시간 상태 모니터링 |
| Tokens | 60초 | 변경 빈도 낮음 |
| Sessions | 30초 | 중간 빈도 업데이트 |

---

## 8. Error Handling

### API 에러 처리

```typescript
// lib/api/client.ts
const api = ky.create({
  prefixUrl: process.env.NEXT_PUBLIC_API_URL,
  hooks: {
    afterResponse: [
      async (request, options, response) => {
        if (!response.ok) {
          const error = await response.json();
          throw new ApiError(error.error.code, error.error.message);
        }
      },
    ],
  },
});
```

### UI 에러 표시

- Toast: 일시적 에러 (네트워크 등)
- Inline Alert: API 응답 에러
- Error Boundary: 예상치 못한 에러

---

## 9. Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 10. File Naming Conventions

| 유형 | 규칙 | 예시 |
|------|------|------|
| Component | kebab-case | `provider-card.tsx` |
| Hook | camelCase with use- | `use-providers.ts` |
| Type | PascalCase | `Provider`, `Session` |
| API | kebab-case | `health.ts`, `sessions.ts` |

---

## 11. Development Workflow

### 초기 설정

```bash
cd src/llm_mcp_hub_web

# Next.js 프로젝트 생성
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*"

# Shadcn 초기화
npx shadcn@latest init

# Shadcn 컴포넌트 추가
npx shadcn@latest add button card table badge alert dialog toast

# 추가 의존성
npm install ky @tanstack/react-query lucide-react
```

### 개발 서버

```bash
# 프론트엔드 (3000)
npm run dev

# 백엔드 (8000) - 별도 터미널
cd ../..
uv run uvicorn llm_mcp_hub.main:app --reload
```

---

## 12. Implementation Phases

### Phase 1: Foundation
- [ ] Next.js 프로젝트 초기화
- [ ] Shadcn/ui 설정
- [ ] Layout 컴포넌트 (Sidebar, Header)
- [ ] API 클라이언트 설정

### Phase 2: F1 메인 대시보드
- [ ] Health API 연동
- [ ] SystemStatus 컴포넌트
- [ ] ComponentCards 컴포넌트
- [ ] TokenAlerts 컴포넌트

### Phase 3: F2 프로바이더 관리
- [ ] Providers API 연동
- [ ] ProviderCard 컴포넌트
- [ ] ProviderGrid 레이아웃

### Phase 4: F3 토큰 모니터링
- [ ] TokenCard 컴포넌트
- [ ] 상태별 색상 구분

### Phase 5: F4 세션 관리
- [ ] Sessions API 연동 (백엔드 구현 필요)
- [ ] SessionTable 컴포넌트
- [ ] SessionDetail 페이지
- [ ] DeleteSessionDialog
