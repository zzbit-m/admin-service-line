import React from 'react';

export interface BookingSlot {
  start_time: string;
  end_time: string;
  full_name?: string;
}

interface TimelineProps {
  slots: BookingSlot[];
  title?: string;
  isCompact?: boolean;
}

export const Timeline: React.FC<TimelineProps> = ({ slots, title = "Daily Schedule View", isCompact = false }) => {
  if (!slots.length) {
    return (
      <div style={{ padding: '4px 0' }}>
        <span style={{ color: 'var(--green)', fontWeight: 600, fontSize: '12px', display: 'block' }}>
          🟢 Available all day
        </span>
      </div>
    );
  }

  // Sort slots by start_time
  const sortedSlots = [...slots].sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  );

  return (
    <div style={{ marginTop: isCompact ? '4px' : '12px', marginBottom: isCompact ? '4px' : '16px' }}>
      {!isCompact && (
        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--slate-400)', textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: '8px' }}>
          {title}
        </div>
      )}
      <div style={{ position: 'relative', height: isCompact ? '16px' : '24px', backgroundColor: 'var(--green-light)', border: isCompact ? '1.2px solid var(--green)' : '1.5px solid var(--green)', borderRadius: isCompact ? '6px' : '8px', overflow: 'hidden' }}>
        {sortedSlots.map((s, idx) => {
          const startDt = new Date(s.start_time);
          const endDt = new Date(s.end_time);
          
          const startMins = startDt.getHours() * 60 + startDt.getMinutes();
          const endMins = endDt.getHours() * 60 + endDt.getMinutes();
          
          const left = (startMins / 1440) * 100;
          const width = ((endMins - startMins) / 1440) * 100;
          
          return (
            <div
              key={idx}
              style={{
                position: 'absolute',
                left: `${left}%`,
                width: `${width}%`,
                height: '100%',
                background: 'linear-gradient(135deg, #ff4d4f 0%, #d93025 100%)',
              }}
              title={s.full_name ? `Booked by ${s.full_name}` : 'Booked'}
            />
          );
        })}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: isCompact ? '8px' : '10px', color: 'var(--slate-400)', marginTop: '2px', fontFamily: 'monospace', fontWeight: 600 }}>
        <span>00:00</span>
        <span>06:00</span>
        <span>12:00</span>
        <span>18:00</span>
        <span>24:00</span>
      </div>

      <div style={{ marginTop: '10px' }}>
        {sortedSlots.map((s, idx) => {
          const start = new Date(s.start_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
          const end = new Date(s.end_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
          return (
            <div
              key={idx}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '6px 0',
                borderBottom: '1px solid var(--slate-100)',
                fontSize: '12px',
              }}
            >
              <span style={{ fontWeight: 500, color: 'var(--red)' }}>
                🔴 Booked {s.full_name ? `(${s.full_name})` : ''}
              </span>
              <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                {start} - {end}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
