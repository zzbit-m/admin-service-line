import React, { createContext, useContext, useState, useEffect } from 'react';
import liff from '@line/liff';

export interface User {
  sub: string;
  role: 'user' | 'admin';
  full_name?: string;
}

export type ReqType = 'room_booking' | 'vehicle_booking' | 'maintenance' | 'other';
export type PriorityType = 'low' | 'normal' | 'urgent';
export type StatusType = 'pending' | 'approved' | 'rejected' | 'cancelled';

export interface RequestDetail {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  request_type: ReqType;
  resource_id: string | null;
  priority: PriorityType;
  status: StatusType;
  admin_note: string | null;
  created_at: string;
  updated_at: string;
  start_time: string | null;
  end_time: string | null;
  full_name?: string;
  conflicts?: Array<{
    id: string;
    full_name?: string;
    start_time: string;
    end_time: string;
  }>;
}

export interface Resource {
  id: string;
  name: string;
  type: 'room' | 'vehicle' | 'equipment' | 'other';
  description?: string;
  is_active: boolean;
  capacity?: number;
  location?: string;
  image_url?: string;
}

export interface Comment {
  id: string;
  request_id: string;
  user_id: string;
  content: string;
  created_at: string;
  full_name?: string;
}

interface AppContextType {
  accessToken: string | null;
  userRole: 'user' | 'admin' | null;
  viewingRole: 'user' | 'admin' | null;
  userName: string | null;
  currentUserId: string | null;
  isDev: boolean;
  loading: boolean;
  loadingMessage: string;
  toast: string | null;
  showToast: (msg: string) => void;
  toggleDarkMode: () => void;
  isDarkMode: boolean;
  switchRole: () => Promise<void>;
  apiCall: (method: string, path: string, body?: any) => Promise<any>;
  uploadAttachment: (requestId: string, file: File) => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

const LIFF_ID = '2010375597-spCTVMCi';
const DEV_ACCOUNTS = {
  user: { email: 'user@test.com', password: 'testpass' },
  admin: { email: 'admin@test.com', password: 'testpass' },
};

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<'user' | 'admin' | null>(null);
  const [viewingRole, setViewingRole] = useState<'user' | 'admin' | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [isDev, setIsDev] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState('Signing you in…');
  const [toast, setToast] = useState<string | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Decode JWT payload
  const decodeToken = (token: string) => {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch {
      return {};
    }
  };

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => {
      setToast((prev) => (prev === msg ? null : prev));
    }, 2800);
  };

  const toggleDarkMode = () => {
    const nextDark = !isDarkMode;
    setIsDarkMode(nextDark);
    if (nextDark) {
      document.body.classList.add('dark-mode');
      localStorage.setItem('theme', 'dark');
    } else {
      document.body.classList.remove('dark-mode');
      localStorage.setItem('theme', 'light');
    }
  };

  // Generic API Helper
  const apiCall = async (method: string, path: string, body?: any) => {
    const headers: Record<string, string> = {};
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }
    const opts: RequestInit = { method, headers };
    if (body !== undefined) {
      headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP error! Status: ${res.status}`);
    }
    return res.json();
  };

  const uploadAttachment = async (requestId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const headers: Record<string, string> = {};
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }
    const res = await fetch(`/requests/${requestId}/attachments`, {
      method: 'POST',
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Upload failed! Status: ${res.status}`);
    }
  };

  // Dev Login
  const devLogin = async (role: 'user' | 'admin', isInitial = false) => {
    setLoading(true);
    setLoadingMessage(`Logging in as ${role} (Dev Mode)…`);
    try {
      const creds = DEV_ACCOUNTS[role];
      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(creds),
      });
      if (!res.ok) throw new Error('Dev login API call failed');
      const data = await res.json();
      const token = data.access_token;
      setAccessToken(token);
      const payload = decodeToken(token);
      const actualRole = payload.role || role;
      setUserRole(actualRole);
      setViewingRole(actualRole);
      setUserName(payload.full_name || payload.sub || role);
      setCurrentUserId(payload.sub || null);
      if (!isInitial) {
        showToast(`⇄ Switched to ${role} view`);
      }
    } catch (err: any) {
      showToast(`Dev login failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Switch Role
  const switchRole = async () => {
    if (isDev) {
      const targetRole = viewingRole === 'user' ? 'admin' : 'user';
      await devLogin(targetRole);
    } else {
      if (userRole === 'admin') {
        const targetView = viewingRole === 'user' ? 'admin' : 'user';
        setViewingRole(targetView);
        showToast(`⇄ Switched to ${targetView} view`);
      }
    }
  };

  // Initialize Auth & Theme
  useEffect(() => {
    // Theme
    const storedTheme = localStorage.getItem('theme');
    if (storedTheme === 'dark') {
      setIsDarkMode(true);
      document.body.classList.add('dark-mode');
    }

    const searchParams = new URLSearchParams(window.location.search);
    const devParam = searchParams.get('dev') === '1';
    setIsDev(devParam);

    const initAuth = async () => {
      if (devParam) {
        // Dev Auth
        await devLogin('user', true);
      } else {
        // LIFF Auth
        try {
          await liff.init({ liffId: LIFF_ID, withLoginOnExternalBrowser: true });
          if (!liff.isLoggedIn()) {
            liff.login();
            return;
          }
          const lineToken = liff.getAccessToken();
          if (!lineToken) throw new Error('No LINE access token');

          const res = await fetch('/auth/line', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ access_token: lineToken }),
          });
          if (!res.ok) throw new Error('Backend authentication failed');
          const data = await res.json();
          const token = data.access_token;
          setAccessToken(token);
          const payload = decodeToken(token);
          const role = payload.role || 'user';
          setUserRole(role);
          setViewingRole(role);
          setUserName(payload.full_name || payload.sub || null);
          setCurrentUserId(payload.sub || null);
        } catch (err: any) {
          showToast('LINE sign in failed, please try again.');
        } finally {
          setLoading(false);
        }
      }
    };

    initAuth();
  }, []);

  return (
    <AppContext.Provider
      value={{
        accessToken,
        userRole,
        viewingRole,
        userName,
        currentUserId,
        isDev,
        loading,
        loadingMessage,
        toast,
        showToast,
        toggleDarkMode,
        isDarkMode,
        switchRole,
        apiCall,
        uploadAttachment,
      }}
    >
      {children}
      {toast && <div id="toast" className="show">{toast}</div>}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within an AppProvider');
  return context;
};
