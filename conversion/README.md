## Conversion scripts

### Скрипты для конвертации данных  

В этой папке находятся скрипты для перевода датасетов из форматов НКРЯ в conllu и обратно.  

* RNCtoUD_tools - переводит xml НКРЯ в conllu UD  
* UDtoRNC - переводит conllu UD в xml НКРЯ  
* UDext2UDbasic - приводит теги UD к базовому набору (для публикации в UD)  
* ConlluToXml - простой конвертор conllu UD в xml НКРЯ (для старорусского корпуса)  

Конверсия проводится с помощью таблицы переходов https://github.com/olesar/ruUD/blob/master/conversion/RNC2UD-ext.md и других вспомогательных словарей.  

### О форматах данных  

Файлы корпусов НКРЯ (помимо Синтагрус) хранятся в xml, в двух вариантах:  

XML корпуса со снятой омонимией (папка standard):
```
<?xml version="1.0" encoding="utf-8"?><html><head>...</head>
<body>
<p><se>
<w><ana lex="программа" gr="S,f,inan=sg,acc"></ana>Прогр`амму</w>"
<w><ana lex="аншлаг" gr="S,m,inan=sg,acc"></ana>Аншл`аг</w> "
<w><ana lex="и" gr="CONJ"></ana>и</w>
<w><ana lex="она" gr="S-PRO,f,sg,3p=dat"></ana>ей</w>
<w><ana lex="подобный" gr="A=pl,nom,plen"></ana>под`обные</w>
<w><ana lex="на" gr="PR"></ana>на</w>
<w><ana lex="государственный" gr="A=n,sg,loc,plen"></ana>госуд`арственном</w>
<w><ana lex="телевидение" gr="S,n,inan=sg,loc"></ana>телев`идении</w>
<w><ana lex="заменить" gr="V,pf,tran=pl,act,fut,3p,indic"></ana>зам`енят</w>
<w><ana lex="передача" gr="S,f,inan=pl,nom"></ana>перед`ачи</w>
<w><ana lex="о" gr="PR"></ana>о</w>
<w><ana lex="культура" gr="S,f,inan=sg,loc"></ana>культ`уре</w>
<w><ana lex="и" gr="CONJ"></ana>и</w>
<w><ana lex="специальный" gr="A=m,sg,nom,plen"></ana>специ`альный</w>
<w><ana lex="детский" gr="A=m,sg,nom,plen"></ana>д`етский</w>
<w><ana lex="канал" gr="S,m,inan=sg,nom"></ana>кан`ал</w> .</se>
</p>
</body></html>
```

XML корпусов без морфологической разметки (папка source и др.):
```
<?xml version="1.0" encoding="utf-8"?><html><head>...</head>
<body>
<p class="h2">Картина вторая</p>

<p><span class="note">Дом баронессы Якобины фон Мюнхгаузен. Богатая обстановка. На стенах многочисленные портреты предков. Последний из портретов завешен черной вуалью. Сидя в кресле, Баронесса слушает рассказ господина фон Рамкопфа мужчины средних лет в парике и с забинтованным лбом.</span></p>
<p>Ее сын Феофил фон Мюнхгаузен -- молодой человек в форме корнета -- нервно</p>
<p>ходит по комнате.</p>
<p sp="Рамкопф" speaker="муж, ?, адвокат"><em>Рамкопф</em> <span class="note">(заканчивая рассказ)</span>. ...Он так и сказал «Отпустите ее, пусть</p>
<p>летает!»</p>

</body></html>
```

В целом, задача нашего проекта состоит в добавлении лексико-грамматических разборов со снятой омонимией (в файлы без морфологической разметки) и синтаксических разборов (во все файлы). HTML-теги и XML-теги специальных слоев разметки, ударения и прочие особенности текста должны быть сохранены. 
В пайплайне xml проходят препроцессинг, включая токенизацию, перевод в conllu, обработку нейросетевым теггером/парсером, перевод в xml, добавление вторых (дополнительных разборов).  

Согласованный формат итоговых данных можно посмотреть тут: https://docs.google.com/document/d/1aqy6YZMQQx0oJgM1Ied-MXtPD08c2Ada3ySevJ4F17E 

Conllu может иметь также два формата. Один - базовый Universal Dependendencies (UD) - используется в репозиториях UD и соревнованиях для трибанков русского языка, другой - UD-ext - разработан для однозначного мэппинга разборов НКРЯ и UD (Lyashevskaya 2019). В [таблице переходов](https://github.com/olesar/ruUD/blob/master/conversion/RNC2UD-ext.md) это расширенное множество тегов особо помечено. Знаки пунктуации в conllu имеют статус размечаемых токенов. Вся служебная информация выносится в последний, десятый столбец conllu, там же проставляется тег SpaceAfter=No, который указывает на правила (не)расстановки пробелов между токенами.  

Conllu по схеме UD basic:
```
# newpar
# sent_id = 1001
1	Рамкопф	Рамкопф	PROPN	_	Animacy=Anim|Case=Nom|Gender=Masc|Number=Sing	0	root	_	before:<p sp="Рамкопф" speaker="муж, ?, адвокат"><em>|</em> <span class="note">|NoIndex=Yes
2	(	(	PUNCT	_	_	17	punct	_	NoIndex=Yes|SpaceAfter=No
3	заканчивая	заканчивать	VERB	_	Aspect=Imp|Tense=Pres|VerbForm=Conv|Voice=Act	1	parataxis	_	NoIndex=Yes
4	рассказ	рассказ	X	_	Animacy=Inan|Case=Acc|Gender=Masc|Number=Sing	17	parataxis	_	</span>|NoIndex=Yes|SpaceAfter=No
5	)	)	PUNCT	_	_	17	punct	_	NoIndex=Yes|SpaceAfter=No
5	.	.	PUNCT	_	_	17	punct	_	NoIndex=Yes

# newpar
# sent_id = 1002
1	...	...	PUNCT	_	_	5	punct	_	SpaceAfter=No
2	Он	он	PRON	_	Case=Nom|Gender=Masc|Number=Sing|Person=3	5	nsubj	_	_
3	так	так	ADV	_	Degree=Pos	5	advmod	_	_
4	и	и	PART	_	_	3	fixed	_	_
5	сказал	сказать	VERB	_	Aspect=Perf|Gender=Masc|Mood=Ind|Number=Sing|Tense=Past|VerbForm=Fin|Voice=Act	0	root	_	_
6	«	«	PUNCT	_	_	7	punct	_	SpaceAfter=No
7	Отпустите	отпустить	VERB	_	Aspect=Perf|Mood=Imp|Number=Plur|Person=2|VerbForm=Fin|Voice=Act	5	parataxis	_	_
8	ее	она	PRON	_	Case=Acc|Gender=Fem|Number=Sing|Person=3	7	obj	_	SpaceAfter=No
9	,	,	PUNCT	_	_	11	punct	_	_
10	пусть	пусть	PART	_	_	11	advmod	_	_
11	летает	летать	VERB	_	Aspect=Imp|Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin|Voice=Act	7	conj	_	SpaceAfter=No
12	!	!	PUNCT	_	_	7	punct	_	SpaceAfter=No
13	»	»	PUNCT	_	_	7	punct	_	_
```

Conllu по схеме UD basic:
```
# newpar
# sent_id = 1001
1	Рамкопф	Рамкопф	PROPN	_	Animacy=Anim|Case=Nom|Gender=Masc|Number=Sing	0	root	_	before:<p sp="Рамкопф" speaker="муж, ?, адвокат"><em>|</em> <span class="note">|NoIndex=Yes
2	(	(	PUNCT	_	_	17	punct	_	NoIndex=Yes|SpaceAfter=No
3	заканчивая	заканчивать	VERB	_	Aspect=Imp|Tense=Pres|Transit=Tran|VerbForm=Conv|Voice=Act	1	parataxis	_	NoIndex=Yes
4	рассказ	рассказ	X	_	Animacy=Inan|Case=Acc|Gender=Masc|Number=Sing	17	parataxis	_	</span>|NoIndex=Yes|SpaceAfter=No
5	)	)	PUNCT	_	_	17	punct	_	NoIndex=Yes|SpaceAfter=No
5	.	.	PUNCT	_	_	17	punct	_	NoIndex=Yes

# newpar
# sent_id = 1002
1	...	...	PUNCT	_	_	5	punct	_	SpaceAfter=No
2	Он	он	PRON	_	Case=Nom|Gender=Masc|Number=Sing|Person=3|PronType=Prs	5	nsubj	_	_
3	так	так	ADVPRO	_	PronType=Dem	5	advmod	_	_
4	и	и	PART	_	_	3	fixed	_	_
5	сказал	сказать	VERB	_	Aspect=Perf|Gender=Masc|Mood=Ind|Number=Sing|Tense=Past|Transit=Tran|VerbForm=Fin|Voice=Act	0	root	_	_
6	«	«	PUNCT	_	_	7	punct	_	SpaceAfter=No
7	Отпустите	отпустить	VERB	_	Aspect=Perf|Mood=Imp|Number=Plur|Person=2|Transit=Tran|VerbForm=Fin|Voice=Act	5	parataxis	_	_
8	ее	она	PRON	_	Case=Acc|Gender=Fem|Number=Sing|Person=3|PronType=Prs	7	obj	_	SpaceAfter=No
9	,	,	PUNCT	_	_	11	punct	_	_
10	пусть	пусть	PART	_	_	11	advmod	_	_
11	летает	летать	VERB	_	Aspect=Imp|Mood=Ind|Number=Sing|Person=3|Tense=Pres|Transit=Intr|VerbForm=Fin|Voice=Act	7	conj	_	SpaceAfter=No
12	!	!	PUNCT	_	_	7	punct	_	SpaceAfter=No
13	»	»	PUNCT	_	_	7	punct	_	_
```

### Нетривиальные задачи конвертации   
* сегментация предложений (в неснятнике)  
* токенизация  
   * включая обработку слов с дефисами (по словнику)   
* нормализация и упаковка существующих тегов, угловых скобок и т.д.  
* добавление синтаксиса к существующей морфологической разметке  
* добавление вторичных разборов для лемм и морфологии (TBD)  
* добавление аспектуальных пар для глаголов  
* добавление разборов майстема, не совпадающих с данным  

