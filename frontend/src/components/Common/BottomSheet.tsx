import React from 'react';

interface BottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export const BottomSheet: React.FC<BottomSheetProps> = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="sheet-overlay" onClick={handleOverlayClick}>
      <div className="sheet" style={{ paddingBottom: '24px' }}>
        <div className="sheet-handle"></div>
        <div className="sheet-title">{title}</div>
        <div style={{ marginBottom: '20px' }}>{children}</div>
      </div>
    </div>
  );
};
