import React, { useState, useEffect, useRef } from 'react';
import { useApp, Comment } from '../../context/AppContext';
import { relativeTime } from '../../utils/format';

interface CommentsSectionProps {
  requestId: string;
}

export const CommentsSection: React.FC<CommentsSectionProps> = ({ requestId }) => {
  const { apiCall, currentUserId, showToast } = useApp();
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [inputText, setInputText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  const fetchComments = async () => {
    try {
      const data = await apiCall('GET', `/requests/${requestId}/comments`);
      setComments(data || []);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComments();
  }, [requestId]);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [comments]);

  const handleSend = async () => {
    const text = inputText.trim();
    if (!text || submitting) return;

    setSubmitting(true);
    try {
      await apiCall('POST', `/requests/${requestId}/comments`, { content: text });
      setInputText('');
      await fetchComments();
    } catch {
      showToast('Failed to send comment');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card" style={{ marginTop: '12px', padding: '14px 16px' }}>
      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--slate-400)', textTransform: 'uppercase', letterSpacing: '.4px', marginBottom: '12px' }}>
        Comments & Discussion
      </div>
      
      <div
        ref={listRef}
        id="comments-list"
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          maxHeight: '280px',
          overflowY: 'auto',
          marginBottom: '12px',
          paddingRight: '4px',
        }}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: '12px', fontSize: '12px', color: 'var(--slate-400)' }}>
            Loading comments…
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '12px', fontSize: '12px', color: 'var(--red)' }}>
            Failed to load comments
          </div>
        ) : comments.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '16px 12px', fontSize: '12px', color: 'var(--slate-400)' }}>
            No messages yet. Start the conversation!
          </div>
        ) : (
          comments.map((c) => {
            const isSelf = c.user_id === currentUserId;
            const name = c.full_name ? c.full_name : 'User';

            return (
              <div
                key={c.id}
                style={{
                  alignSelf: isSelf ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  display: 'flex',
                  flexDirection: 'column',
                  marginBottom: '2px',
                }}
              >
                <div
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    color: 'var(--slate-500)',
                    marginBottom: '2px',
                    display: 'flex',
                    gap: '6px',
                    justifyContent: isSelf ? 'flex-end' : 'flex-start',
                  }}
                >
                  <span>{name}</span>
                  <span style={{ fontWeight: 400, color: 'var(--slate-400)' }}>
                    {relativeTime(c.created_at)}
                  </span>
                </div>
                <div
                  style={{
                    background: isSelf ? 'var(--green-light)' : 'var(--slate-100)',
                    color: 'var(--slate-800)',
                    padding: '8px 12px',
                    borderRadius: isSelf ? '12px 12px 0 12px' : '12px 12px 12px 0',
                    fontSize: '13px',
                    lineHeight: 1.4,
                    wordBreak: 'break-word',
                  }}
                >
                  {c.content}
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="comment-input-row" style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
        <textarea
          className="form-control"
          rows={1}
          placeholder="Type a message…"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={submitting}
          style={{
            margin: 0,
            flex: 1,
            resize: 'none',
            fontSize: '13px',
            borderRadius: '10px',
            border: '1.5px solid var(--slate-200)',
            padding: '8px 12px',
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <button
          className="btn btn-primary"
          onClick={handleSend}
          disabled={submitting || !inputText.trim()}
          style={{
            width: 'auto',
            height: '36px',
            padding: '0 16px',
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '10px',
            fontSize: '13px',
            fontWeight: 600,
          }}
        >
          {submitting ? (
            <div className="spinner spinner-sm" style={{ borderWidth: '2px', width: '12px', height: '12px' }}></div>
          ) : (
            'Send'
          )}
        </button>
      </div>
    </div>
  );
};
