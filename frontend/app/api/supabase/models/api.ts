export interface ApiKeyRequest {
    userId: string;
}

export interface CreditsRequest {
    userId: string;
}

export interface UsageRequest {
    userId: string;
    apiKeyId?: string;
    from?: string;
    to?: string;
}
