import React from 'react';
import { ReqType, PriorityType, StatusType } from '../../context/AppContext';

export const StatusBadge: React.FC<{ status: StatusType }> = ({ status }) => {
  const labels: Record<StatusType, string> = {
    pending: 'Pending',
    approved: 'Approved',
    rejected: 'Rejected',
    cancelled: 'Cancelled',
  };
  return (
    <span className={`badge badge-${status}`}>
      {labels[status] || status}
    </span>
  );
};

export const TypeTag: React.FC<{ type: ReqType }> = ({ type }) => {
  const labels: Record<ReqType, string> = {
    room_booking: '🏢 Room',
    vehicle_booking: '🚗 Vehicle',
    maintenance: '🔧 Maintenance',
    other: '📋 Other',
  };
  return <span className="tag">{labels[type] || type}</span>;
};

export const PriorityBadge: React.FC<{ priority: PriorityType }> = ({ priority }) => {
  const labels: Record<PriorityType, string> = {
    low: 'Low',
    normal: 'Normal',
    urgent: 'Urgent',
  };
  return (
    <span className={`priority-badge priority-${priority}`}>
      {labels[priority] || priority}
    </span>
  );
};
