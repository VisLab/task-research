# Acquisition failures — pdf (2026-06-03)

Total failed refs: **719**.

Buckets are sorted by count desc.  See the JSON sidecar for full ref-ID lists per bucket.

## By `tried` set

Coarse cut: which route combinations got walked.

| Count | Tried | Sample DOIs |
|---:|---|---|
| 275 | `[openalex]` | 10.1146/annurev.psych.093008.100422, 10.1103/revmodphys.12.47, 10.1007/978-0-230-36409-7_1 |
| 61 | `[openalex, openalex]` | 10.1016/j.tics.2006.10.012, 10.1016/j.concog.2011.09.021, 10.1037//0022-3514.35.9.677 |
| 35 | `[]` | 10.1016/j.neuron.2015.09.004, 10.1016/s0896-6273(02)00897-8, 10.1016/s0896-6273(02)00817-6 |
| 35 | `[openalex,unpaywall, s2, openalex]` | 10.1016/j.neuron.2015.09.028, 10.1016/j.tins.2015.07.003, 10.1113/jphysiol.1962.sp006837 |
| 32 | `[openalex, openalex+landing]` | 10.1007/bf00237911, 10.1038/nrn894, 10.1038/nrn.2016.113 |
| 28 | `[openalex, s2, openalex]` | 10.1146/annurev-psych-113011-143750, 10.1146/annurev-neuro-062111-150525, 10.1146/annurev-neuro-061010-113720 |
| 26 | `[openalex, openalex, openalex]` | 10.1126/science.1097011, 10.1016/j.neubiorev.2011.12.013, 10.1111/j.1467-9280.1993.tb00586.x |
| 16 | `[openalex, openalex, openalex, openalex]` | 10.1016/j.tics.2006.03.007, 10.1037/1089-2680.2.3.271, 10.1162/089892902317361886 |
| 13 | `[openalex,s2,unpaywall]` | 10.1111/j.2044-8295.1986.tb02199.x, 10.1016/0092-8674(91)90418-x, 10.1016/0896-6273(95)90304-6 |
| 10 | `[openalex, openalex, openalex+landing]` | 10.1038/nn827, 10.1038/nrn.2017.14, 10.1038/nrn2131 |
| 9 | `[openalex,unpaywall, openalex, s2, openalex]` | 10.1037/0096-3445.132.1.47, 10.1016/j.conb.2012.11.005, 10.1146/annurev.neuro.051508.135546 |
| 9 | `[openalex,unpaywall, s2, openalex, openalex]` | 10.1016/j.tics.2011.10.001, 10.1037/a0015849, 10.1016/j.tics.2020.11.006 |
| 6 | `[openalex, openalex, openalex, openalex+landing]` | 10.1038/nn1560, 10.1038/362342a0, 10.1017/s0140525x00058027 |
| 6 | `[openalex, openalex, s2, openalex]` | 10.1016/0022-0965(74)90101-5, 10.1111/psyp.12871, 10.1037/pspa0000016 |
| 6 | `[openalex, s2, openalex, openalex]` | 10.1016/j.neuroscience.2016.03.021, 10.1016/j.neuroimage.2013.11.001, 10.1016/j.cpr.2009.11.003 |
| 6 | `[openalex,unpaywall, openalex,s2,unpaywall]` | 10.1080/17470218.2016.1181768, 10.1093/cercor/bht091, 10.1111/cogs.12688 |
| 6 | `[openalex,unpaywall, openalex,unpaywall, openalex,s2,unpaywall]` | 10.1073/pnas.1400335111, 10.1016/j.copsyc.2017.04.020, 10.1016/j.tics.2015.05.004 |
| 6 | `[openalex,unpaywall, openalex]` | 10.1016/j.neuron.2012.01.010, 10.1080/17470216508416445, 10.1016/j.neuron.2008.04.017 |
| 5 | `[openalex, openalex+landing, openalex, openalex+landing]` | 10.1038/nature05401, 10.1038/35021052, 10.1038/36846 |
| 5 | `[openalex,unpaywall, openalex, openalex, s2, openalex]` | 10.1037/0033-295x.87.3.252, 10.1037/pas0000036, 10.1126/science.aan8871 |
| 5 | `[s2, openalex]` | 10.1098/rstb.1982.0082, 10.1080/17470214808416738, 10.1080/02699930125768 |
| 4 | `[openalex, openalex, openalex, s2, openalex]` | 10.1162/08989290260138672, 10.1037/0033-295x.94.2.115, 10.1162/jocn.2009.21255 |
| 4 | `[openalex, openalex,s2,unpaywall]` | 10.1093/scan/nsu016, 10.1006/cogp.1998.0681, 10.1016/j.cobeha.2014.08.005 |
| 4 | `[openalex,unpaywall, openalex,s2,unpaywall, openalex]` | 10.1111/nyas.13634, 10.1093/scan/nsn051, 10.1002/hbm.23854 |
| 4 | `[openalex,unpaywall, openalex,unpaywall]` | 10.1016/j.tics.2024.11.008, 10.1016/s0896-6273(02)00755-9, 10.1016/j.neuropsychologia.2016.08.008 |
| … | _75 more buckets_ | |

## By normalized reason component

Compound reasons split on `;`; each component counted independently.  This is the candidate-level cut.

| Count | Reason component | Sample DOIs |
|---:|---|---|
| 565 | `openalex: not pdf (text/html)` | 10.1146/annurev.psych.093008.100422, 10.1016/j.neuron.2015.09.028, 10.1038/npp.2009.131 |
| 294 | `openalex: http 403` | 10.1016/j.neuroscience.2016.03.021, 10.1103/revmodphys.12.47, 10.1126/science.1097011 |
| 161 | `openalex,unpaywall: not pdf (text/html)` | 10.1016/j.neuron.2015.09.028, 10.1146/annurev.psych.54.101601.145124, 10.1016/j.neuron.2011.02.027 |
| 127 | `openalex: sslerror` | 10.1126/science.1097011, 10.1016/j.tics.2006.03.007, 10.1162/08989290260138672 |
| 84 | `openalex+landing: not pdf (text/html)` | 10.1038/nn1560, 10.1007/bf00237911, 10.1038/35784 |
| 77 | `s2: http 500` | 10.1016/j.neuron.2015.09.028, 10.1146/annurev.psych.54.101601.145124, 10.1016/j.neuroscience.2016.03.021 |
| 46 | `openalex: http 404` | 10.1038/nn1560, 10.1016/j.neuron.2011.02.027, 10.1016/j.neuron.2015.09.029 |
| 35 | `no candidate locations` | 10.1016/j.neuron.2015.09.004, 10.1016/s0896-6273(02)00897-8, 10.1016/s0896-6273(02)00817-6 |
| 35 | `openalex,s2,unpaywall: http 403` | 10.1073/pnas.1400335111, 10.1080/17470218.2016.1181768, 10.1093/brain/awu141 |
| 29 | `openalex,unpaywall: http 403` | 10.1016/j.neuron.2011.02.027, 10.1016/j.neuron.2015.09.029, 10.1016/j.neuron.2013.07.051 |
| 27 | `openalex,s2,unpaywall: not pdf (text/html)` | 10.1038/npp.2009.131, 10.1038/35784, 10.1016/j.copsyc.2017.04.020 |
| 24 | `s2: not pdf (text/html)` | 10.1113/jphysiol.1962.sp006837, 10.1162/jocn_a_01768, 10.1002/hbm.20422 |
| 20 | `s2: http 403` | 10.1037/0033-295x.87.3.252, 10.1146/annurev-neuro-062012-170349, 10.1207/s15516709cog0702_3 |
| 11 | `openalex,unpaywall: http 202` | 10.1016/j.copsyc.2017.04.020, 10.1002/hbm.20422, 10.1111/j.1469-8986.2006.00403.x |
| 9 | `s2: http 404` | 10.1162/08989290260138672, 10.1037/0096-3445.132.1.47, 10.1037/xlm0000578 |
| 8 | `openalex,s2,unpaywall+landing: not pdf (text/html)` | 10.1038/npp.2009.131, 10.1038/35784, 10.1038/212438a0 |
| 6 | `openalex,unpaywall+landing: not pdf (text/html)` | 10.1146/annurev.psych.54.101601.145124, 10.1016/j.neuron.2011.10.027, 10.1016/j.neuron.2012.01.010 |
| 5 | `openalex,unpaywall+landing: http 403` | 10.1093/brain/awq148, 10.1016/j.copsyc.2018.12.024, 10.1016/j.neubiorev.2021.10.024 |
| 4 | `openalex,unpaywall: http 410` | 10.1007/s00221-012-3272-8, 10.1016/j.neubiorev.2017.04.026, 10.1111/ejn.12936 |
| 4 | `openalex,unpaywall: readtimeout: httpsconnectionpool(host='www.zora.uzh.ch', port=443): read timed out. (read timeout=30.0)` | 10.1037/xlm0000578, 10.1037/a0017891, 10.1016/j.tics.2007.09.002 |
| 4 | `openalex: connectionerror` | 10.1016/j.neuron.2011.02.027, 10.1207/s15516709cog0702_3, 10.1037/0033-295x.97.3.404 |
| 4 | `openalex: http 202` | 10.1037/a0014282, 10.1111/j.1469-8986.2006.00403.x, 10.1037/0033-295x.97.3.404 |
| 4 | `openalex: not pdf (application/vnd.api+json)` | 10.1111/psyp.12871, 10.1037/pspa0000016, 10.1037/amp0000364 |
| 4 | `s2: connectionerror` | 10.1098/rstb.1982.0082, 10.1037/0033-2909.116.2.220 |
| 3 | `openalex,s2: not pdf (text/html)` | 10.1016/j.tins.2006.04.001, 10.1006/cogp.1997.0659, 10.1016/s1364-6613(00)01839-8 |
| … | _33 more buckets_ | |

## By (tried, normalized reason) pattern

Finest cut.  Top rows are the design input for recovery passes.

| Count | Pattern | Sample DOIs |
|---:|---|---|
| 138 | `[openalex] :: openalex: http 403` | 10.1103/revmodphys.12.47, 10.1111/j.1469-8986.1981.tb02486.x, 10.1037/0096-3445.126.4.349 |
| 136 | `[openalex] :: openalex: not pdf (text/html)` | 10.1146/annurev.psych.093008.100422, 10.1007/978-0-230-36409-7_1, 10.1016/j.biopsych.2018.02.647 |
| 35 | `[] :: no candidate locations` | 10.1016/j.neuron.2015.09.004, 10.1016/s0896-6273(02)00897-8, 10.1016/s0896-6273(02)00817-6 |
| 32 | `[openalex, openalex+landing] :: openalex+landing: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1007/bf00237911, 10.1038/nrn894, 10.1038/nrn.2016.113 |
| 22 | `[openalex, openalex] :: openalex: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.tics.2006.10.012, 10.1016/j.cobeha.2017.11.012, 10.1016/0010-0285(82)90008-1 |
| 19 | `[openalex,unpaywall, s2, openalex] :: openalex,unpaywall: not pdf (text/html) | s2: http 500 | openalex: not pdf (text/html)` | 10.1016/j.neuron.2015.09.028, 10.1016/j.tins.2015.07.003, 10.1016/j.tics.2012.10.011 |
| 17 | `[openalex, s2, openalex] :: openalex: not pdf (text/html) | s2: http 500 | openalex: not pdf (text/html)` | 10.1146/annurev-psych-113011-143750, 10.1146/annurev-neuro-062111-150525, 10.1146/annurev-neuro-061010-113720 |
| 14 | `[openalex, openalex] :: openalex: sslerror | openalex: http 403` | 10.1037/h0027366, 10.1037/0033-295x.85.2.59, 10.1126/science.1117645 |
| 13 | `[openalex, openalex] :: openalex: not pdf (text/html) | openalex: http 403` | 10.1037/0033-295x.91.3.295, 10.1037/0033-295x.108.1.204, 10.1037/a0022288 |
| 8 | `[openalex,unpaywall, s2, openalex] :: openalex,unpaywall: not pdf (text/html) | s2: http 500 | openalex: http 403` | 10.1111/jcpp.12675, 10.1162/jocn_a_00811, 10.1002/hipo.20808 |
| 7 | `[openalex,s2,unpaywall] :: openalex,s2,unpaywall: http 403` | 10.1111/j.2044-8295.1986.tb02199.x, 10.1167/13.12.7, 10.1037/bul0000192 |
| 6 | `[openalex, openalex, openalex+landing] :: openalex: not pdf (text/html) | openalex+landing: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1038/nrn.2017.14, 10.1038/nrn2131, 10.1038/nrn3924 |
| 6 | `[openalex, openalex, openalex] :: openalex: not pdf (text/html) | openalex: not pdf (text/html) | openalex: http 403` | 10.1111/j.1467-9280.1993.tb00586.x, 10.1080/1047840x.2010.487849, 10.1037/0096-1523.31.3.453 |
| 6 | `[openalex,s2,unpaywall] :: openalex,s2,unpaywall: not pdf (text/html)` | 10.1016/0092-8674(91)90418-x, 10.1016/0896-6273(95)90304-6, 10.1006/brcg.1999.1096 |
| 6 | `[openalex,unpaywall, openalex,s2,unpaywall] :: openalex,unpaywall: not pdf (text/html) | openalex,s2,unpaywall: http 403` | 10.1080/17470218.2016.1181768, 10.1093/cercor/bht091, 10.1111/cogs.12688 |
| 5 | `[openalex, openalex+landing, openalex, openalex+landing] :: openalex+landing: not pdf (text/html) | openalex: not pdf (text/html) | openalex+landing: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1038/nature05401, 10.1038/35021052, 10.1038/36846 |
| 5 | `[openalex, openalex, openalex, openalex] :: openalex: sslerror | openalex: sslerror | openalex: sslerror | openalex: http 403` | 10.1037/1089-2680.2.3.271, 10.1162/089892902317361886 |
| 5 | `[openalex, openalex, openalex] :: openalex: sslerror | openalex: sslerror | openalex: http 403` | 10.1037/0033-295x.97.3.332, 10.1037/0033-295x.95.2.163, 10.1037/0033-295x.114.1.152 |
| 4 | `[openalex, openalex, openalex+landing] :: openalex: http 404 | openalex+landing: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1038/nn827, 10.1038/nrn2497, 10.1007/s00221-011-2579-1 |
| 4 | `[openalex,unpaywall, openalex, s2, openalex] :: openalex,unpaywall: not pdf (text/html) | openalex: not pdf (text/html) | s2: http 500 | openalex: not pdf (text/html)` | 10.1016/j.conb.2012.11.005, 10.1146/annurev.neuro.051508.135546, 10.1016/j.biopsych.2015.08.025 |
| 4 | `[openalex,unpaywall, openalex] :: openalex,unpaywall: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.neuron.2012.01.010, 10.1016/j.neuron.2008.04.017, 10.1016/j.tics.2005.05.009 |
| 4 | `[openalex,unpaywall, s2, openalex] :: openalex,unpaywall: not pdf (text/html) | s2: not pdf (text/html) | openalex: http 403` | 10.1113/jphysiol.1962.sp006837, 10.1162/jocn_a_01768, 10.1073/pnas.94.26.14792 |
| 3 | `[openalex, openalex, openalex, openalex+landing] :: openalex: not pdf (text/html) | openalex: not pdf (text/html) | openalex+landing: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1017/s0140525x00058027, 10.1038/nn1574, 10.3758/pbr.17.5.603 |
| 3 | `[openalex, openalex, openalex] :: openalex: not pdf (text/html) | openalex: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.bandc.2009.08.007, 10.1016/s1364-6613(00)01482-0, 10.1016/j.neubiorev.2015.02.007 |
| 3 | `[openalex, openalex,s2,unpaywall, openalex,s2,unpaywall+landing, openalex] :: openalex: not pdf (text/html) | openalex,s2,unpaywall+landing: not pdf (text/html) | openalex,s2,unpaywall: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1038/npp.2009.131 |
| … | _167 more buckets_ | |
