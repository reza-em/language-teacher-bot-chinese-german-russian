# Scripted *illustrative* conversation used to render docs/*.png and docs/demo.gif.
# Usage: MOCK_FONT_DIR=file:///path/to/fonts python3 render.py scenario ../   (needs Chrome + ffmpeg + Pillow)
from render import *
SPEC=dict(name='Language Teacher', icon='🌍', c1='#e0533d', c2='#f2a33a', scenarios=[
 dict(steps=[
  U('/start'),
  B('👋 سلام! به <b>معلم زبان</b> خوش آمدی.\nکدام زبان را می‌خواهی یاد بگیری؟', id='q',
    buttons=[['🇨🇳 چینی','🇩🇪 آلمانی','🇷🇺 روسی']]),
  dict(press='q', label='🇨🇳 چینی'),
  B('🎯 اول یک <b>تعیین سطح</b> ۱۲ سؤالی؟ یا از صفر شروع کنیم؟', id='q2',
    buttons=[['🎯 تعیین سطح'],['🌱 از صفر، قدم‌به‌قدم'],['🤷 خودم انتخاب می‌کنم']]),
  dict(press='q2', label='🌱 از صفر، قدم‌به‌قدم'),
  B('📖 <b>درس ۱ · سلام و احوال‌پرسی</b>\n\n<span style="font-size:30px;line-height:1.3">你好</span>\n<code>nǐ hǎo</code> — سلام\n\n🧠 «nǐ» لحن سوم (پایین‌رو‌-بالا‌رو) دارد.', id='l',
    buttons=[['🔊 تلفظ','➕ جعبهٔ مرور'],['➡️ ادامه']]),
 ]),
 dict(steps=[
  B('❓ <b>تمرین ۳ از ۸</b>\nمعنی <span style="font-size:22px">谢谢</span> (<code>xièxie</code>) چیست؟', id='q',
    buttons=[['سلام','ببخشید'],['ممنون','خداحافظ']]),
  dict(press='q', label='ممنون'),
  B('✅ <b>درست!</b> +۵ امتیاز\n<span style="font-size:20px">谢谢</span> = ممنون / thank you\n\n🔥 رشتهٔ روزانه: ۴ روز', id='r',
    buttons=[['➡️ تمرین بعدی'],['🔁 مرور توضیح']]),
 ]),
 dict(steps=[
  B('🇩🇪 <b>Deutsch · A1</b> — Artikel\nWelcher Artikel passt?\n\n<b>___ Tisch</b>  (میز)', id='q',
    buttons=[['der','die','das']]),
  dict(press='q', label='der'),
  B('✅ <b>der Tisch</b> — مذکر (maskulin)\nجمع: <code>die Tische</code>', id='r'),
  B('🗂 <b>مرور امروز</b>\nکارت‌های موعددار: <b>12</b> · جعبهٔ لایتنر ۱–۵', id='s',
    buttons=[['▶️ شروع مرور'],['📊 پیشرفت','⚙️ تنظیمات']]),
 ]),
])
