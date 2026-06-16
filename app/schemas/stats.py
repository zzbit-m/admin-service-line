from pydantic import BaseModel


class StatusCounts(BaseModel):
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    cancelled: int = 0


class MonthlyReport(BaseModel):
    month: str
    total: int
    approved: int
    rejected: int = 0
    cancelled: int = 0


class WeeklyReport(BaseModel):
    week: str
    total: int


class TopUserReport(BaseModel):
    user_id: str
    full_name: str
    request_count: int


class ResourceUtilization(BaseModel):
    resource_id: str
    resource_name: str
    resource_type: str
    booking_count: int


class AdminStatsResponse(BaseModel):
    total_requests: StatusCounts
    type_distribution: dict[str, int]
    monthly_reports: list[MonthlyReport]
    weekly_reports: list[WeeklyReport]
    avg_response_hours: float | None = None
    top_users: list[TopUserReport] = []
    resource_utilization: list[ResourceUtilization] = []
