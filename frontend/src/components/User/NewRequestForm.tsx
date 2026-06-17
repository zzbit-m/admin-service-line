import React, { useState, useEffect, useRef } from 'react';
import { useApp, Resource, ReqType, PriorityType } from '../../context/AppContext';
import { Timeline, BookingSlot } from '../Common/Timeline';


interface NewRequestFormProps {
  onBack: () => void;
  onSuccess: (requestId: string) => void;
}

export const NewRequestForm: React.FC<NewRequestFormProps> = ({ onBack, onSuccess }) => {
  const { apiCall, uploadAttachment, showToast } = useApp();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [resources, setResources] = useState<Resource[]>([]);

  // Form states
  const [selectedType, setSelectedType] = useState<ReqType | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<PriorityType>('normal');
  const [titleError, setTitleError] = useState(false);

  // Scheduling states
  const [resourceId, setResourceId] = useState('');
  const [bookingDate, setBookingDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [bookedSlots, setBookedSlots] = useState<BookingSlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [timingError, setTimingError] = useState<string | null>(null);

  // Photo state
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchResources = async () => {
    try {
      setLoading(true);
      const data = await apiCall('GET', '/resources');
      setResources(data || []);
    } catch {
      showToast('Could not load resources');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
  }, []);

  // Fetch busy slots when resource or date changes
  useEffect(() => {
    const fetchAvailability = async () => {
      if (!resourceId || !bookingDate) {
        setBookedSlots([]);
        setTimingError(null);
        return;
      }
      setLoadingSlots(true);
      try {
        const slots = await apiCall('GET', `/resources/${resourceId}/availability?date=${bookingDate}`);
        setBookedSlots(slots || []);
      } catch {
        showToast('Failed to check resource availability');
        setBookedSlots([]);
      } finally {
        setLoadingSlots(false);
      }
    };
    fetchAvailability();
  }, [resourceId, bookingDate]);

  // Validate times on time input change
  useEffect(() => {
    validateTimes();
  }, [startTime, endTime, bookedSlots, selectedType]);

  const validateTimes = () => {
    setTimingError(null);
    if (selectedType !== 'room_booking' && selectedType !== 'vehicle_booking') {
      return true;
    }
    if (!resourceId || !bookingDate || !startTime || !endTime) {
      return false;
    }

    const startLocal = new Date(`${bookingDate}T${startTime}`);
    const endLocal = new Date(`${bookingDate}T${endTime}`);

    if (startLocal >= endLocal) {
      setTimingError('End time must be after start time');
      return false;
    }

    for (const slot of bookedSlots) {
      const slotStart = new Date(slot.start_time);
      const slotEnd = new Date(slot.end_time);

      if (startLocal < slotEnd && endLocal > slotStart) {
        setTimingError('This time slot overlaps with an existing booking');
        return false;
      }
    }
    return true;
  };

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const MAX = 5 * 1024 * 1024;
    if (file.size > MAX) {
      showToast('Photo too large — max 5MB');
      return;
    }

    const allowed = ['image/jpeg', 'image/png', 'image/gif'];
    if (!allowed.includes(file.type)) {
      showToast('Only JPG, PNG, GIF allowed');
      return;
    }

    setPhoto(file);
    const reader = new FileReader();
    reader.onload = (event) => {
      setPhotoPreview(event.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleRemovePhoto = () => {
    setPhoto(null);
    setPhotoPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleTypeSelect = (type: ReqType) => {
    setSelectedType(type);
    setResourceId('');
    setBookingDate('');
    setStartTime('');
    setEndTime('');
    setBookedSlots([]);
    setTimingError(null);
  };

  const handleSubmit = async () => {
    if (!title.trim()) {
      setTitleError(true);
      return;
    }
    setTitleError(false);

    if (selectedType === 'room_booking' || selectedType === 'vehicle_booking') {
      if (!validateTimes()) {
        showToast('Please check booking details');
        return;
      }
    }

    setSubmitting(true);
    let startTimeIso: string | null = null;
    let endTimeIso: string | null = null;

    if ((selectedType === 'room_booking' || selectedType === 'vehicle_booking') && bookingDate && startTime && endTime) {
      startTimeIso = new Date(`${bookingDate}T${startTime}`).toISOString();
      endTimeIso = new Date(`${bookingDate}T${endTime}`).toISOString();
    }

    try {
      const newReq = await apiCall('POST', '/requests', {
        title: title.trim(),
        description: description.trim() || null,
        request_type: selectedType,
        resource_id: resourceId || null,
        priority,
        start_time: startTimeIso,
        end_time: endTimeIso,
      });

      if (photo) {
        showToast('Uploading photo…');
        await uploadAttachment(newReq.id, photo);
      }

      showToast(photo ? '✓ Request + photo submitted!' : '✓ Request submitted!');
      onSuccess(newReq.id);
    } catch {
      showToast('Failed to submit — try again');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <button className="back-btn" onClick={onBack}>‹ Back</button>
        <div className="loader">
          <div className="spinner"></div>
          <p className="loader-text">Loading request form…</p>
        </div>
      </div>
    );
  }

  const targetType = selectedType === 'room_booking' ? 'room' : 'vehicle';
  const filteredResources = resources.filter((r) => r.type === targetType);

  return (
    <div className="page">
      <button className="back-btn" onClick={onBack}>‹ Back</button>

      <div className="card">
        <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--slate-800)', marginBottom: '4px' }}>
          New Request
        </div>
        <p style={{ fontSize: '13px', color: 'var(--slate-400)' }}>What do you need help with?</p>

        {/* Request Type Selection Grid */}
        <div className="form-group">
          <label className="form-label">Request Type</label>
          <div className="type-grid">
            {[
              { val: 'room_booking', icon: '🏢', label: 'Room' },
              { val: 'vehicle_booking', icon: '🚗', label: 'Vehicle' },
              { val: 'maintenance', icon: '🔧', label: 'Maintenance' },
              { val: 'other', icon: '📋', label: 'Other' },
            ].map((t) => (
              <div
                key={t.val}
                className={`type-tile ${selectedType === t.val ? 'selected' : ''}`}
                onClick={() => handleTypeSelect(t.val as ReqType)}
              >
                <span className="type-tile-icon">{t.icon}</span>
                <span className="type-tile-label">{t.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Scheduling Section */}
        {(selectedType === 'room_booking' || selectedType === 'vehicle_booking') && (
          <div
            id="scheduling-section"
            style={{
              borderTop: '1px dashed var(--slate-200)',
              borderBottom: '1px dashed var(--slate-200)',
              padding: '14px 0',
              marginBottom: '16px',
            }}
          >
            <div className="form-group">
              <label className="form-label" htmlFor="req-resource-id">
                Select Resource <span className="req">*</span>
              </label>
              <select
                className="form-control"
                id="req-resource-id"
                value={resourceId}
                onChange={(e) => setResourceId(e.target.value)}
                style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px', height: 'auto' }}
              >
                {filteredResources.length === 0 ? (
                  <option value="">No active {targetType}s available</option>
                ) : (
                  <>
                    <option value="">-- Select a {targetType} --</option>
                    {filteredResources.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name}
                      </option>
                    ))}
                  </>
                )}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="req-booking-date">
                Date <span className="req">*</span>
              </label>
              <input
                type="date"
                className="form-control"
                id="req-booking-date"
                value={bookingDate}
                onChange={(e) => setBookingDate(e.target.value)}
                style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px', height: 'auto' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
              <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                <label className="form-label" htmlFor="req-start-time">
                  Start Time <span className="req">*</span>
                </label>
                <input
                  type="time"
                  className="form-control"
                  id="req-start-time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px', height: 'auto' }}
                />
              </div>
              <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
                <label className="form-label" htmlFor="req-end-time">
                  End Time <span className="req">*</span>
                </label>
                <input
                  type="time"
                  className="form-control"
                  id="req-end-time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px', height: 'auto' }}
                />
              </div>
            </div>

            {/* Occupied slots display */}
            {resourceId && bookingDate && (
              <div
                id="availability-box"
                style={{
                  marginTop: '12px',
                  background: 'var(--slate-50)',
                  border: '1px solid var(--slate-200)',
                  borderRadius: '10px',
                  padding: '12px',
                }}
              >
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--slate-600)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
                  Occupied Time Slots
                </div>
                {loadingSlots ? (
                  <div style={{ color: 'var(--slate-400)', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <div className="spinner spinner-sm" style={{ borderWidth: '2px', width: '12px', height: '12px', margin: 0 }}></div>
                    Checking availability…
                  </div>
                ) : (
                  <Timeline slots={bookedSlots} />
                )}
              </div>
            )}

            {timingError && (
              <p className="form-error visible" style={{ marginTop: '6px', marginBottom: 0 }}>
                {timingError}
              </p>
            )}
          </div>
        )}

        {/* Title */}
        <div className="form-group">
          <label className="form-label" htmlFor="req-title">
            Title <span className="req">*</span>
          </label>
          <input
            className={`form-control ${titleError ? 'error' : ''}`}
            id="req-title"
            placeholder="e.g. Meeting Room for Monday standup"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          {titleError && <p className="form-error visible">Please enter a title</p>}
        </div>

        {/* Description */}
        <div className="form-group">
          <label className="form-label" htmlFor="req-desc">
            Description
          </label>
          <textarea
            className="form-control"
            id="req-desc"
            placeholder="Any extra details…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        {/* Priority */}
        <div className="form-group">
          <label className="form-label" htmlFor="req-priority">
            Priority
          </label>
          <select
            className="form-control"
            id="req-priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value as PriorityType)}
            style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px', height: 'auto' }}
          >
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>

        {/* Image Attachment (optional) */}
        <div className="form-group">
          <label className="form-label">Photo (optional)</label>
          <input
            type="file"
            id="photo-input"
            accept="image/jpeg,image/png,image/gif"
            style={{ display: 'none' }}
            ref={fileInputRef}
            onChange={handlePhotoChange}
          />
          <div
            className={`photo-upload-area ${photoPreview ? 'has-file' : ''}`}
            id="photo-area"
            onClick={() => fileInputRef.current?.click()}
          >
            <span className="photo-upload-icon">📷</span>
            <span className="photo-upload-text" id="photo-label">
              {photo ? photo.name : 'Tap to add a photo'}
            </span>
            <span className="photo-upload-hint">JPG, PNG, GIF · Max 5MB</span>
            {photoPreview && <img className="photo-preview visible" src={photoPreview} alt="preview" />}
          </div>
          {photo && (
            <button className="photo-clear visible" onClick={handleRemovePhoto} type="button">
              ✕ Remove photo
            </button>
          )}
        </div>

        {submitting && (
          <div className="upload-progress visible">
            <div className="upload-bar"></div>
          </div>
        )}

        {/* Submit */}
        <button
          className="btn btn-primary"
          id="submit-btn"
          onClick={handleSubmit}
          disabled={
            submitting ||
            ((selectedType === 'room_booking' || selectedType === 'vehicle_booking') &&
              (!resourceId || !bookingDate || !startTime || !endTime || !!timingError))
          }
          style={{ marginTop: '18px' }}
        >
          {submitting ? (
            <>
              <div className="spinner spinner-sm"></div> Submitting…
            </>
          ) : (
            'Submit Request'
          )}
        </button>
        <button className="btn btn-ghost" onClick={onBack} disabled={submitting}>
          Cancel
        </button>
      </div>
    </div>
  );
};
