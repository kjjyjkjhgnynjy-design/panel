from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Admin

HIERARCHY_QUERY_BATCH_SIZE = 500


async def get_admin_ancestor_map(db: AsyncSession, admin_ids: Iterable[int]) -> dict[int, list[int]]:
    """Return each admin's lineage, starting with the admin and ending at the root."""
    requested_ids = {int(admin_id) for admin_id in admin_ids if admin_id is not None}
    if not requested_ids:
        return {}

    parent_by_id: dict[int, int | None] = {}
    frontier = requested_ids
    while frontier:
        frontier_ids = list(frontier)
        rows = []
        for offset in range(0, len(frontier_ids), HIERARCHY_QUERY_BATCH_SIZE):
            result = await db.execute(
                select(Admin.id, Admin.parent_admin_id).where(
                    Admin.id.in_(frontier_ids[offset : offset + HIERARCHY_QUERY_BATCH_SIZE])
                )
            )
            rows.extend(result.all())
        next_frontier: set[int] = set()
        for admin_id, parent_admin_id in rows:
            parent_by_id[admin_id] = parent_admin_id
            if parent_admin_id is not None and parent_admin_id not in parent_by_id:
                next_frontier.add(parent_admin_id)
        frontier = next_frontier

    ancestor_map: dict[int, list[int]] = {}
    for admin_id in requested_ids:
        lineage: list[int] = []
        current_id: int | None = admin_id
        seen: set[int] = set()
        while current_id is not None and current_id not in seen:
            seen.add(current_id)
            lineage.append(current_id)
            current_id = parent_by_id.get(current_id)
        ancestor_map[admin_id] = lineage
    return ancestor_map


async def get_admin_descendant_ids(db: AsyncSession, root_admin_id: int, *, include_self: bool = True) -> set[int]:
    """Return an admin and all descendants, or descendants only when include_self is false."""
    descendants = {root_admin_id} if include_self else set()
    frontier = {root_admin_id}
    while frontier:
        frontier_ids = list(frontier)
        child_ids: set[int] = set()
        for offset in range(0, len(frontier_ids), HIERARCHY_QUERY_BATCH_SIZE):
            result = await db.execute(
                select(Admin.id).where(
                    Admin.parent_admin_id.in_(frontier_ids[offset : offset + HIERARCHY_QUERY_BATCH_SIZE])
                )
            )
            child_ids.update(result.scalars().all())
        next_frontier = child_ids - descendants
        descendants.update(next_frontier)
        frontier = next_frontier
    return descendants


async def adjust_admin_traffic_counters(db: AsyncSession, direct_changes: dict[int, int]) -> None:
    """Apply direct-owner traffic changes to each affected admin and every ancestor."""
    if not direct_changes:
        return

    ancestor_map = await get_admin_ancestor_map(db, direct_changes)
    aggregate_changes: dict[int, int] = {}
    for admin_id, traffic_change in direct_changes.items():
        for ancestor_id in ancestor_map.get(admin_id, [admin_id]):
            aggregate_changes[ancestor_id] = aggregate_changes.get(ancestor_id, 0) + traffic_change

    if not aggregate_changes:
        return

    affected_ids = list(aggregate_changes)
    for offset in range(0, len(affected_ids), HIERARCHY_QUERY_BATCH_SIZE):
        admins = (
            await db.scalars(
                select(Admin).where(
                    Admin.id.in_(affected_ids[offset : offset + HIERARCHY_QUERY_BATCH_SIZE])
                )
            )
        ).all()
        for admin in admins:
            admin.used_traffic = int(admin.used_traffic or 0) + aggregate_changes[admin.id]
