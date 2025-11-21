import { UserData } from '@/lib/utils/models/session';

export interface AuthContextType {
    user: UserData | null;
    setUser: (user: UserData | null) => void;
    notifications: any[];
    setNotifications: (notifications: any[]) => void;
}
