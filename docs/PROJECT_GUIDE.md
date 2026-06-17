# Admin Service Portal - Project Guide

This guide describes the architecture, key capabilities, and usage instructions for the **Admin Service Portal**.

---

## 1. System Overview

The Admin Service Portal is a premium request-management and scheduling web application integrated with **LINE LIFF** and **n8n workflows**. It allows users to submit resource bookings (rooms and vehicles), track request progress, and converse with admins. Admins can manage requests, monitor weekly/monthly stats, and control available resources.

```
+-------------------------------------------------------------+
|                         LIFF Client                         |
|   (User Requests / Admin Dashboard / Resources / Reports)   |
+-------------------------------------------------------------+
                              |
                              v
                      +---------------+
                      | Proxy Server  | (Port 3000)
                      +---------------+
                              |
                              v
                      +---------------+
                      | FastAPI App   | (Port 8001)
                      +---------------+
                         |    |    |
        +----------------+    |    +----------------+
        |                     v                     |
        v                +----------+               v
+--------------+         |  Redis   |        +--------------+
|  PostgreSQL  |         | (ARQ/Key)|        |  MinIO (S3)  |
+--------------+         +----------+        +--------------+
                              |
                              v
                      +---------------+
                      |  ARQ Worker   |
                      +---------------+
                              |
                              v
                      +---------------+
                      | LINE API / Bot|
                      +---------------+
```

---

## 2. Key Features

### 🏢 Resource Management (New)
Allows administrators to add and edit resources directly from the web portal.
- **List Resources**: View all active/inactive resources with live type tags.
- **Add Resources**: Click the floating action button (FAB) to add a resource with a modal form.
- **Strict Database Validation**: Resolves type mismatch (validates options `room` or `vehicle` to prevent 422 errors).
- **Edit Resources**: Toggle the activation status or update descriptions.

![Resource Management UI](file:///C:/Users/Admin/.gemini/antigravity-ide/brain/fd4a3780-f202-4b67-ac98-b6ae8e862198/resource_management.png)

---

### 📊 Reports & Statistics Dashboard (New)
Aggregates and visualizes request metrics for quick analytics.
- **Status Cards**: High-level summary of Total Requests, Pending Approval, Approved, and Approval Rate (Completion Rate).
- **Request Type Distribution**: Elegant, styled horizontal bar charts representing bookings across types (`room_booking`, `vehicle_booking`, `maintenance`, and `other`).
- **Monthly trends**: Clean data grid showing total requests versus approved requests over the last 6 months.
- **Weekly trends**: Displays the total count of requests per calendar week (e.g., `2026-W24`).
- **Postgres Optimization**: Built using safe SQLAlchemy `date_trunc` aggregations paired with custom Python rendering to bypass GroupingErrors.

![Reports Dashboard UI](file:///C:/Users/Admin/.gemini/antigravity-ide/brain/fd4a3780-f202-4b67-ac98-b6ae8e862198/reports_dashboard.png)

---

### 💬 Premium LINE Flex Notifications
Converts plain text push notifications into gorgeous interactive bubbles with contextual colors and structured key-value parameters.
- **Status Banners**:
  - Green banner for Approved status.
  - Red banner for Rejected status.
  - Charcoal banner for Cancelled status.
  - Soft blue banner for New Comments.
- **Review Buttons**: Directly includes a deep link to the specific request inside the LINE LIFF app, driving immediate user action.

---

### 🌙 Premium Dark Mode (New)
Provides a modern dark appearance for both user and admin roles.
- **Persistent Preferences**: Saves the layout theme selection (`light` or `dark`) in the browser's `localStorage` to prevent color flashes on reload.
- **Dynamic Themes**: Styled using standard CSS variables (`var(--white)`, `var(--slate-50)`, etc.) for smooth and harmonious role transitions.

---

### 📅 Resource Booking Timeline (New)
Helps users preview resource schedules and choose non-overlapping booking slots.
- **Visual Schedule View**: Generates a horizontal 24h schedule progress bar with red block indicators representing occupied intervals and green blocks indicating availability.
- **Client-Side Verification**: Intercepts booking submission if selected times conflict with approved slots.

---

### ⚡ LINE Bot Inline Quick Approvals (New)
Empowers administrators to review, approve, or reject user booking requests directly within their chat.
- **Interactive Review Cards**: Typing `pending` returns a carousel of pending requests directly inside the chat.
- **LINE Postback Handlers**: Admins can tap **Approve** or **Reject** inline, changing status and dispatching notification triggers without loading the LIFF client.
- **Dynamic Display Name Sync**: Queries LINE's Messaging API user profile details on message events to replace placeholder user IDs (`line_...`) with real user display names, updating the PostgreSQL database automatically.

---

## 3. Developer & Setup Notes

### Port Configuration
- **FastAPI Backend**: `http://127.0.0.1:8001`
- **Proxy Server (LIFF)**: `http://localhost:3000`
- **LINE LIFF Sandbox Access**: `http://localhost:3000/liff-app.html?dev=1`

### Running the Services
1. **FastAPI Server (Auto-Reloading)**
   ```powershell
   venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8001 --reload
   ```
2. **ARQ Notification Worker**
   ```powershell
   venv\Scripts\python.exe -m arq app.worker.WorkerSettings
   ```
3. **Proxy Server**
   ```powershell
   venv\Scripts\python.exe proxy_server.py 3000
   ```
