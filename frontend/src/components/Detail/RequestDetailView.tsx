import React, { useState, useEffect } from 'react';
import { useApp, RequestDetail } from '../../context/AppContext';
import { formatDateTime, relativeTime } from '../../utils/format';
import { StatusBadge, TypeTag } from '../Common/Badges';
import { CommentsSection } from './CommentsSection';
import { BottomSheet } from '../Common/BottomSheet';

interface RequestDetailViewProps {
  requestId: string;
  onBack: () => void;
  isAdmin?: boolean;
}

export const RequestDetailView: React.FC<RequestDetailViewProps> = ({ requestId, onBack, isAdmin = false }) => {
  const { apiCall, showToast } = useApp();
  const [request, setRequest] = useState<RequestDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [attachments, setAttachments] = useState<any[]>([]);
  const [showCancelSheet, setShowCancelSheet] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  const fetchRequestDetails = async () => {
    try {
      setLoading(true);
      const rData = await apiCall('GET', isAdmin ? `/admin/requests/${requestId}` : `/requests/${requestId}`);
      setRequest(rData);
      
      // Load attachments
      try {
        const aData = await apiCall('GET', `/requests/${requestId}/attachments`);
        setAttachments(aData || []);
      } catch {
        // attachments optional
      }
      
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

  const handleCancelRequest = async () => {
    if (cancelling) return;
    setCancelling(true);
    showToast('Cancelling…');
    try {
      await apiCall('PATCH', `/requests/${requestId}/cancel`, {});
      showToast('Request cancelled');
      setShowCancelSheet(false);
      onBack();
    } catch {
      showToast('Could not cancel — try again');
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <button className="back-btn" onClick={onBack}>‹ Back</button>
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
        <button className="back-btn" onClick={onBack}>‹ Back</button>
        <div className="empty-state">
          <div className="empty-icon">⚠️</div>
          <h3>Could not load request</h3>
          <button className="btn-retry" onClick={fetchRequestDetails}>↻ Retry</button>
        </div>
      </div>
    );
  }

  const isImageType = (url: string) => /\.(jpg|jpeg|png|gif)$/i.test(url);
  const images = attachments.filter(a => isImageType(a.file_url));
  const files = attachments.filter(a => !isImageType(a.file_url));

  // Timeline Progress
  const isDone = ['approved', 'rejected', 'cancelled'].includes(request.status);
  const isFailed = ['rejected', 'cancelled'].includes(request.status);
  const steps = [
    { label: 'Submitted', time: request.created_at, state: 'done' },
    { label: 'Under Review', time: isDone ? request.updated_at : null, state: request.status === 'pending' ? 'active' : 'done' },
    {
      label: request.status === 'approved' ? 'Approved' :
             request.status === 'rejected' ? 'Rejected' :
             request.status === 'cancelled' ? 'Cancelled' : 'Decision',
      time: isDone ? request.updated_at : null,
      state: request.status === 'approved' ? 'done' : isFailed ? 'fail' : ''
    }
  ];

  return (
    <div className="page">
      <button className="back-btn" onClick={onBack}>‹ Back</button>

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

      {/* Progress Timeline */}
      <div className="info-block">
        <div style={{ padding: '14px 16px 2px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--slate-400)', textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '12px' }}>
            Progress
          </div>
          <div className="timeline">
            {steps.map((s, idx) => (
              <div key={idx} className="tl-step">
                <div className={`tl-dot ${s.state}`}></div>
                <div>
                  <div className="tl-label">{s.label}</div>
                  <div className="tl-time">{s.time ? relativeTime(s.time) : 'Waiting…'}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Detail Block */}
      <div className="info-block">
        {request.full_name && (
          <div className="info-row">
            <span className="info-key">From</span>
            <span className="info-val">{request.full_name}</span>
          </div>
        )}
        <div className="info-row">
          <span className="info-key">Created</span>
          <span className="info-val">{formatDateTime(request.created_at)}</span>
        </div>
        <div className="info-row">
          <span className="info-key">Updated</span>
          <span className="info-val">{formatDateTime(request.updated_at)}</span>
        </div>
        {request.start_time && (
          <>
            <div className="info-row">
              <span className="info-key">From</span>
              <span className="info-val">{formatDateTime(request.start_time)}</span>
            </div>
            <div className="info-row">
              <span className="info-key">Until</span>
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

      {request.admin_note && (
        <div className="admin-note-box">
          <div className="note-label">📝 Admin Note</div>
          <p>{request.admin_note}</p>
        </div>
      )}

      {/* Attachments */}
      {attachments.length > 0 && (
        <div className="info-block" style={{ marginBottom: '12px' }}>
          <div style={{ padding: '14px 16px 10px' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--slate-400)', textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '10px' }}>
              Attachments ({attachments.length})
            </div>
            {images.length > 0 && (
              <div className="attachment-grid">
                {images.map((a, idx) => (
                  <img
                    key={idx}
                    className="attachment-img"
                    src={a.file_url}
                    alt={a.filename}
                    onClick={() => window.open(a.file_url, '_blank')}
                  />
                ))}
              </div>
            )}
            {files.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: images.length > 0 ? '10px' : 0 }}>
                {files.map((a, idx) => (
                  <a key={idx} className="attachment-file" href={a.file_url} target="_blank" rel="noopener noreferrer">
                    📄 {a.filename}
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Discussion Board */}
      <CommentsSection requestId={request.id} />

      {/* Cancel Button */}
      {!isAdmin && request.status === 'pending' && (
        <button className="btn btn-danger" onClick={() => setShowCancelSheet(true)}>
          Cancel Request
        </button>
      )}

      {/* Confirmation Bottom Sheet */}
      <BottomSheet isOpen={showCancelSheet} onClose={() => setShowCancelSheet(false)} title="Cancel this request?">
        <div className="sheet-desc">This cannot be undone. Your pending request will be cancelled.</div>
        <button className="btn btn-danger" onClick={handleCancelRequest} disabled={cancelling}>
          {cancelling ? 'Cancelling...' : 'Yes, Cancel It'}
        </button>
        <button className="btn btn-ghost" onClick={() => setShowCancelSheet(false)} style={{ marginTop: '8px' }}>
          Keep It
        </button>
      </BottomSheet>
    </div>
  );
};
