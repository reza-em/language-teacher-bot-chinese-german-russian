"""German A1-A2 vocabulary, curated for this project (own work, AI-assisted; NOT copied from Goethe/ÖSD lists or any dictionary).
Line format:  pos ; word ; extra ; English ; Persian ; level
pos: der/die/das = noun with article (extra = plural), v = verb (extra = 3rd person present / Perfekt), adj, adv, x = other (pronoun, preposition, conjunction, number, phrase)
level: 1 = A1, 2 = A2 (approximate; the lists are my own judgement of everyday frequency). Persian glosses are NOT reviewed by a native speaker."""
RAW = """
x;Hallo;;hello;سلام;1
x;Guten Morgen;;good morning;صبح بخیر;1
x;Guten Tag;;hello (daytime);روز بخیر;1
x;Guten Abend;;good evening;عصر بخیر;1
x;Gute Nacht;;good night;شب بخیر;1
x;Auf Wiedersehen;;goodbye;خداحافظ;1
x;Tschüss;;bye;فعلاً (خداحافظی دوستانه);1
x;Bitte;;please / you're welcome;لطفاً / خواهش می‌کنم;1
x;Danke;;thank you;ممنون;1
x;Entschuldigung;;excuse me / sorry;ببخشید;1
x;Ja;;yes;بله;1
x;Nein;;no;نه (خیر)؛ جواب منفی;1
x;Wie geht's?;;how are you?;حالت چطوره؟;1
x;Es geht mir gut;;I'm fine;حالم خوب است;1
x;Wie heißt du?;;what's your name?;اسمت چیست؟;1
x;Ich heiße;;my name is;اسم من ... است;1
x;ich;;I;من;1
x;du;;you (informal);تو;1
x;er;;he;او (مرد);1
x;sie;;she / they;او (زن) / آن‌ها;1
x;es;;it;آن (خنثی);1
x;wir;;we;ما;1
x;ihr;;you (plural);شما (جمع، غیررسمی);1
x;Sie;;you (formal);شما (رسمی);1
x;mein;;my;مال من;1
x;dein;;your (informal);مال تو;1
x;und;;and;و;1
x;oder;;or;یا;1
x;aber;;but;اما;1
x;nicht;;not;نه (نفی);1
x;kein;;no / not a;هیچ / نه (نفی اسم);1
x;auch;;also, too;همچنین، هم;1
x;sehr;;very;خیلی;1
x;hier;;here;اینجا;1
x;dort;;there;آنجا;1
x;wer;;who;چه کسی;1
x;was;;what;چه چیزی;1
x;wo;;where;کجا;1
x;wohin;;where to;به کجا;1
x;woher;;where from;از کجا;1
x;wann;;when;کی;1
x;wie;;how / like;چگونه;1
x;warum;;why;چرا;1
x;weil;;because;چون;1
x;mit;;with;با;1
x;ohne;;without;بدون;1
x;für;;for;برای;1
x;in;;in;در، توی (حرف اضافه);1
x;auf;;on;روی;1
x;an;;at / on (vertical);کنار / به;1
x;zu;;to;به (سمت);1
x;von;;from / of;از;1
x;aus;;out of / from;از (درون);1
x;nach;;to / after;به (شهر/کشور) / بعد از;1
x;bei;;at / near / with;نزدِ / در حین;1
x;über;;over / about;بالای / درباره;2
x;unter;;under;زیر;2
x;vor;;in front of / before;جلوی / قبل از;2
x;hinter;;behind;پشتِ;2
x;neben;;next to;کنارِ;2
x;zwischen;;between;بین;2
x;null;;zero;صفر;1
x;eins;;one;یک;1
x;zwei;;two;دو;1
x;drei;;three;سه;1
x;vier;;four;چهار;1
x;fünf;;five;پنج;1
x;sechs;;six;شش;1
x;sieben;;seven;هفت;1
x;acht;;eight;هشت;1
x;neun;;nine;نُه (عدد ۹);1
x;zehn;;ten;ده;1
x;zwanzig;;twenty;بیست;1
x;hundert;;hundred;صد;1
x;tausend;;thousand;هزار;1
die;Familie;-n;family;خانواده;1
der;Vater;Väter;father;پدر;1
die;Mutter;Mütter;mother;مادر;1
der;Bruder;Brüder;brother;برادر;1
die;Schwester;-n;sister;خواهر;1
der;Sohn;Söhne;son;پسر (فرزند);1
die;Tochter;Töchter;daughter;دختر (فرزند);1
das;Kind;-er;child;کودک;1
die;Eltern;(pl.);parents;والدین;1
der;Mann;Männer;man / husband;مرد / شوهر;1
die;Frau;-en;woman / wife;زن / همسر;1
der;Freund;-e;friend (male);دوست (مرد);1
die;Freundin;-nen;friend (female);دوست (زن);1
der;Junge;-n;boy;پسر بچه;1
das;Mädchen;-;girl;دختر بچه;1
der;Mensch;-en;person, human;انسان;1
der;Name;-n;name;نام;1
das;Haus;Häuser;house;خانه (ساختمان);1
die;Wohnung;-en;apartment;آپارتمان;1
das;Zimmer;-;room;اتاق;1
die;Küche;-n;kitchen;آشپزخانه;1
das;Bad;Bäder;bathroom;حمام;1
der;Tisch;-e;table;میز;1
der;Stuhl;Stühle;chair;صندلی;1
das;Bett;-en;bed;تخت;1
die;Tür;-en;door;در (درِ خانه);1
das;Fenster;-;window;پنجره;1
der;Garten;Gärten;garden;باغچه، باغ;2
das;Wasser;-;water;آب;1
das;Brot;-e;bread;نان;1
die;Milch;-;milk;شیر;1
der;Kaffee;-s;coffee;قهوه;1
der;Tee;-s;tea;چای;1
das;Essen;-;food, meal;غذا;1
das;Frühstück;-e;breakfast;صبحانه;1
das;Mittagessen;-;lunch;ناهار;2
das;Abendessen;-;dinner;شام;2
der;Apfel;Äpfel;apple;سیب;1
die;Banane;-n;banana;موز;1
das;Ei;-er;egg;تخم‌مرغ;1
das;Fleisch;-;meat;گوشت;1
der;Fisch;-e;fish;ماهی;1
der;Käse;-;cheese;پنیر;1
das;Obst;-;fruit;میوه;1
das;Gemüse;-;vegetables;سبزیجات;2
der;Reis;-;rice;برنج;1
die;Suppe;-n;soup;سوپ;2
der;Zucker;-;sugar;شکر;2
das;Salz;-;salt;نمک;2
die;Zeit;-en;time;زمان;1
der;Tag;-e;day;روز;1
die;Woche;-n;week;هفته;1
der;Monat;-e;month;ماه (تقویم);1
das;Jahr;-e;year;سال;1
der;Morgen;-;morning;صبح;1
der;Abend;-e;evening;عصر، غروب;1
die;Nacht;Nächte;night;شب;1
die;Stunde;-n;hour;ساعت (مدت);1
die;Minute;-n;minute;دقیقه;1
x;heute;;today;امروز;1
x;morgen;;tomorrow;فردا;1
x;gestern;;yesterday;دیروز;1
x;jetzt;;now;الان;1
x;immer;;always;همیشه;1
x;oft;;often;اغلب;1
x;manchmal;;sometimes;گاهی;2
x;nie;;never;هرگز;2
x;schon;;already;قبلاً، از پیش;2
x;noch;;still / yet;هنوز;2
x;Montag;;Monday;دوشنبه;1
x;Dienstag;;Tuesday;سه‌شنبه;1
x;Mittwoch;;Wednesday;چهارشنبه;1
x;Donnerstag;;Thursday;پنجشنبه;1
x;Freitag;;Friday;جمعه;1
x;Samstag;;Saturday;شنبه;1
x;Sonntag;;Sunday;یکشنبه;1
der;Winter;-;winter;زمستان;2
der;Sommer;-;summer;تابستان;2
das;Wetter;-;weather;هوا (آب‌وهوا);2
die;Sonne;-n;sun;خورشید;2
der;Regen;-;rain;باران;2
die;Stadt;Städte;city;شهر;1
das;Land;Länder;country;کشور;1
die;Straße;-n;street;خیابان;1
der;Bahnhof;Bahnhöfe;train station;ایستگاه قطار;1
der;Zug;Züge;train;قطار;1
der;Bus;-se;bus;اتوبوس;1
das;Auto;-s;car;ماشین;1
das;Fahrrad;Fahrräder;bicycle;دوچرخه;1
das;Flugzeug;-e;airplane;هواپیما;2
der;Flughafen;Flughäfen;airport;فرودگاه;2
die;Schule;-n;school;مدرسه;1
die;Universität;-en;university;دانشگاه;2
die;Arbeit;-en;work;کار;1
das;Büro;-s;office;دفتر;2
der;Lehrer;-;teacher (male);معلم (مرد);1
die;Lehrerin;-nen;teacher (female);معلم (زن);1
der;Student;-en;student (male);دانشجو (مرد);2
der;Arzt;Ärzte;doctor (male);پزشک (مرد);1
das;Krankenhaus;Krankenhäuser;hospital;بیمارستان;2
das;Geschäft;-e;shop, business;مغازه، کسب‌وکار;2
der;Supermarkt;Supermärkte;supermarket;سوپرمارکت;1
das;Restaurant;-s;restaurant;رستوران;1
das;Geld;-er;money;پول;1
der;Preis;-e;price;قیمت;2
das;Buch;Bücher;book;کتاب;1
das;Heft;-e;notebook;دفتر (مشق);2
der;Stift;-e;pen/pencil;قلم (مداد/خودکار);1
das;Telefon;-e;telephone;تلفن;1
das;Handy;-s;mobile phone;تلفن همراه;1
der;Computer;-;computer;رایانه;1
die;Tasche;-n;bag;کیف;1
der;Schlüssel;-;key;کلید;2
das;Foto;-s;photo;عکس;2
das;Wort;Wörter;word;واژه;1
die;Frage;-n;question;پرسش;1
die;Antwort;-en;answer;پاسخ;1
die;Sprache;-n;language;زبان;1
das;Problem;-e;problem;مشکل;2
die;Hilfe;-;help;کمک;2
der;Kopf;Köpfe;head;سر;2
die;Hand;Hände;hand;دست;1
das;Auge;-n;eye;چشم;2
das;Ohr;-en;ear;گوش;2
der;Mund;Münder;mouth;دهان;2
der;Fuß;Füße;foot;پا (کف);2
v;sein;ist / war / ist gewesen;to be;بودن;1
v;haben;hat / hatte / hat gehabt;to have;داشتن;1
v;werden;wird / wurde / ist geworden;to become;شدن;1
v;gehen;geht / ging / ist gegangen;to go (on foot);رفتن;1
v;kommen;kommt / kam / ist gekommen;to come;آمدن;1
v;machen;macht / machte / hat gemacht;to do, make;انجام دادن، ساختن;1
v;sagen;sagt / sagte / hat gesagt;to say;گفتن;1
v;sprechen;spricht / sprach / hat gesprochen;to speak;صحبت کردن;1
v;heißen;heißt / hieß / hat geheißen;to be called;نامیده شدن;1
v;wohnen;wohnt / wohnte / hat gewohnt;to live (reside);سکونت داشتن;1
v;leben;lebt / lebte / hat gelebt;to live (be alive);زندگی کردن;2
v;lernen;lernt / lernte / hat gelernt;to learn;یاد گرفتن;1
v;arbeiten;arbeitet / arbeitete / hat gearbeitet;to work;کار کردن;1
v;essen;isst / aß / hat gegessen;to eat;خوردن (غذا);1
v;trinken;trinkt / trank / hat getrunken;to drink;نوشیدن;1
v;kaufen;kauft / kaufte / hat gekauft;to buy;خریدن;1
v;sehen;sieht / sah / hat gesehen;to see;دیدن;1
v;hören;hört / hörte / hat gehört;to hear, listen;شنیدن;1
v;lesen;liest / las / hat gelesen;to read;خواندن (متن);1
v;schreiben;schreibt / schrieb / hat geschrieben;to write;نوشتن;1
v;spielen;spielt / spielte / hat gespielt;to play;بازی کردن;1
v;fahren;fährt / fuhr / ist gefahren;to drive, travel;رانندگی کردن، سفر کردن;1
v;fliegen;fliegt / flog / ist geflogen;to fly;پرواز کردن;2
v;laufen;läuft / lief / ist gelaufen;to run, walk;دویدن، راه رفتن;2
v;stehen;steht / stand / hat gestanden;to stand;ایستاده بودن;2
v;sitzen;sitzt / saß / hat gesessen;to sit;نشسته بودن;2
v;liegen;liegt / lag / hat gelegen;to lie (be lying);خوابیده/قرار داشتن;2
v;schlafen;schläft / schlief / hat geschlafen;to sleep;خوابیدن;1
v;aufstehen;steht auf / stand auf / ist aufgestanden;to get up;بلند شدن، از خواب برخاستن;2
v;geben;gibt / gab / hat gegeben;to give;دادن;1
v;nehmen;nimmt / nahm / hat genommen;to take;گرفتن، برداشتن;1
v;finden;findet / fand / hat gefunden;to find;پیدا کردن;1
v;suchen;sucht / suchte / hat gesucht;to search for;جستجو کردن;2
v;brauchen;braucht / brauchte / hat gebraucht;to need;نیاز داشتن;1
v;wollen;will / wollte / hat gewollt;to want;خواستن;1
v;können;kann / konnte / hat gekonnt;can, to be able to;توانستن;1
v;müssen;muss / musste / hat gemusst;must, have to;باید;1
v;möchten;möchte;would like to;دوست داشتن (مؤدبانه) / می‌خواهم;1
v;mögen;mag / mochte / hat gemocht;to like;دوست داشتن، پسندیدن;1
v;wissen;weiß / wusste / hat gewusst;to know (a fact);دانستن;1
v;kennen;kennt / kannte / hat gekannt;to know (a person/place);شناختن;1
v;verstehen;versteht / verstand / hat verstanden;to understand;فهمیدن;1
v;fragen;fragt / fragte / hat gefragt;to ask;پرسیدن;1
v;antworten;antwortet / antwortete / hat geantwortet;to answer;پاسخ دادن;2
v;helfen;hilft / half / hat geholfen;to help;کمک کردن;2
v;warten;wartet / wartete / hat gewartet;to wait;منتظر ماندن;2
v;öffnen;öffnet / öffnete / hat geöffnet;to open;باز کردن;2
v;schließen;schließt / schloss / hat geschlossen;to close;بستن;2
v;bleiben;bleibt / blieb / ist geblieben;to stay;ماندن;2
v;denken;denkt / dachte / hat gedacht;to think;فکر کردن;2
v;lieben;liebt / liebte / hat geliebt;to love;دوست داشتن (عشق);2
v;kochen;kocht / kochte / hat gekocht;to cook;پختن;2
v;besuchen;besucht / besuchte / hat besucht;to visit;دیدن کردن، ملاقات;2
v;treffen;trifft / traf / hat getroffen;to meet;ملاقات کردن;2
v;anrufen;ruft an / rief an / hat angerufen;to call (phone);تلفن زدن;2
adj;gut;;good;خوب;1
adj;schlecht;;bad;بد;1
adj;groß;;big, tall;بزرگ، قدبلند;1
adj;klein;;small;کوچک;1
adj;neu;;new;جدید;1
adj;alt;;old;پیر، قدیمی;1
adj;jung;;young;جوان;2
adj;schön;;beautiful, nice;زیبا، خوب;1
adj;hässlich;;ugly;زشت;2
adj;heiß;;hot;داغ، گرم;1
adj;kalt;;cold;سرد;1
adj;warm;;warm;گرم، ملایم;2
adj;schnell;;fast;سریع;1
adj;langsam;;slow;آهسته;1
adj;lang;;long;بلند، دراز;2
adj;kurz;;short;کوتاه;2
adj;teuer;;expensive;گران;1
adj;billig;;cheap;ارزان;1
adj;leicht;;easy, light;آسان، سبک;1
adj;schwer;;difficult, heavy;سخت، سنگین;1
adj;müde;;tired;خسته;1
adj;krank;;sick;بیمار;2
adj;gesund;;healthy;سالم;2
adj;glücklich;;happy;خوشحال;2
adj;traurig;;sad;غمگین;2
adj;freundlich;;friendly;مهربان، دوستانه;2
adj;richtig;;correct;درست;1
adj;falsch;;wrong;غلط;1
adj;viel;;much, many;زیاد;1
adj;wenig;;little, few;کم;2
adj;rot;;red;قرمز;1
adj;blau;;blue;آبی;1
adj;grün;;green;سبز;1
adj;gelb;;yellow;زرد;1
adj;schwarz;;black;سیاه;1
adj;weiß;;white;سفید;1
adv;gern;;gladly (like to);با میل، دوست دارم;1
adv;vielleicht;;maybe;شاید;2
adv;zusammen;;together;با هم;2
adv;leider;;unfortunately;متأسفانه;2
adv;sofort;;immediately;فوراً;2
x;Ich verstehe nicht;;I don't understand;نمی‌فهمم;1
x;Noch einmal, bitte;;once more, please;یک بار دیگر، لطفاً;1
x;Wie viel kostet das?;;how much is that?;این چند است؟;1
x;Ich weiß nicht;;I don't know;نمی‌دانم;1
x;Sprechen Sie Englisch?;;do you speak English?;انگلیسی صحبت می‌کنید؟;1
""".strip()
