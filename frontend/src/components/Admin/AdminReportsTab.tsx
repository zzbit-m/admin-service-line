import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../Common/Badges';

export const AdminReportsTab: React.FC = () => {
  const { apiCall, accessToken, showToast } = useApp();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await apiCall('GET', '/admin/stats');
      setStats(data);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const downloadStatsCsv = async () => {
    try {
      const res = await fetch('/admin/stats/export', {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'admin_stats.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch {
      showToast('Failed to download stats CSV');
    }
  };

  const downloadRequestsCsv = async () => {
    try {
      const res = await fetch('/admin/requests/export', {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'service_requests.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch {
      showToast('Failed to download requests CSV');
    }
  };

  if (loading) {
    return (
      <div className="loader">
        <div className="spinner"></div>
        <p className="loader-text">Generating reports…</p>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="empty-state">
        <div className="empty-icon">⚠️</div>
        <h3>Failed to load statistics</h3>
        <button className="btn-retry" onClick={fetchStats}>↻ Retry</button>
      </div>
    );
  }

  const total = stats.total_requests || { pending: 0, approved: 0, rejected: 0, cancelled: 0 };
  const totalSum = total.pending + total.approved + total.rejected + total.cancelled;
  const completionRate = totalSum ? Math.round((total.approved / (totalSum - total.pending - total.cancelled || 1)) * 100) : 0;
  const avgHours = stats.avg_response_hours;

  const typeLabels = {
    room_booking: { label: '🏢 Room Booking', cls: 'room' },
    vehicle_booking: { label: '🚗 Vehicle Booking', cls: 'vehicle' },
    maintenance: { label: '🔧 Maintenance', cls: 'maint' },
    other: { label: '📋 Other Requests', cls: 'other' },
  };

  let avgColor = 'var(--green)';
  let avgLabel = 'Fast';
  if (avgHours > 24) {
    avgColor = 'var(--red)';
    avgLabel = 'Slow';
  } else if (avgHours > 2) {
    avgColor = 'var(--amber)';
    avgLabel = 'Normal';
  }

  return (
    <div>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <button
          className="btn btn-ghost btn-sm"
          onClick={downloadStatsCsv}
          style={{ margin: 0, padding: '8px 12px', fontSize: '12px', flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', height: '36px', borderRadius: '10px' }}
        >
          📥 Export Stats CSV
        </button>
        <button
          className="btn btn-ghost btn-sm"
          onClick={downloadRequestsCsv}
          style={{ margin: 0, padding: '8px 12px', fontSize: '12px', flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', height: '36px', borderRadius: '10px' }}
        >
          📥 Export Requests CSV
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-label">Total Requests</div>
          <div className="stat-card-value">{totalSum}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Pending Approval</div>
          <div className="stat-card-value">{total.pending}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Approved</div>
          <div className="stat-card-value">{total.approved}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Approval Rate</div>
          <div className="stat-card-value">{completionRate}%</div>
        </div>
        {avgHours !== null && avgHours !== undefined && (
          <div className="stat-card" style={{ gridColumn: 'span 2' }}>
            <div className="stat-card-label">Average Response Time</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
              <span className="stat-card-value" style={{ color: avgColor }}>{avgHours} hrs</span>
              <span className="badge" style={{ background: `${avgColor}22`, color: avgColor, border: `1px solid ${avgColor}44`, fontSize: '10px' }}>
                {avgLabel}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Request Type Distribution */}
      <div className="chart-container">
        <div className="chart-title">Request Type Distribution</div>
        {Object.entries(typeLabels).map(([key, val]) => {
          const count = stats.type_distribution?.[key] || 0;
          const pct = totalSum ? Math.round((count / totalSum) * 100) : 0;
          return (
            <div key={key} className="chart-bar-row">
              <div className="chart-bar-header">
                <span>{val.label}</span>
                <span>{count} ({pct}%)</span>
              </div>
              <div className="chart-bar-bg">
                <div className={`chart-bar-fill chart-bar-${val.cls}`} style={{ width: `${pct}%` }}></div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Monthly Trends */}
      <div className="chart-container">
        <div className="chart-title">Monthly Trends (Last 6 Months)</div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--slate-200)', textAlign: 'left', color: 'var(--slate-400)' }}>
              <th style={{ padding: '8px 4px' }}>Month</th>
              <th style={{ padding: '8px 4px', textAlign: 'right' }}>Total</th>
              <th style={{ padding: '8px 4px', textAlign: 'right', color: '#065f46' }}>Appr</th>
              <th style={{ padding: '8px 4px', textAlign: 'right', color: '#991b1b' }}>Rej</th>
              <th style={{ padding: '8px 4px', textAlign: 'right', color: 'var(--slate-500)' }}>Canc</th>
            </tr>
          </thead>
          <tbody>
            {!stats.monthly_reports || stats.monthly_reports.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '12px', color: 'var(--slate-400)' }}>
                  No monthly data yet.
                </td>
              </tr>
            ) : (
              stats.monthly_reports.map((m: any, idx: number) => (
                <tr key={idx} style={{ borderBottom: '1px solid var(--slate-100)' }}>
                  <td style={{ padding: '8px 4px', fontWeight: 600, color: 'var(--slate-700)' }}>{m.month}</td>
                  <td style={{ padding: '8px 4px', textAlign: 'right', color: 'var(--slate-600)' }}>{m.total}</td>
                  <td style={{ padding: '8px 4px', textAlign: 'right', color: 'var(--green)', fontWeight: 600 }}>{m.approved}</td>
                  <td style={{ padding: '8px 4px', textAlign: 'right', color: 'var(--red)', fontWeight: 600 }}>{m.rejected ?? 0}</td>
                  <td style={{ padding: '8px 4px', textAlign: 'right', color: 'var(--slate-500)', fontWeight: 600 }}>{m.cancelled ?? 0}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Weekly Trends */}
      <div className="chart-container">
        <div className="chart-title">Weekly Trends (Last 4 Weeks)</div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--slate-200)', textAlign: 'left', color: 'var(--slate-400)' }}>
              <th style={{ padding: '8px 4px' }}>Week</th>
              <th style={{ padding: '8px 4px', textAlign: 'right' }}>Total Requests</th>
            </tr>
          </thead>
          <tbody>
            {!stats.weekly_reports || stats.weekly_reports.length === 0 ? (
              <tr>
                <td colSpan={2} style={{ textAlign: 'center', padding: '12px', color: 'var(--slate-400)' }}>
                  No weekly data yet.
                </td>
              </tr>
            ) : (
              stats.weekly_reports.map((w: any, idx: number) => (
                <tr key={idx} style={{ borderBottom: '1px solid var(--slate-100)' }}>
                  <td style={{ padding: '8px 4px', fontWeight: 600, color: 'var(--slate-700)' }}>{w.week}</td>
                  <td style={{ padding: '8px 4px', textAlign: 'right', color: 'var(--slate-600)' }}>{w.total}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Top Requisitioners */}
      <div className="chart-container">
        <div className="chart-title">Top Requisitioners</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {!stats.top_users || stats.top_users.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--slate-400)', fontSize: '12px' }}>
              No user activity yet.
            </div>
          ) : (
            stats.top_users.map((u: any, idx: number) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px', padding: '6px 0', borderBottom: '1px solid var(--slate-100)' }}>
                <span style={{ fontWeight: 500, color: 'var(--slate-700)' }}>
                  {idx + 1}. {u.full_name}
                </span>
                <span className="count-chip" style={{ background: 'var(--blue-light)', color: '#1e40af', fontSize: '11px' }}>
                  {u.request_count} requests
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Resource Utilization */}
      <div className="chart-container">
        <div className="chart-title">Resource Utilization</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {!stats.resource_utilization || stats.resource_utilization.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--slate-400)', fontSize: '12px' }}>
              No bookings yet.
            </div>
          ) : (
            stats.resource_utilization.map((ru: any, idx: number) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px', padding: '6px 0', borderBottom: '1px solid var(--slate-100)' }}>
                <div>
                  <span style={{ fontWeight: 600, color: 'var(--slate-700)' }}>
                    {idx + 1}. {ru.resource_name}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--slate-400)', marginLeft: '4px', textTransform: 'capitalize' }}>
                    ({ru.resource_type})
                  </span>
                </div>
                <span className="count-chip" style={{ background: 'var(--green-light)', color: 'var(--green-dark)', fontSize: '11px' }}>
                  {ru.booking_count} bookings
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
