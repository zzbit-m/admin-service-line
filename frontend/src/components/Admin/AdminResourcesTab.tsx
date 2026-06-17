import React, { useState, useEffect } from 'react';
import { useApp, Resource } from '../../context/AppContext';
import { Timeline, BookingSlot } from '../Common/Timeline';
import { BottomSheet } from '../Common/BottomSheet';

export const AdminResourcesTab: React.FC = () => {
  const { apiCall, showToast } = useApp();
  const [resources, setResources] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Availability schedule toggle states
  const [openSchedules, setOpenSchedules] = useState<Record<string, boolean>>({});
  const [schedulesData, setSchedulesData] = useState<Record<string, BookingSlot[]>>({});
  const [schedulesLoading, setSchedulesLoading] = useState<Record<string, boolean>>({});

  // Form Bottom Sheet states
  const [isAddSheetOpen, setIsAddSheetOpen] = useState(false);
  const [isEditSheetOpen, setIsEditSheetOpen] = useState(false);
  const [editingResource, setEditingResource] = useState<Resource | null>(null);

  // Form fields (Add & Edit)
  const [name, setName] = useState('');
  const [type, setType] = useState<'room' | 'vehicle' | 'equipment' | 'other'>('room');
  const [capacity, setCapacity] = useState('');
  const [location, setLocation] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [description, setDescription] = useState('');
  const [isActive, setIsActive] = useState(true);

  // Delete confirm modal state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const fetchResources = async () => {
    try {
      setLoading(true);
      const data = await apiCall('GET', '/admin/resources');
      setResources(data || []);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResources();
  }, []);

  const toggleSchedule = async (id: string) => {
    const nextOpen = !openSchedules[id];
    setOpenSchedules((prev) => ({ ...prev, [id]: nextOpen }));

    if (nextOpen && !schedulesData[id]) {
      setSchedulesLoading((prev) => ({ ...prev, [id]: true }));
      try {
        const todayStr = new Date().toISOString().split('T')[0];
        const slots = await apiCall('GET', `/resources/${id}/availability?date=${todayStr}`);
        setSchedulesData((prev) => ({ ...prev, [id]: slots || [] }));
      } catch {
        showToast('Failed to check today\'s schedule');
      } finally {
        setSchedulesLoading((prev) => ({ ...prev, [id]: false }));
      }
    }
  };

  const handleOpenAddSheet = () => {
    setName('');
    setType('room');
    setCapacity('');
    setLocation('');
    setImageUrl('');
    setDescription('');
    setIsActive(true);
    setIsAddSheetOpen(true);
  };

  const handleOpenEditSheet = (r: Resource) => {
    setEditingResource(r);
    setName(r.name);
    setType(r.type);
    setCapacity(r.capacity !== undefined && r.capacity !== null ? String(r.capacity) : '');
    setLocation(r.location || '');
    setImageUrl(r.image_url || '');
    setDescription(r.description || '');
    setIsActive(r.is_active);
    setIsEditSheetOpen(true);
  };

  const handleAddResource = async () => {
    if (!name.trim()) {
      showToast('Name is required');
      return;
    }
    showToast('Saving…');
    try {
      const capVal = capacity.trim() ? parseInt(capacity, 10) : null;
      await apiCall('POST', '/admin/resources', {
        name: name.trim(),
        type,
        description: description.trim() || null,
        capacity: capVal,
        location: location.trim() || null,
        image_url: imageUrl.trim() || null,
      });
      showToast('✓ Resource added successfully!');
      setIsAddSheetOpen(false);
      await fetchResources();
    } catch {
      showToast('Failed to add resource');
    }
  };

  const handleUpdateResource = async () => {
    if (!editingResource) return;
    if (!name.trim()) {
      showToast('Name is required');
      return;
    }
    showToast('Updating…');
    try {
      const capVal = capacity.trim() ? parseInt(capacity, 10) : null;
      await apiCall('PATCH', `/admin/resources/${editingResource.id}`, {
        name: name.trim(),
        description: description.trim() || null,
        is_active: isActive,
        capacity: capVal,
        location: location.trim() || null,
        image_url: imageUrl.trim() || null,
      });
      showToast('✓ Resource updated!');
      setIsEditSheetOpen(false);
      await fetchResources();
    } catch {
      showToast('Failed to update resource');
    }
  };

  const handleDeleteResource = async () => {
    if (!editingResource) return;
    showToast('Deleting…');
    try {
      await apiCall('DELETE', `/admin/resources/${editingResource.id}`);
      showToast('✓ Resource deleted!');
      setShowDeleteConfirm(false);
      setIsEditSheetOpen(false);
      await fetchResources();
    } catch {
      showToast('Failed to delete resource');
    }
  };

  if (loading) {
    return (
      <div className="loader">
        <div className="spinner"></div>
        <p className="loader-text">Loading resources…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <div className="empty-icon">⚠️</div>
        <h3>Failed to load resources</h3>
        <button className="btn-retry" onClick={fetchResources}>↻ Retry</button>
      </div>
    );
  }

  return (
    <div style={{ paddingBottom: '60px' }}>
      <div className="section-hd">
        <h2>Registered Resources</h2>
        <span className="count-chip">{resources.length}</span>
      </div>

      <div className="resource-list">
        {resources.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🏢</div>
            <h3>No resources registered</h3>
            <p>Tap the button below to add your first resource.</p>
          </div>
        ) : (
          resources.map((r) => {
            const hasTimeline = r.type === 'room' || r.type === 'vehicle';
            const isSchedOpen = openSchedules[r.id] || false;
            const isSchedLoading = schedulesLoading[r.id] || false;
            const slots = schedulesData[r.id] || [];

            return (
              <div key={r.id} className="resource-card" style={{ display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'stretch' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                  {r.image_url && (
                    <img
                      src={r.image_url}
                      style={{ width: '50px', height: '50px', objectFit: 'cover', borderRadius: '8px', border: '1px solid var(--slate-200)', marginTop: '2px' }}
                      alt={r.name}
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                  )}
                  <div className="resource-info" style={{ flex: 1 }}>
                    <span className="resource-name">{r.name}</span>
                    <span className="resource-desc">
                      {r.description ? r.description : 'No description'}
                      <br />
                      <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                        {r.type.replace('_', ' ')}
                      </span>
                      {r.location && ` · 📍 ${r.location}`}
                      {r.capacity && ` · 👥 Cap: ${r.capacity}`}
                    </span>
                  </div>
                  <div className="resource-actions" style={{ flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
                    <span className={`badge badge-${r.is_active ? 'approved' : 'rejected'}`} style={{ margin: 0 }}>
                      {r.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginTop: '4px' }}>
                      {hasTimeline && (
                        <span
                          className="badge badge-pending"
                          onClick={() => toggleSchedule(r.id)}
                          style={{
                            margin: 0,
                            cursor: 'pointer',
                            fontSize: '11px',
                            padding: '4px 8px',
                            borderRadius: '6px',
                            background: isSchedOpen ? 'var(--green-light)' : '#fffbeb',
                            color: isSchedOpen ? 'var(--green-dark)' : '#92400e',
                            border: `1px solid ${isSchedOpen ? 'var(--green)' : '#fde68a'}`,
                          }}
                        >
                          📅 Schedule
                        </span>
                      )}
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => handleOpenEditSheet(r)}
                        style={{ width: 'auto', margin: 0, padding: '4px 10px', fontSize: '12px', borderRadius: '6px', height: '22px', lineHeight: '22px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}
                      >
                        Edit
                      </button>
                    </div>
                  </div>
                </div>

                {/* Collapsible Timeline */}
                {hasTimeline && isSchedOpen && (
                  <div
                    id={`sched-container-${r.id}`}
                    style={{ borderTop: '1px dashed var(--slate-200)', paddingTop: '8px', marginTop: '4px' }}
                  >
                    {isSchedLoading ? (
                      <div style={{ fontSize: '11px', color: 'var(--slate-400)', display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 0' }}>
                        <div className="spinner spinner-sm" style={{ borderWidth: '2px', width: '12px', height: '12px', margin: 0 }}></div>
                        Checking availability…
                      </div>
                    ) : (
                      <Timeline slots={slots} isCompact={true} />
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Floating Action Button */}
      <button className="fab" onClick={handleOpenAddSheet}>
        <span>＋</span> Add Resource
      </button>

      {/* Add Resource Sheet */}
      <BottomSheet isOpen={isAddSheetOpen} onClose={() => setIsAddSheetOpen(false)} title="Add New Resource">
        <div style={{ textAlign: 'left', width: '100%', marginTop: '10px', maxHeight: '380px', overflowY: 'auto', paddingRight: '4px' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="res-name">
              Resource Name <span className="req">*</span>
            </label>
            <input
              className="form-control"
              id="res-name"
              placeholder="e.g. Conference Room A"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px' }}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Type <span className="req">*</span></label>
            <select
              id="res-type"
              className="form-control"
              value={type}
              onChange={(e) => setType(e.target.value as any)}
              style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px', height: 'auto' }}
            >
              <option value="room">🏢 Room</option>
              <option value="vehicle">🚗 Vehicle</option>
              <option value="equipment">🛠️ Equipment</option>
              <option value="other">📦 Other</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="res-capacity">Capacity</label>
            <input
              type="number"
              className="form-control"
              id="res-capacity"
              placeholder="e.g. 10 (optional)"
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
              style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px' }}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="res-location">Location</label>
            <input
              className="form-control"
              id="res-location"
              placeholder="e.g. 2nd Floor, Building B"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px' }}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="res-image-url">Image URL</label>
            <input
              className="form-control"
              id="res-image-url"
              placeholder="https://example.com/image.jpg"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px' }}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="res-desc">Description</label>
            <textarea
              className="form-control"
              id="res-desc"
              placeholder="Details or amenities…"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px' }}
            />
          </div>
        </div>
        <button className="btn btn-primary" onClick={handleAddResource} style={{ marginTop: '14px' }}>
          Save Resource
        </button>
        <button className="btn btn-ghost" onClick={() => setIsAddSheetOpen(false)} style={{ marginTop: '8px' }}>
          Cancel
        </button>
      </BottomSheet>

      {/* Edit Resource Sheet */}
      <BottomSheet isOpen={isEditSheetOpen} onClose={() => setIsEditSheetOpen(false)} title="Edit Resource">
        <div style={{ textAlign: 'left', width: '100%', marginTop: '10px', maxHeight: '380px', overflowY: 'auto', paddingRight: '4px' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="edit-res-name">
              Resource Name <span className="req">*</span>
            </label>
            <input
              className="form-control"
              id="edit-res-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px' }}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="edit-res-capacity">Capacity</label>
            <input
              type="number"
              className="form-control"
              id="edit-res-capacity"
              value={capacity}
              placeholder="e.g. 10"
              onChange={(e) => setCapacity(e.target.value)}
              style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px' }}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="edit-res-location">Location</label>
            <input
              className="form-control"
              id="edit-res-location"
              value={location}
              placeholder="e.g. Building A"
              onChange={(e) => setLocation(e.target.value)}
              style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px' }}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="edit-res-image-url">Image URL</label>
            <input
              className="form-control"
              id="edit-res-image-url"
              value={imageUrl}
              placeholder="https://example.com/image.jpg"
              onChange={(e) => setImageUrl(e.target.value)}
              style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px' }}
            />
          </div>
          <div className="form-group">
            <label className="form-label" htmlFor="edit-res-desc">Description</label>
            <textarea
              className="form-control"
              id="edit-res-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{ border: '1.5px solid var(--slate-200)', borderRadius: '10px', padding: '10px' }}
            />
          </div>
          <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px' }}>
            <input
              type="checkbox"
              id="edit-res-active"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              style={{ width: '18px', height: '18px', cursor: 'pointer' }}
            />
            <label htmlFor="edit-res-active" style={{ fontWeight: 600, cursor: 'pointer', fontSize: '13px', color: 'var(--slate-700)' }}>
              Active (Available for booking)
            </label>
          </div>
        </div>
        <button className="btn btn-primary" onClick={handleUpdateResource} style={{ marginTop: '14px' }}>
          Update Resource
        </button>
        <button className="btn btn-danger" onClick={() => setShowDeleteConfirm(true)} style={{ marginTop: '8px' }}>
          Delete Resource
        </button>
        <button className="btn btn-ghost" onClick={() => setIsEditSheetOpen(false)} style={{ marginTop: '8px' }}>
          Cancel
        </button>
      </BottomSheet>

      {/* Delete confirmation modal */}
      <BottomSheet isOpen={showDeleteConfirm} onClose={() => setShowDeleteConfirm(false)} title="Delete Resource?">
        <div className="sheet-desc">
          Are you sure you want to permanently delete this resource? Any requests referencing this resource will keep their records but will no longer be linked to it.
        </div>
        <button className="btn btn-danger" onClick={handleDeleteResource}>
          Delete It
        </button>
        <button className="btn btn-ghost" onClick={() => setShowDeleteConfirm(false)} style={{ marginTop: '8px' }}>
          Cancel
        </button>
      </BottomSheet>
    </div>
  );
};
