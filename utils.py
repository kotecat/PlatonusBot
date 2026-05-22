import json
import math


def save_json(data: dict, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filename: str, default: list = []) -> list:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def diff_journal(old_journal: list[dict], new_journal: list[dict]) -> list[dict]:
    """
    Сравнивает два снимка журнала и возвращает список изменений.

    Отслеживает:
    - totalMark (итоговая оценка)
    - оценки внутри exams (Экз., Ср.тек., РК, Рейтинг и т.д.)
    """
    changes = []

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

    return result_text


def make_changes_string(changes: list[dict]) -> str:
    if not changes:
        return "Нет изменений в оценках."

    result_text = "Изменения в оценках:\n"
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
