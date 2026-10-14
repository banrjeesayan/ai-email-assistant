from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class IntentAnalysis(BaseModel):
    primary: str = Field(description="Primary intent of the email")
    secondary: List[str] = Field(default_factory=list, description="Secondary intents if any")
    explanation: str = Field(description="One line explanation of intent in plain English")


class ActionItem(BaseModel):
    task: str = Field(description="Actionable task description")
    owner: str = Field(description="'user' | 'sender' | 'third_party:<name>'")
    deadline: Optional[str] = Field(default=None, description="Associated deadline string if any")
    explicit: bool = Field(default=True, description="True if explicitly requested, False if implied")


class DeadlineItem(BaseModel):
    original_text: str = Field(description="Original temporal phrase in text, e.g. 'by EOD Friday'")
    resolved_date: Optional[str] = Field(default=None, description="ISO or human-readable resolved absolute date/time")
    type: str = Field(default="soft", description="hard or soft deadline")
    ambiguity_note: Optional[str] = Field(default=None, description="Ambiguity explanation if date expression is unclear")

    @model_validator(mode='after')
    def normalize_deadline_type(self):
        """Normalize type to hard/soft after model creation."""
        v = str(self.type).lower().strip()
        if "hard" in v:
            self.type = "hard"
        else:
            self.type = "soft"
        return self


class SentimentAnalysis(BaseModel):
    label: str = Field(description="positive | neutral | negative | frustrated | angry | anxious | mixed")
    reason: str = Field(description="One line reason for sentiment score")

    @model_validator(mode='after')
    def normalize_sentiment_label(self):
        self.label = str(self.label).lower().strip()
        return self


class UrgencyAnalysis(BaseModel):
    level: str = Field(description="low | medium | high | critical")
    reason: str = Field(description="One line reason for urgency score")

    @model_validator(mode='after')
    def normalize_urgency_level(self):
        v = str(self.level).lower().strip()
        if v in ["low", "medium", "high", "critical"]:
            self.level = v
        elif "crit" in v:
            self.level = "critical"
        elif "high" in v:
            self.level = "high"
        elif "med" in v:
            self.level = "medium"
        else:
            self.level = "low"
        return self


class SuggestedResponse(BaseModel):
    subject: Optional[str] = Field(default=None, description="Subject line if it needs to change, else null")
    body: Optional[str] = Field(default=None, description="Draft reply body written in 1st person as user")
    reason_if_none: Optional[str] = Field(default=None, description="Explanation if reply_needed is false")


class EmailAnalysisResult(BaseModel):
    summary: str = Field(description="1-3 sentences stating who wants what and why it matters")
    intent: IntentAnalysis
    action_items: List[ActionItem] = Field(default_factory=list)
    deadlines: List[DeadlineItem] = Field(default_factory=list)
    sentiment: SentimentAnalysis
    urgency: UrgencyAnalysis
    flags: List[str] = Field(default_factory=list)
    reply_needed: bool = Field(default=True)
    suggested_response: SuggestedResponse
    needs_user_input: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Overall confidence score from 0.0 to 1.0")

    @model_validator(mode='before')
    @classmethod
    def coerce_nulls_to_lists(cls, data):
        """Convert any None list fields to empty lists before validation."""
        if isinstance(data, dict):
            # Fix hallucinated nesting: Ollama sometimes puts needs_user_input inside confidence
            if isinstance(data.get("confidence"), dict):
                conf_dict = data.pop("confidence")
                if "confidence" in conf_dict:
                    data["confidence"] = conf_dict["confidence"]
                if "needs_user_input" in conf_dict and "needs_user_input" not in data:
                    data["needs_user_input"] = conf_dict["needs_user_input"]
                    
            for key in ["action_items", "deadlines", "flags", "needs_user_input"]:
                if data.get(key) is None:
                    data[key] = []
        return data


class AnalyzeEmailRequest(BaseModel):
    user_name: Optional[str] = "Alex Morgan"
    user_role: Optional[str] = "Executive Director"
    tone: Optional[str] = "professional but warm"
    signoff: Optional[str] = "Best regards,\nAlex"
    received_at: Optional[str] = "2026-09-29 10:15 IST"
    sender: str
    recipients: Optional[str] = "Alex Morgan <alex@company.com>"
    subject: str
    body: str
    api_key: Optional[str] = None
    model_name: Optional[str] = "gemini-2.5-flash"
