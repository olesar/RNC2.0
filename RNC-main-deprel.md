# Список синтаксических тегов UD, используемых в разметке Основного корпуса НКРЯ и других современных корпусов

| Relation | Definition |
| --- | --- |
| [acl](https://universaldependencies.org/ru/dep/acl.html) |  clausal modifier of noun (adnominal clause) |
| [acl:relcl](https://universaldependencies.org/ru/dep/acl:relcl.html) |  relative clause modifier |
| [advcl](https://universaldependencies.org/ru/dep/advcl.html) |  adverbial clause modifier |
| [advmod](https://universaldependencies.org/ru/dep/advmod.html) |  adverbial modifier |
| [amod](https://universaldependencies.org/ru/dep/amod.html) |  adjectival modifier |
| [appos](https://universaldependencies.org/ru/dep/appos.html) |  appositional modifier |
| [aux](https://universaldependencies.org/ru/dep/aux.html) |  auxiliary |
| [aux:pass](https://universaldependencies.org/ru/dep/aux:pass.html) |  passive auxiliary |
| [case](https://universaldependencies.org/ru/dep/case.html) |  case marking |
| [cc](https://universaldependencies.org/ru/dep/cc.html) |  coordinating conjunction |
| [ccomp](https://universaldependencies.org/ru/dep/ccomp.html) |  clausal complement |
| [compound](https://universaldependencies.org/ru/dep/compound.html) |  compound |
| [conj](https://universaldependencies.org/ru/dep/conj.html) |  conjunct |
| [cop](https://universaldependencies.org/ru/dep/cop.html) |  copula |
| [csubj](https://universaldependencies.org/ru/dep/csubj.html) |  clausal subject |
| [csubj:pass](https://universaldependencies.org/ru/dep/csubj:pass.html) |  clausal passive subject |
| [dep](https://universaldependencies.org/ru/dep/dep.html) |  unspecified dependency |
| [det](https://universaldependencies.org/ru/dep/det.html) |  determiner |
| [discourse](https://universaldependencies.org/ru/dep/discourse.html) |  discourse element |
| [dislocated](https://universaldependencies.org/ru/dep/dislocated.html) |  dislocated elements |
| [expl](https://universaldependencies.org/ru/dep/expl.html) |  expletive |
| [fixed](https://universaldependencies.org/ru/dep/fixed.html) |  fixed multiword expression |
| [flat](https://universaldependencies.org/ru/dep/flat.html) |  flat multiword expression |
| [flat:foreign](https://universaldependencies.org/ru/dep/flat:foreign.html) |  foreign words |
| [flat:name](https://universaldependencies.org/ru/dep/flat:name.html) |  names |
| [goeswith](https://universaldependencies.org/ru/dep/goeswith.html) |  goes with |
| [iobj](https://universaldependencies.org/ru/dep/iobj.html) |  indirect object |
| [list](https://universaldependencies.org/ru/dep/list.html) |  list |
| [mark](https://universaldependencies.org/ru/dep/mark.html) |  marker |
| [nmod](https://universaldependencies.org/ru/dep/nmod.html) |  nominal modifier |
| [nsubj](https://universaldependencies.org/ru/dep/nsubj.html) |  nominal subject |
| [nsubj:pass](https://universaldependencies.org/ru/dep/nsubj:pass.html) |  passive nominal subject |
| [nummod](https://universaldependencies.org/ru/dep/nummod.html) |  numeric modifier |
| [nummod:gov](https://universaldependencies.org/ru/dep/nummod:gov.html) |  numeric modifier governing the case of the noun |
| [obj](https://universaldependencies.org/ru/dep/obj.html) |  object |
| [obl](https://universaldependencies.org/ru/dep/obl.html) |  oblique nominal |
| [obl:agent](https://universaldependencies.org/ru/dep/obl:agent.html) |  agent modifier |
| [obl:tmod](https://universaldependencies.org/ru/dep/obl:tmod.html) |  temporal modifier |
| [orphan](https://universaldependencies.org/ru/dep/orphan.html) |  orphan |
| [parataxis](https://universaldependencies.org/ru/dep/parataxis.html) |  parataxis |
| parataxis:discourse | parentheticals |
| [punct](https://universaldependencies.org/ru/dep/punct.html) |  punctuation |
| [reparandum](https://universaldependencies.org/ru/dep/reparandum.html) |  overridden disfluency |
| [root](https://universaldependencies.org/ru/dep/root.html) |  root |
| [vocative](https://universaldependencies.org/ru/dep/vocative.html) |  vocative |
| [xcomp](https://universaldependencies.org/ru/dep/xcomp.html) |  open clausal complement |

### New relations, under annotation in training data  

| Relation | Definition |
| --- | --- |
| *obl:float | floating quantifier, _**сам** пришел_ |
| *obl:pronmod | modifier in indefinite pronominal series, e.g. _Бог **знает** кого_ |
| *obl:depict | depictive, _она вошла в комнату **грустная**_ |
| *obl:spec | modifier: _утром в пять **часов**_, _там на **веранде**_ |


### References
* UD [guidelines](https://universaldependencies.org/u/dep/)
* UD-Russian [guidelines](https://universaldependencies.org/ru/dep/)  
* RNC test [page](https://py3ruscorpora.ru/new/search-regional.html) (for internal use only)

### UD tags not in use in Russian 

clf: classifier  
compound:lvc: light verb construction  
compound:prt: phrasal verb particle  
compound:redup: reduplicated compounds  
compound:svc: serial verb compounds  
expl:impers: impersonal expletive  
expl:pass: reflexive pronoun used in reflexive passive  
expl:pv: reflexive clitic with an inherently reflexive verb  
obl:arg: oblique argument  
obl:lmod: locative modifier  

### UD tags used in UD-Russian_GSD

nmod:gmod  
nmod:poss  
nummod:entity  
