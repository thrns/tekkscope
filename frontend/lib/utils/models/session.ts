export interface UserData {
    uuid: string;
    email: string;
    onboarding?: boolean;
    name?: string;
    avatarURL?: string;
    loggedin_at?: string;
    notifications?: any[]; // Replace with specific Notification type if available
    [key: string]: any; // Allow other properties for now
}

export interface SessionData {
    uuid: string;
    email: string;
    onboarding?: boolean;
    name?: string;
    avatarURL?: string;
    loggedin_at?: string;
}
