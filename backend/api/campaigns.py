"""
Campaign Management API Router — Outbound Campaign CRUD & Task Generation.

This module provides endpoints for scheduling, monitoring, and cancelling batch outbound call campaigns.

Endpoints:
    - GET /api/campaigns: Paginated list of campaigns with status counts.
    - POST /api/campaigns: Creates campaign and generates call tasks (Admin required).
    - GET /api/campaigns/{id}: Campaign details and status breakdown.
    - PATCH /api/campaigns/{id}/cancel: Cancels pending campaign tasks (Admin required).
    - GET /api/campaigns/{id}/tasks: Paginated call task breakdown.

Dependencies:
    - fastapi >= 0.111
    - sqlalchemy >= 2.0
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user, require_admin
from backend.database.models import CallCampaign, CallScript, CallTask, StaffUser, utc_now
from backend.database.session import get_async_session, get_sync_session
from backend.scheduler.campaign_runner import CampaignRunner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


# ------------------------------------------------------------------------------
# Pydantic Schemas
# ------------------------------------------------------------------------------
class CampaignCreateRequest(BaseModel):
    """Payload for creating a new outbound call campaign."""

    name: str = Field(..., example="BTech 2026 Semester Fee Reminder")
    script_id: int = Field(..., example=1)
    target_filter: Dict[str, Any] = Field(
        default_factory=dict, example={"department": "CS", "semester": 4}
    )
    scheduled_at: datetime = Field(..., example="2026-10-15T10:00:00Z")
    max_retries: int = Field(default=2, ge=0, le=5)
    retry_delay_min: int = Field(default=60, ge=5, le=1440)


class CampaignResponse(BaseModel):
    """Public campaign data representation."""

    id: int
    name: str
    script_id: int
    target_filter: Dict[str, Any]
    scheduled_at: datetime
    max_retries: int
    retry_delay_min: int
    status: str
    created_by: Optional[int]
    created_at: datetime
    task_counts: Optional[Dict[str, int]] = None


class PaginatedCampaigns(BaseModel):
    """Paginated list wrapper for campaigns."""

    total: int
    page: int
    limit: int
    items: List[CampaignResponse]


# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------
@router.get("", response_model=PaginatedCampaigns)
async def list_campaigns(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    session: AsyncSession = Depends(get_async_session),
    current_user: StaffUser = Depends(get_current_user),
) -> PaginatedCampaigns:
    """Returns a paginated list of campaigns filtered by status."""
    query = select(CallCampaign)
    if status_filter:
        query = query.where(CallCampaign.status == status_filter)

    # Count total
    count_stmt = select(func.count()).select_from(query.subquery())
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one()

    # Paginate
    query = query.order_by(CallCampaign.created_at.desc()).offset((page - 1) * limit).limit(limit)
    res = await session.execute(query)
    campaigns = res.scalars().all()

    items = [CampaignResponse.model_validate(c, from_attributes=True) for c in campaigns]
    return PaginatedCampaigns(total=total, page=page, limit=limit, items=items)


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreateRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: StaffUser = Depends(require_admin),
) -> CampaignResponse:
    """Creates a campaign and generates CallTask records for matching students (Admin required)."""
    # Verify script exists
    script_res = await session.execute(select(CallScript).where(CallScript.id == payload.script_id))
    script = script_res.scalar_one_or_none()
    if not script or not script.is_active:
        raise HTTPException(status_code=400, detail="Invalid or inactive CallScript ID.")

    campaign = CallCampaign(
        name=payload.name,
        script_id=payload.script_id,
        target_filter=payload.target_filter,
        scheduled_at=payload.scheduled_at,
        max_retries=payload.max_retries,
        retry_delay_min=payload.retry_delay_min,
        status="pending",
        created_by=current_user.id,
    )
    session.add(campaign)
    await session.commit()
    await session.refresh(campaign)

    # Generate task rows synchronously via NullPool engine
    def _sync_generate_tasks():
        with get_sync_session() as sync_db:
            return CampaignRunner.generate_tasks_for_campaign(campaign.id, sync_db)

    task_count = await session.run_sync(lambda _: _sync_generate_tasks())
    logger.info("Campaign ID %d created by %s. Generated %d tasks.", campaign.id, current_user.email, task_count)

    response = CampaignResponse.model_validate(campaign, from_attributes=True)
    response.task_counts = {"total": task_count, "pending": task_count}
    return response


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: StaffUser = Depends(get_current_user),
) -> CampaignResponse:
    """Returns detailed campaign metadata and task status summary."""
    res = await session.execute(select(CallCampaign).where(CallCampaign.id == campaign_id))
    campaign = res.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    # Calculate status counts
    count_stmt = (
        select(CallTask.status, func.count(CallTask.id))
        .where(CallTask.campaign_id == campaign_id)
        .group_by(CallTask.status)
    )
    count_res = await session.execute(count_stmt)
    status_counts = {row[0]: row[1] for row in count_res.all()}

    response = CampaignResponse.model_validate(campaign, from_attributes=True)
    response.task_counts = status_counts
    return response


@router.patch("/{campaign_id}/cancel", response_model=CampaignResponse)
async def cancel_campaign(
    campaign_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: StaffUser = Depends(require_admin),
) -> CampaignResponse:
    """Cancels a pending/running campaign and updates pending tasks to 'cancelled' (Admin required)."""
    res = await session.execute(select(CallCampaign).where(CallCampaign.id == campaign_id))
    campaign = res.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    campaign.status = "cancelled"

    # Cancel pending tasks
    await session.execute(
        update(CallTask)
        .where(CallTask.campaign_id == campaign_id, CallTask.status.in_(["pending", "ringing"]))
        .values(status="cancelled", outcome="cancelled")
    )
    await session.commit()
    await session.refresh(campaign)

    logger.info("Campaign ID %d cancelled by %s", campaign_id, current_user.email)
    return CampaignResponse.model_validate(campaign, from_attributes=True)
