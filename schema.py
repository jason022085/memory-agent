from pydantic import BaseModel, Field
from typing import List, Optional

class TroubleshootingSOP(BaseModel):
    process_area: str = Field(description="The process area or section (e.g., Photo, Etch, Thin Film)")
    alarm_id: str = Field(description="The alarm ID, error code, or exact symptom name (e.g., Dose Energy OOC, PEB Temp Uniformity)")
    symptom_description: str = Field(description="Detailed description of the failure symptoms and FDC chart changes")
    root_cause: str = Field(description="Physical and mechanical explanation of the root cause (why it happened)")
    resolution_steps: List[str] = Field(description="Step-by-step verified action list (SOP) to resolve the issue")
    preventive_actions: List[str] = Field(description="Actionable recommendations to prevent recurrence (e.g., PM adjustment, calibration rules)")
    engineers_involved: List[str] = Field(description="List of engineer user IDs who handled or contributed to these incidents")
    session_references: List[str] = Field(description="Session IDs or reference thread IDs of the processed raw logs")
    confidence_level: str = Field(description="Confidence rating of this troubleshooting entry (e.g., 'Low - Unverified', 'Medium - Experienced', 'High - Confirmed SOP')")
    last_updated: int = Field(description="Epoch millisecond timestamp of the last update")

class SleepConsolidationDecision(BaseModel):
    is_merge: bool = Field(description="True if we are merging/enriching an existing consolidated SOP, False if creating a new one")
    existing_memory_id: Optional[str] = Field(description="The ID of the existing memory being updated (e.g., cons_123456). Required if is_merge is True")
    troubleshooting_data: TroubleshootingSOP = Field(description="The complete, structured troubleshooting memory (either newly created or fully merged/enriched)")

class SleepConsolidationOutput(BaseModel):
    decisions: List[SleepConsolidationDecision] = Field(description="The list of consolidation decisions for each distinct failure mode or alarm type found in the raw logs")
