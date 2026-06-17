import React, { useState } from 'react';
import { AdminRequestsTab } from './AdminRequestsTab';
import { AdminResourcesTab } from './AdminResourcesTab';
import { AdminReportsTab } from './AdminReportsTab';

type AdminTab = 'pending' | 'approved' | 'all' | 'resources' | 'reports';

interface AdminDashboardProps {
  onSelectRequest: (id: string) => void;
  initialTab?: AdminTab;
  onTabChange?: (tab: AdminTab) => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ onSelectRequest, initialTab = 'pending', onTabChange }) => {
  const [activeTab, setActiveTab] = useState<AdminTab>(initialTab);
  const [pendingCount, setPendingCount] = useState<number | null>(null);

  const handleTabClick = (tab: AdminTab) => {
    setActiveTab(tab);
    if (onTabChange) {
      onTabChange(tab);
    }
  };

  const renderActiveTabContent = () => {
    switch (activeTab) {
      case 'pending':
      case 'approved':
      case 'all':
        return (
          <AdminRequestsTab
            filter={activeTab}
            onSelectRequest={onSelectRequest}
            updatePendingCount={(count) => setPendingCount(count)}
          />
        );
      case 'resources':
        return <AdminResourcesTab />;
      case 'reports':
        return <AdminReportsTab />;
      default:
        return null;
    }
  };

  return (
    <div className="page">
      {/* Header Tabs */}
      <div
        className="tabs"
        id="admin-tabs"
        style={{
          overflowX: 'auto',
          whiteSpace: 'nowrap',
          WebkitOverflowScrolling: 'touch',
          marginBottom: '12px',
          gap: '8px',
          display: 'flex',
        }}
      >
        <div
          className={`tab ${activeTab === 'pending' ? 'active' : ''}`}
          onClick={() => handleTabClick('pending')}
          style={{ flex: '0 0 auto', padding: '10px 16px' }}
        >
          ⏳ Pending {pendingCount !== null && pendingCount > 0 ? `(${pendingCount})` : ''}
        </div>
        <div
          className={`tab ${activeTab === 'approved' ? 'active' : ''}`}
          onClick={() => handleTabClick('approved')}
          style={{ flex: '0 0 auto', padding: '10px 16px' }}
        >
          ✅ Done
        </div>
        <div
          className={`tab ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => handleTabClick('all')}
          style={{ flex: '0 0 auto', padding: '10px 16px' }}
        >
          All
        </div>
        <div
          className={`tab ${activeTab === 'resources' ? 'active' : ''}`}
          onClick={() => handleTabClick('resources')}
          style={{ flex: '0 0 auto', padding: '10px 16px' }}
        >
          🏢 Resources
        </div>
        <div
          className={`tab ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => handleTabClick('reports')}
          style={{ flex: '0 0 auto', padding: '10px 16px' }}
        >
          📊 Reports
        </div>
      </div>

      {/* Tab Content */}
      {renderActiveTabContent()}
    </div>
  );
};
