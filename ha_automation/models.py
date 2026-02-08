"""Data models for Home Assistant automations."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class AutomationState(BaseModel):
    """Represents the current state of an automation."""

    entity_id: str = Field(..., description="Entity ID (e.g., automation.my_automation)")
    state: str = Field(..., description="Current state: 'on' or 'off'")
    friendly_name: Optional[str] = Field(None, description="Human-readable name")
    last_triggered: Optional[datetime] = Field(None, description="Last time automation was triggered")
    current: int = Field(0, description="Number of currently running instances")
    mode: str = Field("single", description="Automation mode (single, restart, queued, parallel)")
    max: Optional[int] = Field(None, description="Maximum concurrent runs (for queued/parallel modes)")
    automation_id: Optional[str] = Field(None, description="Unique automation ID")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    @classmethod
    def from_ha_state(cls, state_dict: Dict[str, Any]) -> "AutomationState":
        """
        Create AutomationState from Home Assistant state dictionary.

        Args:
            state_dict: State dictionary from HA API

        Returns:
            AutomationState instance
        """
        attributes = state_dict.get('attributes', {})

        # Parse last_triggered datetime
        last_triggered = None
        if attributes.get('last_triggered'):
            try:
                last_triggered = datetime.fromisoformat(
                    attributes['last_triggered'].replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                pass

        return cls(
            entity_id=state_dict.get('entity_id', ''),
            state=state_dict.get('state', 'unknown'),
            friendly_name=attributes.get('friendly_name'),
            last_triggered=last_triggered,
            current=attributes.get('current', 0),
            mode=attributes.get('mode', 'single'),
            max=attributes.get('max'),
            automation_id=attributes.get('id')
        )


class TriggerConfig(BaseModel):
    """Automation trigger configuration."""

    platform: str = Field(..., description="Trigger platform (state, time, event, etc.)")
    # Additional fields are platform-specific, so we keep it flexible
    extra: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        extra = "allow"  # Allow additional fields


class ConditionConfig(BaseModel):
    """Automation condition configuration."""

    condition: str = Field(..., description="Condition type (state, time, template, etc.)")
    # Additional fields are condition-specific
    extra: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        extra = "allow"


class ActionConfig(BaseModel):
    """Automation action configuration."""

    # Actions can be service calls, delays, conditions, etc.
    # We keep it flexible to handle all action types
    extra: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        extra = "allow"


class AutomationConfig(BaseModel):
    """Complete automation configuration."""

    id: str = Field(..., description="Unique automation ID")
    alias: str = Field(..., description="Automation name/alias")
    description: Optional[str] = Field(None, description="Automation description")
    trigger: List[Dict[str, Any]] = Field(..., description="List of triggers")
    condition: Optional[List[Dict[str, Any]]] = Field(None, description="List of conditions")
    action: List[Dict[str, Any]] = Field(..., description="List of actions")
    mode: str = Field("single", description="Automation mode")
    max: Optional[int] = Field(None, description="Maximum concurrent runs")

    class Config:
        """Pydantic configuration."""
        extra = "allow"  # Allow additional fields like 'max_exceeded'


class AutomationInfo(BaseModel):
    """Combined automation state and configuration info."""

    state: AutomationState
    config: Optional[AutomationConfig] = None

    @property
    def entity_id(self) -> str:
        """Get entity ID."""
        return self.state.entity_id

    @property
    def friendly_name(self) -> str:
        """Get friendly name."""
        return self.state.friendly_name or self.state.entity_id

    @property
    def is_on(self) -> bool:
        """Check if automation is enabled."""
        return self.state.state == "on"


class Device(BaseModel):
    """Represents a Home Assistant device/entity."""

    entity_id: str = Field(..., description="Entity ID (e.g., light.living_room)")
    friendly_name: str = Field(..., description="Human-readable name")
    domain: str = Field(..., description="Domain (light, switch, sensor, etc.)")
    device_class: Optional[str] = Field(None, description="Device class (motion, door, temperature, etc.)")
    state: str = Field(..., description="Current state")
    area: Optional[str] = Field(None, description="Area/room name")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Additional attributes")

    @classmethod
    def from_ha_state(cls, state_dict: Dict[str, Any]) -> "Device":
        """
        Create Device from Home Assistant state dictionary.

        Args:
            state_dict: State dictionary from HA API

        Returns:
            Device instance
        """
        entity_id = state_dict.get('entity_id', '')
        domain = entity_id.split('.')[0] if '.' in entity_id else ''
        attributes = state_dict.get('attributes', {})

        return cls(
            entity_id=entity_id,
            friendly_name=attributes.get('friendly_name', entity_id),
            domain=domain,
            device_class=attributes.get('device_class'),
            state=state_dict.get('state', 'unknown'),
            area=attributes.get('area_id') or attributes.get('area_name'),
            attributes=attributes
        )
