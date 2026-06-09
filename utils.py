import json
import math
from os import path
from pathlib import Path
from schemas.journal import ExamSchema, Journal, JournalMarksResponse

from config import app_config


def save_json(data: dict, filename: str):
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filename: str, default=None):
    if default is None:
        default = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        save_json(default, filename)  # Создаем файл с дефолтными данными
        return default
    except json.JSONDecodeError:
        save_json(default, filename)  # Перезаписываем файл, если он поврежден
        return default


def get_journal_path(user_id: int, login: str, year: int, semester: int) -> str:
    return path.join(app_config.JOURNAL_DIRECTORY, str(user_id), f"{login}_{year}_{semester}.json")


def _exam_key(exams: list[ExamSchema]) -> dict[int, ExamSchema]:
    return {
        i: e
        for i, e in enumerate(exams)
        if e.mark is not None
    }


def diff_journal(old_journal: list[Journal], new_journal: list[Journal]) -> list[dict]:
    changes = []

    if not old_journal:
        return changes

    old_map = {s.subject_id: s for s in old_journal}
    new_map = {s.subject_id: s for s in new_journal}

    for subject_id, new_subj in new_map.items():
        old_subj = old_map.get(subject_id)

        if old_subj is None:
            continue

        # --- totalMark ---
        old_total = str(old_subj.total_mark).strip()
        new_total = str(new_subj.total_mark).strip()

        if old_total != new_total and new_total not in ("", "-", "0", "0.0"):
            changes.append({
                "subject": new_subj.subject_name,
                "field": "total",
                "old": old_total,
                "value": new_total,
            })

        # --- exams ---
        old_exams = _exam_key(old_subj.exams)
        new_exams = _exam_key(new_subj.exams)

        for i, new_exam in new_exams.items():
            old_exam = old_exams.get(i)
            old_mark = old_exam.mark if old_exam else "0"
            if str(old_mark).strip() != str(new_exam.mark).strip():
                changes.append({
                    "subject": new_subj.subject_name,
                    "field": "exam",
                    "exam_name": new_exam.name,
                    "old": str(old_mark),
                    "value": str(new_exam.mark),
                })

    return changes

def make_journal_string(journal: list[Journal], year: int = 2000, semester: int = 1) -> str:
    result_text = ""

    for subject in journal:
        exam_text = "<blockquote expandable>"

        for exam in subject.exams:
            if not exam.name:
                continue
            exam_text += f"  - {exam.name}: {exam.mark or '—'}\n"

        exam_text += "</blockquote>"

        color_mark = "⚪️"

        try:
            mark_rounded = math.ceil(float(subject.total_mark))

            if mark_rounded > 0:
                color_mark = "🔴"
            if mark_rounded >= 50:
                color_mark = "🟡"
            if mark_rounded >= 70:
                color_mark = "🔵"
            if mark_rounded >= 90:
                color_mark = "🟢"

        except ValueError:
            pass

        result_text += (
            f"\n<a href='t.me/testcat_mew_bot?start=subject_{subject.subject_id}_{year}_{semester}'>📚 <b>{subject.subject_name}</b></a>\n"
            f"{'👥' if ',' in subject.tutor_list else '👤'} {subject.tutor_list}\n"
            f"{color_mark} {subject.total_mark}{exam_text}\n"
        )

    return result_text or "<i><b>Нет данных в журнале.</b></i>"


def make_changes_string(changes: list[dict], year: int = 2000, semester_name: str = "1") -> str:
    if not changes:
        return "Нет изменений в оценках."

    result_text = f"❗️<b>Изменения в оценках ({year} / {semester_name})</b>\n"
    current_subject = None

    for change in changes:
        subject = change["subject"]
        field = change["field"]
        old = change["old"]
        value = change["value"]

        if subject != current_subject:
            result_text += f"\n📚 <b>{subject}</b>\n"
            current_subject = subject

        if field == "total":
            result_text += f"   🏆 <u>Итоговая оценка</u>: {old} → {value}\n"
        elif field == "exam":
            exam_name = change.get("exam_name", "Unknown Exam")
            result_text += f"   • {exam_name}: {old} → {value}\n"

    return result_text


def make_journal_marks_string(journal_marks_resp: JournalMarksResponse) -> str:
    journal = journal_marks_resp.journal_response.subjects
    marks = journal_marks_resp.journal_marks
    
    if not journal:
        return "<b>Нет данных по этому предмету.</b>"
    
    result_lines = [
        f"📚 <b>Оценки по предмету</b>",
        f"<b>{journal.subject_name}</b>",
        "",
    ]

    for i, mark in enumerate(marks):
        if i > 0:
            result_lines.append("──────────────────")
            result_lines.append("")

        result_lines.append(f"<b>📂 {mark.group_name}</b>")
        result_lines.append(f"    👤 <i>{mark.tutor}</i>")

        if not mark.months:
            result_lines.append("    <i>Нет оценок</i>")
        else:
            for month in mark.months:
                result_lines.append(f"    📅 <b>{month.month}</b>")
                for m in month.marks:
                    result_lines.append(f"        • {m.day:>2} число  →  <code>{m.mark}</code>")

        result_lines.append("")

    return "\n".join(result_lines)


def get_auth(user_id: int) -> tuple[str, str, str] | None:
    """Возвращает (login, password, host) или None если не авторизован."""
    auth_data = load_json(path.join(app_config.AUTH_DIRECTORY, f"{user_id}.json"), default={})
    login = auth_data.get("login", None)
    password = auth_data.get("password", None)
    host = auth_data.get("host", None)
    if not login or not password or not host:
        return None
    return login, password, host


_CYR_TO_LAT = {
    'а': 'a',  'б': 'b',  'в': 'v',  'г': 'g',  'д': 'd',
    'е': 'e',  'ё': 'yo', 'ж': 'zh', 'з': 'z',  'и': 'i',
    'й': 'j',  'к': 'k',  'л': 'l',  'м': 'm',  'н': 'n',
    'о': 'o',  'п': 'p',  'р': 'r',  'с': 's',  'т': 't',
    'у': 'u',  'ф': 'f',  'х': 'h',  'ц': 'ts', 'ч': 'ch',
    'ш': 'sh', 'щ': 'sch','ъ': '',   'ы': 'y',  'ь': '',
    'э': 'e',  'ю': 'yu', 'я': 'ya',
    # казахские буквы
    'ә': 'a',  'ғ': 'g',  'қ': 'k',  'ң': 'n',  'ө': 'o',
    'ұ': 'u',  'ү': 'u',  'һ': 'h',  'і': 'i',
}


def translit(text: str) -> str:
    result = []
    for ch in text.lower():
        result.append(_CYR_TO_LAT.get(ch, ch))
    return "".join(result)

