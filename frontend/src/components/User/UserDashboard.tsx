import React, { useState, useEffect } from 'react';
import { useApp, RequestDetail, ReqType } from '../../context/AppContext';
import { relativeTime } from '../../utils/format';
import { StatusBadge, TypeTag } from '../Common/Badges';
import { BottomSheet } from '../Common/BottomSheet';

interface UserDashboardProps {
  onSelectRequest: (id: string) => void;
  onNewRequest: () => void;
  flashId: string | null;
  clearFlashId: () => void;
}

export const UserDashboard: React.FC<UserDashboardProps> = ({
  onSelectRequest,
  onNewRequest,
  flashId,
  clearFlashId,
}) => {
  const { apiCall, showToast } = useApp();
  const [requests, setRequests] = useState<RequestDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<ReqType | ''>('');
  const [showClearHistorySheet, setShowClearHistorySheet] = useState(false);
  const [clearingHistory, setClearingHistory] = useState(false);

  const fetchRequests = async () => {
    try {
      setLoading(true);
      const data = await apiCall('GET', '/requests/me');
      setRequests(Array.isArray(data) ? data : data.requests || []);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleClearHistory = async () => {
    if (clearingHistory) return;
    setClearingHistory(true);
    try {
      await apiCall('POST', '/requests/archive');
      showToast('✓ History cleared');
      setShowClearHistorySheet(false);
      await fetchRequests();
    } catch {
      showToast('Failed to clear history');
    } finally {
      setClearingHistory(false);
    }
  };

  // Clear flashId after applying class
  useEffect(() => {
    if (flashId && requests.some((r) => r.id === flashId)) {
      const timer = setTimeout(() => {
        clearFlashId();
      }, 1600);
      return () => clearTimeout(timer);
    }
  }, [flashId, requests]);

  if (loading) {
    return (
      <div className="page pb-fab">
        <div className="skeleton skeleton-card"></div>
        <div className="skeleton skeleton-card"></div>
        <div className="skeleton skeleton-card"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page pb-fab">
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <h3>Could not load requests</h3>
          <p>Check your connection and try again.</p>
          <button className="btn-retry" onClick={fetchRequests}>↻ Retry</button>
        </div>
      </div>
    );
  }

  const filteredRequests = requests.filter((r) => {
    const matchesSearch =
      !searchQuery ||
      r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.description && r.description.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = !typeFilter || r.request_type === typeFilter;
    return matchesSearch && matchesType;
  });

  const pending = filteredRequests.filter((r) => r.status === 'pending');
  const history = filteredRequests.filter((r) => r.status !== 'pending');

  return (
    <div className="page pb-fab">
      {/* Search and Filters */}
      <div className="search-filter-row" style={{ marginBottom: '16px', display: 'flex', gap: '8px' }}>
        <input
          type="text"
          className="form-control"
          placeholder="Search title..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            margin: 0,
            padding: '9px 12px',
            fontSize: '13px',
            borderRadius: '10px',
            border: '1.5px solid var(--slate-200)',
          }}
        />
        <select
          className="form-control"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value as ReqType | '')}
          style={{
            margin: 0,
            width: '120px',
            padding: '9px 12px',
            fontSize: '13px',
            borderRadius: '10px',
            border: '1.5px solid var(--slate-200)',
            height: 'auto',
          }}
        >
          <option value="">All Types</option>
          <option value="room_booking">🏢 Room</option>
          <option value="vehicle_booking">🚗 Vehicle</option>
          <option value="maintenance">🔧 Maintenance</option>
          <option value="other">📋 Other</option>
        </select>
      </div>

      {/* List Container */}
      <div id="user-list-container">
        {filteredRequests.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🔍</div>
            <h3>No matching requests</h3>
            <p>Try adjusting your search or filter.</p>
          </div>
        ) : (
          <>
            {pending.length > 0 && (
              <>
                <div className="section-hd">
                  <h2>Active</h2>
                  <span className="count-chip">{pending.length}</span>
                </div>
                {pending.map((r) => (
                  <div
                    key={r.id}
                    className={`card clickable ${r.id === flashId ? 'flash' : ''}`}
                    data-status={r.status}
                    data-id={r.id}
                    onClick={() => onSelectRequest(r.id)}
                  >
                    <div className="card-row">
                      <span className="card-title">{r.title}</span>
                      <span className="card-arrow">›</span>
                    </div>
                    <div className="card-meta">
                      <StatusBadge status={r.status} />
                      <TypeTag type={r.request_type} />
                      <span className="card-date">{relativeTime(r.created_at)}</span>
                    </div>
                    {r.description && <p className="card-desc">{r.description}</p>}
                  </div>
                ))}
              </>
            )}

            {history.length > 0 && (
              <>
                <div className="section-hd" style={{ marginTop: pending.length > 0 ? 20 : 0 }}>
                  <h2>History</h2>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => setShowClearHistorySheet(true)}
                    style={{ margin: 0, padding: '6px 12px', fontSize: '11px', width: 'auto' }}
                  >
                    Clear History
                  </button>
                </div>
                {history.map((r) => (
                  <div
                    key={r.id}
                    className="card clickable"
                    data-status={r.status}
                    data-id={r.id}
                    onClick={() => onSelectRequest(r.id)}
                  >
                    <div className="card-row">
                      <span className="card-title">{r.title}</span>
                      <span className="card-arrow">›</span>
                    </div>
                    <div className="card-meta">
                      <StatusBadge status={r.status} />
                      <TypeTag type={r.request_type} />
                      <span className="card-date">{relativeTime(r.created_at)}</span>
                    </div>
                    {r.description && <p className="card-desc">{r.description}</p>}
                  </div>
                ))}
              </>
            )}
          </>
        )}
      </div>

      {/* Floating Action Button */}
      <button className="fab" onClick={onNewRequest}>
        <span>＋</span> New Request
      </button>

      {/* Clear History Confirmation */}
      <BottomSheet
        isOpen={showClearHistorySheet}
        onClose={() => setShowClearHistorySheet(false)}
        title="Clear History"
      >
        <div className="sheet-desc">
          Are you sure you want to clear your completed request history? This will hide all done and cancelled requests.
        </div>
        <button className="btn btn-danger" onClick={handleClearHistory} disabled={clearingHistory}>
          {clearingHistory ? 'Clearing...' : 'Clear It'}
        </button>
        <button
          className="btn btn-ghost"
          onClick={() => setShowClearHistorySheet(false)}
          style={{ marginTop: '8px' }}
        >
          Keep It
        </button>
      </BottomSheet>
    </div>
  );
};
