import datetime

BRAIN_REGION_REPLACEMENTS = {
    "Accessory supraoptic group: Other": "2218808594",
    "Agranular insular area, dorsal part, layer 2": "3250982806",
    "Agranular insular area, dorsal part, layer 3": "3088876178",
    "Agranular insular area, posterior part, layer 2": "1672280517",
    "Agranular insular area, posterior part, layer 3": "2414821463",
    "Agranular insular area, ventral part, layer 2": "2224619882",
    "Agranular insular area, ventral part, layer 3": "3376791707",
    "Anterior area, layer 2": "1695203883",
    "Anterior area, layer 3": "1160721590",
    "Anterior cingulate area, dorsal part, layer 2": "3095364455",
    "Anterior cingulate area, dorsal part, layer 3": "2862362532",
    "Anterior cingulate area, ventral part, layer 2": "2949903222",
    "Anterior cingulate area, ventral part, layer 3": "3582239403",
    "Anterior hypothalamic nucleus: Other": "1690235425",
    "Anterior olfactory nucleus: Other": "2561915647",
    "Anterolateral visual area, layer 2": "1463157755",
    "Anterolateral visual area, layer 3": "2845253318",
    "Anteromedial visual area, layer 2": "1645194511",
    "Anteromedial visual area, layer 3": "2292194787",
    "Bed nuclei of the stria terminalis: Other": "2791423253",
    "Cerebellum: Other": "3092369320",
    "Cortical amygdalar area, anterior part: Other": "1466095084",
    "Cortical amygdalar area, posterior part, lateral zone: Other": "1992072790",
    "Cortical amygdalar area, posterior part, medial zone: Other": "1375046773",
    "Cortical subplate: Other": "2416897036",
    "Dorsal auditory area, layer 2": "3781663036",
    "Dorsal auditory area, layer 3": "2186168811",
    "Dorsal peduncular area: Other": "1953921139",
    "Dorsomedial nucleus of the hypothalamus: Other": "1463730273",
    "Ectorhinal area, layer 2": "2218254883",
    "Ectorhinal area, layer 3": "3516629919",
    "Frontal pole, layer 2": "2646114338",
    "Frontal pole, layer 3": "2536061413",
    "Gustatory areas, layer 2": "3683796018",
    "Gustatory areas, layer 3": "3893800328",
    "Hippocampal formation: Other": "3263488087",
    "Hypothalamus: Other": "1842735199",
    "Infralimbic area, layer 3": "2078623765",
    "Interpeduncular nucleus: Other": "2183090366",
    "Lateral visual area, layer 2": "3927629261",
    "Lateral visual area, layer 3": "3962734174",
    "Laterointermediate area, layer 2": "3808183566",
    "Laterointermediate area, layer 3": "2985091592",
    "Main olfactory bulb: Other": "2358040414",
    "Medial amygdalar nucleus: Other": "2445320853",
    "Medial preoptic nucleus: Other": "2254557934",
    "Mediodorsal nucleus of thalamus: Other": "3009745967",
    "Medulla: Other": "1557651847",
    "Midbrain reticular nucleus: Other": "1040222935",
    "Midbrain: Other": "3101970431",
    "Nucleus of the lateral lemniscus: Other": "2127067043",
    "Nucleus of the solitary tract: Other": "2316153360",
    "Olfactory areas: Other": "1024543562",
    "Olfactory tubercle: Other": "3672106733",
    "Orbital area, lateral part, layer 2": "3803368771",
    "Orbital area, lateral part, layer 3": "1037481934",
    "Orbital area, medial part, layer 3": "2012716980",
    "Orbital area, ventrolateral part, layer 2": "3653590473",
    "Orbital area, ventrolateral part, layer 3": "2413172686",
    "Pallidum: Other": "2165415682",
    "Parabrachial nucleus: Other": "3409505442",
    "Parapyramidal nucleus: Other": "2114704803",
    "Parasubiculum: Other": "2952544119",
    "Paraventricular hypothalamic nucleus, descending division: Other": "3467149620",
    "Paraventricular hypothalamic nucleus: Other": "2869757686",
    "Periaqueductal gray: Other": "2956165934",
    "Perirhinal area, layer 2": "3132124329",
    "Perirhinal area, layer 3": "2668242174",
    "Piriform area: Other": "1668688439",
    "Piriform-amygdalar area: Other": "1203939479",
    "Pons: Other": "1140764290",
    "Posterior auditory area, layer 2": "1307372013",
    "Posterior auditory area, layer 3": "1598869030",
    "Posterolateral visual area, layer 2": "2153924985",
    "Posterolateral visual area, layer 3": "1431942459",
    "Postpiriform transition area: Other": "1209357605",
    "Postrhinal area, layer 2": "2782023316",
    "Postrhinal area, layer 3": "3920533696",
    "Postsubiculum: Other": "2063775638",
    "Prelimbic area, layer 3": "2790124484",
    "Presubiculum: Other": "1580329576",
    "Primary auditory area, layer 2": "2927119608",
    "Primary auditory area, layer 3": "1165809076",
    "Primary motor area, layer 2": "3718675619",
    "Primary motor area, layer 3": "1758306548",
    "Primary somatosensory area, barrel field, A1 barrel layer 1": "1344105173",
    "Primary somatosensory area, barrel field, A1 barrel layer 2": "3116469840",
    "Primary somatosensory area, barrel field, A1 barrel layer 2/3": "2615618683",
    "Primary somatosensory area, barrel field, A1 barrel layer 3": "3379356047",
    "Primary somatosensory area, barrel field, A1 barrel layer 4": "1315119484",
    "Primary somatosensory area, barrel field, A1 barrel layer 5": "2436888515",
    "Primary somatosensory area, barrel field, A1 barrel layer 6a": "3577346235",
    "Primary somatosensory area, barrel field, A1 barrel layer 6b": "3902978127",
    "Primary somatosensory area, barrel field, A1 barrel": "1370229894",
    "Primary somatosensory area, barrel field, A2 barrel layer 1": "1310126712",
    "Primary somatosensory area, barrel field, A2 barrel layer 2": "3324056088",
    "Primary somatosensory area, barrel field, A2 barrel layer 2/3": "1446874462",
    "Primary somatosensory area, barrel field, A2 barrel layer 3": "2593521448",
    "Primary somatosensory area, barrel field, A2 barrel layer 4": "3685934448",
    "Primary somatosensory area, barrel field, A2 barrel layer 5": "3575805529",
    "Primary somatosensory area, barrel field, A2 barrel layer 6a": "1210837267",
    "Primary somatosensory area, barrel field, A2 barrel layer 6b": "1258169895",
    "Primary somatosensory area, barrel field, A2 barrel": "3651721123",
    "Primary somatosensory area, barrel field, A3 barrel layer 1": "1994494334",
    "Primary somatosensory area, barrel field, A3 barrel layer 2": "2590882612",
    "Primary somatosensory area, barrel field, A3 barrel layer 2/3": "1447791371",
    "Primary somatosensory area, barrel field, A3 barrel layer 3": "3761146439",
    "Primary somatosensory area, barrel field, A3 barrel layer 4": "3139552203",
    "Primary somatosensory area, barrel field, A3 barrel layer 5": "2692580507",
    "Primary somatosensory area, barrel field, A3 barrel layer 6a": "1677451927",
    "Primary somatosensory area, barrel field, A3 barrel layer 6b": "3379749055",
    "Primary somatosensory area, barrel field, A3 barrel": "2732283703",
    "Primary somatosensory area, barrel field, Alpha barrel layer 1": "2835342929",
    "Primary somatosensory area, barrel field, Alpha barrel layer 2": "3173729836",
    "Primary somatosensory area, barrel field, Alpha barrel layer 2/3": "1897248316",
    "Primary somatosensory area, barrel field, Alpha barrel layer 3": "3926962776",
    "Primary somatosensory area, barrel field, Alpha barrel layer 4": "2168807353",
    "Primary somatosensory area, barrel field, Alpha barrel layer 5": "3137025327",
    "Primary somatosensory area, barrel field, Alpha barrel layer 6a": "2406188897",
    "Primary somatosensory area, barrel field, Alpha barrel layer 6b": "3670777223",
    "Primary somatosensory area, barrel field, Alpha barrel": "3896406483",
    "Primary somatosensory area, barrel field, B1 barrel layer 1": "1516851569",
    "Primary somatosensory area, barrel field, B1 barrel layer 2": "2196657368",
    "Primary somatosensory area, barrel field, B1 barrel layer 2/3": "3913053667",
    "Primary somatosensory area, barrel field, B1 barrel layer 3": "3986345576",
    "Primary somatosensory area, barrel field, B1 barrel layer 4": "3495145594",
    "Primary somatosensory area, barrel field, B1 barrel layer 5": "1644849336",
    "Primary somatosensory area, barrel field, B1 barrel layer 6a": "3289019263",
    "Primary somatosensory area, barrel field, B1 barrel layer 6b": "2194674250",
    "Primary somatosensory area, barrel field, B1 barrel": "2525641171",
    "Primary somatosensory area, barrel field, B2 barrel layer 1": "3853526235",
    "Primary somatosensory area, barrel field, B2 barrel layer 2": "1311366798",
    "Primary somatosensory area, barrel field, B2 barrel layer 2/3": "3456985752",
    "Primary somatosensory area, barrel field, B2 barrel layer 3": "1126601402",
    "Primary somatosensory area, barrel field, B2 barrel layer 4": "3966633210",
    "Primary somatosensory area, barrel field, B2 barrel layer 5": "2812530569",
    "Primary somatosensory area, barrel field, B2 barrel layer 6a": "1641347046",
    "Primary somatosensory area, barrel field, B2 barrel layer 6b": "3416776496",
    "Primary somatosensory area, barrel field, B2 barrel": "1673450198",
    "Primary somatosensory area, barrel field, B3 barrel layer 1": "3565367498",
    "Primary somatosensory area, barrel field, B3 barrel layer 2": "1881029055",
    "Primary somatosensory area, barrel field, B3 barrel layer 2/3": "2657138906",
    "Primary somatosensory area, barrel field, B3 barrel layer 3": "3080022137",
    "Primary somatosensory area, barrel field, B3 barrel layer 4": "1547817274",
    "Primary somatosensory area, barrel field, B3 barrel layer 5": "2369238059",
    "Primary somatosensory area, barrel field, B3 barrel layer 6a": "2478012832",
    "Primary somatosensory area, barrel field, B3 barrel layer 6b": "2739084189",
    "Primary somatosensory area, barrel field, B3 barrel": "1626685236",
    "Primary somatosensory area, barrel field, B4 barrel layer 1": "2006047173",
    "Primary somatosensory area, barrel field, B4 barrel layer 2": "1456682260",
    "Primary somatosensory area, barrel field, B4 barrel layer 2/3": "2180527067",
    "Primary somatosensory area, barrel field, B4 barrel layer 3": "3562601313",
    "Primary somatosensory area, barrel field, B4 barrel layer 4": "1970686062",
    "Primary somatosensory area, barrel field, B4 barrel layer 5": "3890169311",
    "Primary somatosensory area, barrel field, B4 barrel layer 6a": "2936441103",
    "Primary somatosensory area, barrel field, B4 barrel layer 6b": "3215542274",
    "Primary somatosensory area, barrel field, B4 barrel": "3347675430",
    "Primary somatosensory area, barrel field, Beta barrel layer 1": "3486673188",
    "Primary somatosensory area, barrel field, Beta barrel layer 2": "3970522306",
    "Primary somatosensory area, barrel field, Beta barrel layer 2/3": "3783583602",
    "Primary somatosensory area, barrel field, Beta barrel layer 3": "1054221329",
    "Primary somatosensory area, barrel field, Beta barrel layer 4": "3895794866",
    "Primary somatosensory area, barrel field, Beta barrel layer 5": "1496257237",
    "Primary somatosensory area, barrel field, Beta barrel layer 6a": "2152572352",
    "Primary somatosensory area, barrel field, Beta barrel layer 6b": "3048883337",
    "Primary somatosensory area, barrel field, Beta barrel": "1521759875",
    "Primary somatosensory area, barrel field, C1 barrel layer 1": "1337935688",
    "Primary somatosensory area, barrel field, C1 barrel layer 2": "1558550786",
    "Primary somatosensory area, barrel field, C1 barrel layer 2/3": "1667660763",
    "Primary somatosensory area, barrel field, C1 barrel layer 3": "2563782304",
    "Primary somatosensory area, barrel field, C1 barrel layer 4": "3219108088",
    "Primary somatosensory area, barrel field, C1 barrel layer 5": "1420546517",
    "Primary somatosensory area, barrel field, C1 barrel layer 6a": "1945434117",
    "Primary somatosensory area, barrel field, C1 barrel layer 6b": "2866280389",
    "Primary somatosensory area, barrel field, C1 barrel": "1013068637",
    "Primary somatosensory area, barrel field, C2 barrel layer 1": "1082141991",
    "Primary somatosensory area, barrel field, C2 barrel layer 2": "2525505631",
    "Primary somatosensory area, barrel field, C2 barrel layer 2/3": "2157537321",
    "Primary somatosensory area, barrel field, C2 barrel layer 3": "1714311201",
    "Primary somatosensory area, barrel field, C2 barrel layer 4": "2930307508",
    "Primary somatosensory area, barrel field, C2 barrel layer 5": "3188993656",
    "Primary somatosensory area, barrel field, C2 barrel layer 6a": "1843338795",
    "Primary somatosensory area, barrel field, C2 barrel layer 6b": "3291535006",
    "Primary somatosensory area, barrel field, C2 barrel": "2072239244",
    "Primary somatosensory area, barrel field, C3 barrel layer 1": "3835740469",
    "Primary somatosensory area, barrel field, C3 barrel layer 2": "2629778705",
    "Primary somatosensory area, barrel field, C3 barrel layer 2/3": "1125438717",
    "Primary somatosensory area, barrel field, C3 barrel layer 3": "3581771805",
    "Primary somatosensory area, barrel field, C3 barrel layer 4": "3877358805",
    "Primary somatosensory area, barrel field, C3 barrel layer 5": "1667278413",
    "Primary somatosensory area, barrel field, C3 barrel layer 6a": "2743616995",
    "Primary somatosensory area, barrel field, C3 barrel layer 6b": "1093211310",
    "Primary somatosensory area, barrel field, C3 barrel": "2937437636",
    "Primary somatosensory area, barrel field, C4 barrel layer 1": "2151167540",
    "Primary somatosensory area, barrel field, C4 barrel layer 2": "3167765177",
    "Primary somatosensory area, barrel field, C4 barrel layer 2/3": "2460702429",
    "Primary somatosensory area, barrel field, C4 barrel layer 3": "1639524986",
    "Primary somatosensory area, barrel field, C4 barrel layer 4": "1549069626",
    "Primary somatosensory area, barrel field, C4 barrel layer 5": "3085221154",
    "Primary somatosensory area, barrel field, C4 barrel layer 6a": "2659044087",
    "Primary somatosensory area, barrel field, C4 barrel layer 6b": "2700046659",
    "Primary somatosensory area, barrel field, C4 barrel": "3404738524",
    "Primary somatosensory area, barrel field, C5 barrel layer 1": "1246610280",
    "Primary somatosensory area, barrel field, C5 barrel layer 2": "1035739465",
    "Primary somatosensory area, barrel field, C5 barrel layer 2/3": "3880590912",
    "Primary somatosensory area, barrel field, C5 barrel layer 3": "1105483506",
    "Primary somatosensory area, barrel field, C5 barrel layer 4": "1792980078",
    "Primary somatosensory area, barrel field, C5 barrel layer 5": "3556494715",
    "Primary somatosensory area, barrel field, C5 barrel layer 6a": "1706307657",
    "Primary somatosensory area, barrel field, C5 barrel layer 6b": "1869881498",
    "Primary somatosensory area, barrel field, C5 barrel": "2062992388",
    "Primary somatosensory area, barrel field, C6 barrel layer 1": "2933568634",
    "Primary somatosensory area, barrel field, C6 barrel layer 2": "1805611561",
    "Primary somatosensory area, barrel field, C6 barrel layer 2/3": "2013207018",
    "Primary somatosensory area, barrel field, C6 barrel layer 3": "3719447735",
    "Primary somatosensory area, barrel field, C6 barrel layer 4": "2371017187",
    "Primary somatosensory area, barrel field, C6 barrel layer 5": "3985188708",
    "Primary somatosensory area, barrel field, C6 barrel layer 6a": "3796365620",
    "Primary somatosensory area, barrel field, C6 barrel layer 6b": "1714819828",
    "Primary somatosensory area, barrel field, C6 barrel": "1261138116",
    "Primary somatosensory area, barrel field, D1 barrel layer 1": "3724099631",
    "Primary somatosensory area, barrel field, D1 barrel layer 2": "2558258359",
    "Primary somatosensory area, barrel field, D1 barrel layer 2/3": "2833279579",
    "Primary somatosensory area, barrel field, D1 barrel layer 3": "3859877696",
    "Primary somatosensory area, barrel field, D1 barrel layer 4": "2108774369",
    "Primary somatosensory area, barrel field, D1 barrel layer 5": "3320050311",
    "Primary somatosensory area, barrel field, D1 barrel layer 6a": "3628159968",
    "Primary somatosensory area, barrel field, D1 barrel layer 6b": "3638507875",
    "Primary somatosensory area, barrel field, D1 barrel": "1171261412",
    "Primary somatosensory area, barrel field, D2 barrel layer 1": "1743009264",
    "Primary somatosensory area, barrel field, D2 barrel layer 2": "3623254419",
    "Primary somatosensory area, barrel field, D2 barrel layer 2/3": "1884779226",
    "Primary somatosensory area, barrel field, D2 barrel layer 3": "1926976537",
    "Primary somatosensory area, barrel field, D2 barrel layer 4": "2047390011",
    "Primary somatosensory area, barrel field, D2 barrel layer 5": "2798287336",
    "Primary somatosensory area, barrel field, D2 barrel layer 6a": "2987319910",
    "Primary somatosensory area, barrel field, D2 barrel layer 6b": "3872485424",
    "Primary somatosensory area, barrel field, D2 barrel": "3329043535",
    "Primary somatosensory area, barrel field, D3 barrel layer 1": "1781030954",
    "Primary somatosensory area, barrel field, D3 barrel layer 2": "3521164295",
    "Primary somatosensory area, barrel field, D3 barrel layer 2/3": "2841658580",
    "Primary somatosensory area, barrel field, D3 barrel layer 3": "1876807310",
    "Primary somatosensory area, barrel field, D3 barrel layer 4": "1501393228",
    "Primary somatosensory area, barrel field, D3 barrel layer 5": "1972094100",
    "Primary somatosensory area, barrel field, D3 barrel layer 6a": "3302405705",
    "Primary somatosensory area, barrel field, D3 barrel layer 6b": "1099096371",
    "Primary somatosensory area, barrel field, D3 barrel": "2036081150",
    "Primary somatosensory area, barrel field, D4 barrel layer 1": "1117257996",
    "Primary somatosensory area, barrel field, D4 barrel layer 2": "2567067139",
    "Primary somatosensory area, barrel field, D4 barrel layer 2/3": "1453537399",
    "Primary somatosensory area, barrel field, D4 barrel layer 3": "2427348802",
    "Primary somatosensory area, barrel field, D4 barrel layer 4": "3859818063",
    "Primary somatosensory area, barrel field, D4 barrel layer 5": "1588504257",
    "Primary somatosensory area, barrel field, D4 barrel layer 6a": "3571205574",
    "Primary somatosensory area, barrel field, D4 barrel layer 6b": "1096265790",
    "Primary somatosensory area, barrel field, D4 barrel": "3202423327",
    "Primary somatosensory area, barrel field, D5 barrel layer 1": "1326886999",
    "Primary somatosensory area, barrel field, D5 barrel layer 2": "2341450864",
    "Primary somatosensory area, barrel field, D5 barrel layer 2/3": "1787178465",
    "Primary somatosensory area, barrel field, D5 barrel layer 3": "2551618170",
    "Primary somatosensory area, barrel field, D5 barrel layer 4": "1170723867",
    "Primary somatosensory area, barrel field, D5 barrel layer 5": "1038004598",
    "Primary somatosensory area, barrel field, D5 barrel layer 6a": "1149652689",
    "Primary somatosensory area, barrel field, D5 barrel layer 6b": "1582478571",
    "Primary somatosensory area, barrel field, D5 barrel": "1412541198",
    "Primary somatosensory area, barrel field, D6 barrel layer 1": "1315950883",
    "Primary somatosensory area, barrel field, D6 barrel layer 2": "3990698322",
    "Primary somatosensory area, barrel field, D6 barrel layer 2/3": "1947266943",
    "Primary somatosensory area, barrel field, D6 barrel layer 3": "3301183793",
    "Primary somatosensory area, barrel field, D6 barrel layer 4": "1464978040",
    "Primary somatosensory area, barrel field, D6 barrel layer 5": "2387503636",
    "Primary somatosensory area, barrel field, D6 barrel layer 6a": "2023633893",
    "Primary somatosensory area, barrel field, D6 barrel layer 6b": "1913328693",
    "Primary somatosensory area, barrel field, D6 barrel": "1588741938",
    "Primary somatosensory area, barrel field, D7 barrel layer 1": "1877482733",
    "Primary somatosensory area, barrel field, D7 barrel layer 2": "3673895945",
    "Primary somatosensory area, barrel field, D7 barrel layer 2/3": "2358987890",
    "Primary somatosensory area, barrel field, D7 barrel layer 3": "1393608993",
    "Primary somatosensory area, barrel field, D7 barrel layer 4": "2978179471",
    "Primary somatosensory area, barrel field, D7 barrel layer 5": "3338653017",
    "Primary somatosensory area, barrel field, D7 barrel layer 6a": "2384899589",
    "Primary somatosensory area, barrel field, D7 barrel layer 6b": "2710463424",
    "Primary somatosensory area, barrel field, D7 barrel": "3920024588",
    "Primary somatosensory area, barrel field, D8 barrel layer 1": "1406402073",
    "Primary somatosensory area, barrel field, D8 barrel layer 2": "1156116970",
    "Primary somatosensory area, barrel field, D8 barrel layer 2/3": "1373744894",
    "Primary somatosensory area, barrel field, D8 barrel layer 3": "3453175542",
    "Primary somatosensory area, barrel field, D8 barrel layer 4": "3652474151",
    "Primary somatosensory area, barrel field, D8 barrel layer 5": "2236457933",
    "Primary somatosensory area, barrel field, D8 barrel layer 6a": "3277826222",
    "Primary somatosensory area, barrel field, D8 barrel layer 6b": "1005899076",
    "Primary somatosensory area, barrel field, D8 barrel": "3055000922",
    "Primary somatosensory area, barrel field, Delta barrel layer 1": "1691306271",
    "Primary somatosensory area, barrel field, Delta barrel layer 2": "1275601165",
    "Primary somatosensory area, barrel field, Delta barrel layer 2/3": "3434166213",
    "Primary somatosensory area, barrel field, Delta barrel layer 3": "3946289800",
    "Primary somatosensory area, barrel field, Delta barrel layer 4": "2004775342",
    "Primary somatosensory area, barrel field, Delta barrel layer 5": "1456398198",
    "Primary somatosensory area, barrel field, Delta barrel layer 6a": "3561503481",
    "Primary somatosensory area, barrel field, Delta barrel layer 6b": "1901850664",
    "Primary somatosensory area, barrel field, Delta barrel": "2438939909",
    "Primary somatosensory area, barrel field, E1 barrel layer 1": "3807479791",
    "Primary somatosensory area, barrel field, E1 barrel layer 2": "2980820846",
    "Primary somatosensory area, barrel field, E1 barrel layer 2/3": "2803418480",
    "Primary somatosensory area, barrel field, E1 barrel layer 3": "3188360247",
    "Primary somatosensory area, barrel field, E1 barrel layer 4": "1477785742",
    "Primary somatosensory area, barrel field, E1 barrel layer 5": "2964598138",
    "Primary somatosensory area, barrel field, E1 barrel layer 6a": "3093795446",
    "Primary somatosensory area, barrel field, E1 barrel layer 6b": "1507784331",
    "Primary somatosensory area, barrel field, E1 barrel": "1071521092",
    "Primary somatosensory area, barrel field, E2 barrel layer 1": "3748961581",
    "Primary somatosensory area, barrel field, E2 barrel layer 2": "2185403483",
    "Primary somatosensory area, barrel field, E2 barrel layer 2/3": "3128223634",
    "Primary somatosensory area, barrel field, E2 barrel layer 3": "1433026796",
    "Primary somatosensory area, barrel field, E2 barrel layer 4": "1104248884",
    "Primary somatosensory area, barrel field, E2 barrel layer 5": "3545403109",
    "Primary somatosensory area, barrel field, E2 barrel layer 6a": "1536696383",
    "Primary somatosensory area, barrel field, E2 barrel layer 6b": "3527105324",
    "Primary somatosensory area, barrel field, E2 barrel": "3054551821",
    "Primary somatosensory area, barrel field, E3 barrel layer 1": "1897015494",
    "Primary somatosensory area, barrel field, E3 barrel layer 2": "2795738785",
    "Primary somatosensory area, barrel field, E3 barrel layer 2/3": "3331790659",
    "Primary somatosensory area, barrel field, E3 barrel layer 3": "2768475141",
    "Primary somatosensory area, barrel field, E3 barrel layer 4": "2658097375",
    "Primary somatosensory area, barrel field, E3 barrel layer 5": "2157528000",
    "Primary somatosensory area, barrel field, E3 barrel layer 6a": "3309772165",
    "Primary somatosensory area, barrel field, E3 barrel layer 6b": "1928393658",
    "Primary somatosensory area, barrel field, E3 barrel": "2811301625",
    "Primary somatosensory area, barrel field, E4 barrel layer 1": "3841505448",
    "Primary somatosensory area, barrel field, E4 barrel layer 2": "3325173834",
    "Primary somatosensory area, barrel field, E4 barrel layer 2/3": "3999683881",
    "Primary somatosensory area, barrel field, E4 barrel layer 3": "1798728430",
    "Primary somatosensory area, barrel field, E4 barrel layer 4": "3299719941",
    "Primary somatosensory area, barrel field, E4 barrel layer 5": "2360313730",
    "Primary somatosensory area, barrel field, E4 barrel layer 6a": "3043750963",
    "Primary somatosensory area, barrel field, E4 barrel layer 6b": "2641148319",
    "Primary somatosensory area, barrel field, E4 barrel": "3840818183",
    "Primary somatosensory area, barrel field, E5 barrel layer 1": "1427961626",
    "Primary somatosensory area, barrel field, E5 barrel layer 2": "3092405473",
    "Primary somatosensory area, barrel field, E5 barrel layer 2/3": "1643593739",
    "Primary somatosensory area, barrel field, E5 barrel layer 3": "1181035221",
    "Primary somatosensory area, barrel field, E5 barrel layer 4": "3118601025",
    "Primary somatosensory area, barrel field, E5 barrel layer 5": "2374653061",
    "Primary somatosensory area, barrel field, E5 barrel layer 6a": "3026302666",
    "Primary somatosensory area, barrel field, E5 barrel layer 6b": "2197459620",
    "Primary somatosensory area, barrel field, E5 barrel": "1468793762",
    "Primary somatosensory area, barrel field, E6 barrel layer 1": "1666373161",
    "Primary somatosensory area, barrel field, E6 barrel layer 2": "2815501138",
    "Primary somatosensory area, barrel field, E6 barrel layer 2/3": "3620340000",
    "Primary somatosensory area, barrel field, E6 barrel layer 3": "2091848107",
    "Primary somatosensory area, barrel field, E6 barrel layer 4": "2658756176",
    "Primary somatosensory area, barrel field, E6 barrel layer 5": "2097438884",
    "Primary somatosensory area, barrel field, E6 barrel layer 6a": "2868822451",
    "Primary somatosensory area, barrel field, E6 barrel layer 6b": "3331415743",
    "Primary somatosensory area, barrel field, E6 barrel": "1965375801",
    "Primary somatosensory area, barrel field, E7 barrel layer 1": "2613674898",
    "Primary somatosensory area, barrel field, E7 barrel layer 2": "3413451609",
    "Primary somatosensory area, barrel field, E7 barrel layer 2/3": "1951878763",
    "Primary somatosensory area, barrel field, E7 barrel layer 3": "2225157452",
    "Primary somatosensory area, barrel field, E7 barrel layer 4": "2842134861",
    "Primary somatosensory area, barrel field, E7 barrel layer 5": "2064317417",
    "Primary somatosensory area, barrel field, E7 barrel layer 6a": "2123772309",
    "Primary somatosensory area, barrel field, E7 barrel layer 6b": "1510133109",
    "Primary somatosensory area, barrel field, E7 barrel": "3618095278",
    "Primary somatosensory area, barrel field, E8 barrel layer 1": "1094902124",
    "Primary somatosensory area, barrel field, E8 barrel layer 2": "3312222592",
    "Primary somatosensory area, barrel field, E8 barrel layer 2/3": "3134535128",
    "Primary somatosensory area, barrel field, E8 barrel layer 3": "1518704958",
    "Primary somatosensory area, barrel field, E8 barrel layer 4": "1475527815",
    "Primary somatosensory area, barrel field, E8 barrel layer 5": "1612593605",
    "Primary somatosensory area, barrel field, E8 barrel layer 6a": "2915675742",
    "Primary somatosensory area, barrel field, E8 barrel layer 6b": "2644357350",
    "Primary somatosensory area, barrel field, E8 barrel": "1624778115",
    "Primary somatosensory area, barrel field, Gamma barrel layer 1": "2810081477",
    "Primary somatosensory area, barrel field, Gamma barrel layer 2": "2790136061",
    "Primary somatosensory area, barrel field, Gamma barrel layer 2/3": "3513655281",
    "Primary somatosensory area, barrel field, Gamma barrel layer 3": "2667261098",
    "Primary somatosensory area, barrel field, Gamma barrel layer 4": "2302833148",
    "Primary somatosensory area, barrel field, Gamma barrel layer 5": "3278290071",
    "Primary somatosensory area, barrel field, Gamma barrel layer 6a": "2688781451",
    "Primary somatosensory area, barrel field, Gamma barrel layer 6b": "1848522986",
    "Primary somatosensory area, barrel field, Gamma barrel": "1171320182",
    "Primary somatosensory area, barrel field, layer 2": "2835688982",
    "Primary somatosensory area, barrel field, layer 3": "2598818153",
    "Primary somatosensory area, lower limb, layer 2": "1454256797",
    "Primary somatosensory area, lower limb, layer 3": "2951747260",
    "Primary somatosensory area, mouth, layer 2": "2102386393",
    "Primary somatosensory area, mouth, layer 3": "3049552521",
    "Primary somatosensory area, nose, layer 2": "3591549811",
    "Primary somatosensory area, nose, layer 3": "1624848466",
    "Primary somatosensory area, trunk, layer 2": "3562104832",
    "Primary somatosensory area, trunk, layer 3": "2260827822",
    "Primary somatosensory area, unassigned, layer 2": "3808433473",
    "Primary somatosensory area, unassigned, layer 3": "2208057363",
    "Primary somatosensory area, upper limb, layer 2": "3693772975",
    "Primary somatosensory area, upper limb, layer 3": "1890964946",
    "Primary visual area, layer 2": "2683995601",
    "Primary visual area, layer 3": "3894563657",
    "Prosubiculum: Other": "2449182232",
    "Retrosplenial area, dorsal part, layer 2": "2361776473",
    "Retrosplenial area, dorsal part, layer 3": "3956191525",
    "Retrosplenial area, lateral agranular part, layer 2": "3192952047",
    "Retrosplenial area, lateral agranular part, layer 3": "2892558637",
    "Retrosplenial area, ventral part, layer 3": "3314370483",
    "Rostrolateral visual area, layer 2": "1430875964",
    "Rostrolateral visual area, layer 3": "3714509274",
    "Secondary motor area, layer 2": 3412423041,
    "Secondary motor area, layer 3": "2511156654",
    "Spinal nucleus of the trigeminal, oral part: Other": "1593308392",
    "Striatum: Other": "3034756217",
    "Subiculum: Other": "1792026161",
    "Superior central nucleus raphe: Other": "2557684018",
    "Superior colliculus, motor related, intermediate gray layer: Other": "3654510924",
    "Supplemental somatosensory area, layer 2": "2336071181",
    "Supplemental somatosensory area, layer 3": "2542216029",
    "Supramammillary nucleus: Other": "3449035628",
    "Taenia tecta, dorsal part: Other": "3389528505",
    "Taenia tecta, ventral part: Other": "1860102496",
    "Temporal association areas, layer 2": "2439179873",
    "Temporal association areas, layer 3": "2854337283",
    "Thalamus: Other": "2614168502",
    "Ventral auditory area, layer 2": "1942628671",
    "Ventral auditory area, layer 3": "2167613582",
    "Ventral part of the lateral geniculate complex: Other": "1043765183",
    "Ventromedial hypothalamic nucleus: Other": "2723065947",
    "Visceral area, layer 2": "3964792502",
    "Visceral area, layer 3": "2189208794",
    "Zona incerta: Other": "1171543751",
    "corpus callosum, anterior forceps: Other": "3228324150",
    "corticospinal tract: Other": "2718688460",
    "facial nerve: Other": "3283016083",
    "fiber tracts: Other": "2500193001",
    "fourth ventricle: Other": "3774104740",
    "inferior cerebellar peduncle: Other": "3140724988",
    "lateral ventricle: Other": "1744978404",
    "oculomotor nerve: Other": "3944974149",
    "optic nerve: Other": "1166850207",
    "posteromedial visual area, layer 2": "2544082156",
    "posteromedial visual area, layer 3": "3710667749",
    "root: Other": "1811993763",
    "rubrospinal tract: Other": "1428498274",
    "sensory root of the trigeminal nerve: Other": "2176156825",
    "stria terminalis: Other": "2923485783",
    "superior cerebelar peduncles: Other": "2692485271",
    "superior cerebellar peduncle decussation: Other": "2434751741",
    "supraoptic commissures: Other": "1060511842",
    "trochlear nerve: Other": "3537828992",
}


def curate_role(role):
    if not role:
        return {"@id": "unspecified", "label": "unspecified"}

    if role["@id"] in {
        "neuronmorphology:ReconstructionRole",
        "neuron:MorphologyReconstructionRole",
        "https://bbp.epfl.ch/data/bbp/mmb-point-neuron-framework-model/NeuronMorphologyReconstruction",
        "https://bbp.epfl.ch/data/public/sscx/NeuronMorphologyReconstruction",
    }:
        role = {
            "@id": "Neuron:MorphologyReconstructionRole",
            "label": "neuron morphology reconstruction role",
        }
    elif role["@id"] == "neuron:ElectrophysiologyRecordingRole":
        role = {
            "@id": "Neuron:ElectrophysiologyRecordingRole",
            "label": "neuron electrophysiology recording role",
        }

    return role


def curate_annotation_body(annotation_body):
    if "Mtype" in annotation_body["@type"]:
        annotation_body["@type"] = ["MType", "AnnotationBody"]
    if annotation_body.get("@id", "") == "nsg:InhibitoryNeuron":
        annotation_body["label"] = "Inhibitory neuron"
    return annotation_body


def curate_person(person):
    if name := person.get("name", ""):
        if name == "Weina Ji":
            person["givenName"] = "Weina"
            person["familyName"] = "Ji"
        elif name == "None None":  # noqa: SIM114
            person["givenName"] = "bbp-dke-bluebrainatlas-sa"
            person["familyName"] = "bbp-dke-bluebrainatlas-sa"
        elif name == "None brain-modeling-ontology-ci-cd":
            person["givenName"] = "bbp-dke-bluebrainatlas-sa"
            person["familyName"] = "bbp-dke-bluebrainatlas-sa"

    return person


def curate_contribution(contribution):
    if isinstance(contribution, list):
        return [curate_contribution(c) for c in contribution]

    if contribution["agent"]["@id"] == "f:0fdadef7-b2b9-492b-af46-c65492d459c2:ajaquier":
        contribution["agent"]["@id"] = "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/ajaquier"
    elif contribution["agent"]["@id"] == "f:0fdadef7-b2b9-492b-af46-c65492d459c2:mandge":
        contribution["agent"]["@id"] = "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/mandge"

    return contribution


def default_curate(obj):
    return obj


def curate_synapses_per_connections(data):
    if not data.get("description", None):
        data["description"] = "unspecified"

    return data


def curate_trace(data):
    if not data.get("description", None):
        data["description"] = "unspecified"

    return data


def curate_brain_region(data):
    if data["@id"] == "mba:977" and data["label"] == "root":
        data["@id"] = "mba:997"

    data["@id"] = data["@id"].replace("mba:", "")
    data["@id"] = data["@id"].replace("http://api.brain-map.org/api/v2/data/Structure/", "")

    if data["@id"] == "root":
        data["@id"] = "997"

    if data["label"] in BRAIN_REGION_REPLACEMENTS:
        data["@id"] = BRAIN_REGION_REPLACEMENTS[data["label"]]

    return data


def curate_etype(data):
    if data["label"] == "TH_cAD_noscltb":
        data["definition"] = (
            "Thalamus continuous adapting non-oscillatory low-threshold bursting electrical type"
        )
    elif data["label"] == "TH_cNAD_noscltb":
        data["definition"] = (
            "Thalamus continuous non-adapting non-oscillatory low-threshold bursting electrical type"  # noqa: E501
        )
    elif data["label"] == "TH_dAD_ltb":
        data["definition"] = "Thalamus delayed adapting low-threshold bursting electrical type"
        data["alt_label"] = "Thalamus delayed adapting low-threshold bursting electrical type"
    elif data["label"] == "TH_dNAD_ltb":
        data["definition"] = "Thalamus delayed non-adapting low-threshold bursting electrical type"
        data["alt_label"] = "Thalamus delayed non-adapting low-threshold bursting electrical type"

    return data


def curate_morphology(data):
    if data.get("name", "") == "cylindrical_morphology_20.5398":
        data["subject"] = {
            "species": {
                "@id": "NCBITaxon:10090",
                "label": "Mus musculus",
            },
        }
    return data


def default_agents():
    return [
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/ikilic",
            "@type": "Person",
            "givenName": "Ilkan",
            "familyName": "Kilic",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        # TODO: find out who that is.
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/harikris",
            "@type": "Person",
            "givenName": "h",
            "familyName": "arikris",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/ricardi",
            "@type": "Person",
            "givenName": "Niccolò",
            "familyName": "Ricardi",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/akkaufma",
            "@type": "Person",
            "givenName": "Anna-Kristin",
            "familyName": "Kaufmann",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/gbarrios",
            "@type": "Person",
            "givenName": "Gil",
            "familyName": "Barrios",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://bbp.epfl.ch/nexus/v1/realms/bbp/users/okeeva",
            "@type": "Person",
            "givenName": "Ayima",
            "familyName": "Okeeva",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
        {
            "@id": "https://www.grid.ac/institutes/grid.83440.3b ",
            "@type": "Organization",
            "name": "University College London",
            "alternativeName": "UCL",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
    ]


def default_licenses():
    return [
        {
            "@id": "https://bbp.epfl.ch/neurosciencegraph/data/licenses/97521f71-605d-4f42-8f1b-c37e742a30bf",
            "label": "undefined",
            "description": "undefined",
            "_createdAt": datetime.datetime.now(datetime.UTC).isoformat(),
            "_updatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        },
    ]


def curate_distribution(distribution, project_context):
    if isinstance(distribution, list):
        return [curate_distribution(c, project_context) for c in distribution]
    assert distribution["@type"] == "DataDownload"
    assert distribution["contentSize"]["unitCode"] == "bytes"
    assert distribution["contentSize"]["value"] > 0
    assert distribution["digest"]["algorithm"] == "SHA-256"
    assert distribution["digest"]["value"] is not None
    assert distribution["atLocation"]["@type"] == "Location"
    return distribution
