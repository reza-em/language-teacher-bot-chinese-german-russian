"""Static pinyin / tones / strokes / radicals curriculum. Persian is the primary explanation language; en/de are provided too.
Each hint is (fa, en, de)."""

# (letter, example hanzi, example pinyin, example meaning-en, (fa, en, de) pronunciation hint)
INITIALS = [
 ("b", "爸", "bà", "dad", ("شبیه «پ» نرم و بدون فوت هوا", "like p in “spy” (no puff of air)", "wie p in „Spiel“ (ohne Hauch)")),
 ("p", "怕", "pà", "afraid", ("«پ» همراه با فوت هوا (کاغذ جلوی دهان تکان می‌خورد)", "like p in “pie” (with a puff of air)", "wie p in „Pass“ (mit Hauch)")),
 ("m", "妈", "mā", "mom", ("مثل «م» فارسی", "like m in “mom”", "wie m in „Mama“")),
 ("f", "发", "fā", "to send out", ("مثل «ف» فارسی", "like f in “fan”", "wie f in „fein“")),
 ("d", "大", "dà", "big", ("شبیه «ت» نرم و بدون هوا", "like t in “sty” (no puff)", "wie t in „Stein“ (ohne Hauch)")),
 ("t", "他", "tā", "he", ("«ت» همراه با فوت هوا", "like t in “top” (with a puff)", "wie t in „Tag“ (mit Hauch)")),
 ("n", "你", "nǐ", "you", ("مثل «ن»", "like n in “no”", "wie n in „nein“")),
 ("l", "来", "lái", "to come", ("مثل «ل»", "like l in “let”", "wie l in „Land“")),
 ("g", "个", "gè", "(measure word)", ("شبیه «گ» نرم و بدون هوا", "like g in “sky” (no puff)", "wie g in „Gast“ (ohne Hauch)")),
 ("k", "看", "kàn", "to look", ("«ک» همراه با فوت هوا", "like k in “kite” (with a puff)", "wie k in „Kalt“ (mit Hauch)")),
 ("h", "好", "hǎo", "good", ("شبیه «خ» ملایم", "like a soft “kh”/ch in “Bach”", "wie ch in „Bach“ (weich)")),
 ("j", "家", "jiā", "home", ("شبیه «جی» نرم؛ زبان تخت پشت دندان‌های پایین", "like “j” in “jeep”, tongue flat behind lower teeth", "wie „dsch“ in „Dschungel“, Zunge flach")),
 ("q", "去", "qù", "to go", ("شبیه «چی» با فوت هوا؛ زبان تخت", "like “ch” in “cheese”, tongue flat, aspirated", "wie „tschi“, Zunge flach, mit Hauch")),
 ("x", "学", "xué", "to study", ("بین «سی» و «شی»؛ زبان تخت", "between “s” and “sh”, tongue flat", "zwischen „s“ und „sch“, Zunge flach")),
 ("zh", "中", "zhōng", "middle", ("شبیه «ج» با زبان به عقب برگشته", "like “j” in “judge” with the tongue curled back", "wie „dsch“ mit zurückgebogener Zunge")),
 ("ch", "吃", "chī", "to eat", ("شبیه «چ» با زبان برگشته و فوت هوا", "like “ch” in “church”, tongue curled back, aspirated", "wie „tsch“, Zunge zurückgebogen, mit Hauch")),
 ("sh", "是", "shì", "to be", ("شبیه «ش» با زبان برگشته", "like “sh” in “shirt”, tongue curled back", "wie „sch“, Zunge zurückgebogen")),
 ("r", "人", "rén", "person", ("شبیه «ژ» (مثل ژ در «ژاکت») با زبان برگشته", "like “r”/“zh” (as in “measure”), tongue curled back", "zwischen „r“ und stimmhaftem „sch“ (wie in „Genie“)")),
 ("z", "做", "zuò", "to do", ("شبیه «دز» نرم و بدون هوا", "like “ds” in “kids” (no puff)", "wie „ds“ in „abends“ (ohne Hauch)")),
 ("c", "菜", "cài", "dish", ("شبیه «تس» با فوت هوا", "like “ts” in “cats” (with a puff)", "wie „ts“/z in „Zeit“ (mit Hauch)")),
 ("s", "三", "sān", "three", ("مثل «س»", "like s in “sun”", "wie s in „Sonne“ (stimmlos)")),
 ("y", "一", "yī", "one", ("مثل «ی» (در املا)", "like y in “yes” (spelling)", "wie j in „ja“ (Schreibweise)")),
 ("w", "我", "wǒ", "I", ("مثل «و» (در املا)", "like w in “we” (spelling)", "wie w in engl. „we“ (Schreibweise)")),
]
INITIAL_GROUPS = [
 ("b p m f", ("لبی", "labials", "Lippenlaute")), ("d t n l", ("دندانی", "alveolars", "Zahnlaute")), ("g k h", ("کامی نرم", "velars", "Gaumenlaute")),
 ("j q x", ("کامی (زبان تخت)", "palatals", "Palatale")), ("zh ch sh r", ("زبان برگشته", "retroflex", "Retroflexe")), ("z c s", ("دندانی سایشی", "dental sibilants", "Zischlaute")),
]

# (final, example hanzi, example pinyin, meaning-en)
FINALS = [
 ("a", "啊", "ā", "ah"), ("o", "喔", "ō", "oh"), ("e", "鹅", "é", "goose"), ("i", "衣", "yī", "clothes"), ("u", "乌", "wū", "crow"), ("ü", "鱼", "yú", "fish"),
 ("ai", "爱", "ài", "love"), ("ei", "飞", "fēi", "to fly"), ("ao", "好", "hǎo", "good"), ("ou", "头", "tóu", "head"),
 ("an", "安", "ān", "peace"), ("en", "人", "rén", "person"), ("ang", "忙", "máng", "busy"), ("eng", "灯", "dēng", "lamp"), ("ong", "中", "zhōng", "middle"), ("er", "儿", "ér", "son"),
 ("ia", "家", "jiā", "home"), ("ie", "写", "xiě", "to write"), ("iao", "小", "xiǎo", "small"), ("iu", "六", "liù", "six"), ("ian", "天", "tiān", "sky"), ("in", "今", "jīn", "today"),
 ("iang", "两", "liǎng", "two"), ("ing", "名", "míng", "name"), ("iong", "用", "yòng", "to use"),
 ("ua", "花", "huā", "flower"), ("uo", "我", "wǒ", "I"), ("uai", "快", "kuài", "fast"), ("ui", "水", "shuǐ", "water"), ("uan", "关", "guān", "to close"), ("un", "春", "chūn", "spring"), ("uang", "光", "guāng", "light"),
 ("üe", "月", "yuè", "moon"), ("üan", "远", "yuǎn", "far"), ("ün", "云", "yún", "cloud"),
]
FINAL_GROUPS = [
 ("a o e i u ü", ("وان‌های ساده", "simple finals", "einfache Finale")),
 ("ai ei ao ou", ("ترکیبی", "compound finals", "zusammengesetzte Finale")),
 ("an en ang eng ong er", ("خیشومی و ویژه", "nasal & special", "Nasale & Spezielle")),
 ("ia ie iao iu ian in iang ing iong", ("گروه i", "i-group", "i-Gruppe")),
 ("ua uo uai ui uan un uang", ("گروه u", "u-group", "u-Gruppe")),
 ("üe üan ün", ("گروه ü", "ü-group", "ü-Gruppe")),
]
SPELLING_RULES = [
 ("«ü» بعد از j، q، x، y بدون دو نقطه نوشته می‌شود (ju, qu, xu, yu) ولی مثل ü خوانده می‌شود. بعد از n و l دو نقطه می‌ماند: nü, lü.",
  "After j, q, x, y the letter ü is written as u (ju, qu, xu, yu) but still pronounced ü. After n and l the dots stay: nü, lü.",
  "Nach j, q, x, y wird ü als u geschrieben (ju, qu, xu, yu), aber wie ü gesprochen. Nach n und l bleiben die Punkte: nü, lü."),
 ("وقتی هجا با i، u، ü شروع شود و حرف آغازین ندارد: i→yi، u→wu، ü→yu، ia→ya، ie→ye، uo→wo، ...",
  "Syllables starting with i, u, ü and no initial are spelled with y/w: i→yi, u→wu, ü→yu, ia→ya, ie→ye, uo→wo …",
  "Silben ohne Anlaut mit i, u, ü werden mit y/w geschrieben: i→yi, u→wu, ü→yu, ia→ya, ie→ye, uo→wo …"),
 ("iou، uei، uen بعد از حرف آغازین کوتاه می‌شوند: iu، ui، un (مثلاً liù، guī، chūn).",
  "After an initial, iou, uei, uen are written iu, ui, un (e.g. liù, guī, chūn).",
  "Nach einem Anlaut werden iou, uei, uen zu iu, ui, un (z. B. liù, guī, chūn)."),
 ("جداکنندهٔ هجا: وقتی هجای a/o/e بعد از هجای دیگر بیاید، آپوستروف می‌گذاریم تا اشتباه خوانده نشود: xī’ān (西安) در برابر xiān (先).",
  "Apostrophe: when a syllable starting with a/o/e follows another syllable, write ’ to avoid ambiguity: xī’ān (西安) vs xiān (先).",
  "Apostroph: Beginnt eine Silbe mit a/o/e nach einer anderen, steht ’ zur Klarheit: xī’ān (西安) vs. xiān (先)."),
]

TONES = [  # (number, mark, name fa/en/de, contour fa/en/de, example hanzi, pinyin, meaning-en)
 (1, "ˉ", ("لحن اول", "1st tone", "1. Ton"), ("بالا و صاف (مثل نت بلند ثابت)", "high and flat", "hoch und gleichbleibend"), "妈", "mā", "mom"),
 (2, "ˊ", ("لحن دوم", "2nd tone", "2. Ton"), ("صعودی (مثل پرسش «ها؟»)", "rising (like a surprised “huh?”)", "steigend (wie ein erstauntes „Hä?“)"), "麻", "má", "hemp"),
 (3, "ˇ", ("لحن سوم", "3rd tone", "3. Ton"), ("پایین‌رونده و دوباره بالا (دره)", "falling then rising (a dip)", "fallend-steigend (Senke)"), "马", "mǎ", "horse"),
 (4, "ˋ", ("لحن چهارم", "4th tone", "4. Ton"), ("تند و پایین‌رونده (مثل فرمان «برو!»)", "sharp falling (like a command)", "kurz fallend (wie ein Befehl)"), "骂", "mà", "to scold"),
 (5, "", ("لحن خنثی", "neutral tone", "neutraler Ton"), ("کوتاه و سبک، بدون علامت", "short and light, no mark", "kurz und leicht, ohne Zeichen"), "吗", "ma", "(question particle)"),
]
TONE_MARK_RULES = [
 ("۱) اگر a داریم، علامت روی a می‌رود: hǎo، māng.", "1) If there is an a, the mark goes on a: hǎo, máng.", "1) Gibt es ein a, steht das Zeichen auf a: hǎo, máng."),
 ("۲) اگر a نبود ولی e یا o بود، روی e یا o می‌رود: xiě، duō.", "2) No a? Then on e or o: xiě, duō.", "2) Kein a? Dann auf e oder o: xiě, duō."),
 ("۳) در ou، علامت روی o است: gǒu، tóu.", "3) In ou the mark is on o: gǒu, tóu.", "3) Bei ou steht es auf o: gǒu, tóu."),
 ("۴) در iu و ui، علامت روی حرف آخر می‌رود: liù، guì، shuǐ.", "4) In iu and ui the mark goes on the last letter: liù, guì, shuǐ.", "4) Bei iu und ui auf dem letzten Buchstaben: liù, guì, shuǐ."),
 ("۵) روی i علامت می‌آید و نقطه‌اش حذف می‌شود: yī، nǐ. روی ü دو نقطه می‌ماند: lǜ.", "5) On i the dot is replaced by the mark: yī, nǐ. On ü the dots stay: lǜ.", "5) Auf i ersetzt das Zeichen den Punkt: yī, nǐ. Auf ü bleiben die Punkte: lǜ."),
]
SANDHI = [
 ("لحن ۳ + لحن ۳ ← لحن اولی ۲ می‌شود: 你好 نوشته می‌شود nǐ hǎo ولی خوانده می‌شود ní hǎo.", "3rd + 3rd tone: the first becomes 2nd: 你好 is written nǐ hǎo but said ní hǎo.", "3. + 3. Ton: der erste wird 2. Ton: 你好 schreibt man nǐ hǎo, spricht man ní hǎo."),
 ("«不» قبل از لحن ۴ می‌شود bú: 不是 bú shì (در بقیهٔ حالت‌ها bù).", "“不” before a 4th tone becomes bú: 不是 bú shì (otherwise bù).", "„不“ vor dem 4. Ton wird bú: 不是 bú shì (sonst bù)."),
 ("«一» قبل از لحن ۴ می‌شود yí (一个 yí gè) و قبل از ۱، ۲، ۳ می‌شود yì (一天 yì tiān). به‌تنهایی یا در شماره yī است.", "“一” before a 4th tone is yí (一个 yí gè); before tones 1–3 it is yì (一天 yì tiān). Alone or in numbers it is yī.", "„一“ vor dem 4. Ton ist yí (一个 yí gè); vor Ton 1–3 yì (一天 yì tiān). Allein oder in Zahlen yī."),
]
TONE_PAIRS = [("妈", "麻", "马", "骂"), ("吃", "池", "尺", "赤")]
TONE_TIPS = [
 ("لحن‌ها معنی را عوض می‌کنند: mā «مادر»، mǎ «اسب»، mà «دشنام دادن». حتماً لحن را همراه هر واژه یاد بگیر.", "Tones change meaning: mā “mom”, mǎ “horse”, mà “scold”. Always learn the tone with every word.", "Töne ändern die Bedeutung: mā „Mama“, mǎ „Pferd“, mà „schimpfen“. Lerne den Ton immer mit."),
 ("برای لحن ۱ صدایت را روی یک نت بالا نگه دار؛ تصور کن داری یک «آآآ» ثابت می‌خوانی.", "For tone 1 hold your voice on one high note, like singing a steady “aaa”.", "Für den 1. Ton halte die Stimme auf einer hohen Note, wie ein gleichmäßiges „aaa“."),
 ("لحن ۳ در وسط جمله معمولاً فقط «پایین» اجرا می‌شود (نیم‌لحن ۳)؛ کامل فقط آخر جمله پایین-بالا می‌شود.", "A 3rd tone in the middle of a sentence is usually just the low dip (half third); the full dip-and-rise happens at the end.", "Der 3. Ton mitten im Satz ist meist nur die Tiefe (Halb-Dritter); ganz fallend-steigend nur am Satzende."),
 ("با دست حرکت لحن را بکش: ✋ صاف، ↗️ بالا، ↘️↗️ دره، ↘️ پایین. بدن به حافظه کمک می‌کند.", "Draw tones in the air with your hand: flat, up, dip, down. Your body helps memory.", "Zeichne die Töne mit der Hand in die Luft: flach, hoch, Senke, runter. Der Körper hilft dem Gedächtnis."),
 ("جفت‌های کمینه را تمرین کن: mā/má/mǎ/mà و shì/shí/shǐ/shī. هر بار به صدای خودت گوش بده.", "Practise minimal pairs: mā/má/mǎ/mà and shī/shí/shǐ/shì. Listen to yourself each time.", "Übe Minimalpaare: mā/má/mǎ/mà und shī/shí/shǐ/shì. Höre dir dabei zu."),
 ("لحن خنثی کوتاه و سبک است و بعد از لحن ۱ پایین‌تر، بعد از ۲ میانه، بعد از ۳ بالاتر می‌نشیند: 妈妈 māma، 爸爸 bàba.", "The neutral tone is short and light: 妈妈 māma, 爸爸 bàba, 你们 nǐmen.", "Der neutrale Ton ist kurz und leicht: 妈妈 māma, 爸爸 bàba, 你们 nǐmen."),
 ("در گفتار دو لحن ۳ پشت‌سرهم: اولی ۲ می‌شود (你好 ní hǎo). این را در املا نمی‌نویسند.", "Two 3rd tones in a row: the first becomes 2nd (你好 ní hǎo). This is not written in pinyin.", "Zwei dritte Töne hintereinander: der erste wird 2. Ton (你好 ní hǎo). In Pinyin nicht geschrieben."),
 ("«不» و «一» بسته به لحن بعدی تغییر می‌کنند: 不是 bú shì، 一个 yí gè.", "“不” and “一” change with the following tone: 不是 bú shì, 一个 yí gè.", "„不“ und „一“ ändern sich je nach Folgeton: 不是 bú shì, 一个 yí gè."),
]

STROKES = [  # (name zh, pinyin, shape, (fa, en, de) name, example)
 ("横", "héng", "一", ("افقی (چپ به راست)", "horizontal", "waagerecht"), "二 十 三"),
 ("竖", "shù", "丨", ("عمودی (بالا به پایین)", "vertical", "senkrecht"), "十 中 仆"),
 ("撇", "piě", "丿", ("کج به چپ‌پایین", "left-falling", "links abfallend"), "人 八 千"),
 ("捺", "nà", "㇏", ("کج به راست‌پایین", "right-falling", "rechts abfallend"), "人 大 天"),
 ("点", "diǎn", "丶", ("نقطه", "dot", "Punkt"), "小 六 学"),
 ("提", "tí", "㇀", ("بالا‌رونده", "rising flick", "aufsteigend"), "我 冷 打"),
 ("横折", "héng zhé", "𠃍", ("افقی با خمش", "horizontal-turn", "waagerecht mit Knick"), "口 日 国"),
 ("竖钩", "shù gōu", "亅", ("عمودی با قلاب", "vertical hook", "senkrecht mit Haken"), "小 水 到"),
]
STROKE_RULES = [
 ("از بالا به پایین", "Top to bottom", "Von oben nach unten", "三 (一، 二، 三)"),
 ("از چپ به راست", "Left to right", "Von links nach rechts", "明 (日 سپس 月)"),
 ("افقی قبل از عمودی", "Horizontal before vertical", "Waagerecht vor senkrecht", "十 (横 ← 竖)"),
 ("«撇» قبل از «捺»", "Left-falling before right-falling", "Links- vor rechtsfallend", "人 (撇 ← 捺)"),
 ("بیرون قبل از درون", "Outside before inside", "Außen vor innen", "月 (قاب ← داخل)"),
 ("وسط قبل از دو طرف", "Middle before the sides", "Mitte vor den Seiten", "小 (丨 ← 丿 ← 丶)"),
 ("بستن قاب در آخر", "Close the box last", "Rahmen zuletzt schließen", "国 (口 ← ... ← 一)"),
]

# radical, pinyin, en, fa, de, example chars
RADICALS = [
 ("人/亻", "rén", "person", "آدم", "Mensch", "你 他 们"), ("口", "kǒu", "mouth", "دهان", "Mund", "吃 喝 叫"), ("水/氵", "shuǐ", "water", "آب", "Wasser", "河 海 洗"),
 ("火/灬", "huǒ", "fire", "آتش", "Feuer", "热 烧 点"), ("木", "mù", "tree, wood", "درخت/چوب", "Baum, Holz", "树 林 桌"), ("日", "rì", "sun, day", "خورشید/روز", "Sonne, Tag", "明 时 星"),
 ("月", "yuè", "moon, flesh", "ماه/گوشت", "Mond, Fleisch", "朋 有 服"), ("心/忄", "xīn", "heart", "قلب", "Herz", "想 忙 快"), ("手/扌", "shǒu", "hand", "دست", "Hand", "打 找 拿"),
 ("言/讠", "yán", "speech", "گفتار", "Sprache", "说 请 谁"), ("食/饣", "shí", "food", "غذا", "Essen", "饭 饿 饱"), ("金/钅", "jīn", "metal, gold", "فلز/طلا", "Metall, Gold", "钱 银 铅"),
 ("女", "nǚ", "woman", "زن", "Frau", "妈 好 姐"), ("子", "zǐ", "child", "کودک", "Kind", "学 孩 字"), ("宀", "mián", "roof", "سقف", "Dach", "家 字 客"),
 ("门", "mén", "door", "در", "Tür", "问 间 开"), ("辶", "chuò", "walk", "راه رفتن", "gehen", "这 过 还"), ("艹", "cǎo", "grass", "گیاه", "Gras", "菜 茶 花"),
 ("目", "mù", "eye", "چشم", "Auge", "看 眼 睡"), ("耳", "ěr", "ear", "گوش", "Ohr", "聪 闻 耳"), ("足/⻊", "zú", "foot", "پا", "Fuß", "跑 跳 路"),
 ("车", "chē", "vehicle", "ماشین/چرخ", "Fahrzeug", "辆 车 轮"), ("雨", "yǔ", "rain", "باران", "Regen", "雪 雷 零"), ("山", "shān", "mountain", "کوه", "Berg", "山 岁 岛"),
 ("土", "tǔ", "earth", "خاک", "Erde", "地 坐 城"), ("大", "dà", "big", "بزرگ", "groß", "大 太 夫"), ("刀/刂", "dāo", "knife", "چاقو", "Messer", "到 刷 刻"),
 ("力", "lì", "power", "نیرو", "Kraft", "动 男 努"), ("田", "tián", "field", "کشتزار", "Feld", "男 画 留"), ("禾", "hé", "grain", "غلات", "Getreide", "秋 种 和"),
 ("竹/⺮", "zhú", "bamboo", "بامبو", "Bambus", "笑 筷 笔"), ("糸/纟", "sī", "silk", "ابریشم", "Seide", "红 绿 级"), ("衣/衤", "yī", "clothes", "لباس", "Kleidung", "衣 裤 裙"),
 ("疒", "nè", "sickness", "بیماری", "Krankheit", "病 疼 痛"), ("走", "zǒu", "to walk", "راه رفتن", "gehen", "起 超 赶"), ("彳", "chì", "step", "گام", "Schritt", "很 得 往"),
 ("攵", "pū", "tap", "ضربه", "klopfen", "教 数 收"), ("鸟", "niǎo", "bird", "پرنده", "Vogel", "鸟 鸡 鸭"), ("鱼", "yú", "fish", "ماهی", "Fisch", "鱼 鲜 鲁"),
 ("犭", "quǎn", "dog", "سگ", "Hund", "狗 猫 狼"), ("贝", "bèi", "shell, money", "صدف/پول", "Muschel, Geld", "贵 财 贫"), ("又", "yòu", "again, hand", "دوباره/دست", "wieder, Hand", "友 取 双"),
 ("石", "shí", "stone", "سنگ", "Stein", "石 破 码"), ("爪/爫", "zhǎo", "claw", "چنگال", "Kralle", "爬 爱 爸"), ("广", "guǎng", "shelter", "سرپناه", "Schutzdach", "店 床 度"),
 ("囗", "wéi", "enclosure", "قاب/حصار", "Umschließung", "国 四 回"), ("夕", "xī", "evening", "غروب", "Abend", "外 多 名"), ("寸", "cùn", "inch, hand", "اینچ/دست", "Zoll, Hand", "对 寺 导"),
 ("方", "fāng", "square, direction", "چهارگوش/سو", "Quadrat, Richtung", "旁 旅 放"), ("立", "lì", "stand", "ایستادن", "stehen", "站 音 童"), ("止", "zhǐ", "stop", "ایستادن", "anhalten", "步 正 此"),
]
