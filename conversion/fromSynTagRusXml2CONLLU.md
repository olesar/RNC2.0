# Как перейти от представления файлов СинТагРус в XML-TGT к UD в формате CONLLU 

### 1. Представление XML

Разберем начало файла текста Л. Серовой "А он, мятежный, просит бури..." [Наука и жизнь, № 2, 2003] (2003/A_on_myatezhnyi.tgt). 
Здесь позиция токена указана в атрибуте `ID`, синтаксический хозяин - в атрибуте `DOM`, синтаксическая роль - в атрибуте `LINK`.

```
<S ID="89">
<W DOM="3" FEAT="ADV" ID="1" LEMMA="ПОТОМ" LINK="обст">Пото́м</W> 
<W DOM="3" FEAT="S ЕД ЖЕН ИМ ОД" ID="2" LEMMA="ОНА" LINK="предик">она́</W> 
<W DOM="_root" FEAT="V НЕСОВ ИЗЪЯВ НЕПРОШ ЕД 3-Л" ID="3" KSNAME="ВЫХОДИТЬ1" LEMMA="ВЫХОДИТЬ">выхо́дит</W> 
<W DOM="3" FEAT="ADV" ID="4" LEMMA="ЗАМУЖ" LINK="2-компл">за́муж</W> 
<W DOM="4" FEAT="PR" ID="5" KSNAME="ЗА1" LEMMA="ЗА" LINK="1-компл">за</W> 
<W DOM="5" FEAT="S ЕД МУЖ ВИН ОД" ID="6" KSNAME="НИКОЛАЙ" LEMMA="НИКОЛАЙ" LINK="предл">Никола́я</W> 
<W DOM="6" FEAT="S ЕД МУЖ ВИН ОД" ID="7" KSNAME="ФИКТ-ФАМИЛИЯ" LEMMA="РАТМАНОВ" LINK="аппоз">Ратманова</W>, 
<W DOM="3" FEAT="PR" ID="8" KSNAME="У1" LEMMA="У" LINK="сент-соч">у</W> 
<W DOM="8" FEAT="S ЕД ЖЕН РОД ОД" ID="9" LEMMA="ОНА" LINK="предл">неё</W> 
<W DOM="11" FEAT="NUM ЖЕН ИМ" ID="10" LEMMA="ДВА" LINK="количест">две</W> 
<W DOM="8" FEAT="S ЕД ЖЕН РОД ОД" ID="11" LEMMA="ДОЧЬ" LINK="предик">до́чери</W>. 
</S>
```

### 2. Представление CONLLU, промежуточный вариант  

ID ставим в столбец 1, словоформу в столбец 2, лемму в столбец 3, "родное" морфологическое представление в столбец 5, 
ID хозяина (DOM) в столбец 7, синтаксическую роль (LINK) в столбец 8, остальную ценную информацию храним в столбце 10, где может быть все что угодно.
В этом представлении знаки пунктуации пока не имеют статуса токенов (хранятся в колонке 10 как PunctBefore, PunctAfter="...").
Вершина дерева (`DOM="_root"`) обозначается как 0 и root (см. первую строку).  

```
# sent_id = 89
1	Пото́м	потом	_	ADV	_	3	обст	_	_
2	она́	она	_	S ЕД ЖЕН ИМ ОД	_	3	предик	_	_
3	выхо́дит	выходить	_	V НЕСОВ ИЗЪЯВ НЕПРОШ ЕД 3-Л	_	0	root	_	KSNAME="ВЫХОДИТЬ1"
4	за́муж	замуж	_	ADV	_	3	2-компл	_	_
5	за	за	_	PR	_	4	1-компл	_	KSNAME="ЗА1"
6	Никола́я	Николай	_	S ЕД МУЖ ВИН ОД	_	5	предл	_	KSNAME="НИКОЛАЙ"
7	Ратманова	Ратманов	_	S ЕД МУЖ ВИН ОД	_	6	аппоз	_	KSNAME="ФИКТ-ФАМИЛИЯ"|PunctAfter=","
8	у	у	_	PR	_	3	сент-соч	_	KSNAME="У1"
9	неё	она	_	S ЕД ЖЕН РОД ОД	_	8	предл	_	_
10	две	два	_	NUM ЖЕН ИМ	_	11	количест	_	_
11	до́чери	дочь	_	S ЕД ЖЕН РОД ОД	_	8	предик	_	PunctAfter="."
```

### 3. Представление CONLLU, конвертация в теги UD  

Переведем морфологические и синтаксические теги в UD (столбец 4 - часть речи, 6 - морфология, 8 - синт. роль), 
а представление лемм общей лексики в нижний регистр (в леммах имен собственных и аббревиатур используются прописные буквы). 
Уберем ударение со словоформ, а представление словоформ с ударением перенесем в атрибут wf в столбец 10.

```
# sent_id = 89
1	Потом	потом	ADV	ADV	Degree=Pos	3	advmod	_	wf="Пото́м"
2	она	она	PRON	S ЕД ЖЕН ИМ ОД	Case=Nom|Gender=Fem|Number=Sing|Person=3|PronType=Prs	3	nsubj	_	wf="она́"
3	выходит	выходить	VERB	V НЕСОВ ИЗЪЯВ НЕПРОШ ЕД 3-Л	Aspect=Imp|Mood=Ind|Number=Plur|Person=3|Tense=Pres|Transit=Intr|VerbForm=Fin|Voice=Act	0	root	_	wf="выхо́дит"|KSNAME="ВЫХОДИТЬ1"
4	замуж	замуж	ADV	ADV	Degree=Pos	3	advmod	_	wf="за́муж"
5	за	за	ADP	PR	_	6	case	_	wf="за"|KSNAME="ЗА1"
6	Николая	Николай	PROPN	S ЕД МУЖ ВИН ОД	Animacy=Anim|Case=Acc|Gender=Masc|NameType=Giv|Number=Sing	3	obl	_	wf="Никола́я"|KSNAME="НИКОЛАЙ"
7	Ратманова	Ратманов	PROPN	S ЕД МУЖ ВИН ОД	Animacy=Anim|Case=Acc|Gender=Masc|NameType=Sur|Number=Sing	6	flat:name	_	wf="Ратманова"|KSNAME="ФИКТ-ФАМИЛИЯ"|PunctAfter=","
8	у	у	ADP	PR	_	9	case	_	wf="у"|KSNAME="У1"
9	неё	она	PRON	S ЕД ЖЕН РОД ОД	Case=Gen|Gender=Fem|Number=Sing|Person=3|PronType=Prs	3	conj	_	wf="неё"
10	две	два	NUM	NUM ЖЕН ИМ	Case=Nom|Gender=Fem|NumForm=Word|NumType=Card	11	nummod:gov	_	wf="две"
11	дочери	дочь	NOUN	S ЕД ЖЕН РОД ОД	Animacy=Anim|Case=Gen|Gender=Fem|Number=Sing	9	nsubj	_	wf="до́чери"|PunctAfter="."
```

Согласно схеме UD, здесь другое направление стрелок "хозяин-зависимое" у предлогов, союзов и в ряде других конструкций.

### 4. Итоговое представление UD-CONLLU

Пунктуацию добавим как отдельные токены. Поскольку ID словоформ при этой операции изменятся, изменим и позиции хозяев. 
Отсутствие пробела после токена в явном виде указывается в атрибуте SpaceAfter=No в столбце 10. 
Текст предложения добавляется в строку `# text = ...`.

```
# sent_id = 89
# text = Потом она выходит замуж за Николая Ратманова, у неё две дочери.
1	Потом	потом	ADV	ADV	Degree=Pos	3	advmod	_	wf="Пото́м"
2	она	она	PRON	S ЕД ЖЕН ИМ ОД	Case=Nom|Gender=Fem|Number=Sing|Person=3|PronType=Prs	3	nsubj	_	wf="она́"
3	выходит	выходить	VERB	V НЕСОВ ИЗЪЯВ НЕПРОШ ЕД 3-Л	Aspect=Imp|Mood=Ind|Number=Plur|Person=3|Tense=Pres|Transit=Intr|VerbForm=Fin|Voice=Act	0	root	_	wf="выхо́дит"|KSNAME="ВЫХОДИТЬ1"
4	замуж	замуж	ADV	ADV	Degree=Pos	3	advmod	_	wf="за́муж"
5	за	за	ADP	PR	_	6	case	_	wf="за"|KSNAME="ЗА1"
6	Николая	Николай	PROPN	S ЕД МУЖ ВИН ОД	Animacy=Anim|Case=Acc|Gender=Masc|NameType=Giv|Number=Sing	3	obl	_	wf="Никола́я"|KSNAME="НИКОЛАЙ"
7	Ратманова	Ратманов	PROPN	S ЕД МУЖ ВИН ОД	Animacy=Anim|Case=Acc|Gender=Masc|NameType=Sur|Number=Sing	6	flat:name	_	wf="Ратманова"|KSNAME="ФИКТ-ФАМИЛИЯ"|SpaceAfter=No
8	,	,	PUNCT	_	_	10	punct	_	_
9	у	у	ADP	PR	_	10	case	_	wf="у"|KSNAME="У1"
10	неё	она	PRON	S ЕД ЖЕН РОД ОД	Case=Gen|Gender=Fem|Number=Sing|Person=3|PronType=Prs	3	conj	_	wf="неё"
11	две	два	NUM	NUM ЖЕН ИМ	Case=Nom|Gender=Fem|NumForm=Word|NumType=Card	12	nummod:gov	_	wf="две"
12	дочери	дочь	NOUN	S ЕД ЖЕН РОД ОД	Animacy=Anim|Case=Gen|Gender=Fem|Number=Sing	10	nsubj	_	wf="до́чери"|SpaceAfter=No
13	.	.	PUNCT	_	_	3	punct	_	_
```

Примечание. При переводе в UD-CONLLU могут понадобиться и другие операции, такие как преобразование неоднословных выражений в отдельные токены или включение информации о лексических функциях. 

