import React, { useState } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { UserDashboard } from './components/User/UserDashboard';
import { NewRequestForm } from './components/User/NewRequestForm';
import { RequestDetailView } from './components/Detail/RequestDetailView';
import { AdminDashboard } from './components/Admin/AdminDashboard';
import { AdminDetailView } from './components/Admin/AdminDetailView';

type ViewState = 'dashboard' | 'new_request' | 'detail';

const AppContent: React.FC = () => {
  const {
    userRole,
    viewingRole,
    isDev,
    loading,
    loadingMessage,
    isDarkMode,
    toggleDarkMode,
    switchRole,
  } = useApp();

  const [view, setView] = useState<ViewState>('dashboard');
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);
  const [flashId, setFlashId] = useState<string | null>(null);
  const [adminTab, setAdminTab] = useState<'pending' | 'approved' | 'all' | 'resources' | 'reports'>('pending');

  const handleRefresh = () => {
    // Basic reload simulation
    window.location.reload();
  };

  const handleBackToDashboard = () => {
    setView('dashboard');
    setSelectedRequestId(null);
  };

  const handleNewRequestSuccess = (reqId: string) => {
    setFlashId(reqId);
    setView('dashboard');
  };

  if (loading) {
    return (
      <div className="page">
        <div className="loader">
          <div className="spinner"></div>
          <p className="loader-text">{loadingMessage}</p>
        </div>
      </div>
    );
  }

  // Header render helpers
  const canSwitchRole = isDev || userRole === 'admin';

  return (
    <>
      <header className="header" id="header">
        <div className="header-inner">
          <div className="header-title" id="header-title">
            <span>⚡</span>
            <span>Service Portal</span>
            <span className="role-chip">{viewingRole === 'admin' ? 'Admin' : 'User'}</span>
            {isDev && (
              <span className="role-chip" style={{ background: 'rgba(255,200,0,.35)', color: '#fff' }}>
                DEV
              </span>
            )}
          </div>
          <div className="header-actions">
            <button className="icon-btn" onClick={toggleDarkMode} title="Toggle theme">
              {isDarkMode ? '☀️' : '🌙'}
            </button>
            {canSwitchRole && (
              <button className="icon-btn" onClick={switchRole} title="Switch view">
                ⇄
              </button>
            )}
            {view === 'dashboard' && (
              <button className="icon-btn" onClick={handleRefresh} title="Refresh">
                ↻
              </button>
            )}
          </div>
        </div>
      </header>

      <div id="app" className={view === 'dashboard' && viewingRole === 'user' ? 'page pb-fab' : 'page'}>
        {viewingRole === 'admin' ? (
          // Admin Routing
          view === 'detail' && selectedRequestId ? (
            <AdminDetailView requestId={selectedRequestId} onBack={handleBackToDashboard} />
          ) : (
            <AdminDashboard
              initialTab={adminTab}
              onTabChange={setAdminTab}
              onSelectRequest={(id) => {
                setSelectedRequestId(id);
                setView('detail');
              }}
            />
          )
        ) : (
          // User Routing
          view === 'new_request' ? (
            <NewRequestForm onBack={handleBackToDashboard} onSuccess={handleNewRequestSuccess} />
          ) : view === 'detail' && selectedRequestId ? (
            <RequestDetailView requestId={selectedRequestId} onBack={handleBackToDashboard} />
          ) : (
            <UserDashboard
              onSelectRequest={(id) => {
                setSelectedRequestId(id);
                setView('detail');
              }}
              onNewRequest={() => setView('new_request')}
              flashId={flashId}
              clearFlashId={() => setFlashId(null)}
            />
          )
        )}
      </div>
    </>
  );
};

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;
