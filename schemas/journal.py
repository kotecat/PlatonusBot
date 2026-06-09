from __future__ import annotations
from enum import IntEnum
from typing import Optional
from pydantic import AliasChoices, Field
from .base import BaseSchema


# ===== JOURNAL =====

class ExamSchema(BaseSchema):
    name: Optional[str] = None
    mark: Optional[str] = None
    mark_type_id: Optional[int] = Field(None, alias="markTypeId")


class Journal(BaseSchema):
    subject_name: str = Field(alias="subjectName")
    tutor_list: str = Field(alias="tutorList")
    center_mark: float = Field(alias="centerMark")
    total_mark: str = Field(alias="totalMark")
    color: str
    box_height: Optional[str] = Field(None, alias="boxHeight")
    subject_id: int = Field(
        validation_alias=AliasChoices("subjectID", "subjectId"),
        serialization_alias="subjectID"
    )
    exams: list[ExamSchema]
    control_form_id: int = Field(
        validation_alias=AliasChoices("controlFormID", "controlFormId"),
        serialization_alias="controlFormID"
    )


# ===== ATTENDANCE =====

class AttendanceCheckType(IntEnum):
    BY_QR = 1
    BY_TUTOR = 2
    BY_ABSENCE_VALID_REASON = 3
    BY_DELETE_ABSENT_MARK = 4
    BY_ATTENDANCE_PAGE_PRESENT = 5
    BY_ATTENDANCE_PAGE_ABSENT_UNKNOWN = 6
    BY_ATTENDANCE_PAGE_ABSENT_VALID_REASON = 7
    BY_FINANCIAL_DEBT = 8


class AttendanceRecord(BaseSchema):
    date: str
    check_type: AttendanceCheckType = Field(alias="checkType")


class Attendance(BaseSchema):
    attendance_percent: float = Field(alias="attendancePercent")
    conducted_lessons_count: int = Field(alias="conductedLessonsCount")
    planned_lessons_count: int = Field(alias="plannedLessonsCount")
    attended_classes_count: int = Field(alias="attendedClassesCount")
    missed_classes_count: int = Field(alias="missedClassesCount")
    records: list[AttendanceRecord]


# ===== JOURNAL MARKS =====

class Mark(BaseSchema):
    day: int
    mark: float
    mark_type_id: int = Field(alias="markTypeID")
    add_mark_type_id: int = Field(alias="addMarkTypeID")
    mark_name: Optional[str] = Field(None, alias="markName")


class Month(BaseSchema):
    month: str
    marks: list[Mark]


class JournalMarks(BaseSchema):
    group_name: str = Field(alias="groupName")
    tutor: str
    months: list[Month]
    study_group_id: int = Field(alias="studyGroupID")


class JournalResponse(BaseSchema):
    subjects: Optional[Journal] = None


class JournalMarksResponse(BaseSchema):
    journal_response: JournalResponse = Field(alias="journalResponse")
    journal_marks: list[JournalMarks] = Field(alias="journalMarks")
