from __future__ import annotations

from datetime import date

from app.schemas import CropType, GrowthStage, GrowthStageResponse


DEFAULT_TOMATO_STAGE_DAYS: dict[GrowthStage, int] = {
    GrowthStage.INITIAL: 30,
    GrowthStage.DEVELOPMENT: 40,
    GrowthStage.MID_SEASON: 45,
    GrowthStage.LATE_SEASON: 30,
}

DEFAULT_STAGE_CONFIG_SOURCE = "mvp_fao56_style_tomato_assumed_stage_durations"


def validate_stage_days(stage_days: dict[GrowthStage, int]) -> None:
    """Validate that stage days contain the exact four tomato growth stages."""
    if set(stage_days.keys()) != set(DEFAULT_TOMATO_STAGE_DAYS.keys()):
        missing = set(DEFAULT_TOMATO_STAGE_DAYS.keys()) - set(stage_days.keys())
        extra = set(stage_days.keys()) - set(DEFAULT_TOMATO_STAGE_DAYS.keys())
        if missing or extra:
            raise ValueError(
                f"stage_days must contain exactly the tomato GrowthStage keys; missing={missing}, extra={extra}."
            )
    for stage, value in stage_days.items():
        if not isinstance(value, int):
            raise ValueError(f"Duration for {stage} must be an int.")
        if value <= 0:
            raise ValueError(f"Duration for {stage} must be positive.")


def days_since_planting(planting_date: date, current_date: date) -> int:
    """Return the number of days since planting including the planting day as day 0."""
    days = (current_date - planting_date).days
    if days < 0:
        raise ValueError("current_date must not be before planting_date.")
    return days


def resolve_stage_from_days(
    days: int,
    stage_days: dict[GrowthStage, int] | None = None,
) -> tuple[GrowthStage, float]:
    """Resolve the current tomato growth stage and stage progress.

    stage_progress is progress through the current stage, not progress through
    the total crop cycle.
    """
    if not isinstance(days, int):
        raise ValueError("days must be an int.")
    if days < 0:
        raise ValueError("days must be >= 0.")

    stage_days = stage_days if stage_days is not None else DEFAULT_TOMATO_STAGE_DAYS
    validate_stage_days(stage_days)

    durations = [
        (GrowthStage.INITIAL, stage_days[GrowthStage.INITIAL]),
        (GrowthStage.DEVELOPMENT, stage_days[GrowthStage.DEVELOPMENT]),
        (GrowthStage.MID_SEASON, stage_days[GrowthStage.MID_SEASON]),
        (GrowthStage.LATE_SEASON, stage_days[GrowthStage.LATE_SEASON]),
    ]

    stage_start = 0
    for stage, duration in durations:
        stage_end = stage_start + duration - 1
        if days <= stage_end:
            stage_day_index = days - stage_start
            if duration <= 1:
                progress = 1.0
            else:
                progress = stage_day_index / (duration - 1)
            return stage, min(max(progress, 0.0), 1.0)
        stage_start += duration

    final_stage = GrowthStage.LATE_SEASON
    return final_stage, 1.0


def resolve_growth_stage(
    *,
    state_id: str,
    crop_type: CropType,
    planting_date: date,
    current_date: date,
    stage_days: dict[GrowthStage, int] | None = None,
    stage_config_source: str = DEFAULT_STAGE_CONFIG_SOURCE,
) -> GrowthStageResponse:
    """Resolve a GrowthStageResponse for a tomato crop given planting and current dates."""
    if not isinstance(state_id, str) or not state_id.strip():
        raise ValueError("state_id must be a non-empty string.")
    if crop_type is not CropType.TOMATO:
        raise ValueError("Only CropType.TOMATO is supported.")
    if not isinstance(stage_config_source, str) or not stage_config_source.strip():
        raise ValueError("stage_config_source must be a non-empty string.")

    days = days_since_planting(planting_date, current_date)
    stage, progress = resolve_stage_from_days(days, stage_days)

    return GrowthStageResponse(
        state_id=state_id,
        crop_type=crop_type,
        planting_date=planting_date,
        current_date=current_date,
        days_since_planting=days,
        growth_stage=stage,
        stage_progress=progress,
        stage_config_source=stage_config_source,
    )
