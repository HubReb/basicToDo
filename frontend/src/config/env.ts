/**
 * Environment configuration module
 * Centralizes all environment-specific configuration
 */

interface Config {
  apiBaseUrl: string;
  environment: string;
}

const getConfig = (): Config => {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

  if (!apiBaseUrl) {
    throw new Error(
      'VITE_API_BASE_URL is not defined. Please check your .env file.'
    );
  }

  return {
    apiBaseUrl,
    environment: import.meta.env.MODE || 'development',
  };
};

export const config = getConfig();
