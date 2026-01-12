export interface ProviderInfo {
  name: string;
  models: string[];
  default_model: string;
}

export interface ProviderDetailResponse {
  name: string;
  status: string;
  models: string[];
  default_model: string;
  auth_method?: string;
}
