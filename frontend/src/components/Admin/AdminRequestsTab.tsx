import React, { useState, useEffect } from 'react';
import { useApp, RequestDetail, ReqType, StatusType } from '../../context/AppContext';
import { relativeTime, shortId } from '../../utils/format';
import { StatusBadge, TypeTag, PriorityBadge } from '../Common/Badges';

interface AdminRequestsTabProps {
  filter: 'pending' | 'approved' | 'all';
  onSelectRequest: (id: string) => void;
  updatePendingCount: (count: number) => void;
}

export const AdminRequestsTab: React.FC<AdminRequestsTabProps> = ({
  filter,
  onSelectRequest,
  updatePendingCount,
}) => {
  const { apiCall, accessToken, showToast } = useApp();
  const [requests, setRequests] = useState<RequestDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Filters & Sorting
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<ReqType | ''>('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState(filter === 'pending' ? 'asc' : 'desc');

  const fetchRequests = async () => {
    try {
      setLoading(true);
      const status = filter !== 'all' ? filter : '';
      let q = `?sort_by=${sortBy}&sort_order=${sortOrder}&limit=100`;
      if (status) q += `&status=${status}`;
      if (startDate) q += `&start_date=${startDate}`;
      if (endDate) q += `&end_date=${endDate}`;

      const data = await apiCall('GET', `/admin/requests${q}`);
      const list = Array.isArray(data) ? data : data.requests || [];
      setRequests(list);
      setError(false);

      // Trigger pending count badge update
      if (filter === 'pending') {
        updatePendingCount(list.length);
      } else {
        // Fetch pending count separately if current tab is not pending
        try {
          const pData = await apiCall('GET', '/admin/requests?status=pending&limit=100');
          const pList = Array.isArray(pData) ? pData : pData.requests || [];
          updatePendingCount(pList.length);
        } catch {
          // silent
        }
      }
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [filter, startDate, endDate, sortBy, sortOrder]);

  const handleExportCsv = async () => {
    try {
      const status = filter !== 'all' ? filter : '';
      let q = `?sort_by=${sortBy}&sort_order=${sortOrder}`;
      if (status) q += `&status=${status}`;
      if (startDate) q += `&start_date=${startDate}`;
      if (endDate) q += `&end_date=${endDate}`;

      const res = await fetch(`/admin/requests/export${q}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `service_requests${status ? '_' + status : ''}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch {
      showToast('Failed to download requests CSV');
    }
  };

  const filteredRequests = requests.filter((r) => {
    const search = searchQuery.toLowerCase();
    const matchesSearch =
      !searchQuery ||
      r.title.toLowerCase().includes(search) ||
      (r.description && r.description.toLowerCase().includes(search)) ||
      (r.full_name && r.full_name.toLowerCase().includes(search)) ||
      r.user_id.toLowerCase().includes(search);
    const matchesType = !typeFilter || r.request_type === typeFilter;
    return matchesSearch && matchesType;
  });

  const label = filter === 'pending' ? 'Pending Review' : filter === 'approved' ? 'Approved' : 'All Requests';

  return (
    <div>
      {/* Controls */}
      <div className="search-filter-row" style={{ marginBottom: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            className="form-control"
            placeholder="Search title or user..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ margin: 0, padding: '9px 12px', fontSize: '13px', borderRadius: '10px', border: '1.5px solid var(--slate-200)', flex: 1 }}
          />
          <select
            className="form-control"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as ReqType | '')}
            style={{ margin: 0, width: '120px', padding: '9px 12px', fontSize: '13px', borderRadius: '10px', border: '1.5px solid var(--slate-200)', height: 'auto' }}
          >
            <option value="">All Types</option>
            <option value="room_booking">🏢 Room</option>
            <option value="vehicle_booking">🚗 Vehicle</option>
            <option value="maintenance">🔧 Maintenance</option>
            <option value="other">📋 Other</option>
          </select>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <input
            type="date"
            className="form-control"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={{ margin: 0, padding: '6px 8px', fontSize: '12px', borderRadius: '8px', border: '1.5px solid var(--slate-200)', flex: 1 }}
            placeholder="Start Date"
          />
          <span style={{ fontSize: '12px', color: 'var(--slate-400)' }}>to</span>
          <input
            type="date"
            className="form-control"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={{ margin: 0, padding: '6px 8px', fontSize: '12px', borderRadius: '8px', border: '1.5px solid var(--slate-200)', flex: 1 }}
            placeholder="End Date"
          />
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--slate-400)', textTransform: 'uppercase' }}>Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{ padding: '4px 8px', fontSize: '12px', borderRadius: '6px', border: '1.5px solid var(--slate-200)', color: 'var(--slate-600)', height: 'auto', background: 'white' }}
            >
              <option value="created_at">Submission Date</option>
              <option value="priority">Priority</option>
              <option value="title">Title</option>
            </select>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              style={{ padding: '4px 8px', fontSize: '12px', borderRadius: '6px', border: '1.5px solid var(--slate-200)', color: 'var(--slate-600)', height: 'auto', background: 'white' }}
            >
              <option value="desc">Desc</option>
              <option value="asc">Asc</option>
            </select>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={handleExportCsv}
            style={{ margin: 0, padding: '6px 10px', fontSize: '11px', width: 'auto', display: 'flex', alignItems: 'center', gap: '4px', height: '28px', borderRadius: '6px' }}
          >
            📥 Export
          </button>
        </div>
      </div>

      {/* List */}
      <div id="admin-list">
        {loading ? (
          <>
            <div className="skeleton skeleton-card"></div>
            <div className="skeleton skeleton-card"></div>
            <div className="skeleton skeleton-card"></div>
          </>
        ) : error ? (
          <div className="empty-state">
            <div className="empty-icon">⚠️</div>
            <h3>Could not load requests</h3>
            <button className="btn-retry" onClick={fetchRequests}>↻ Retry</button>
          </div>
        ) : filteredRequests.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🔍</div>
            <h3>No matching requests</h3>
            <p>Try adjusting your search or filter.</p>
          </div>
        ) : (
          <>
            <div className="section-hd">
              <h2>{label}</h2>
              <span className="count-chip">{filteredRequests.length}</span>
            </div>
            {filteredRequests.map((r) => {
              const name = r.full_name ? r.full_name : shortId(r.user_id);
              return (
                <div
                  key={r.id}
                  className="card clickable"
                  data-status={r.status}
                  onClick={() => onSelectRequest(r.id)}
                >
                  <div className="card-row">
                    <span className="card-title">{r.title}</span>
                    <span className="card-arrow">›</span>
                  </div>
                  <div className="card-meta">
                    <StatusBadge status={r.status} />
                    <TypeTag type={r.request_type} />
                    <PriorityBadge priority={r.priority || 'normal'} />
                    <span className="user-chip">👤 {name}</span>
                    <span className="card-date">{relativeTime(r.created_at)}</span>
                  </div>
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
};
