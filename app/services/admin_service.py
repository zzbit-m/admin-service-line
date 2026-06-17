from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.request import ServiceRequest
from app.models.resource import Resource

VALID_TRANSITIONS = {
    "pending": {"approved", "rejected"},
    "approved": {"cancelled"},
    "rejected": set(),
    "cancelled": set(),
}


async def list_all_requests(
    db: AsyncSession,
    status_filter: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    skip: int = 0,
    limit: int = 20,
) -> list[ServiceRequest]:
    from datetime import datetime, time, timezone

    query = select(ServiceRequest).options(selectinload(ServiceRequest.user))
    if status_filter:
        query = query.where(ServiceRequest.status == status_filter)

    if start_date:
        try:
            if "T" in start_date or " " in start_date:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            else:
                start_dt = datetime.combine(datetime.fromisoformat(start_date).date(), time.min)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            query = query.where(ServiceRequest.created_at >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            if "T" in end_date or " " in end_date:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            else:
                end_dt = datetime.combine(datetime.fromisoformat(end_date).date(), time.max)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            query = query.where(ServiceRequest.created_at <= end_dt)
        except ValueError:
            pass

    col_map = {
        "created_at": ServiceRequest.created_at,
        "priority": ServiceRequest.priority,
        "status": ServiceRequest.status,
        "request_type": ServiceRequest.request_type,
        "title": ServiceRequest.title,
    }
    col = col_map.get(sort_by, ServiceRequest.created_at)
    if sort_order == "asc":
        query = query.order_by(col.asc(), ServiceRequest.created_at.asc())
    else:
        query = query.order_by(col.desc(), ServiceRequest.created_at.desc())

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_request_by_id(db: AsyncSession, request_id: UUID) -> ServiceRequest:
    result = await db.execute(select(ServiceRequest).options(selectinload(ServiceRequest.user)).where(ServiceRequest.id == request_id))
    sr = result.scalar_one_or_none()
    if sr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return sr


async def update_request_status(db: AsyncSession, request_id: UUID, new_status: str, admin_id: UUID, admin_note: str | None = None) -> ServiceRequest:
    result = await db.execute(
        select(ServiceRequest)
        .options(selectinload(ServiceRequest.user))
        .where(ServiceRequest.id == request_id)
    )
    sr = result.scalar_one_or_none()
    if sr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    allowed = VALID_TRANSITIONS.get(sr.status)
    if allowed is None or new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{sr.status}' to '{new_status}'",
        )

    sr.status = new_status
    if admin_note is not None:
        sr.admin_note = admin_note
    
    from datetime import datetime, timezone
    sr.resolved_by = admin_id
    sr.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(sr)
    return sr


async def list_resources(db: AsyncSession) -> list[Resource]:
    result = await db.execute(select(Resource).order_by(Resource.created_at.desc()))
    return list(result.scalars().all())


async def create_resource(
    db: AsyncSession,
    name: str,
    type: str,
    description: str | None = None,
    capacity: int | None = None,
    location: str | None = None,
    image_url: str | None = None,
) -> Resource:
    resource = Resource(
        name=name,
        type=type,
        description=description,
        capacity=capacity,
        location=location,
        image_url=image_url,
    )
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource


async def update_resource(
    db: AsyncSession,
    resource_id: UUID,
    name: str | None,
    description: str | None,
    is_active: bool | None,
    capacity: int | None = None,
    location: str | None = None,
    image_url: str | None = None,
) -> Resource:
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    if name is not None:
        resource.name = name
    if description is not None:
        resource.description = description
    if is_active is not None:
        resource.is_active = is_active
    if capacity is not None:
        resource.capacity = capacity
    if location is not None:
        resource.location = location
    if image_url is not None:
        resource.image_url = image_url

    from datetime import datetime, timezone
    resource.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(resource)
    return resource


async def delete_resource(db: AsyncSession, resource_id: UUID) -> None:
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    
    from sqlalchemy import update
    await db.execute(
        update(ServiceRequest)
        .where(ServiceRequest.resource_id == resource_id)
        .values(resource_id=None)
    )
    await db.delete(resource)
    await db.commit()



async def get_admin_stats(db: AsyncSession) -> dict:
    from sqlalchemy import func, literal_column
    from app.models.user import User

    # 1. Total requests by status
    status_res = await db.execute(
        select(ServiceRequest.status, func.count(ServiceRequest.id)).group_by(ServiceRequest.status)
    )
    status_map = {row[0]: row[1] for row in status_res.all()}

    # 2. Request type distribution
    type_res = await db.execute(
        select(ServiceRequest.request_type, func.count(ServiceRequest.id)).group_by(ServiceRequest.request_type)
    )
    type_map = {row[0] or "other": row[1] for row in type_res.all()}

    # 3. Monthly reports (last 6 months)
    month_trunc = func.date_trunc(literal_column("'month'"), ServiceRequest.created_at)
    monthly_res = await db.execute(
        select(
            month_trunc.label('month_date'),
            func.count(ServiceRequest.id).label('total'),
            func.count(ServiceRequest.id).filter(ServiceRequest.status == 'approved').label('approved'),
            func.count(ServiceRequest.id).filter(ServiceRequest.status == 'rejected').label('rejected'),
            func.count(ServiceRequest.id).filter(ServiceRequest.status == 'cancelled').label('cancelled')
        )
        .group_by(month_trunc)
        .order_by(month_trunc)
    )
    monthly_list = [
        {
            "month": row.month_date.strftime('%b %Y') if row.month_date else "Unknown",
            "total": row.total,
            "approved": row.approved,
            "rejected": row.rejected,
            "cancelled": row.cancelled
        }
        for row in monthly_res.all()
    ][-6:]

    # 4. Weekly reports (last 4 weeks)
    week_trunc = func.date_trunc(literal_column("'week'"), ServiceRequest.created_at)
    weekly_res = await db.execute(
        select(
            week_trunc.label('week_date'),
            func.count(ServiceRequest.id).label('total')
        )
        .group_by(week_trunc)
        .order_by(week_trunc)
    )
    weekly_list = []
    for row in weekly_res.all():
        if row.week_date:
            isocal = row.week_date.isocalendar()
            week_str = f"{isocal[0]}-W{isocal[1]:02d}"
        else:
            week_str = "Unknown"
        weekly_list.append({
            "week": week_str,
            "total": row.total
        })
    weekly_list = weekly_list[-4:]

    # 5. Average response time in hours
    avg_res = await db.execute(
        select(
            func.avg(
                func.extract('epoch', ServiceRequest.resolved_at - ServiceRequest.created_at) / 3600.0
            )
        ).where(ServiceRequest.resolved_at.isnot(None))
    )
    avg_hours = avg_res.scalar()
    avg_response_hours = round(float(avg_hours), 2) if avg_hours is not None else None

    # 6. Top Users
    top_users_res = await db.execute(
        select(
            User.id,
            func.coalesce(User.full_name, User.email).label('full_name'),
            func.count(ServiceRequest.id).label('request_count')
        )
        .join(ServiceRequest, ServiceRequest.user_id == User.id)
        .group_by(User.id)
        .order_by(func.count(ServiceRequest.id).desc())
        .limit(5)
    )
    top_users_list = [
        {
            "user_id": str(row.id),
            "full_name": row.full_name,
            "request_count": row.request_count
        }
        for row in top_users_res.all()
    ]

    # 7. Resource Utilization
    resource_res = await db.execute(
        select(
            Resource.id,
            Resource.name,
            Resource.type,
            func.count(ServiceRequest.id).label('booking_count')
        )
        .join(ServiceRequest, ServiceRequest.resource_id == Resource.id)
        .group_by(Resource.id)
        .order_by(func.count(ServiceRequest.id).desc())
        .limit(5)
    )
    resource_list = [
        {
            "resource_id": str(row.id),
            "resource_name": row.name,
            "resource_type": row.type,
            "booking_count": row.booking_count
        }
        for row in resource_res.all()
    ]

    return {
        "total_requests": {
            "pending": status_map.get("pending", 0),
            "approved": status_map.get("approved", 0),
            "rejected": status_map.get("rejected", 0),
            "cancelled": status_map.get("cancelled", 0),
        },
        "type_distribution": type_map,
        "monthly_reports": monthly_list,
        "weekly_reports": weekly_list,
        "avg_response_hours": avg_response_hours,
        "top_users": top_users_list,
        "resource_utilization": resource_list,
    }


async def export_requests_csv(
    db: AsyncSession,
    status_filter: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> str:
    from datetime import datetime, time, timezone
    from sqlalchemy.orm import selectinload
    
    query = select(ServiceRequest).options(
        selectinload(ServiceRequest.user),
        selectinload(ServiceRequest.resource)
    )
    if status_filter:
        query = query.where(ServiceRequest.status == status_filter)

    if start_date:
        try:
            if "T" in start_date or " " in start_date:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            else:
                start_dt = datetime.combine(datetime.fromisoformat(start_date).date(), time.min)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)
            query = query.where(ServiceRequest.created_at >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            if "T" in end_date or " " in end_date:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            else:
                end_dt = datetime.combine(datetime.fromisoformat(end_date).date(), time.max)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            query = query.where(ServiceRequest.created_at <= end_dt)
        except ValueError:
            pass

    col_map = {
        "created_at": ServiceRequest.created_at,
        "priority": ServiceRequest.priority,
        "status": ServiceRequest.status,
        "request_type": ServiceRequest.request_type,
        "title": ServiceRequest.title,
    }
    col = col_map.get(sort_by, ServiceRequest.created_at)
    if sort_order == "asc":
        query = query.order_by(col.asc(), ServiceRequest.created_at.asc())
    else:
        query = query.order_by(col.desc(), ServiceRequest.created_at.desc())

    result = await db.execute(query)
    requests = result.scalars().all()

    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Request ID", "User Name", "User Email", "Title", "Description", 
        "Request Type", "Priority", "Status", "Resource Name", "Resource Type", 
        "Resource Location", "Start Time", "End Time", "Resolved At", "Created At"
    ])
    
    for r in requests:
        user_name = r.user.full_name or r.user.email if r.user else ""
        user_email = r.user.email if r.user else ""
        res_name = r.resource.name if r.resource else ""
        res_type = r.resource.type if r.resource else ""
        res_loc = r.resource.location if r.resource else ""
        
        writer.writerow([
            str(r.id),
            user_name,
            user_email,
            r.title,
            r.description or "",
            r.request_type or "",
            r.priority,
            r.status,
            res_name,
            res_type,
            res_loc,
            r.start_time.isoformat() if r.start_time else "",
            r.end_time.isoformat() if r.end_time else "",
            r.resolved_at.isoformat() if r.resolved_at else "",
            r.created_at.isoformat() if r.created_at else ""
        ])
        
    return output.getvalue()


async def export_stats_csv(db: AsyncSession) -> str:
    stats = await get_admin_stats(db)
    
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Metric Category", "Metric Key / Dimension", "Metric Value"])
    
    # 1. Total Requests
    for k, v in stats["total_requests"].items():
        writer.writerow(["Total Requests", f"status_{k}", v])
        
    # 2. Type Distribution
    for k, v in stats["type_distribution"].items():
        writer.writerow(["Request Type Distribution", k, v])
        
    # 3. Monthly Reports
    for m in stats["monthly_reports"]:
        writer.writerow(["Monthly Trend (Total)", m["month"], m["total"]])
        writer.writerow(["Monthly Trend (Approved)", m["month"], m["approved"]])
        writer.writerow(["Monthly Trend (Rejected)", m["month"], m.get("rejected", 0)])
        writer.writerow(["Monthly Trend (Cancelled)", m["month"], m.get("cancelled", 0)])
        
    # 4. Weekly Reports
    for w in stats["weekly_reports"]:
        writer.writerow(["Weekly Trend (Total)", w["week"], w["total"]])
        
    # 5. Average Response Time
    writer.writerow(["Performance", "avg_response_hours", stats["avg_response_hours"] or "N/A"])
    
    # 6. Top Users
    for idx, u in enumerate(stats["top_users"], 1):
        writer.writerow(["Top Requisitioner", f"Rank {idx} - {u['full_name']} (ID: {u['user_id']})", u["request_count"]])
        
    # 7. Resource Utilization
    for idx, ru in enumerate(stats["resource_utilization"], 1):
        writer.writerow(["Resource Booking Count", f"Rank {idx} - {ru['resource_name']} ({ru['resource_type']})", ru["booking_count"]])
        
    return output.getvalue()
