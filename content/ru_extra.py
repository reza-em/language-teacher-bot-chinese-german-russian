"""Russian: example sentences, alphabet, reading rules, grammar notes, drills (own work; Persian/English texts unreviewed by native speakers).
Stress is marked with an apostrophe after the stressed vowel (converted to a combining acute accent when displayed)."""
# text | English | Persian     ([bracket] = cloze word; must equal a vocabulary headword (plain, without stress marks))
SENT = """
Это моя' [мама].|This is my mom.|این مامان من است.
Мой [брат] живёт в Москве'.|My brother lives in Moscow.|برادرم در مسکو زندگی می‌کند.
Где мой [телефо'н]?|Where is my phone?|تلفن من کجاست؟
Я люблю' [чай].|I like tea.|من چای دوست دارم.
Э'то хоро'шая [кни'га].|This is a good book.|این کتاب خوبی است.
У меня' есть [семья'].|I have a family.|من خانواده دارم.
Мы живём в большо'м [до'ме].|We live in a big house.|ما در یک خانهٔ بزرگ زندگی می‌کنیم.
Он чита'ет [газе'ту].|He reads a newspaper.|او روزنامه می‌خواند.
Я пью [во'ду].|I drink water.|من آب می‌نوشم.
Мой [друг] студе'нт.|My friend is a student.|دوست من دانشجو است.
Как тебя' зову'т? Меня' зову'т Али'.|What is your name? My name is Ali.|اسمت چیست؟ اسم من علی است.
Я рабо'таю в [шко'ле].|I work at a school.|من در مدرسه کار می‌کنم.
Сего'дня хоро'шая [пого'да].|The weather is good today.|امروز هوا خوب است.
За'втра я иду' в [магази'н].|Tomorrow I am going to the shop.|فردا به مغازه می‌روم.
Я не [зна'ю].|I don't know.|نمی‌دانم.
Мы [говори'м] по-ру'сски.|We speak Russian.|ما روسی صحبت می‌کنیم.
Я хочу' [пить].|I want to drink.|می‌خواهم بنوشم.
Он [рабо'тает] в больни'це.|He works in a hospital.|او در بیمارستان کار می‌کند.
Ма'ма гото'вит [у'жин].|Mom is cooking dinner.|مامان شام می‌پزد.
Мой оте'ц врач.|My father is a doctor.|پدرم پزشک است.
Это но'вый [стол].|This is a new table.|این یک میز جدید است.
В ко'мнате есть [окно'].|There is a window in the room.|در اتاق یک پنجره هست.
Я пишу' [письмо'].|I am writing a letter.|من نامه می‌نویسم.
Мы лю'бим [хлеб] и сыр.|We love bread and cheese.|ما نان و پنیر دوست داریم.
Где [вокза'л]?|Where is the train station?|ایستگاه قطار کجاست؟
Э'то мой [город].|This is my city.|این شهر من است.
Он [бы'стрый] ма'льчик.|He is a quick boy.|او پسر چابکی است.
Это [дорого'й] магази'н.|This is an expensive shop.|این یک فروشگاه گران است.
Э'то [дешёвый] телефо'н.|This is a cheap phone.|این یک تلفن ارزان است.
Мой дом [большо'й].|My house is big.|خانهٔ من بزرگ است.
У нас [ма'ленькая] ко'мната.|We have a small room.|ما اتاق کوچکی داریم.
На столе' [чёрный] ко'фе.|There is black coffee on the table.|روی میز قهوهٔ سیاه است.
Мы [идём] в шко'лу.|We are going to school.|ما به مدرسه می‌رویم.
Я [е'ду] на рабо'ту на авто'бусе.|I am going to work by bus.|من با اتوبوس به سر کار می‌روم.
Она' [смо'трит] фильм.|She is watching a film.|او فیلم تماشا می‌کند.
Ты [понима'ешь] меня'?|Do you understand me?|مرا می‌فهمی؟
Я [слу'шаю] му'зыку.|I listen to music.|من موسیقی گوش می‌دهم.
Он [ду'мает] о рабо'те.|He thinks about work.|او به کار فکر می‌کند.
Мы [за'втракаем] в семь часо'в.|We have breakfast at seven.|ما ساعت هفت صبحانه می‌خوریم.
Де'ти [игра'ют] в саду'.|The children play in the garden.|بچه‌ها در باغ بازی می‌کنند.
Сего'дня о'чень [жа'рко].|It is very hot today.|امروز خیلی گرم است.
Зимо'й [хо'лодно].|It is cold in winter.|زمستان سرد است.
Я о'чень [уста'л].|I am very tired.|من خیلی خسته‌ام.
Э'то [пра'вильно].|That is correct.|درست است.
Я [говорю'] по-англи'йски.|I speak English.|من انگلیسی صحبت می‌کنم.
""".strip()

# alphabet: (Upper+lower, transliteration, Persian hint, English hint, example (stress marked), example meaning)
ALPHABET = [
 ("Аа", "a", "«آ» کوتاه (a)", "like “a” in father", "а'вгуст", "August"),
 ("Бб", "b", "«ب»", "like “b”", "брат", "brother"),
 ("Вв", "v", "«و» لب‌ودندانی (v)", "like “v”", "вода'", "water"),
 ("Гг", "g", "«گ»", "like “g” in go", "го'род", "city"),
 ("Дд", "d", "«د»", "like “d”", "дом", "house"),
 ("Ее", "ye / e", "«یِ» (بعد از همخوان فقط نرم‌کننده)", "like “ye” in yes", "не'т", "no"),
 ("Ёё", "yo", "«یُ»", "like “yo” in yonder", "ёлка", "fir tree"),
 ("Жж", "zh", "«ژ»", "like “s” in measure", "жена'", "wife"),
 ("Зз", "z", "«ز»", "like “z”", "зима'", "winter"),
 ("Ии", "i", "«ی» کشیده (ee)", "like “ee” in see", "и'мя", "name"),
 ("Йй", "y", "«ی» کوتاه (y)", "like “y” in boy", "мой", "my"),
 ("Кк", "k", "«ک»", "like “k”", "кни'га", "book"),
 ("Лл", "l", "«ل»", "like “l”", "ла'мпа", "lamp"),
 ("Мм", "m", "«م»", "like “m”", "ма'ма", "mom"),
 ("Нн", "n", "«ن»", "like “n”", "нос", "nose"),
 ("Оо", "o", "«اُ» (o) – بی‌تکیه: «آ»", "like “o” in more (unstressed: “a”)", "окно'", "window"),
 ("Пп", "p", "«پ»", "like “p”", "па'па", "dad"),
 ("Рр", "r", "«ر» غلتان", "rolled “r”", "рука'", "hand"),
 ("Сс", "s", "«س»", "like “s”", "стол", "table"),
 ("Тт", "t", "«ت»", "like “t”", "три", "three"),
 ("Уу", "u", "«او» (oo)", "like “oo” in moon", "у'тро", "morning"),
 ("Фф", "f", "«ف»", "like “f”", "фо'то", "photo"),
 ("Хх", "kh", "«خ»", "like “ch” in Bach", "хлеб", "bread"),
 ("Цц", "ts", "«تس»", "like “ts” in cats", "цена'", "price"),
 ("Чч", "ch", "«چ» نرم", "like “ch” in cheese", "час", "hour"),
 ("Шш", "sh", "«ش» (سفت)", "like “sh” (hard)", "шко'ла", "school"),
 ("Щщ", "shch", "«شچ» نرم (ش نرمِ بلند)", "long soft “sh”", "борщ", "borscht"),
 ("Ъъ", "(hard sign)", "علامت سخت: جداکننده", "hard sign: no sound, separates", "объём", "volume"),
 ("Ыы", "y", "صدایی بین «ای» و «او» (ɨ)", "a sound between “i” and “u”", "мы", "we"),
 ("Ьь", "(soft sign)", "علامت نرم: همخوان قبلی را نرم می‌کند", "soft sign: softens the consonant before it", "день", "day"),
 ("Ээ", "e", "«اِ» باز (e)", "like “e” in bed", "э'то", "this"),
 ("Юю", "yu", "«یو»", "like “you”", "юг", "south"),
 ("Яя", "ya", "«یا»", "like “ya” in yard", "я", "I"),
]

# reading rules: (title (fa, en), body (fa, en), examples)
RULES = [
 (("حروف باصدای سخت و نرم", "Hard and soft vowels"), ("ده مصوت در پنج جفت‌اند: а–я، э–е، о–ё، у–ю، ы–и. مصوت «نرم» (я، е، ё، ю، и) همخوان قبلی را نرم می‌کند: мат (مات) ≠ мять. بعد از همخوان نرم می‌شود: «ی» + مصوت.", "Ten vowel letters form five pairs: а–я, э–е, о–ё, у–ю, ы–и. The “soft” vowel (я, е, ё, ю, и) softens the preceding consonant: мат ≠ мять."), "мат / мять · лук / люк"),
 (("علامت نرم ь و سخت ъ", "Soft sign ь and hard sign ъ"), ("ь صدا ندارد و همخوان قبلی را نرم می‌کند: день، мать. ъ خیلی کم است و بین پیشوند و ریشه می‌آید: объём.", "ь has no sound, it softens the consonant before it: день, мать. ъ is rare, between a prefix and a root: объём."), "день · мать · объём"),
 (("تکیه و تبدیل مصوت‌ها", "Stress and vowel reduction"), ("تکیه در روسی ثابت نیست و باید با هر واژه یاد گرفته شود (ما با علامت ´ نشان می‌دهیم). مصوت بی‌تکیه ضعیف می‌شود: «о» بی‌تکیه ≈ «а» (молоко' ← ملاکو)، «я/е» بی‌تکیه ≈ «ی» (язы'к ← ایزیک).", "Stress is not fixed and must be learned with each word (we mark it with ´). Unstressed vowels weaken: unstressed «о» sounds like «а» (молоко' ≈ malako), unstressed «я/е» like «и» (язы'к ≈ yizyk)."), "молоко' · вода' · язы'к"),
 (("همخوان‌های پایانی بی‌واک", "Final devoicing"), ("همخوان واک‌دار در پایان واژه بی‌واک می‌شود: хлеб ← хлеп، друг ← دروک (k)، год ← گوت. همچنین پیش از همخوان بی‌واک.", "A voiced consonant at the end of a word is pronounced voiceless: хлеб ≈ khlyep, друг ≈ druk, год ≈ got."), "хлеб · друг · год"),
 (("ж، ш، ц سخت؛ ч، щ، й نرم", "ж, ш, ц always hard; ч, щ, й always soft"), ("ж و ш و ц همیشه سخت‌اند و ч و щ و й همیشه نرم‌اند، هر مصوتی بعدشان بیاید. پس بعد از آن‌ها «ы» نمی‌آید، «и» می‌آید (жить، шины).", "ж, ш, ц are always hard and ч, щ, й are always soft, whatever vowel follows. So after them one writes и, not ы (жить, шины)."), "жить · шина · ча'сто"),
 (("ё و نقطه‌هایش", "ё and its dots"), ("در متن‌های معمول ё را اغلب بدون دو نقطه (е) می‌نویسند؛ ё همیشه تکیه‌دار است: всё، её. در این ربات دو نقطه نشان داده می‌شود.", "In ordinary texts ё is often printed as е; ё is always stressed: всё, её. This bot shows the two dots."), "ёлка · всё · её"),
]

# (id, (title fa, en), pattern, example, (example fa, en), (body fa, en))
GRAMMAR = [
 ("gender", ("جنسیت اسم‌ها", "Gender of nouns"), "мужской · женский · средний", "стол, кни'га, окно'", ("میز (مذکر)، کتاب (مؤنث)، پنجره (خنثی)", "table (m), book (f), window (n)"),
  ("روسی سه جنس دارد و ختم اسم معمولاً جنس را نشان می‌دهد: همخوان یا -й ← مذکر (стол)؛ -а/-я ← مؤنث (кни'га)؛ -о/-е ← خنثی (окно')؛ -ь ← مذکر یا مؤنث (день m، дверь f). در روسی «a / the» وجود ندارد.", "Russian has three genders and the ending usually shows it: consonant or -й → masculine (стол); -а/-я → feminine (кни'га); -о/-е → neuter (окно'); -ь → masculine or feminine (день m, дверь f). There are no articles (“a / the”).")),
 ("tobe", ("«بودن» در حال حاضر حذف می‌شود", "“To be” is dropped in the present"), "A — B", "Я студе'нт. Э'то кни'га.", ("من دانشجو هستم. این کتاب است.", "I am a student. This is a book."),
  ("در زمان حال از فعل «быть» استفاده نمی‌شود: «Он врач» = «او پزشک است». برای اشاره: «Это …» (این … است). برای داشتن: «У меня' есть …» (نزد من … هست). نفی: «У меня' нет …».", "In the present tense «быть» is not used: «Он врач» = “He is a doctor”. For pointing: «Это …» (this is …). For having: «У меня' есть …» (“at me there is”). Negation: «У меня' нет …».")),
 ("plural", ("جمع", "Plural"), "-ы / -и", "стол → столы'; кни'га → кни'ги", ("میزها، کتاب‌ها", "tables, books"),
  ("جمع معمولاً با -ы یا -и ساخته می‌شود: стол → столы'، кни'га → кни'ги (بعد از г، к، х، ж، ш، ч، щ همیشه -и). خنثی: -а/-я (окно' → о'кна). استثنا زیاد است: друг → друзья'، ребёнок → де'ти، челове'к → лю'ди.", "Plural is usually -ы or -и: стол → столы', кни'га → кни'ги (after г, к, х, ж, ш, ч, щ always -и). Neuter: -а/-я (окно' → о'кна). Many exceptions: друг → друзья', ребёнок → де'ти, челове'к → лю'ди.")),
 ("present", ("فعل‌ها در حال", "Present tense"), "я -ю · ты -ешь · он -ет · мы -ем · вы -ете · они -ют", "Я чита'ю. Ты чита'ешь.", ("می‌خوانم. می‌خوانی.", "I read. You read."),
  ("دو گروه صرف: گروه ۱ (-ешь): читать → я чита'ю, ты чита'ешь, он чита'ет, мы чита'ем, вы чита'ете, они чита'ют. گروه ۲ (-ишь): говори'ть → я говорю', ты говори'шь, он говори'т, мы говори'м, вы говори'те, они говоря'т.", "Two conjugations: group 1 (-ешь): читать → я чита'ю, ты чита'ешь, он чита'ет, мы чита'ем, вы чита'ете, они чита'ют. Group 2 (-ишь): говори'ть → я говорю', ты говори'шь, он говори'т, мы говори'м, вы говори'те, они говоря'т.")),
 ("past", ("گذشته", "Past tense"), "-л · -ла · -ло · -ли", "Он чита'л. Она' чита'ла.", ("او (مرد) می‌خواند/خواند. او (زن) …", "He read. She read."),
  ("گذشته ساده است: مصدر منهای -ть + -л (مذکر)، -ла (مؤنث)، -ло (خنثی)، -ли (جمع). فعل با جنس فاعل هماهنگ می‌شود، نه با شخص: я чита'л (مرد) / я чита'ла (زن).", "The past is easy: infinitive minus -ть + -л (m), -ла (f), -ло (n), -ли (pl). The verb agrees with the gender of the subject, not the person: я чита'л (male) / я чита'ла (female).")),
 ("cases", ("شش حالت دستوری", "The six cases"), "Им. Р. Д. В. Тв. Пр.", "Я вижу кни'гу.", ("کتاب را می‌بینم.", "I see the book."),
  ("اسم‌ها شش حالت دارند: نامی (кто/что؟) فاعل؛ ملکی (кого'/чего'؟) نبودن و مالکیت؛ بخشی/مفعول غیرمستقیم (кому'/чему'؟)؛ مفعولی (кого'/что؟) مفعول مستقیم؛ ابزاری (кем/чем؟) با/به‌وسیله؛ حرف‌اضافه‌ای (о ком/о чём؟) مکان و موضوع. برای شروع: مفعولی و حرف‌اضافه‌ای را تمرین کن.", "Nouns have six cases: nominative (who/what?) subject; genitive (of whom/what?) absence and possession; dative (to whom?) indirect object; accusative (whom/what?) direct object; instrumental (with whom/what?); prepositional (about whom/what?) location and topic. Start with the accusative and prepositional.")),
 ("accusative", ("مفعولی (винительный)", "Accusative"), "-а → -у · -я → -ю", "Я чита'ю кни'гу. Я ви'жу бра'та.", ("کتاب می‌خوانم. برادر را می‌بینم.", "I read a book. I see my brother."),
  ("مؤنث: -а ← -у (кни'га → кни'гу)، -я ← -ю (неде'ля → неде'лю). مذکر غیرجاندار و خنثی تغییر نمی‌کنند (стол، окно'). مذکر جاندار مثل ملکی می‌شود: брат → бра'та، друг → дру'га. بعد از «в/на» با حرکت (куда'؟): Я иду' в шко'лу.", "Feminine: -а → -у (кни'га → кни'гу), -я → -ю (неде'ля → неде'лю). Inanimate masculine and neuter don't change (стол, окно'). Animate masculine looks like the genitive: брат → бра'та, друг → дру'га. After в/на with motion (куда'?): Я иду' в шко'лу.")),
 ("prepositional", ("حرف‌اضافه‌ای (предложный)", "Prepositional"), "в/на + -е", "Я живу' в го'роде. Мы в шко'ле.", ("در شهر زندگی می‌کنم. ما در مدرسه‌ایم.", "I live in the city. We are at school."),
  ("برای مکان (где؟) با в (درون) و на (روی/رویداد): в до'ме، на рабо'те. پایانه -е: го'род → в го'роде، шко'ла → в шко'ле. برای «درباره»: о + -е (о ма'ме). استثنا: в саду'، в лесу'.", "For location (где?) with в (inside) and на (on/at events): в до'ме, на рабо'те. Ending -е: го'род → в го'роде, шко'ла → в шко'ле. For “about”: о + -е (о ма'ме). Exceptions: в саду', в лесу'.")),
 ("genitive", ("ملکی (родительный)", "Genitive"), "-а/-я · -ы/-и", "У меня' нет сестры'. Э'то кни'га дру'га.", ("خواهر ندارم. این کتابِ دوست است.", "I have no sister. This is a friend's book."),
  ("بعد از «нет» (نبودن)، «у» (نزدِ)، «из»، «для»، «без» و برای مالکیت. مؤنث: -а ← -ы (сестра' → сестры')، -я ← -и؛ مذکر: +а/+я (друг → дру'га). «У меня' есть брат» = «برادر دارم»؛ «У меня' нет бра'та».", "After «нет» (there is no), «у» (at), «из», «для», «без» and for possession. Feminine: -а → -ы (сестра' → сестры'), -я → -и; masculine: +а/+я (друг → дру'га). «У меня' есть брат» = “I have a brother”; «У меня' нет бра'та».")),
 ("motion", ("فعل‌های حرکت: идти / ходить، ехать / ездить", "Verbs of motion: идти / ходить, ехать / ездить"), "идти' (یک‌سویه) · ходи'ть (عادت/رفت‌وبرگشت)", "Я иду' в шко'лу. Я хожу' в шко'лу ка'ждый день.", ("الان به مدرسه می‌روم. هر روز به مدرسه می‌روم.", "I'm going to school (now). I go to school every day."),
  ("هر مفهوم «رفتن» دو فعل دارد: یک‌سویه/الان (идти' پیاده، е'хать با وسیله) و عادت/چندسویه/رفت‌وبرگشت (ходи'ть پیاده، е'здить با وسیله). «Я иду' в магази'н» (الان، یک مسیر)، «Я хожу' в магази'н» (معمولاً/می‌روم و برمی‌گردم)، «Я е'ду на рабо'ту» (الان با وسیله)، «Я е'зжу на рабо'ту ка'ждый день».", "Each idea of “going” has two verbs: one-direction/now (идти' on foot, е'хать by vehicle) and habitual/round trip (ходи'ть on foot, е'здить by vehicle). «Я иду' в магази'н» (now, one way), «Я хожу' в магази'н» (usually / go and come back), «Я е'ду на рабо'ту» (now, by vehicle), «Я е'зжу на рабо'ту ка'ждый день».")),
 ("aspect", ("نمود فعل: ناقص و کامل", "Verb aspect: imperfective vs perfective"), "дела'ть / сде'лать", "Я чита'л кни'гу. Я прочита'л кни'гу.", ("مشغول خواندن بودم / کتاب را (تا آخر) خواندم.", "I was reading the book / I read the book (finished)."),
  ("بیشتر فعل‌ها جفت دارند: ناقص (فرایند/تکرار: чита'ть) و کامل (نتیجه، یک‌بار: прочита'ть). نمود کامل در حال، آینده ساده می‌سازد: «Я прочита'ю» (خواهم خواند، تا آخر). در ابتدا فقط بدان که جفت‌ها وجود دارند و آن‌ها را با هم یاد بگیر.", "Most verbs come in pairs: imperfective (process/repetition: чита'ть) and perfective (result, one-time: прочита'ть). The perfective has no present, its “present” form means the future: «Я прочита'ю» (I will read it through). At first just know the pairs exist and learn them together.")),
 ("questions", ("جمله‌های پرسشی", "Questions"), "کلمهٔ پرسشی + جمله · «ли»", "Где ты живёшь? Ты живёшь в Москве'?", ("کجا زندگی می‌کنی؟ در مسکو زندگی می‌کنی؟", "Where do you live? Do you live in Moscow?"),
  ("پرسش بله/خیر فقط با آهنگ صدا ساخته می‌شود (آهنگ بالا روی کلمهٔ مورد پرسش): «Ты чита'ешь?». با کلمهٔ پرسشی: кто، что، где، куда'، когда'، почему'، как. ترتیب جمله انعطاف‌پذیر است.", "Yes/no questions are made with intonation only (rising on the word asked about): «Ты чита'ешь?». With a question word: кто, что, где, куда', когда', почему', как. Word order is flexible.")),
]

# drills: (sentence with ___, options, right, explanation (fa, en))
DRILLS = [
 ("Я чита'ю ___ .", ["кни'гу", "кни'га", "кни'ге", "кни'ги"], "кни'гу", ("مفعولی مؤنث: -а ← -у", "accusative feminine: -а → -у")),
 ("Я живу' в ___ .", ["го'роде", "го'род", "го'рода", "го'роду"], "го'роде", ("حرف‌اضافه‌ای (در شهر): -е", "prepositional (in the city): -е")),
 ("У меня' нет ___ .", ["сестры'", "сестра'", "сестру'", "сестре'"], "сестры'", ("ملکی بعد از «нет»: -а ← -ы", "genitive after «нет»: -а → -ы")),
 ("Я иду' в ___ .", ["шко'лу", "шко'ла", "шко'ле", "шко'лы"], "шко'лу", ("مفعولی با حرکت (куда'؟)", "accusative with motion (куда'?)")),
 ("Я говорю' о ___ .", ["ма'ме", "ма'ма", "ма'му", "ма'мы"], "ма'ме", ("о + حرف‌اضافه‌ای: -е", "о + prepositional: -е")),
 ("Я ви'жу ___ .", ["бра'та", "брат", "бра'ту", "бра'те"], "бра'та", ("مفعولی مذکر جاندار = ملکی", "animate masculine accusative = genitive")),
 ("Это кни'га ___ .", ["дру'га", "друг", "дру'гу", "дру'ге"], "дру'га", ("ملکی: +а", "genitive: +а")),
 ("Мы живём в ___ .", ["кварти'ре", "кварти'ра", "кварти'ру", "кварти'ры"], "кварти'ре", ("در آپارتمان: حرف‌اضافه‌ای -е", "in the apartment: prepositional -е")),
 ("Я люблю' ___ .", ["ма'му", "ма'ма", "ма'ме", "ма'мы"], "ма'му", ("مفعولی مؤنث: -а ← -у", "accusative feminine: -а → -у")),
 ("Он рабо'тает в ___ .", ["магази'не", "магази'н", "магази'на", "магази'ну"], "магази'не", ("حرف‌اضافه‌ای (مکان): -е", "prepositional (place): -е")),
 ("Я ___ в шко'лу пешко'м сейча'с.", ["иду'", "хожу'", "е'ду", "е'зжу"], "иду'", ("الان، پیاده، یک‌سویه: идти'", "now, on foot, one direction: идти'")),
 ("Я ка'ждый день ___ на рабо'ту на авто'бусе.", ["е'зжу", "е'ду", "иду'", "хожу'"], "е'зжу", ("هر روز، با وسیله: е'здить", "every day, by vehicle: е'здить")),
 ("Мы сейча'с ___ в Москву' на по'езде.", ["е'дем", "е'здим", "идём", "хо'дим"], "е'дем", ("الان، با قطار: е'хать", "now, by train: е'хать")),
 ("Он ка'ждое у'тро ___ в парк.", ["хо'дит", "идёт", "е'дет", "е'здит"], "хо'дит", ("هر صبح، پیاده، عادت: ходи'ть", "every morning, on foot, habit: ходи'ть")),
]
