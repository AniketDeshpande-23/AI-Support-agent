export type Priority = 'Critical' | 'High' | 'Medium' | 'Low';
export type HealthStatus = 'healthy' | 'degraded' | 'down';

export interface AnalyzeRequest {
  text: string;
  customer_id?: string;
  thread_id?: string;
}

export interface AnalyzeResult {
  ticket_id: number;
  category: string;
  priority: Priority;
  confidence: number; // 0-100
  grounded: boolean;
  route_to: string;
  reply_draft: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  provider: string;
  model: string;
  auth: boolean;
}

export interface Ticket {
  id: string | number;
  timestamp: string;
  ticket_text: string;
  category: string;
  priority: Priority;
  confidence: number;
  grounded: boolean;
  route_to: string;
  reply: string;
  customer_id?: string;
  thread_id?: string;
}

export interface Metrics {
  total: number;
  avg_confidence: number;
  human_review_count: number;
  grounding_rate: number;
  by_category: Record<string, number>;
  by_priority: Record<string, number>;
}

export interface FeedbackRequest {
  approved: boolean;
  corrected_category?: string | null;
  corrected_reply?: string | null;
}

export type ApiErrorKind = 'validation' | 'rate_limit' | 'server' | 'network';

export class ApiError extends Error {
  kind: ApiErrorKind;
  status: number;
  retryAfter?: number;

  constructor(kind: ApiErrorKind, status: number, message: string, retryAfter?: number) {
    super(message);
    this.name = 'ApiError';
    this.kind = kind;
    this.status = status;
    this.retryAfter = retryAfter;
  }
}

export type ViewKey = 'analyze' | 'dashboard' | 'feed' | 'review';
