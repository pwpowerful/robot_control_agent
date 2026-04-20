import { request } from "../http/client";

export type HealthResponse = {
  status: string;
  version?: string;
};

export function getHealth() {
  return request<HealthResponse>("/health");
}
