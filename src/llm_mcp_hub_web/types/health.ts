export type HealthStatus = "healthy" | "degraded" | "unhealthy";

export interface HealthResponse {
  status: HealthStatus;
  version: string;
  timestamp: string;
}

export interface ComponentHealth {
  status: "healthy" | "unhealthy";
  latency_ms?: number;
  error?: string;
  supported_models?: string[];
  last_success?: string;
}

export interface DetailedHealthResponse {
  status: HealthStatus;
  version: string;
  components: Record<string, ComponentHealth>;
}

export interface TokenStatus {
  valid: boolean;
  status?: string;
  error?: string;
  expires_at?: string;
  days_remaining?: number;
}

export interface TokenHealthResponse {
  claude?: TokenStatus;
  gemini?: TokenStatus;
}
