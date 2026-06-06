# Acquisition failures — pdf (2026-06-01)

Total failed refs: **780**.

Buckets are sorted by count desc.  See the JSON sidecar for full ref-ID lists per bucket.

## By `tried` set

Coarse cut: which route combinations got walked.

| Count | Tried | Sample DOIs |
|---:|---|---|
| 261 | `[openalex]` | 10.1007/bf00237911, 10.1007/978-0-230-36409-7_1, 10.1038/nrn894 |
| 163 | `[]` | 10.1016/j.neuron.2015.09.004, 10.1016/s0896-6273(02)00897-8, 10.1016/s0896-6273(02)00817-6 |
| 69 | `[openalex, openalex]` | 10.1016/j.tics.2006.10.012, 10.1016/j.concog.2011.09.021, 10.1038/nn827 |
| 33 | `[openalex,unpaywall, s2, openalex]` | 10.1016/j.neuron.2015.09.028, 10.1016/j.tins.2015.07.003, 10.1016/j.tics.2012.10.011 |
| 28 | `[openalex, openalex, openalex]` | 10.1038/nn1560, 10.1016/j.neubiorev.2011.12.013, 10.1038/362342a0 |
| 25 | `[openalex, s2, openalex]` | 10.1038/nrn3158, 10.1038/nrn755, 10.1016/j.conb.2012.06.001 |
| 13 | `[openalex, openalex, openalex, openalex]` | 10.1037/a0014211, 10.1037/0033-2909.133.2.227, 10.1162/089892902317361886 |
| 13 | `[openalex,s2,unpaywall]` | 10.1016/0092-8674(91)90418-x, 10.1016/0896-6273(95)90304-6, 10.1006/brcg.1999.1096 |
| 9 | `[openalex,unpaywall, openalex, openalex]` | 10.1007/978-1-4614-5465-6_1, 10.1016/j.neuron.2015.02.018, 10.1038/386604a0 |
| 8 | `[openalex,unpaywall, openalex, s2, openalex]` | 10.1016/j.conb.2012.11.005, 10.1111/j.1469-8986.2006.00403.x, 10.1016/s0022-5371(70)80059-7 |
| 8 | `[openalex,unpaywall, s2, openalex, openalex]` | 10.1016/j.tics.2011.10.001, 10.1016/j.tics.2020.11.006, 10.1016/j.tics.2016.01.007 |
| 7 | `[openalex, s2, openalex, openalex]` | 10.1016/j.neuroscience.2016.03.021, 10.1016/j.neuroimage.2013.11.001, 10.1016/j.cpr.2009.11.003 |
| 7 | `[openalex,unpaywall, openalex]` | 10.1016/j.neuron.2012.01.010, 10.1016/j.neuron.2008.04.017, 10.1016/j.tics.2005.05.009 |
| 6 | `[openalex, openalex, s2, openalex]` | 10.1016/0022-0965(74)90101-5, 10.1037/pspa0000016, 10.1126/science.1102941 |
| 5 | `[openalex,unpaywall, openalex,s2,unpaywall, openalex,unpaywall, openalex]` | 10.1016/j.tics.2014.03.002, 10.1016/j.neuron.2016.03.037, 10.1177/0963721417689881 |
| 5 | `[openalex,unpaywall, openalex,s2,unpaywall]` | 10.1038/npp.2010.129, 10.1111/cogs.12688, 10.1073/pnas.0706111104 |
| 5 | `[openalex,unpaywall, openalex,unpaywall, openalex,s2,unpaywall]` | 10.1016/j.copsyc.2017.04.020, 10.1016/j.tics.2015.05.004, 10.1016/j.neuroimage.2020.117601 |
| 5 | `[openalex,unpaywall, openalex,unpaywall]` | 10.1016/j.tics.2024.11.008, 10.1016/s0896-6273(02)00755-9, 10.1016/j.neuropsychologia.2016.08.008 |
| 5 | `[openalex,unpaywall]` | 10.1016/j.neuron.2011.10.027, 10.1016/j.neuroscience.2018.05.014, 10.1016/j.cub.2020.04.091 |
| 4 | `[openalex, openalex,s2,unpaywall, openalex]` | 10.1038/npp.2009.131, 10.1073/pnas.1117807108 |
| 4 | `[openalex,s2,unpaywall, openalex]` | 10.1038/35784, 10.1111/ejn.13720, 10.1093/brain/awq152 |
| 4 | `[openalex,unpaywall, openalex, openalex, openalex]` | 10.1162/jocn.2008.20.1.1, 10.1111/ejn.12936, 10.1016/j.neuron.2010.04.016 |
| 4 | `[openalex,unpaywall, openalex, openalex, s2, openalex]` | 10.1037/abn0000406, 10.1037/pas0000036, 10.1037/0033-295x.87.3.252 |
| 4 | `[openalex,unpaywall, openalex,s2,unpaywall, openalex]` | 10.1111/nyas.13634, 10.1093/scan/nsn051, 10.1002/hbm.23854 |
| 3 | `[openalex, openalex, openalex, openalex, openalex]` | 10.1080/02643290903343149, 10.1016/s0896-6273(03)00466-5, 10.1006/brcg.2000.1225 |
| … | _62 more buckets_ | |

## By normalized reason component

Compound reasons split on `;`; each component counted independently.  This is the candidate-level cut.

| Count | Reason component | Sample DOIs |
|---:|---|---|
| 563 | `openalex: not pdf (text/html)` | 10.1016/j.neuron.2015.09.028, 10.1038/npp.2009.131, 10.1038/nn1560 |
| 224 | `openalex: http 403` | 10.1016/j.neuroscience.2016.03.021, 10.1016/j.concog.2011.09.021, 10.1111/jcpp.12675 |
| 206 | `openalex,unpaywall: not pdf (text/html)` | 10.1016/j.neuron.2015.09.028, 10.1016/j.neuron.2011.02.027, 10.1016/j.neuron.2015.09.029 |
| 163 | `no candidate locations` | 10.1016/j.neuron.2015.09.004, 10.1016/s0896-6273(02)00897-8, 10.1016/s0896-6273(02)00817-6 |
| 92 | `openalex: sslerror` | 10.1016/j.tics.2011.12.010, 10.1002/hbm.20422, 10.1016/0022-0965(74)90101-5 |
| 64 | `s2: http 500` | 10.1016/j.neuron.2015.09.028, 10.1016/j.neuroscience.2016.03.021, 10.1016/j.tins.2015.07.003 |
| 47 | `openalex: http 404` | 10.1038/nn1560, 10.1016/j.neuron.2011.02.027, 10.1016/j.neuron.2015.09.029 |
| 36 | `openalex,s2,unpaywall: http 403` | 10.1016/j.tics.2014.03.002, 10.1016/j.neuron.2016.03.037, 10.1111/ejn.13720 |
| 32 | `openalex,s2,unpaywall: not pdf (text/html)` | 10.1038/npp.2009.131, 10.1038/35784, 10.1016/j.copsyc.2017.04.020 |
| 32 | `openalex,unpaywall: http 403` | 10.1016/j.neuron.2011.02.027, 10.1016/j.neuron.2015.09.029, 10.1016/j.neuron.2013.07.051 |
| 24 | `s2: not pdf (text/html)` | 10.1162/jocn_a_01768, 10.1002/hbm.20422, 10.1038/nrn3158 |
| 14 | `s2: http 403` | 10.1016/s0022-5371(70)80059-7, 10.1037/pas0000036, 10.1080/17470218.2012.676055 |
| 13 | `openalex,unpaywall: http 202` | 10.1016/j.copsyc.2017.04.020, 10.1002/hbm.20422, 10.1111/j.1469-8986.2006.00403.x |
| 8 | `openalex: not pdf (application/vnd.api+json)` | 10.1037/abn0000406, 10.1037/pspa0000016, 10.1037/amp0000364 |
| 7 | `s2: http 404` | 10.1016/j.jml.2009.06.002, 10.1016/j.tics.2007.09.002, 10.1080/02699930125768 |
| 6 | `openalex: connectionerror` | 10.1016/j.neuron.2011.02.027, 10.1016/j.jbtep.2006.10.008, 10.1038/nature04766 |
| 4 | `openalex,unpaywall: http 410` | 10.1007/s00221-012-3272-8, 10.1016/j.neubiorev.2017.04.026, 10.1111/ejn.12936 |
| 4 | `openalex,unpaywall: http 500` | 10.1016/j.cub.2009.07.066, 10.1016/j.neuroimage.2013.11.034, 10.1016/j.jml.2019.104082 |
| 4 | `openalex: http 202` | 10.1111/j.1469-8986.2006.00403.x, 10.1037/0033-295x.97.3.404, 10.1016/j.actpsy.2018.10.016 |
| 4 | `s2: readtimeout: httpsconnectionpool(host='europepmc.org', port=443): read timed out. (read timeout=30.0)` | 10.1016/j.neuropsychologia.2012.12.014, 10.1016/j.tics.2008.07.005, 10.1016/j.cogpsych.2013.07.001 |
| 3 | `openalex,s2: not pdf (text/html)` | 10.1016/j.tins.2006.04.001, 10.1006/cogp.1997.0659, 10.1016/s1364-6613(00)01839-8 |
| 3 | `openalex: http 500` | 10.1007/978-1-4614-5465-6_1, 10.1162/jocn.2007.19.5.761, 10.1016/j.neuron.2020.01.026 |
| 3 | `s2: http 202` | 10.1111/j.1469-8986.2006.00403.x, 10.1016/j.conb.2004.03.012, 10.1177/0956797619842191 |
| 3 | `unpaywall: not pdf (text/html)` | 10.1111/j.1749-6632.2012.06751.x, 10.7554/elife.11305 |
| 2 | `openalex,unpaywall: http 503` | 10.1016/j.jml.2009.06.002, 10.1038/nrn3776 |
| … | _17 more buckets_ | |

## By (tried, normalized reason) pattern

Finest cut.  Top rows are the design input for recovery passes.

| Count | Pattern | Sample DOIs |
|---:|---|---|
| 163 | `[] :: no candidate locations` | 10.1016/j.neuron.2015.09.004, 10.1016/s0896-6273(02)00897-8, 10.1016/s0896-6273(02)00817-6 |
| 157 | `[openalex] :: openalex: not pdf (text/html)` | 10.1007/bf00237911, 10.1007/978-0-230-36409-7_1, 10.1038/nrn894 |
| 103 | `[openalex] :: openalex: http 403` | 10.1037/13798-000, 10.1037/0022-3514.50.2.229, 10.1037/0022-3514.64.5.723 |
| 34 | `[openalex, openalex] :: openalex: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.tics.2006.10.012, 10.1038/nrn.2017.14, 10.1038/nrn2131 |
| 17 | `[openalex,unpaywall, s2, openalex] :: openalex,unpaywall: not pdf (text/html) | s2: http 500 | openalex: not pdf (text/html)` | 10.1016/j.neuron.2015.09.028, 10.1016/j.tins.2015.07.003, 10.1016/j.tics.2012.10.011 |
| 12 | `[openalex, openalex] :: openalex: not pdf (text/html) | openalex: http 403` | 10.1037/0033-295x.91.3.295, 10.1037/0033-2909.120.1.3, 10.1037/a0016923 |
| 11 | `[openalex, s2, openalex] :: openalex: not pdf (text/html) | s2: http 500 | openalex: not pdf (text/html)` | 10.1016/j.conb.2012.06.001, 10.1146/annurev-neuro-062111-150525, 10.1016/j.tics.2010.10.002 |
| 10 | `[openalex, openalex] :: openalex: sslerror | openalex: http 403` | 10.1126/science.1117645, 10.1177/0888439004269072, 10.1163/156856888x00122 |
| 8 | `[openalex, openalex, openalex] :: openalex: not pdf (text/html) | openalex: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.bandc.2009.08.007, 10.1016/s1364-6613(00)01482-0, 10.1017/s0140525x00058027 |
| 8 | `[openalex,unpaywall, s2, openalex] :: openalex,unpaywall: not pdf (text/html) | s2: http 500 | openalex: http 403` | 10.1111/jcpp.12675, 10.1162/jocn_a_00811, 10.1002/hipo.20808 |
| 7 | `[openalex,s2,unpaywall] :: openalex,s2,unpaywall: not pdf (text/html)` | 10.1016/0092-8674(91)90418-x, 10.1016/0896-6273(95)90304-6, 10.1006/brcg.1999.1096 |
| 7 | `[openalex,unpaywall, openalex] :: openalex,unpaywall: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.neuron.2012.01.010, 10.1016/j.neuron.2008.04.017, 10.1016/j.tics.2005.05.009 |
| 6 | `[openalex,s2,unpaywall] :: openalex,s2,unpaywall: http 403` | 10.1167/13.12.7, 10.1037/bul0000192, 10.1093/brain/awm011 |
| 5 | `[openalex, openalex, openalex] :: openalex: not pdf (text/html) | openalex: not pdf (text/html) | openalex: http 403` | 10.1080/1047840x.2010.487849, 10.1037/0096-1523.31.3.453, 10.1037/0033-2909.121.3.371 |
| 5 | `[openalex, openalex] :: openalex: http 404 | openalex: not pdf (text/html)` | 10.1038/nn827, 10.1038/nrn2497, 10.1007/s00221-011-2579-1 |
| 4 | `[openalex,unpaywall, openalex,s2,unpaywall, openalex,unpaywall, openalex] :: openalex,unpaywall: not pdf (text/html) | openalex,s2,unpaywall: http 403 | openalex,unpaywall: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.tics.2014.03.002, 10.1016/j.neuron.2016.03.037 |
| 4 | `[openalex,unpaywall, openalex,s2,unpaywall] :: openalex,unpaywall: not pdf (text/html) | openalex,s2,unpaywall: http 403` | 10.1111/cogs.12688, 10.1073/pnas.0706111104, 10.1093/sleep/34.5.581 |
| 4 | `[openalex,unpaywall, s2, openalex] :: openalex,unpaywall: not pdf (text/html) | s2: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1038/nn.3655, 10.1016/j.neuroimage.2008.05.046, 10.1038/nn2007 |
| 3 | `[openalex, openalex, openalex, openalex] :: openalex: not pdf (text/html) | openalex: not pdf (text/html) | openalex: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.neuropsychologia.2011.12.022, 10.1038/nature02043, 10.1016/j.concog.2012.04.014 |
| 3 | `[openalex, openalex, openalex] :: openalex: http 404 | openalex: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1038/nn1560, 10.1016/j.tics.2006.11.002 |
| 3 | `[openalex, openalex,s2,unpaywall, openalex] :: openalex: not pdf (text/html) | openalex,s2,unpaywall: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1038/npp.2009.131 |
| 3 | `[openalex, openalex] :: openalex: http 403 | openalex: not pdf (text/html)` | 10.1016/j.concog.2011.09.021, 10.1016/s0022-5371(69)80069-1, 10.1016/j.joep.2011.05.007 |
| 3 | `[openalex, s2, openalex, openalex] :: openalex: not pdf (text/html) | s2: http 500 | openalex: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1016/j.neuroimage.2013.11.001, 10.1016/j.cpr.2009.11.003, 10.1016/j.neuropsychologia.2013.07.020 |
| 3 | `[openalex, s2, openalex] :: openalex: not pdf (text/html) | s2: not pdf (text/html) | openalex: not pdf (text/html)` | 10.1038/nrn3158, 10.1038/nrn755 |
| 3 | `[openalex,unpaywall, openalex,s2,unpaywall, openalex] :: openalex,unpaywall: not pdf (text/html) | openalex,s2,unpaywall: http 403 | openalex: not pdf (text/html)` | 10.1111/nyas.13634, 10.1093/scan/nsn051, 10.1002/hbm.23854 |
| … | _162 more buckets_ | |
