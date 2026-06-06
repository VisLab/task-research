# Acquisition failures — pdf (2026-06-02)

Total failed refs: **743**.

Buckets are sorted by count desc.  See the JSON sidecar for full ref-ID lists per bucket.

## By `tried` set

Coarse cut: which route combinations got walked.

| Count | Tried | Sample DOIs |
|---:|---|---|
| 222 | `[openalex]` | 10.1007/978-0-230-36409-7_1, 10.1016/j.biopsych.2018.02.647, 10.1016/s1364-6613(00)01520-5 |
| 156 | `[]` | 10.1016/j.neuron.2006.07.029, 10.1037/a0039036, 10.1037/bul0000077 |
| 52 | `[openalex, openalex]` | 10.1016/j.tics.2006.10.012, 10.1016/j.concog.2011.09.021, 10.1016/j.cobeha.2017.11.012 |
| 32 | `[openalex, openalex+landing]` | 10.1007/bf00237911, 10.1038/nrn894, 10.1038/nrn.2016.113 |
| 19 | `[openalex, openalex, openalex]` | 10.1016/j.neubiorev.2011.12.013, 10.1037/0033-295x.112.4.862, 10.1016/j.neuropsychologia.2005.07.001 |
| 17 | `[openalex,unpaywall, s2, synthesized:pmc, openalex]` | 10.1016/j.neuron.2015.09.028, 10.1016/j.tins.2015.07.003, 10.1111/jcpp.12675 |
| 11 | `[openalex,unpaywall, s2, openalex]` | 10.1016/j.tics.2012.10.011, 10.1016/j.tics.2008.02.003, 10.1016/j.neuroimage.2008.05.046 |
| 10 | `[openalex, openalex, openalex+landing]` | 10.1038/nn827, 10.1038/nrn.2017.14, 10.1038/nrn2131 |
| 10 | `[openalex, openalex, openalex, openalex]` | 10.1037/a0014211, 10.1037/0033-2909.133.2.227, 10.1162/089892902317361886 |
| 10 | `[openalex, s2, synthesized:pmc, openalex]` | 10.1016/j.conb.2012.06.001, 10.1146/annurev-neuro-062111-150525, 10.1037/a0027205 |
| 9 | `[openalex, s2, openalex]` | 10.1016/j.tics.2010.10.002, 10.1037/0278-7393.34.1.167, 10.1080/17470218.2012.676055 |
| 9 | `[openalex,s2,unpaywall]` | 10.1016/0092-8674(91)90418-x, 10.1016/0896-6273(95)90304-6, 10.1006/brcg.1999.1096 |
| 7 | `[synthesized:doi]` | 10.1016/j.neuron.2015.09.004, 10.1016/s0896-6273(02)00897-8, 10.1016/s0896-6273(02)00817-6 |
| 6 | `[openalex, openalex, openalex, openalex+landing]` | 10.1038/nn1560, 10.1038/362342a0, 10.1017/s0140525x00058027 |
| 6 | `[openalex, openalex, s2, openalex]` | 10.1016/0022-0965(74)90101-5, 10.1037/pspa0000016, 10.1126/science.1102941 |
| 5 | `[openalex, openalex+landing, openalex, openalex+landing]` | 10.1038/nature05401, 10.1038/35021052, 10.1038/36846 |
| 5 | `[openalex, s2, synthesized:pmc, openalex, openalex]` | 10.1016/j.neuroscience.2016.03.021, 10.1016/j.neuroimage.2013.11.001, 10.1016/j.cpr.2009.11.003 |
| 5 | `[openalex,unpaywall, s2, synthesized:pmc, openalex, openalex]` | 10.1016/j.tics.2020.11.006, 10.1016/j.tics.2016.01.007, 10.1016/j.intell.2014.10.005 |
| 4 | `[openalex,unpaywall, openalex, s2, openalex]` | 10.1111/j.1469-8986.2006.00403.x, 10.1016/s0022-5371(70)80059-7, 10.1037/amp0000364 |
| 4 | `[openalex,unpaywall, openalex,s2,unpaywall, synthesized:doi]` | 10.1111/cogs.12688, 10.1073/pnas.0706111104, 10.1093/sleep/34.5.581 |
| 3 | `[openalex, openalex, openalex, openalex, openalex]` | 10.1080/02643290903343149, 10.1016/s0896-6273(03)00466-5, 10.1006/brcg.2000.1225 |
| 3 | `[openalex, openalex,s2,unpaywall, openalex,s2,unpaywall+landing, openalex, synthesized:doi, synthesized:doi+landing]` | 10.1038/npp.2009.131 |
| 3 | `[openalex,s2,unpaywall, synthesized:doi]` | 10.1093/brain/awm011, 10.1016/j.acn.2006.06.010, 10.1093/arclin/acz034.29 |
| 3 | `[openalex,unpaywall, openalex, s2, synthesized:pmc, openalex]` | 10.1016/j.conb.2012.11.005, 10.1016/j.biopsych.2015.08.025 |
| 3 | `[openalex,unpaywall, openalex, synthesized:pmc, synthesized:doi]` | 10.1016/j.neuron.2012.01.010 |
| … | _104 more buckets_ | |

## By normalized reason component

Compound reasons split on `;`; each component counted independently.  This is the candidate-level cut.

| Count | Reason component | Sample DOIs |
|---:|---|---|
| 514 | `openalex: not pdf (text/html)` | 10.1016/j.neuron.2015.09.028, 10.1038/npp.2009.131, 10.1038/nn1560 |
| 220 | `openalex: http 403` | 10.1016/j.neuroscience.2016.03.021, 10.1016/j.concog.2011.09.021, 10.1111/jcpp.12675 |
| 156 | `no candidate locations` | 10.1016/j.neuron.2006.07.029, 10.1037/a0039036, 10.1037/bul0000077 |
| 147 | `openalex,unpaywall: not pdf (text/html)` | 10.1016/j.neuron.2015.09.028, 10.1016/j.neuron.2011.02.027, 10.1016/j.neuron.2015.09.029 |
| 89 | `openalex: sslerror` | 10.1016/j.tics.2011.12.010, 10.1002/hbm.20422, 10.1016/0022-0965(74)90101-5 |
| 88 | `openalex+landing: not pdf (text/html)` | 10.1038/nn1560, 10.1007/bf00237911, 10.1038/35784 |
| 87 | `synthesized:pmc: not pdf (text/html)` | 10.1016/j.neuron.2015.09.028, 10.1016/j.neuroscience.2016.03.021, 10.1016/j.tins.2015.07.003 |
| 54 | `s2: http 500` | 10.1016/j.neuron.2015.09.028, 10.1016/j.neuroscience.2016.03.021, 10.1016/j.tins.2015.07.003 |
| 44 | `synthesized:doi: not pdf (text/html)` | 10.1038/npp.2009.131, 10.1016/j.neuron.2011.02.027, 10.1038/35784 |
| 41 | `openalex: http 404` | 10.1038/nn1560, 10.1016/j.neuron.2011.02.027, 10.1016/j.neuron.2015.09.029 |
| 30 | `openalex,s2,unpaywall: http 403` | 10.1016/j.tics.2014.03.002, 10.1111/ejn.13720, 10.1167/13.12.7 |
| 27 | `openalex,unpaywall: http 403` | 10.1016/j.neuron.2011.02.027, 10.1016/j.neuron.2015.09.029, 10.1016/j.neuron.2013.07.051 |
| 26 | `openalex,s2,unpaywall: not pdf (text/html)` | 10.1038/npp.2009.131, 10.1038/35784, 10.1016/j.copsyc.2017.04.020 |
| 22 | `synthesized:doi: http 403` | 10.1111/ejn.13720, 10.1111/j.1749-6632.2012.06751.x, 10.1093/scan/nsu016 |
| 21 | `s2: not pdf (text/html)` | 10.1162/jocn_a_01768, 10.1002/hbm.20422, 10.1038/nrn3158 |
| 14 | `openalex,unpaywall+landing: not pdf (text/html)` | 10.1017/s0140525x99451775, 10.1016/j.tics.2011.10.001, 10.1016/j.tics.2007.09.002 |
| 13 | `s2: http 403` | 10.1016/s0022-5371(70)80059-7, 10.1037/pas0000036, 10.1080/17470218.2012.676055 |
| 13 | `s2: readtimeout: httpsconnectionpool(host='europepmc.org', port=443): read timed out. (read timeout=30.0)` | 10.1016/j.conb.2012.06.001, 10.1016/j.jml.2015.04.004, 10.1016/j.neubiorev.2016.01.003 |
| 11 | `openalex,unpaywall: http 202` | 10.1016/j.copsyc.2017.04.020, 10.1002/hbm.20422, 10.1111/j.1469-8986.2006.00403.x |
| 10 | `synthesized:doi+landing: not pdf (text/html)` | 10.1038/npp.2009.131, 10.1038/35784, 10.1038/212438a0 |
| 8 | `openalex,s2,unpaywall+landing: not pdf (text/html)` | 10.1038/npp.2009.131, 10.1038/35784, 10.1038/212438a0 |
| 6 | `s2: http 404` | 10.1016/j.tics.2007.09.002, 10.1080/02699930125768, 10.1038/s41562-020-0905-y |
| 5 | `openalex,unpaywall+landing: http 403` | 10.1093/brain/awq148, 10.1016/j.copsyc.2018.12.024, 10.1016/j.neubiorev.2021.10.024 |
| 5 | `openalex: connectionerror` | 10.1016/j.neuron.2011.02.027, 10.1016/j.tics.2006.11.002, 10.1080/02643290903343149 |
| 4 | `openalex,unpaywall: http 410` | 10.1007/s00221-012-3272-8, 10.1016/j.neubiorev.2017.04.026, 10.1111/ejn.12936 |
| … | _32 more buckets_ | |

## By (tried, normalized reason) pattern

Finest cut.  Top rows are the design input for recovery passes.

| Count | Pattern | Sample DOIs |
|---:|---|---|
| 156 | `[] :: no candidate locations` | 10.1016/j.neuron.2006.07.029, 10.1037/a0039036, 10.1037/bul0000077 |
| 119 | `[openalex] :: openalex: not pdf (text/html)` | 10.1007/978-0-230-36409-7_1, 10.1016/j.biopsych.2018.02.647, 10.1016/s1364-6613(00)01520-5 |
| 103 | `[openalex] :: openalex: http 403` | 10.1037/13798-000, 10.1037/0022-3514.50.2.229, 10.1037/0022-3514.64.5.723 |
| 32 | `[openalex, openalex+landing] :: openalex+landing: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1007/bf00237911, 10.1038/nrn894, 10.1038/nrn.2016.113 |
| 21 | `[openalex, openalex] :: openalex: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.tics.2006.10.012, 10.1016/j.cobeha.2017.11.012, 10.1016/0010-0285(82)90008-1 |
| 11 | `[openalex, openalex] :: openalex: not pdf (text/html) | openalex: http 403` | 10.1037/0033-295x.91.3.295, 10.1037/0033-2909.120.1.3, 10.1037/a0016923 |
| 10 | `[openalex, openalex] :: openalex: sslerror | openalex: http 403` | 10.1126/science.1117645, 10.1177/0888439004269072, 10.1163/156856888x00122 |
| 9 | `[openalex,unpaywall, s2, synthesized:pmc, openalex] :: openalex,unpaywall: not pdf (text/html) | s2: http 500 | synthesized:pmc: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.neuron.2015.09.028, 10.1016/j.tins.2015.07.003, 10.1016/j.tins.2011.06.006 |
| 6 | `[openalex, openalex, openalex+landing] :: openalex: not pdf (text/html) | openalex+landing: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1038/nrn.2017.14, 10.1038/nrn2131, 10.1038/nrn3924 |
| 6 | `[openalex, s2, synthesized:pmc, openalex] :: openalex: not pdf (text/html) | s2: http 500 | synthesized:pmc: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.conb.2012.06.001, 10.1146/annurev-neuro-062111-150525, 10.1016/j.neuropharm.2013.06.013 |
| 6 | `[openalex,s2,unpaywall] :: openalex,s2,unpaywall: not pdf (text/html)` | 10.1016/0092-8674(91)90418-x, 10.1016/0896-6273(95)90304-6, 10.1006/brcg.1999.1096 |
| 6 | `[synthesized:doi] :: synthesized:doi: not pdf (text/html)` | 10.1016/j.neuron.2015.09.004, 10.1016/s0896-6273(02)00897-8, 10.1016/s0896-6273(02)00817-6 |
| 5 | `[openalex, openalex+landing, openalex, openalex+landing] :: openalex+landing: not pdf (text/html) | openalex: not pdf (text/html) | openalex+landing: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1038/nature05401, 10.1038/35021052, 10.1038/36846 |
| 5 | `[openalex, openalex, openalex] :: openalex: not pdf (text/html) | openalex: not pdf (text/html) | openalex: http 403` | 10.1080/1047840x.2010.487849, 10.1037/0096-1523.31.3.453, 10.1037/0033-2909.121.3.371 |
| 5 | `[openalex,unpaywall, s2, openalex] :: openalex,unpaywall: not pdf (text/html) | s2: http 500 | openalex: not pdf (text/html)` | 10.1016/j.tics.2012.10.011, 10.1016/j.tics.2008.02.003, 10.1016/j.neuroimage.2008.04.025 |
| 4 | `[openalex, openalex, openalex+landing] :: openalex: http 404 | openalex+landing: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1038/nn827, 10.1038/nrn2497, 10.1007/s00221-011-2579-1 |
| 4 | `[openalex,unpaywall, openalex,s2,unpaywall, synthesized:doi] :: openalex,unpaywall: not pdf (text/html) | openalex,s2,unpaywall: http 403 | synthesized:doi: http 403` | 10.1111/cogs.12688, 10.1073/pnas.0706111104, 10.1093/sleep/34.5.581 |
| 4 | `[openalex,unpaywall, s2, synthesized:pmc, openalex] :: openalex,unpaywall: not pdf (text/html) | s2: http 500 | synthesized:pmc: not pdf (text/html) | openalex: http 403` | 10.1111/jcpp.12675, 10.1162/jocn_a_00811, 10.1002/hipo.20808 |
| 3 | `[openalex, openalex, openalex, openalex+landing] :: openalex: not pdf (text/html) | openalex: not pdf (text/html) | openalex+landing: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1017/s0140525x00058027, 10.1038/nn1574, 10.3758/pbr.17.5.603 |
| 3 | `[openalex, openalex, openalex] :: openalex: not pdf (text/html) | openalex: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.bandc.2009.08.007, 10.1016/s1364-6613(00)01482-0, 10.1016/j.neubiorev.2015.02.007 |
| 3 | `[openalex, openalex,s2,unpaywall, openalex,s2,unpaywall+landing, openalex, synthesized:doi, synthesized:doi+landing] :: openalex: not pdf (text/html) | openalex,s2,unpaywall+landing: not pdf (text/html) | openalex,s2,unpaywall: not pdf (text/html) | openalex: not pdf (text/html) | synthesized:doi+landing: not pdf (text/html) | synthesized:doi: not pdf (text/html)` | 10.1038/npp.2009.131 |
| 3 | `[openalex, openalex] :: openalex: http 403 | openalex: not pdf (text/html)` | 10.1016/j.concog.2011.09.021, 10.1016/s0022-5371(69)80069-1, 10.1016/j.joep.2011.05.007 |
| 3 | `[openalex, s2, openalex] :: openalex: not pdf (text/html) | s2: http 500 | openalex: not pdf (text/html)` | 10.1016/j.tics.2010.10.002, 10.1016/j.neuropsychologia.2012.12.014, 10.1016/j.cogpsych.2013.07.001 |
| 3 | `[openalex, s2, synthesized:pmc, openalex] :: openalex: not pdf (text/html) | s2: readtimeout: httpsconnectionpool(host='europepmc.org', port=443): read timed out. (read timeout=30.0) | synthesized:pmc: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.conb.2012.06.001, 10.1146/annurev-neuro-062111-150525, 10.1016/j.tics.2013.12.006 |
| 3 | `[openalex,s2,unpaywall, synthesized:doi] :: openalex,s2,unpaywall: http 403 | synthesized:doi: http 403` | 10.1093/brain/awm011, 10.1016/j.acn.2006.06.010, 10.1093/arclin/acz034.29 |
| … | _178 more buckets_ | |
