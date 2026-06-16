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


class WeeklyReport(BaseModel):
    week: str
    total: int


class AdminStatsResponse(BaseModel):
    total_requests: StatusCounts
    type_distribution: dict[str, int]
    monthly_reports: list[MonthlyReport]
    weekly_reports: list[WeeklyReport]
