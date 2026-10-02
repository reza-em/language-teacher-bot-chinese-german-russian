#!/usr/bin/env python3
"""Apply the bot profile through the Bot API: name, descriptions, short descriptions, commands (with scopes + languages), profile photo, default admin rights.
Usage: CHINESE_TELEGRAM_BOT_TOKEN=... ./venv/bin/python setup_profile.py [--no-photo]. Never prints the token."""
import os, sys, json
import config
import core as C

NAMES = {"default": "معلم زبان | Language Teacher", "fa": "معلم زبان | Language Teacher", "en": "Language Teacher | معلم زبان", "de": "Sprachlehrer | معلم زبان"}
SHORT = {
    "default": "معلم خصوصی زبان: چینی 🇨🇳 آلمانی 🇩🇪 روسی 🇷🇺 | Private teacher: Chinese, German, Russian",
    "fa": "معلم خصوصی زبان: چینی، آلمانی و روسی — دورهٔ از صفر، دیکشنری، تمرین و مرور هوشمند",
    "en": "Private language teacher: Chinese, German & Russian — course from zero, dictionary, drills, smart review",
    "de": "Privater Sprachlehrer: Chinesisch, Deutsch & Russisch — Kurs ab null, Wörterbuch, Übungen, smarte Wiederholung",
}
DESC = {
    "default": ("🌍 معلم زبان برای فارسی‌زبان‌ها | Language teacher for Persian speakers\n\n"
                "🇨🇳 中文 · 🇩🇪 Deutsch · 🇷🇺 Русский — /lang\n"
                "📅 دورهٔ قدم‌به‌قدم از صفر + تعیین سطح، درس روزانه\n"
                "🧠 تمرین با اصلاح خطا، مرور لایتنر/SM-2، تلفظ صوتی، دیکشنری\n"
                "👥 در گروه‌ها: /quiz /word /dict /ask\n\n"
                "Course from zero, placement test, exercises with corrections, spaced repetition, audio. Send /start!"),
    "fa": ("🌍 معلم خصوصی زبان برای فارسی‌زبان‌ها\n\n"
           "🇨🇳 چینی (HSK ۱ تا ۳) · 🇩🇪 آلمانی (A1–A2) · 🇷🇺 روسی (A1–A2)\n"
           "هر زبان پیشرفت و مرور جداگانه دارد؛ با /lang زبان را عوض کن یا چند زبان را هم‌زمان بخوان.\n\n"
           "📅 دورهٔ قدم‌به‌قدم از صفر و آزمون تعیین سطح\n"
           "🔤 الفبا و تلفظ (پین‌یین، سیریلیک و تکیه، حروف ä ö ü آلمانی)\n"
           "🧠 تمرین‌های متنوع با اصلاح خطا، مرور لایتنر، یادآوری دلخواه\n"
           "🔍 دیکشنری و تلفظ صوتی  💬 پرسش دستوری\n"
           "👥 در گروه: /quiz /word /dict /ask\n/start را بزن!"),
    "en": ("🌍 Your private language teacher (for Persian, English & German speakers)\n\n"
           "🇨🇳 Chinese (HSK 1–3) · 🇩🇪 German (A1–A2) · 🇷🇺 Russian (A1–A2)\n"
           "Each language has its own progress and review; switch or study several with /lang.\n\n"
           "📅 Guided course from zero + placement test\n🔤 Alphabet & pronunciation (pinyin, Cyrillic & stress, German umlauts)\n"
           "🧠 Varied exercises with corrections, Leitner/SM-2 review, optional reminders\n🔍 Dictionary & audio  💬 Grammar Q&A\n"
           "👥 Works in groups: /quiz /word /dict /ask\nSend /start!"),
    "de": ("🌍 Dein privater Sprachlehrer (für Persisch-, Englisch- und Deutschsprachige)\n\n"
           "🇨🇳 Chinesisch (HSK 1–3) · 🇩🇪 Deutsch (A1–A2) · 🇷🇺 Russisch (A1–A2)\n"
           "Jede Sprache hat eigenen Fortschritt und Wiederholung; wechseln oder mehrere lernen mit /lang.\n\n"
           "📅 Geführter Kurs ab null + Einstufungstest\n🔤 Alphabet & Aussprache (Pinyin, Kyrillisch & Betonung, Umlaute)\n"
           "🧠 Übungen mit Korrektur, Leitner/SM-2, Erinnerungen\n🔍 Wörterbuch & Audio  💬 Grammatikfragen\n"
           "👥 Auch in Gruppen: /quiz /word /dict /ask\nSende /start!"),
}
_C = {  # command -> (fa, en, de)
    "start": ("شروع / منوی اصلی", "Start / main menu", "Start / Hauptmenü"),
    "today": ("درس امروز", "Today's lesson", "Heutige Lektion"),
    "learn": ("یادگیری لغت‌های جدید", "Learn new words", "Neue Vokabeln lernen"),
    "quiz": ("تمرین و آزمون", "Practice & quizzes", "Üben & Quiz"),
    "review": ("مرور (جعبهٔ لایتنر)", "Review (Leitner boxes)", "Wiederholen (Leitner)"),
    "dict": ("دیکشنری", "Dictionary", "Wörterbuch"),
    "ask": ("پرسش دربارهٔ زبان", "Ask about the language", "Frage zur Sprache"),
    "lang": ("انتخاب / تغییر زبان", "Choose / switch language", "Sprache wählen / wechseln"),
    "alphabet": ("الفبا و تلفظ", "Alphabet & pronunciation", "Alphabet & Aussprache"),
    "read": ("داستان کوتاه (چینی)", "Short stories (Chinese)", "Kurztexte (Chinesisch)"),
    "progress": ("پیشرفت من", "My progress", "Mein Fortschritt"),
    "settings": ("تنظیمات", "Settings", "Einstellungen"),
    "stroke": ("ترتیب نوشتن نویسهٔ چینی", "Chinese stroke order", "Chinesische Strichfolge"),
    "help": ("راهنما", "Help", "Hilfe"),
    "cancel": ("لغو", "Cancel", "Abbrechen"),
    "course": ("دورهٔ قدم‌به‌قدم از صفر", "Step-by-step course from zero", "Schritt-für-Schritt-Kurs von null"),
    "placement": ("تعیین سطح", "Placement test", "Einstufungstest"),
    "word": ("واژهٔ روز", "Word of the day", "Wort des Tages"),
    "top": ("رتبه‌های گروه", "Group leaderboard", "Gruppen-Rangliste"),
}
_PRIVATE = ["start", "lang", "course", "placement", "today", "learn", "quiz", "review", "dict", "ask", "alphabet", "read", "progress", "settings", "stroke", "help", "cancel"]
_GROUP = ["quiz", "word", "dict", "ask", "top", "help"]
_ADMINS = ["quiz", "word", "dict", "ask", "top", "settings", "help"]
def _cmds(names, i): return [(n, _C[n][i]) for n in names]
def _langs(names): return {"default": _cmds(names, 1), "fa": _cmds(names, 0), "en": _cmds(names, 1), "de": _cmds(names, 2)}
COMMANDS = {"default": _langs(_PRIVATE), "all_private_chats": _langs(_PRIVATE), "all_group_chats": _langs(_GROUP), "all_chat_administrators": _langs(_ADMINS)}

def run(photo=True):
    ok = True
    def step(name, method, data=None, files=None):
        nonlocal ok
        try: C.call(method, data, files, timeout=90); print("ok  ", name)
        except C.ApiError as e: ok = False; print("FAIL", name, "-", C.safe(e)[:120])
    for lang in ("default", "fa", "en", "de"):
        lc = {} if lang == "default" else {"language_code": lang}
        step(f"name[{lang}]", "setMyName", {"name": NAMES[lang], **lc})
        step(f"short[{lang}]", "setMyShortDescription", {"short_description": SHORT[lang], **lc})
        step(f"description[{lang}]", "setMyDescription", {"description": DESC[lang], **lc})
    for scope, per in COMMANDS.items():
        for lang, lst in per.items():
            d = {"commands": json.dumps([{"command": c, "description": t} for c, t in lst], ensure_ascii=False), "scope": json.dumps({"type": scope})}
            if lang != "default": d["language_code"] = lang
            step(f"commands[{scope}/{lang}]", "setMyCommands", d)
    step("default admin rights (groups)", "setMyDefaultAdministratorRights", {"rights": json.dumps({"can_manage_chat": True, "can_delete_messages": True, "can_pin_messages": True, "can_invite_users": True}), })
    step("default admin rights (channels)", "setMyDefaultAdministratorRights", {"rights": json.dumps({"can_manage_chat": True, "can_post_messages": True, "can_edit_messages": True, "can_pin_messages": True}), "for_channels": "true"})
    if photo:
        p = os.path.join(config.ASSETS, "avatar_lang.png")
        if os.path.exists(p):
            with open(p, "rb") as f:
                step("profile photo", "setMyProfilePhoto", {"photo": json.dumps({"type": "static", "photo": "attach://pic"})}, {"pic": ("avatar_lang.png", f, "image/png")})
        else: print("skip profile photo: assets/avatar_lang.png missing")
    return ok

if __name__ == "__main__":
    if not C.TOKEN: print(f"ERROR: {config.TOKEN_ENV} is not set", file=sys.stderr); sys.exit(1)
    me = C.call("getMe"); print("bot: @" + me["username"])
    sys.exit(0 if run(photo="--no-photo" not in sys.argv) else 2)
