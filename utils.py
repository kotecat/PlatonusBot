import json
import math
from os import path
from pathlib import Path

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
        return default


def get_journal_path(user_id: int, login: str, year: int, semester: int) -> str:
    return path.join(app_config.JOURNAL_DIRECTORY, str(user_id), f"{login}_{year}_{semester}.json")


def diff_journal(old_journal: list[dict], new_journal: list[dict]) -> list[dict]:
    """
    Сравнивает два снимка журнала и возвращает список изменений.

    Отслеживает:
    - totalMark (итоговая оценка)
    - оценки внутри exams (Экз., Ср.тек., РК, Рейтинг и т.д.)
    """
    changes = []

    if old_journal is None:
        return changes
    
    old_map = {s["subjectID"]: s for s in old_journal}
    new_map = {s["subjectID"]: s for s in new_journal}

    for subject_id, new_subj in new_map.items():
        old_subj = old_map.get(subject_id)
        subject_name = new_subj["subjectName"]

        # Предмет появился впервые — пропускаем
        if old_subj is None:
            continue

        # --- totalMark ---
        old_total = str(old_subj.get("totalMark", "")).strip()
        new_total = str(new_subj.get("totalMark", "")).strip()

        if old_total != new_total and new_total not in ("", "-", "0", "0.0"):
            changes.append({
                "subject": subject_name,
                "field": "total",
                "old": old_total,
                "value": new_total,
            })

        # --- exams ---
        old_exams = {
            e["name"]: e["mark"]
            for e in old_subj.get("exams", [])
            if e.get("name") and e.get("mark") is not None
        }
        new_exams = {
            e["name"]: e["mark"]
            for e in new_subj.get("exams", [])
            if e.get("name") and e.get("mark") is not None
        }

        for exam_name, new_mark in new_exams.items():
            old_mark = old_exams.get(exam_name, "0")
            if str(old_mark).strip() != str(new_mark).strip():
                changes.append({
                    "subject": subject_name,
                    "field": "exam",
                    "exam_name": exam_name,
                    "old": str(old_mark),
                    "value": str(new_mark),
                })

    return changes


def make_journal_string(journal: list[dict]) -> str:
    print(f"Making journal string for {len(journal)} subjects")
    result_text = f""

    for subject in journal:
        subject_name = subject.get("subjectName", "Unknown Subject")
        tutor_list = subject.get("tutorList", "No Tutors")
        total_mark = subject.get("totalMark", "0.0")

        exam_text = "<blockquote expandable>"

        for exam in subject.get("exams", []):
            if not exam:
                continue
            exam_name = exam.get("name", "Unknown Exam")
            exam_mark = exam.get("mark", "0.0")

            exam_text += f"  - {exam_name}: {exam_mark}\n"

        exam_text += "</blockquote>"

        color_mark = "⚪️"

        try:
            mark_rounded = math.ceil(float(total_mark))

            if mark_rounded > 0:
                color_mark = "🔴"
            if mark_rounded >= 50:
                color_mark = "🟡"
            if mark_rounded >= 70:
                color_mark = "🔵"
            if mark_rounded >= 90:
                color_mark = "🟢"

        except (ValueError):
            pass

        result_text += (
            f"\n📚 <b>{subject_name}</b>\n"
            f"{'👥' if ',' in tutor_list else '👤'} {tutor_list}\n"
            f"{color_mark} {total_mark}{exam_text}\n"
        )

    return result_text or "<i><b>Нет данных в журнале.</b></i>"


def make_changes_string(changes: list[dict], year: int = 2000, semester: str = "1") -> str:
    if not changes:
        return "Нет изменений в оценках."

    result_text = f"❗️<b>Изменения в оценках ({year} / {semester})</b>\n"
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
