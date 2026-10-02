"""German: example sentences, grammar notes, pronunciation rules, case drills (own work; Persian/English texts unreviewed by native speakers)."""
# text | English | Persian     ([bracket] marks the word used for cloze exercises: it must be a headword of the vocabulary, noun without article)
SENT = """
Das [Wasser] ist kalt.|The water is cold.|آب سرد است.
Ich möchte einen [Kaffee].|I would like a coffee.|من یک قهوه می‌خواهم.
Er ist mein [Bruder].|He is my brother.|او برادر من است.
Meine [Mutter] kocht heute.|My mother is cooking today.|مادرم امروز آشپزی می‌کند.
Wir wohnen in einer großen [Stadt].|We live in a big city.|ما در یک شهر بزرگ زندگی می‌کنیم.
Das [Buch] ist sehr gut.|The book is very good.|این کتاب خیلی خوب است.
Ich trinke jeden Morgen [Tee].|I drink tea every morning.|من هر صبح چای می‌نوشم.
Der [Zug] ist schnell.|The train is fast.|قطار سریع است.
Sie hat ein neues [Auto].|She has a new car.|او یک ماشین جدید دارد.
Wo ist der [Bahnhof]?|Where is the train station?|ایستگاه قطار کجاست؟
Ich habe keine [Zeit].|I have no time.|من وقت ندارم.
Das [Essen] ist heiß.|The food is hot.|غذا داغ است.
Mein [Vater] arbeitet im Büro.|My father works in the office.|پدرم در دفتر کار می‌کند.
Wir müssen heute [lernen].|We have to study today.|ما امروز باید درس بخوانیم.
Kannst du mir [helfen]?|Can you help me?|می‌توانی به من کمک کنی؟
Ich will heute nicht [arbeiten].|I don't want to work today.|امروز نمی‌خواهم کار کنم.
Die [Schule] beginnt um acht Uhr.|School starts at eight o'clock.|مدرسه ساعت هشت شروع می‌شود.
Der [Lehrer] ist sehr freundlich.|The teacher is very friendly.|معلم خیلی مهربان است.
Das [Kind] ist müde.|The child is tired.|بچه خسته است.
Wir kaufen [Brot] und Käse.|We buy bread and cheese.|ما نان و پنیر می‌خریم.
Ich komme aus dem [Iran].|I come from Iran.|من اهل ایران هستم.
Die [Wohnung] ist klein, aber schön.|The apartment is small but nice.|آپارتمان کوچک ولی زیباست.
Hast du einen [Freund]?|Do you have a (male) friend?|آیا دوست (پسر) داری؟
Ich lese gern ein [Buch].|I like reading a book.|دوست دارم کتاب بخوانم.
Das [Wetter] ist heute schön.|The weather is nice today.|هوا امروز خوب است.
Die [Straße] ist lang.|The street is long.|خیابان طولانی است.
Ich brauche mein [Handy].|I need my mobile phone.|به تلفن همراهم نیاز دارم.
Wir sind morgen im [Restaurant].|We are in the restaurant tomorrow.|فردا ما در رستوران هستیم.
Er trinkt [Milch] zum Frühstück.|He drinks milk for breakfast.|او برای صبحانه شیر می‌نوشد.
Meine [Schwester] ist Ärztin.|My sister is a doctor.|خواهرم پزشک است.
Ich [verstehe] das nicht.|I don't understand that.|من این را نمی‌فهمم.
Die [Frau] liest ein Buch.|The woman is reading a book.|زن کتاب می‌خواند.
Der [Mann] hat einen Hund.|The man has a dog.|مرد یک سگ دارد.
Ich [wohne] in Berlin.|I live in Berlin.|من در برلین زندگی می‌کنم.
Wir [spielen] heute Fußball.|We play football today.|ما امروز فوتبال بازی می‌کنیم.
Sie [kauft] ein Brot.|She buys a bread.|او یک نان می‌خرد.
Das Zimmer ist [groß].|The room is big.|اتاق بزرگ است.
Der Kaffee ist zu [heiß].|The coffee is too hot.|قهوه بیش از حد داغ است.
Die Suppe ist [kalt].|The soup is cold.|سوپ سرد است.
Mein Auto ist [alt].|My car is old.|ماشین من قدیمی است.
Das Hotel ist [teuer].|The hotel is expensive.|هتل گران است.
Das Brot ist [billig].|The bread is cheap.|نان ارزان است.
Die Aufgabe ist [leicht].|The task is easy.|تمرین آسان است.
Ich bin sehr [müde].|I am very tired.|من خیلی خسته‌ام.
Die Katze ist [klein].|The cat is small.|گربه کوچک است.
Die Tür ist [offen].|The door is open.|در باز است.
Der Apfel ist [rot].|The apple is red.|سیب قرمز است.
Der [Garten] ist grün.|The garden is green.|باغچه سبز است.
Ich möchte ein [Zimmer] für zwei Nächte.|I would like a room for two nights.|یک اتاق برای دو شب می‌خواهم.
Wir [fahren] morgen nach Hamburg.|We are travelling to Hamburg tomorrow.|فردا به هامبورگ می‌رویم.
Er [schläft] noch.|He is still sleeping.|او هنوز خواب است.
Ich [lerne] Deutsch.|I am learning German.|من آلمانی یاد می‌گیرم.
""".strip()

# (id, (title fa, en), pattern, example, (example fa, en), (body fa, en))
GRAMMAR = [
 ("gender", ("Nomen و جنسیت: der / die / das", "Nouns and gender: der / die / das"), "der · die · das", "der Tisch, die Lampe, das Buch", ("میز، چراغ، کتاب", "table, lamp, book"),
  ("هر اسم آلمانی جنسیت دارد: مذکر (der)، مؤنث (die)، خنثی (das). جنسیت را همیشه همراه اسم یاد بگیر («der Tisch»، نه فقط «Tisch»). همهٔ اسم‌ها با حرف بزرگ نوشته می‌شوند.\nراهنمای سرانگشتی: -ung، -heit، -keit، -schaft، -ion ← معمولاً die؛ -chen، -lein ← das؛ فصل‌ها، روزها، ماه‌ها ← der. استثنا زیاد است، پس با تکرار فاصله‌دار یاد بگیر.",
   "Every German noun has a gender: masculine (der), feminine (die) or neuter (das). Always learn the article with the noun (“der Tisch”, not just “Tisch”). All nouns are capitalised.\nRules of thumb: -ung, -heit, -keit, -schaft, -ion → usually die; -chen, -lein → das; seasons, days, months → der. There are many exceptions, so learn them with spaced repetition.")),
 ("plural", ("جمع بستن", "Plural forms"), "-e · -er · -(e)n · -s · ¨", "das Kind → die Kinder", ("کودک ← کودکان", "child → children"),
  ("جمع در آلمانی چند الگو دارد: -e (Tisch→Tische)، ¨-e با اومالوت (Stuhl→Stühle)، -er (Kind→Kinder)، -(e)n (Frau→Frauen)، -s (Auto→Autos)، بدون پایانه (Lehrer). در جمع همیشه «die» می‌آید. جمع را همراه اسم یاد بگیر.",
   "German has several plural patterns: -e (Tisch→Tische), umlaut + -e (Stuhl→Stühle), -er (Kind→Kinder), -(e)n (Frau→Frauen), -s (Auto→Autos), or no ending (Lehrer). The plural article is always “die”. Learn the plural together with the noun.")),
 ("present", ("فعل‌ها در زمان حال", "Present tense of verbs"), "ich -e · du -st · er -t · wir -en · ihr -t · sie -en", "ich lerne, du lernst, er lernt", ("یاد می‌گیرم، یاد می‌گیری، یاد می‌گیرد", "I learn, you learn, he learns"),
  ("ریشهٔ فعل (مصدر منهای -en) + پایانه‌های ثابت. بعضی فعل‌ها در du/er تغییر مصوت می‌دهند: essen → du isst، lesen → er liest، fahren → du fährst، sprechen → er spricht. «sein» و «haben» بی‌قاعده‌اند: ich bin, du bist, er ist / ich habe, du hast, er hat.",
   "Verb stem (infinitive minus -en) + fixed endings. Some verbs change the vowel for du/er: essen → du isst, lesen → er liest, fahren → du fährst, sprechen → er spricht. “sein” and “haben” are irregular: ich bin, du bist, er ist / ich habe, du hast, er hat.")),
 ("wordorder", ("ترتیب جمله: فعل در جایگاه دوم", "Word order: the verb is second"), "Subjekt + Verb + … / Zeit + Verb + Subjekt", "Heute lerne ich Deutsch.", ("امروز من آلمانی یاد می‌گیرم.", "Today I learn German."),
  ("در جملهٔ خبری، فعل صرف‌شده همیشه در جایگاه دوم است؛ اگر چیز دیگری (مثلاً زمان) اول بیاید، فاعل بعد از فعل می‌آید: «Heute lerne ich…». در پرسش بدون کلمهٔ پرسشی فعل اول است: «Lernst du Deutsch?». با کلمهٔ پرسشی: «Was lernst du?». بعد از weil فعل به آخر می‌رود: «…, weil ich Zeit habe.»",
   "In a statement the conjugated verb is always in second position; if something else (e.g. time) comes first, the subject follows the verb: “Heute lerne ich …”. Yes/no questions start with the verb: “Lernst du Deutsch?”. With a question word: “Was lernst du?”. After “weil” the verb goes to the end: “…, weil ich Zeit habe.”")),
 ("cases", ("چهار حالت: Nominativ, Akkusativ, Dativ, Genitiv", "The four cases"), "N: der/die/das · A: den/die/das · D: dem/der/dem · G: des/der/des", "Ich sehe den Mann.", ("من آن مرد را می‌بینم.", "I see the man."),
  ("Nominativ: فاعل. Akkusativ: مفعول مستقیم. Dativ: مفعول غیرمستقیم / بعد از mit, aus, bei, nach, von, zu. Genitiv: مالکیت. فقط مذکر در Akkusativ عوض می‌شود: der → den (ein → einen). در Dativ: dem / der / dem و جمع «den + n». کار با مثال: Ich sehe den Mann (Akk.). Ich helfe dem Mann (Dat.).",
   "Nominative: subject. Accusative: direct object. Dative: indirect object / after mit, aus, bei, nach, von, zu. Genitive: possession. Only the masculine changes in the accusative: der → den (ein → einen). Dative: dem / der / dem, plural “den + n”. Examples: Ich sehe den Mann (Acc.). Ich helfe dem Mann (Dat.).")),
 ("negation", ("نفی: nicht و kein", "Negation: nicht vs kein"), "kein + اسم · nicht + بقیه", "Ich habe keine Zeit. / Ich komme nicht.", ("وقت ندارم. / نمی‌آیم.", "I have no time. / I'm not coming."),
  ("اسمِ بدون artikel یا با «ein» را با kein نفی کن (ein Buch → kein Buch). فعل، صفت و بقیه را با nicht نفی کن (Ich komme nicht. Das ist nicht gut.). kein مثل ein صرف می‌شود: keine Zeit، keinen Bruder.",
   "Negate nouns with “ein” or no article with kein (ein Buch → kein Buch). Negate verbs, adjectives and the rest with nicht (Ich komme nicht. Das ist nicht gut.). kein declines like ein: keine Zeit, keinen Bruder.")),
 ("modal", ("افعال کمکی: können, müssen, wollen, möchten", "Modal verbs"), "Modalverb (2.) … Infinitiv (آخر)", "Ich möchte einen Kaffee trinken.", ("می‌خواهم یک قهوه بنوشم.", "I would like to drink a coffee."),
  ("فعل کمکی در جایگاه دوم صرف می‌شود و فعل اصلی به شکل مصدر در آخر جمله می‌آید: «Ich kann gut schwimmen.»، «Wir müssen lernen.»، «Er will gehen.». ich/er بدون پایانه: ich kann، er kann؛ du kannst.",
   "The modal verb is conjugated in second position and the main verb goes to the end as an infinitive: “Ich kann gut schwimmen.”, “Wir müssen lernen.”, “Er will gehen.” ich/er take no ending: ich kann, er kann; du kannst.")),
 ("separable", ("فعل‌های جداشدنی", "Separable verbs"), "aufstehen → ich stehe … auf", "Ich stehe um sieben Uhr auf.", ("ساعت هفت بیدار می‌شوم.", "I get up at seven."),
  ("بعضی فعل‌ها پیشوند جداشدنی دارند (auf-, an-, ein-, mit-, zu-…). در جملهٔ اصلی پیشوند به آخر جمله می‌رود: aufstehen → «Ich stehe um sieben Uhr auf.»، anrufen → «Ich rufe dich an.»",
   "Some verbs have a separable prefix (auf-, an-, ein-, mit-, zu- …). In a main clause the prefix goes to the end: aufstehen → “Ich stehe um sieben Uhr auf.”, anrufen → “Ich rufe dich an.”")),
 ("perfekt", ("گذشتهٔ نقلی (Perfekt)", "The perfect tense (Perfekt)"), "haben / sein (2.) … Partizip II (آخر)", "Ich habe Kaffee getrunken. / Er ist gegangen.", ("قهوه نوشیدم. / او رفت.", "I drank coffee. / He went."),
  ("گذشته در گفتار: haben یا sein در جایگاه دوم + Partizip II در آخر. بیشتر فعل‌ها haben می‌گیرند؛ فعل‌های حرکت/تغییر حالت (gehen, kommen, fahren, bleiben) sein. Partizip II: ge-…-t (gemacht) یا ge-…-en (gegangen).",
   "Spoken past: haben or sein in second position + Partizip II at the end. Most verbs use haben; verbs of motion/change of state (gehen, kommen, fahren, bleiben) use sein. Partizip II: ge-…-t (gemacht) or ge-…-en (gegangen).")),
 ("prepositions", ("حروف اضافه: Akkusativ / Dativ / Wechsel", "Prepositions: accusative / dative / two-way"), "mit, aus, bei, nach, von, zu + Dativ", "Ich fahre mit dem Bus.", ("با اتوبوس می‌روم.", "I go by bus."),
  ("همیشه Dativ: mit, aus, bei, nach, von, zu. همیشه Akkusativ: für, ohne, durch, gegen. حروف دوحالته (in, auf, an, über, unter, vor, hinter, neben, zwischen): «Wo?» (جا) ← Dativ: Ich bin in der Schule. «Wohin?» (جهت) ← Akkusativ: Ich gehe in die Schule.",
   "Always dative: mit, aus, bei, nach, von, zu. Always accusative: für, ohne, durch, gegen. Two-way prepositions (in, auf, an, über, unter, vor, hinter, neben, zwischen): “Wo?” (location) → dative: Ich bin in der Schule. “Wohin?” (direction) → accusative: Ich gehe in die Schule.")),
 ("time", ("زمان و ساعت", "Telling the time"), "Es ist … Uhr · um … Uhr", "Es ist acht Uhr. Um halb neun.", ("ساعت هشت است. ساعت هشت و نیم.", "It is eight o'clock. At half past eight."),
  ("«Wie spät ist es?» ← «Es ist drei Uhr.». «Um wie viel Uhr?» ← «Um drei Uhr.». «halb neun» یعنی ۸:۳۰ (نیم ساعت مانده به نه!). Viertel nach / vor = ربع گذشته / به. روزها با «am» (am Montag)، ماه‌ها با «im» (im Mai).",
   "“Wie spät ist es?” → “Es ist drei Uhr.” “Um wie viel Uhr?” → “Um drei Uhr.” “halb neun” means 8:30 (half an hour TO nine!). Viertel nach / vor = quarter past / to. Days take “am” (am Montag), months “im” (im Mai).")),
]

# pronunciation / spelling rules: (title (fa, en), body (fa, en), examples)
SOUNDS = [
 (("اومالوت: ä ö ü", "Umlauts: ä ö ü"), ("ä شبیه «اِ» باز (مثل e در bed)، ö شبیه «اُ» با لب گرد و زبان «اِ»، ü شبیه «ای» با لب گرد (مثل ü/ي در «ایـ» با لب غنچه).", "ä like the e in “bed”, ö like “e” with rounded lips (as in French “peu”), ü like “ee” with rounded lips."), "Mädchen · schön · Tür · Bücher"),
 (("ß و ss", "ß and ss"), ("ß یعنی «س» تیز (ss) بعد از مصوت بلند یا دوگانه: Straße، heißen. بعد از مصوت کوتاه ss می‌نویسند: essen.", "ß is a sharp “ss” after a long vowel or diphthong: Straße, heißen. After a short vowel one writes ss: essen."), "Straße · heißen · essen"),
 (("ch: دو تلفظ", "ch: two sounds"), ("بعد از i، e، ä، ö، ü، ei، eu: نرم مثل «ش» ملایم (ich-Laut): ich، Küche. بعد از a، o، u، au: مثل «خ» (ach-Laut): Buch، acht.", "After i, e, ä, ö, ü, ei, eu: soft, like a hissed “h” (ich-sound): ich, Küche. After a, o, u, au: like “kh” (ach-sound): Buch, acht."), "ich · Küche · Buch · acht"),
 (("sch، sp، st", "sch, sp, st"), ("sch = «ش». sp و st در آغاز واژه «شپ» و «شت» خوانده می‌شود: sprechen = [شپِرشن]، Student = [شتودنت].", "sch = “sh”. At the start of a word sp and st sound like “shp” and “sht”: sprechen, Student."), "Schule · sprechen · Student · Stadt"),
 (("ei، ie، eu", "ei, ie, eu"), ("ei = «آی» (مثل «ای» در mine): nein، drei. ie = «ایـ» کشیده: Bier، Liebe. eu و äu = «اُی»: Deutsch، Häuser. (حواست باشد: ei و ie برعکس انگلیسی‌اند!)", "ei = “eye”: nein, drei. ie = long “ee”: Bier, Liebe. eu/äu = “oy”: Deutsch, Häuser. (careful: ei and ie are the reverse of what English readers expect)"), "nein · Bier · Deutsch · Häuser"),
 (("w، v، z، j", "w, v, z, j"), ("w مثل «و» لب‌ودندانی (v انگلیسی): Wasser. v معمولاً «ف»: Vater. z = «تس»: Zeit. j = «ی»: ja. s قبل از مصوت «ز» است: Sonne.", "w sounds like English v: Wasser. v is usually “f”: Vater. z = “ts”: Zeit. j = “y”: ja. s before a vowel is voiced “z”: Sonne."), "Wasser · Vater · Zeit · ja · Sonne"),
 (("r و -er", "r and -er"), ("r در آغاز واژه از ته گلو (غلتان کوتاه مثل «غ» ملایم) است؛ -er در پایان واژه تقریباً «آ» کوتاه: Lehrer ≈ لِرَ.", "Initial r is made in the throat (uvular); final -er sounds like a short “uh”: Lehrer ≈ “LEH-ruh”."), "rot · Lehrer · Wasser"),
 (("مصوت کوتاه و بلند", "Short and long vowels"), ("اگر بعد از مصوت دو همخوان بیاید معمولاً مصوت کوتاه است (Bett، kommen)؛ مصوت بلند: یک همخوان یا h (Tag، Bahn) یا مصوت دوتایی (Boot). کوتاه/بلند معنی را عوض می‌کند: Stadt/Staat.", "Two consonants after a vowel usually mean it is short (Bett, kommen); long: one consonant or h (Tag, Bahn) or a doubled vowel (Boot). Length can change meaning: Stadt/Staat."), "Bett · Tag · Bahn · Boot"),
 (("همخوان پایانی بی‌واک", "Final devoicing"), ("b، d، g در پایان هجا بی‌واک می‌شوند: Hund = [هونت]، Tag = [تاک]، ab = [آپ].", "b, d, g at the end of a syllable become p, t, k: Hund = “hunt”, Tag = “tahk”, ab = “ahp”."), "Hund · Tag · ab"),
]

# drills: sentence with ___, options, right, case/grammar name (fa, en)
DRILLS = [
 ("Ich sehe ___ Mann.", ["den", "der", "dem", "des"], "den", ("Akkusativ مذکر: der → den", "accusative masculine: der → den")),
 ("Ich gebe ___ Frau das Buch.", ["der", "die", "den", "dem"], "der", ("Dativ مؤنث: der", "dative feminine: der")),
 ("Das ist ___ Buch.", ["ein", "eine", "einen", "einem"], "ein", ("Nominativ خنثی: ein", "nominative neuter: ein")),
 ("Ich kaufe ___ Brot.", ["das", "der", "dem", "den"], "das", ("Akkusativ خنثی = Nominativ: das", "accusative neuter = nominative: das")),
 ("Wir fahren mit ___ Bus.", ["dem", "den", "der", "das"], "dem", ("mit + Dativ مذکر: dem", "mit + dative masculine: dem")),
 ("Ich wohne in ___ Stadt. (wo?)", ["der", "die", "den", "dem"], "der", ("Wechselpräposition + «wo?» ← Dativ مؤنث: der", "two-way preposition + “wo?” → dative feminine: der")),
 ("Er geht in ___ Schule. (wohin?)", ["die", "der", "dem", "das"], "die", ("«wohin؟» ← Akkusativ مؤنث: die", "“wohin?” → accusative feminine: die")),
 ("Ich habe ___ Bruder.", ["einen", "ein", "einem", "eine"], "einen", ("Akkusativ مذکر: einen", "accusative masculine: einen")),
 ("Das ist das Auto ___ Lehrers.", ["des", "dem", "den", "der"], "des", ("Genitiv مذکر: des (+s)", "genitive masculine: des (+s)")),
 ("Sie kommt aus ___ Schule.", ["der", "die", "den", "dem"], "der", ("aus + Dativ مؤنث: der", "aus + dative feminine: der")),
 ("Ich trinke ___ Kaffee.", ["einen", "ein", "einem", "einer"], "einen", ("Akkusativ مذکر: einen", "accusative masculine: einen")),
 ("Ich helfe ___ Kind.", ["dem", "das", "den", "der"], "dem", ("helfen + Dativ: dem", "helfen + dative: dem")),
 ("Ich habe ___ Zeit.", ["keine", "kein", "keinen", "nicht"], "keine", ("نفی اسم مؤنث: keine", "negating a feminine noun: keine")),
 ("Ich komme ___.", ["nicht", "kein", "keine", "nichts"], "nicht", ("نفی فعل: nicht", "negating a verb: nicht")),
]
