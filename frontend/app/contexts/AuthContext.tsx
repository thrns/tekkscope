'use client';
//================ IMPORTS ================//
import { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { supabase } from '@/Clients/supabase/client';
import Cookies from 'js-cookie';
import isEqual from 'lodash/isEqual';
import {
  getUserData,
  storeUserData,
} from '@/lib/utils/sessionUtils';
import { AuthContextType } from './models/auth';
import { UserData } from '@/lib/utils/models/session';

//================ CONTEXT CREATION ================//
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

//================ PROVIDER COMPONENT ================//
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  //================ STATE & HOOKS ================//
  const [user, setUser] = useState<UserData | null>(() => {
    return getUserData(Cookies) || null;
  });

  const [notifications, setNotifications] = useState<any[]>(user?.notifications || []);

  //================ EFFECTS ================//
  // User Initialization
  useEffect(() => {
    const getUser = () => {
      if (user) return;

      const userData = getUserData(Cookies);
      if (userData) {
        setUser(userData);
      }
    };

    getUser();
  }, []);

  // User Synchronization
  useEffect(() => {
    const syncUser = async () => {
      const {
        data: { user: authUser },
      } = await supabase.auth.getUser();

      if (authUser && authUser?.email) {
        // Fetch user data from Supabase (read-only here is fine if RLS allows)
        const { data: userData, error } = await supabase
          .from('user_data')
          .select('*')
          .eq('email', authUser.email)
          .single();

        if (error) {
          console.error('Error fetching user data for sync:', error);
          return;
        }

        // Check if we need to sync the UUID
        if (userData?.uuid != authUser?.id) {
          try {
            // Call the new secure API endpoint
            const response = await fetch('/api/supabase/sync-user', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                email: authUser.email,
                authId: authUser.id,
              }),
            });

            if (!response.ok) {
              const errorData = await response.json();
              console.error('Error syncing user via API:', errorData.error);
            }
          } catch (apiError) {
            console.error('Network error syncing user:', apiError);
          }
        }

        const inUserSync = await isEqual(userData, user);

        if (inUserSync) {
          console.log('User in sync, Good to go');
          return;
        }

        console.log('User not in sync, syncing user');

        // Use the new hybrid storage approach
        storeUserData(userData, Cookies);
        setUser(userData);
      }
    };

    // Only sync if we have a user email
    if (user?.email) {
      syncUser();
    }
  }, [user?.email]);

  //================ RENDER ================//
  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        notifications,
        setNotifications,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

//================ CUSTOM HOOK ================//
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
