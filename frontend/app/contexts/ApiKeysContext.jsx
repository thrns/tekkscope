//================ IMPORTS ================//
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { toast } from 'sonner';

//================ CONTEXT CREATION ================//
const ApiKeysContext = createContext();

//================ CUSTOM HOOK ================//
export const useApiKeys = () => useContext(ApiKeysContext);

//================ PROVIDER COMPONENT ================//
export const ApiKeysProvider = ({ children }) => {
  //================ STATE & HOOKS ================//
  const { user } = useAuth();
  const [apiKeys, setApiKeys] = useState([]);

  //================ HANDLERS ================//
  const fetchApiKeys = useCallback(async () => {
    try {
      const response = await fetch('/api/supabase/api-keys', {
        method: 'GET',
      });
      if (!response.ok) throw new Error('Failed to fetch API keys');

      const { data } = await response.json();
      setApiKeys(data || []);
    } catch (error) {
      console.error('Error fetching API keys:', error);
      toast.error('Failed to fetch API keys');
    }
  }, []);

  const generateApiKey = async (name) => {
    try {
      const response = await fetch('/api/supabase/api-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate API key');
      }

      const data = await response.json();
      await fetchApiKeys();
      return data.api_key;
    } catch (error) {
      console.error('Error generating API key:', error);
      toast.error(error.message);
    }
  };

  const deleteApiKey = async (apiKeyId) => {
    try {
      const response = await fetch(`/api/supabase/api-keys?id=${apiKeyId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete API key');
      }

      fetchApiKeys();
      toast.success('API key deleted');
    } catch (error) {
      console.error('Error deleting API key:', error);
      toast.error('Failed to delete API key');
    }
  };

  //================ EFFECTS ================//
  useEffect(() => {
    const loadApiKeys = async () => {
      if (user?.uuid) {
        await fetchApiKeys();
      }
    };
    loadApiKeys();
  }, [user, fetchApiKeys]);

  const value = {
    apiKeys,
    fetchApiKeys,
    generateApiKey,
    deleteApiKey,
  };

  //================ RENDER ================//
  return <ApiKeysContext.Provider value={value}>{children}</ApiKeysContext.Provider>;
};
