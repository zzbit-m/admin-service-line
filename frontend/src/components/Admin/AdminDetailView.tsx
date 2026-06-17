import React, { useState, useEffect } from 'react';
import { useApp, RequestDetail } from '../../context/AppContext';
import { formatDateTime, relativeTime, shortId } from '../../utils/format';
import { StatusBadge, TypeTag } from '../Common/Badges';
import { CommentsSection } from '../Detail/CommentsSection';

interface AdminDetailViewProps {
  requestId: string;
  onBack: () => void;
}

export const AdminDetailView: React.FC<AdminDetailViewProps> = ({ requestId, onBack }) => {
  const { apiCall, showToast } = useApp();
  const [request, setRequest] = useState<RequestDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Decision fields
  const [adminNote, setAdminNote] = useState('');
  const [selectedChip, setSelectedChip] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submittingStatus, setSubmittingStatus] = useState<'approved' | 'rejected' | null>(null);

  const fetchRequestDetails = async () => {
    try {
      setLoading(true);
      const data = await apiCall('GET', `/admin/requests/${requestId}`);
      setRequest(data);
      setAdminNote(data?.admin_note || '');
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequestDetails();
  }, [requestId]);

  const handleAdminAction = async (status: 'approved' | 'rejected') => {
    setSubmitting(true);
    setSubmittingStatus(status);
    try {
      await apiCall('PATCH', `/admin/requests/${requestId}/status`, {
        status,
        admin_note: adminNote.trim() || null,
      });
      showToast(`✓ Request ${status}`);
      onBack();
    } catch {
      showToast('Action failed — try again');
    } finally {
      setSubmitting(false);
      setSubmittingStatus(null);
    }
  };

  const handleApplyChip = (chipText: string) => {
    setAdminNote(chipText);
    setSelectedChip(chipText);
  };

  if (loading) {
    return (
      <div className="page">
        <button className="back-btn" onClick={onBack}>‹ Dashboard</button>
        <div className="loader">
          <div className="spinner"></div>
          <p className="loader-text">Loading request details…</p>
        </div>
      </div>
    );
  }

  if (error || !request) {
    return (
      <div className="page">
        <button className="back-btn" onClick={onBack}>‹ Dashboard</button>
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <h3>Could not load request</h3>
          <button className="btn-retry" onClick={fetchRequestDetails}>↻ Retry</button>
        </div>
      </div>
    );
  }

  const isPending = request.status === 'pending';
  const name = request.full_name ? request.full_name : shortId(request.user_id);

  const quickNotes = [
    'Resource unavailable',
    'Duplicate request',
    'Need more details',
    'Out of working hours',
  ];

  return (
    <div className="page">
      <button className="back-btn" onClick={onBack}>‹ Dashboard</button>

      <div className="detail-hero">
        <div className="detail-hero-title">{request.title}</div>
        <div className="detail-hero-meta">
          <StatusBadge status={request.status} />
          <TypeTag type={request.request_type} />
          <span className={`priority-badge priority-${request.priority || 'normal'}`} style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.3)' }}>
            {request.priority || 'normal'}
          </span>
        </div>
      </div>

      <div className="info-block">
        <div className="info-row">
          <span className="info-key">From</span>
          <span className="info-val">{name}</span>
        </div>
        <div className="info-row">
          <span className="info-key">Submitted</span>
          <span className="info-val">{formatDateTime(request.created_at)} · {relativeTime(request.created_at)}</span>
        </div>
        {request.start_time && (
          <>
            <div className="info-row">
              <span className="info-key">Start</span>
              <span className="info-val">{formatDateTime(request.start_time)}</span>
            </div>
            <div className="info-row">
              <span className="info-key">End</span>
              <span className="info-val">{formatDateTime(request.end_time)}</span>
            </div>
          </>
        )}
        {request.description && (
          <div className="info-row">
            <span className="info-key">Details</span>
            <span className="info-val">{request.description}</span>
          </div>
        )}
      </div>

      {request.admin_note && !isPending && (
        <div className="admin-note-box">
          <div className="note-label">📝 Admin Note</div>
          <p>{request.admin_note}</p>
        </div>
      )}

      {/* Scheduling Conflict warning banner */}
      {isPending && request.conflicts && request.conflicts.length > 0 && (
        <div className="admin-note-box" style={{ background: 'linear-gradient(135deg, #fff1f0, #ffe5e5)', borderColor: 'var(--red)', padding: '14px 16px', borderRadius: 'var(--radius-md)', marginBottom: '12px' }}>
          <div style={{ fontWeight: 700, fontSize: '12px', textTransform: 'uppercase', letterSpacing: '.5px', color: 'var(--red)', marginBottom: '6px' }}>
            ⚠️ Scheduling Conflict Detected
          </div>
          <p style={{ fontSize: '12px', color: '#991b1b', marginBottom: '8px', lineHeight: 1.4 }}>
            The requested time overlaps with these already approved booking(s):
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {request.conflicts.map((c) => (
              <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', padding: '4px 0', borderBottom: '1px solid rgba(255, 77, 79, 0.15)', color: '#991b1b' }}>
                <span style={{ fontWeight: 600 }}>{c.full_name || 'User'}</span>
                <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                  {formatDateTime(c.start_time)} - {formatDateTime(c.end_time).split(', ').pop()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Admin Decision Form */}
      {isPending && (
        <div className="card">
          <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--slate-700)', marginBottom: '10px' }}>
            Admin Decision
          </div>
          <label className="form-label" htmlFor="admin-note-inp">
            Note for requester (optional)
          </label>
          <textarea
            className="form-control"
            id="admin-note-inp"
            rows={2}
            placeholder="Add a note…"
            value={adminNote}
            onChange={(e) => {
              setAdminNote(e.target.value);
              setSelectedChip(null);
            }}
          />

          <div style={{ marginTop: '6px', fontSize: '11px', fontWeight: 600, color: 'var(--slate-400)', textTransform: 'uppercase', letterSpacing: '.4px' }}>
            Quick notes
          </div>
          <div className="chip-group">
            {quickNotes.map((c) => (
              <div
                key={c}
                className={`chip ${selectedChip === c ? 'selected' : ''}`}
                onClick={() => handleApplyChip(c)}
              >
                {c}
              </div>
            ))}
          </div>

          <div className="btn-row" style={{ marginTop: '14px' }}>
            <button
              className="btn btn-primary"
              id="approve-btn"
              disabled={submitting}
              onClick={() => handleAdminAction('approved')}
            >
              {submitting && submittingStatus === 'approved' ? (
                <div className="spinner spinner-sm"></div>
              ) : (
                '✓ Approve'
              )}
            </button>
            <button
              className="btn btn-danger"
              id="reject-btn"
              disabled={submitting}
              onClick={() => handleAdminAction('rejected')}
            >
              {submitting && submittingStatus === 'rejected' ? (
                <div className="spinner spinner-sm"></div>
              ) : (
                '✕ Reject'
              )}
            </button>
          </div>
        </div>
      )}

      {/* Discussion section */}
      <CommentsSection requestId={request.id} />
    </div>
  );
};
