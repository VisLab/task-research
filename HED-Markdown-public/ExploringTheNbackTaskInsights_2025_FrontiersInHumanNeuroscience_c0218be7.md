# Exploring the n-back task: insights, applications, and future directions

## Abstract

The n-back task has become a central paradigm for investigating the mechanisms of working memory (WM) and related executive functions. This review provides an integrative analysis of the n-back experiment, covering its cognitive operations, task variants, neuroimaging findings, and practical applications across multiple domains. We first delineate three core cognitive components—updating, maintenance, and attentional control—and summarize converging evidence that these functions rely on overlapping fronto-striatal and fronto-parietal networks. We then examine major task variants and review applications in: (1) cognitive training and transfer effects, particularly the proposed association between WM and fluid intelligence; (2) clinical contexts including attention deficit hyperactivity disorder (ADHD), depression, and neurological rehabilitation; (3) developmental and educational settings; and (4) emerging research on social cognition, stress, and emotional regulation. Critically, this review evaluates ongoing inconsistencies in how the n-back task is interpreted as a measure of WM and highlights methodological factors, such as task heterogeneity, multi-process interference, and mental fatigue, that complicate both behavioral and neural inferences. To address these issues, we outline methodological recommendations including adaptive task design, multimodal physiological monitoring, and standardized experimental protocols. We further discuss future directions involving virtual reality (VR), mobile platforms, and brain-computer interface (BCI) integration to improve ecological validity and translational relevance. By synthesizing behavioral and neural evidence, this review underscores the n-back task’s versatility while emphasizing the need for improved construct clarity and methodological rigor.

## Introduction

WM is essential for the temporary storage and manipulation of information that supports reasoning, learning, and decision-making. Among numerous paradigms used to study WM, the n-back task has become one of the most versatile and widely adopted approaches because it allows dynamic manipulation of cognitive load and continuous monitoring of neural activity. Originally introduced by, the paradigm requires participants to judge whether the current stimulus matches one presented n trials earlier, thereby engaging processes of updating, maintenance, and attentional control.

Many meta-analyses have examined the n-back paradigm from behavioral, neuroimaging, and training perspectives (Table 1), yet key methodological and interpretational inconsistencies remain unresolved. Existing reviews tend to focus on isolated aspects of the paradigm, whereas a unified synthesis integrating cognitive mechanisms, task variants, and multimodal neural evidence is still lacking. In addition, variability in task parameters, multi-process cognitive interference, and the often-overlooked impact of mental fatigue have contributed to inconsistent conclusions regarding what the n-back task measures and how its results should be interpreted. Clarifying these issues is essential for improving the validity, reliability, and practical utility of the n-back paradigm in both research and clinical applications.

**Table T1**: n-back experiment related meta-analysis.

| Theme | Number of papers and experiments | Analysis methods | Moderators tested | Effect size | Publication bias evidence | Conclusion |  | WM deficits in MDD with the n-back task | 31/34 | Random-effects meta-analysis (SMDs) based on Acc. and RT; bias diagnostics reported when available | Age, clinical status | SMDs for Acc. (-0.23 to -0.13) and RT (0.37∼0.64) at each load level | Trim-and-fill did not change effect; no evidence of publication bias. | Patients with depression exhibit a significant decrease in accuracy on tasks of higher complexity, such as 2-back and 3-back, especially when 2-back displays the maximum effect size. Among all task complexities (including 0-back), the reaction time of patients with depression was significantly prolonged, indicating the presence of widespread psychomotor retardation. |  | Neuroimage for various n-back tasks | 24/N.A. | ALE meta-analysis | N.A. | N.A. | N.A. | The core brain regions activated by the n-back task include the dlPFC (Brodmann 46/9 area), the vlPFC (Brodmann 45/47 area), parietal cortex (including medial and lateral parietal lobes), and SMA. Verbal stimulation activates the left ventrolateral prefrontal and posterior parietal lobes more, while the nonverbal stimuli activate more of the right dlPFC and parietal lobe. |  | Transfer effect of n-back training | 33/41 | Random-effects meta-analysis (Hedges’ g); subgroup and moderator analyses; bias diagnostics when available | Control group type (active vs. passive) | n-back: 0.62; WM: 0.24; Gf: 0.16 | PET-PEESE and funnel plot analyses show small far-transfer effect, but no strong publication bias after model correction | Explore the effects of age, training duration (dose), training type (single task vs. dual task), and task content (language vs. visual space) on transfer performance. Medium transfer effects to untrained versions of the trained n-back tasks and small transfer effects to other WM tasks, cognitive control, and Gf. |  | Aging and n-back performance | 58/74 | Random-effects meta-analysis (SMD) based on Acc. and RT | One level of n to the next in an n-back task, age effect at each level n | Younger: Acc.: 0.3∼0.57, RT: 0.09∼0.44 Older: Acc.: 0.33∼0.62, RT: 0.05∼0.64; Acc.: 0.28∼1.05, RT: 1.15∼1.4 | Egger’s test n.s.; Funnel plot symmetric. No publication bias detected | The decline in performance of elderly people on n-back tasks is mainly related to the difficulty of focus switching, rather than overall WM load. Self-pacing allows older adults to optimize their pace and thus will enable them to compensate for age-related slowing. |  | Complex span and n-back measures of WM | N.A. | Correlation analysis | Complex and simple span | r = 0.16∼0.31 | No publication bias analysis reported; variability attributed to construct differences, not reporting bias | The complex span and n-back tasks cannot be used interchangeably as WM measures in research applications. |  | N-back WM Task for children with fMRI | 17/29 | ALE meta-analysis of functional activation patterns | N.A. | N.A. | N.A. | Compared to adults, children’s consistent brain activation pattern during n-back WM tasks shows that children rely more on the posterior cortex and less on prefrontal activation. Significant concordance is observed in the insula and cerebellum for children. |  | The n-back task while driving | 20/N.A. | Meta-analysis using correlation coefficients (r) with moderator analysis | Experimental environment, simulator fidelity, age, etc. | total effect size r = 0.46 | Fail-safe N = 1,141 feffect robust, unlikely to be driven by bias | An increase in n-back levels significantly enhances cognitive load, supporting the applicability of n-back tasks as a cognitive load measurement tool in driving research. |  | Coordinate-based meta-analysis of the n-back WM paradigm | 96/120 | ALE meta-analysis. | Age, sex, stimulus, task load, etc. | N.A. | N.A. | This work confirmed the centrality of the frontoparietal network in n-back tasks and identified key differences in activation patterns based on task conditions and participant characteristics. |  | fMRI evidence of age-related changes in prefrontal cortex involvement across the adult lifespan | 82/N.A. | ALE meta-analysis with contrast analyses and effect-size seed-based meta-regression | Age | N.A. | N.A. | All age groups showed consistent activation in the parietal cortex and cingulate gyrus, indicating that these regions are key WM areas for n-back tasks. The insula and cerebellum also exhibit consistent activation. Prefrontal cortex engagement is concordant for young, to a lesser degree for middle-aged adults, and absent in older adults, suggesting a gradual linear decline in concordance of prefrontal cortex engagement. |  | Network dysfunction across psychopathologies | N.A./160 | ALE meta-analysis with contrast analyses | Task load; stimulus type | N.A. | N.A. | The psychopathologies exhibit consistent hyperactivation in the left anterior cingulate cortex/medial prefrontal cortex which is the hub region of the DMN. Abnormal activation of DMN can interfere with task-related cognitive processing, leading to a decline in WM performance. |  | N-back training improves Gf | 20/N.A. | Random-effects meta-analysis (Hedges’ g) with subgroup and regression analyses; bias diagnostics when available. | n-back types, environment, etc. | Overall g = 0.24 | Funnel plot asymmetry; far-transfer decreases to ∼0 when using active controls. → evidence of publication bias and control-design sensitivity | Through n-back training, Gf can be significantly improved, but the effect is small and is moderated by experimental design and participant characteristics. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

*MDD, Major depressive disorder; SMDs, Standardized mean differences; Acc., accuracy; RT, reaction time; dlPFC, dorsal lateral prefrontal cortex; vlPFC, ventrolateral prefrontal cortex; ALE, activation likelihood estimation; DMN, default mode network; SMA, supplementary movement area; Gf, fluid intelligence; bias diagnostics: Egger’s regression and Funnel plot.*

Although numerous meta-analyses and reviews have examined the n-back paradigm from behavioral, neuroimaging, and training perspectives, their conclusions remain inconsistent, largely due to methodological heterogeneity. For example, studies differ in whether they treat the n-back as a measure of updating, storage capacity, or attentional control, and task implementations vary in stimulus modality, adaptive difficulty procedures, and baseline contrasts. These discrepancies contribute to well-known concerns regarding the test-retest reliability of n-back performance, the validity of training effects, and its uncertain relationship to complex span tasks, which are considered the gold standard of working memory assessment. Moreover, studies on neural mechanisms have reported both overlapping and divergent activation patterns across fronto-parietal and striatal networks, which reflects unresolved debates about whether the n-back captures a unitary executive function or a composite of multiple cognitive processes. These unresolved controversies highlight a critical need for an integrated framework that not only synthesizes cognitive and neural findings across task variants but also evaluates the methodological assumptions underlying the interpretation of n-back performance. To address this gap, the present review provides a structured comparison of cognitive mechanisms, modality-specific neural recruitment, task variants, and application domains, which aims to clarify under what conditions the n-back task serves as a valid index of working memory and executive control.

Relevant studies were identified through searches in Google Scholar and PubMed using combinations of the following keywords: “n-back,” “working memory,” “updating,” “maintenance,” “attentional control,” “fMRI,” “EEG,” “training,” and “cognitive load.” Searches focused on peer-reviewed articles and meta-analyses, with no strict publication year restrictions to ensure comprehensive coverage. Additional references were identified through citation tracking of key review papers. Literature selection was guided by the thematic structure of the present review.

## The n-back task: cognitive mechanisms and variants

### Core mechanism

The n-back task primarily engages three interrelated cognitive mechanisms: updating, maintenance, and attentional control. Updating refers to the replacement of outdated information with newly relevant input. Maintenance involves the sustained activation of task-relevant representations across short time intervals. Attentional control regulates the selection of relevant items while suppressing interference from irrelevant ones. Although conceptually separable, these three components operate in parallel during n-back performance, with their relative contributions varying systematically depending on task load and stimulus characteristics. This functional interplay provides the foundation for understanding how different variants of the n-back task differentially tax executive control and neural resources.

#### Updating

The defining feature of the n-back task is the continuous updating of information in working memory (WM). On each trial, participants must integrate a new stimulus while discarding the no-longer-relevant item, requiring flexible adjustment of the content and temporal order of stored representations. This dynamic updating process differentiates the n-back from static storage tasks, such as the digit span test, which emphasize capacity rather than manipulation.

Neuroimaging evidence indicates that both the dlPFC and the striatum play central roles in this updating process. Activation in the dlPFC is closely related to task load, typically showing an inverted U-shaped pattern: activity increases as WM demand rises but declines once capacity is exceeded. Such modulation reflects the dlPFC’s function in maintaining optimal cognitive control and updating efficiency. Consistent with these findings, our exploratory image-based meta-analysis (IBMA) using unthresholded WM maps from NeuroVault also showed robust load-dependent convergence in the bilateral dlPFC and inferior parietal lobule (IPL), aligning with the core neural architecture supporting n-back updating (see Supplementary Figures 1, 2). In contrast, striatal activation tends to increase with the need for updating, reflecting its contribution to the gating and replacement of information in WM. Reduced dlPFC and IPL activation following training is often interpreted as improved neural efficiency, whereas increased striatal engagement indicates enhanced updating performance. Together, these patterns suggest that efficient n-back performance depends on a dynamic interplay between fronto-striatal circuits, where the dlPFC regulates task-load-related control demands and the striatum supports the flexible updating of memory contents.

#### Maintenance

Despite its emphasis on updating, the n-back task also involves a strong maintenance component. Participants must actively retain several recent items and their temporal sequence to perform comparisons accurately. Neuroimaging studies have shown that this maintenance process depends on sustained activation within the dlPFC and parietal regions, particularly the IPL and precuneus, which together support the short-term retention and manipulation of information in WM.

In particular, the dlPFC is thought to maintain task-relevant representations over time, enabling the comparison between current and prior stimuli, whereas the parietal cortex contributes to the temporal ordering and attentional focus necessary for accurate retrieval. Some studies also implicate the supplementary motor area (SMA) and posterior superior frontal sulcus (SFS) in sustaining sequential information, especially in visuospatial n-back paradigms.

Importantly, maintenance in the n-back task is not a passive storage process but an active one, requiring rehearsal, temporal tagging, and binding mechanisms to preserve the ordered structure of recent stimuli. The strength and stability of prefrontal-parietal coupling largely determine the upper limit of task performance as n increases, which reflects the neural capacity constraints of WM.

#### Attentional control and selection

A third critical process is attentional control, which governs the selection of task-relevant information and the inhibition of irrelevant or interfering stimuli. Given the constant stream of incoming items, successful performance requires the ability to focus attention on the current trial while suppressing proactive interference from earlier ones. The parietal cortex and anterior cingulate cortex (ACC) are often implicated in this control process. The parietal cortex plays a critical role in attention allocation and spatial memory, showing robust load-dependent activation during n-back tasks. The ACC is involved in error detection and stimulus monitoring, particularly in high-load or complex tasks. Post-training reductions in ACC activation, alongside changes in other cerebral regions, suggest enhanced task efficiency. Notably, individual differences in attentional control, rather than memory span per se, have been shown to explain a substantial portion of performance variability in the n-back task.

Although updating, maintenance, and attentional control are often discussed as distinct components of WM, neuroimaging evidence suggests that they rely on highly overlapping neural substrates. Across n-back studies, consistent activation has been observed within a fronto-parietal network, including the dlPFC, IPL, ACC, and striatum. These regions jointly support the continuous monitoring, manipulation, and selection of information required by the task. The dlPFC serves as the central hub coordinating executive control and maintaining task goals, the IPL and precuneus contribute to short-term storage and spatial-temporal organization, the striatum facilitates flexible updating through gating mechanisms, and the ACC monitors conflicts and errors to adjust control demands.

### n-back task variants

This convergence indicates that n-back performance does not reflect a single cognitive operation but rather an integrated interaction among fronto-striatal and fronto-parietal circuits. Different n-back variants can be understood as shifting the relative weighting of these three components (Figure 1). For example, increasing the value of n primarily elevates demands on updating, whereas stimulus similarity and proactive interference increase demands on attentional control. In contrast, visuospatial n-back tasks place proportionally greater demands on maintenance and parietal-mediated spatial rehearsal. Therefore, behavioral and neural outcomes across task versions can be predicted based on which component is most heavily weighted by the specific task configuration.

![F1](ExploringTheNbackTaskInsights_2025_FrontiersInHumanNeuroscience_c0218be7.assets/fnhum-19-1721330-g001.jpg)

**Figure F1**: Different types of n-back tasks.

#### Visual n-back task

The visual n-back task assesses visual working memory by requiring participants to monitor and update stimulus sequences presented in the visual modality. Common stimulus sets, such as letters, numbers, spatial markers, or objects, are typically grouped into verbal, spatial, and object-based categories. The choice of stimulus type is not incidental but determines the representational format and cognitive control demands of the task.

Different neural circuits are engaged depending on whether the stimuli are verbal or non-verbal. For verbal stimuli, WM involves a network that includes the ventrolateral prefrontal cortex (vlPFC), thalamus, bilateral premotor cortex, and posterior parietal cortex. In contrast, WM for non-verbal visual stimuli primarily engages the right dorsolateral prefrontal cortex (dlPFC), right medial posterior parietal cortex, and the dorsal cingulate/medial premotor cortex.

Behavioral and electrophysiological studies have shown that these stimulus categories differ in susceptibility to interference, response strategies, and neural activation patterns. Therefore, the visual n-back design must align stimulus selection with the specific cognitive mechanism under investigation, as varying stimulus types effectively shift the underlying neural computation supporting task performance.

#### Auditory n-back task

The auditory n-back task presents sequences of spoken letters, tones, or sounds and requires updating based on auditory representations. Although stimulus modality differs, responses are typically recorded via button press rather than vocal judgments to ensure consistency in behavioral measurement. Relative to visual n-back tasks, auditory n-back performance is generally more accurate but slower, which reflects more stable but less rapidly accessible memory traces in the auditory domain. In addition, there is controversy between the brain regions that support auditory n-back tasks and those that support visual n-back tasks (Figure 2; Table 2), even though both are used to study WM.

![F2](ExploringTheNbackTaskInsights_2025_FrontiersInHumanNeuroscience_c0218be7.assets/fnhum-19-1721330-g002.jpg)

**Figure F2**: Brain activation with different stimulus modalities. We used Montreal Neurological Institute (MNI) coordinates with BrainNet Viewer. The BrainMesh_Ch2withCerebellum surface was adopted. The location of the nodes is derived from the peak coordinates of and unified normalization is carried out for the size of the nodes. We plot the brain activation regions of the visual stimulus only and the auditory stimulus only in the same template (visual: purple and auditory: yellow). Then the common activation and the activation with differences for the two modalities are drawn in three templates (common: orange, auditory > visual: blue and visual > auditory: green colors). Finally, we plot brain activations for both auditory stimuli and visual stimuli, respectively.

**Table T2**: Various types of n-back experiments with neuroimage methods.

| Type | Stimuli | V. or NonV. | Load factor | Research field | Method | References | Cortical areas for related n-back task |  | Vis. | Number | V. | 1–3 | Sensitivity of ERP to WM load. | EEG |  | Fz, F3, F4, Pz, P3, P4, Cz, C3, C4 |  | Letter | V. | 0–2 | The function connectivity patterns of human cerebro-cerebellar circuits and their associations with verbal WM performance. | fMRI |  | Bilateral cerebellum lobule VI, right PPC, right cuneus, right ACC, bilateral SFG |  | Letter (vis. and aud.) | V. | 2 | Compare the pattern of brain activation while performing auditory and visual n-back tasks. | fMRI |  | Bilateral frontoparietal (e.g., dlPFC), superior temporal gyrus, the ACC and occipital areas |  | Spatial object | NonV. | 1–4 | Aging, task difficulty, and training effects on WM. | EEG |  | CP1, inferior parietal lobe (IPL) |  | Letter | V. | 0–2 | Neural oscillatory processes in simple WM task | MEG |  | DMN, cingulate cortex, bilateral frontal operculum, IPLs, left and right parietal lobes, left temporal lobe, left-lateralized Wernicke’s area |  | Spatial object | NonV. | 2 | TMS treatment enhanced WM performance in a verbal digit span and a visuospatial 2-back task. | TMS |  | dlPFC |  | Words, pictures, and color | Both | 1–3 | Multi-factors like stimulus type, task structure, preprocessing method, and lab factors influence the ERP of n-back results. | EEG |  | Fz, Cz, Pz |  | Number | V. | 0–4 | Identify characteristics of WM capacity with fMRI. | fMRI |  | dlPFC, the premotor cortex, thalamus, pericingulate and superior parietal lobule |  | Digits | V. | 0–2 | Driver workload estimation | EEG |  | Frontal and parietal EEG spectrum |  | Number | V. | 0–3 | auditory steady-state response and cognitive workload. | MEG |  | The auditory cortex, the frontal, parietal, and occipital cortices |  | Number | V. | 0–4 | Influence of WM load to driving performance. | fNIRS |  | bilateral inferior frontal areas and the bilateral temporo-occipital areas |  | Aud. | Letter | V. | 3 | Verbal WM is modality-independent and is mediated by a circuit involving frontal, parietal, and cerebellar mechanisms. | PET |  | Dorsolateral frontal, Broca’s area, SMA, and premotor cortex in the left hemisphere; bilateral superior and posterior parietal cortices and anterior cingulate; and right cerebellum |  | Number | V. | 2 | Modality effects on verbal WM with the comparison of prefrontal and parietal responses to auditory and visual stimuli. | fMRI |  | The dlPFC, premotor and ventrolateral prefrontal cortex, intraparietal sulcus, supramarginal gyrus and the basal ganglia, the left posterior parietal cortex, the superior and middle temporal cortex and the occipital cortex |  | Dual | Chinese character and spatial | Both | 0, 2 | Brain activation of Schizophrenia patients under dual n-back tasks | fMRI |  | The right middle frontal gyrus and the posterior parietal regions, the right hippocampus, superior parietal lobule, IPL |  | Letter and shape | Both | 0–3 | Studies on load-dependent processing in single and dual tasks in the prefrontal cortex. | fMRI |  | The prefrontal cortex, the precentral gyrus and the superior parietal lobule, the dlPFC |  | Faces and words | Both | Ad. | Systematic WM training has the potential to augment affective cognitive control. | fMRI |  | The inferior parietal cortex, middle frontal gyrus, middle OFC, sgACC, dlPFC, IPC, hippocampus/amygdala and insula |  | Letter and spatial position | Both | 0, 2 | Understand the cognitive and neural effects of WM training and transfer. | fMRI |  | Bilaterally in the striatum, the bilateral cuneus, the bilateral occipital cortex, the frontoparietal cortices (the bilateral premotor cortex, the bilateral PFC, and the right IPL), the right ACC, the left posterior cingulate cortex, the superior temporal lobe, the bilateral thalamus, the right middle frontal gyrus and in the left IPL |  | Letter and spatial position | Both | Ad. | Dual n-back training improves functional connectivity of the right inferior frontal gyrus at rest. | fMRI |  | The right inferior frontal gyrus, prefrontal cortex, the left superior parietal cortex |  | Letter and spatial position | Both | Ad. | Dual n-back training produces increased integrity in white matter pathways connecting different brain regions. | MRI |  | The corticospinal tract, temporal/parietal lobes, the frontal lobe, the occipital and temporal lobes, the occipital and frontal lobes, the left and the right frontal lobes, the genuofcorpus callosum |  | Letter and spatial position | Both | 2 | Personality traits change the impact of emotional stimuli. | Offline fNIRS |  | dlPFC |  | Em. | Words | V. | 2 | Investigate the behavioral effects and neuronal correlates of emotional content and emotional components in verbal WM tasks. | fMRI |  | Lateral prefrontal regions, cortical mid-line regions, dorsolateral prefrontal, the bilateral dlPFC, dACC, medial cortical regions such as the vmPFC/pACC, dmPFC, PCC, medial temporal gyrus and also in the rostral ACC and orbitofrontal cortex |  | Words | V. | 1 | Examine the effect of stress induction on n-back performance among female students for emotional and non-emotional stimuli. | N.A. |  | Auditory cortex, hippocampus, and frontal area |  | Words | V. | 1–3 | The influence of valence on a verbal WM task. | fNIRS |  | The prefrontal cortex |  | Pictures | NonV. | 1, 2 | Investigate interactions between WM load and affective valence with EEG. | EEG |  | Frontal and parietal area |  | Face | NonV. | Ad. | ERP component P3 is highly sensitive to the influence of emotion on WM with 3-back experiments. | EEG |  | The whole brain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

*Vis., Visual; Aud., Auditory; Em., Emotional; Ad., Adaptive; V. or NonV., Verbal or Nonverbal; PCC, posterior cingulate cortex; ACC, anterior cingulate cortex; pACC, pregenual anterior cingulate; dACC, dorsal anterior cingulate cortex; sgACC, subgenual anterior cingulate; IPC, inferior parietal cortex; vmPFC, ventromedial prefrontal cortex; dmPFC, dorsomedial prefrontal cortex; SFG, superior frontal gyrus; dlPFC, dorsolateral prefrontal cortex; DMN, default mode network; including the medial frontal cortex, medial parietal cortex, and posterior parietal lobules; SMA, supplementary motor area; OFC, orbitofrontal cortex. An adaptive (Ad.) n-back task is a dynamic variant of the n-back paradigm in which the memory load n automatically increases or decreases based on the participant’s ongoing performance. Instead of using a fixed load level (e.g., 1-back or 2-back), the task adjusts n after each block to maintain performance near an individualized difficulty threshold. Typically, n increases when accuracy is high and decreases when performance falls below a preset criterion, ensuring that the participant is consistently challenged at the upper edge of their working memory capacity.*

Importantly, the auditory n-back task is particularly suitable as a secondary workload probe because it does not interfere with ongoing visual processing and can be embedded in visually guided primary tasks to index mental workload. Accordingly, auditory n-back is frequently used in driving and human-machine interaction research to assess cognitive load under real-time perceptual demands.

#### Dual n-back task

The dual n-back task simultaneously presents visual and auditory stimuli, requiring participants to monitor both modalities and update WM representations in parallel. This paradigm increases cognitive load and highlights the modality-specific nature of WM, as the neural demands of dual-task performance reflect integrated fronto-parietal and striatal engagement rather than a simple sum of single-modality n-back activations. Because of its higher task demands, dual n-back performance has been shown to correlate with broader cognitive abilities, including individual differences in Gf and attentional control. The paradigm has therefore been widely used in cognitive training research. However, evidence increasingly suggests that improvements from dual n-back practice largely reflect task-specific updating efficiency, with transfer primarily observed in closely related WM tasks rather than in generalized cognitive domains.

#### Modality-specific effect

The comparison between the visual and auditory all brain activation maps (Figure 2) demonstrates that sensory modality determines the entry point of information processing in n-back tasks, while higher-level WM operations are supported by a shared supramodal control network.

Specifically, visual n-back tasks reliably activate regions in the occipital cortex and dorsal parietal areas (e.g., intraparietal sulcus, superior and IPLs), reflecting reliance on visuospatial attention and visual feature updating. In contrast, auditory n-back tasks prominently recruit the superior temporal gyrus and auditory cortex, as well as inferior frontal language-related regions, consistent with phonological encoding and auditory-verbal rehearsal.

Despite these modality-dependent sensory pathways, the two tasks converge on a common fronto-parietal WM control network, including bilateral dlPFC and parietal cortex, which supports maintenance, updating, and cognitive control independent of stimulus format. This overlapping supramodal network reflects the central executive component of WM.

Furthermore, dual-modality n-back tasks require simultaneous coordination across both sensory systems, which is evident in bilateral activation expansions and engagement of additional integrative hubs, such as the temporal-parietal lobe. This network-level integration requirement suggests that dual n-back tasks impose greater executive control and cross-modal binding demands, and thus contribute to transfer effects observed in some training studies. In summary, modality determines where information enters the system (visual vs. auditory cortex), but the core working memory computations rely on a shared, supramodal fronto-parietal control network. Dual-modality conditions extend this system by imposing cross-sensory integration demands, recruiting broader and more coordinated large-scale brain networks.

#### Emotional n-back task

The emotional n-back task embeds emotional valence stimuli (e.g., facial expressions or affective words) into the standard n-back paradigm to examine how affective states interact with WM. Because emotional regulation and WM share overlapping neural substrates, particularly the dlPFC, inferior parietal cortex (IPC), and anterior cingulate cortex (ACC), emotional distraction can compete with WM for cognitive resources.

Neuroimaging results show that emotional valence modulates dlPFC activation during WM updating, with increased recruitment under positive or high-arousal states and reduced activation under negative states. Emotional n-back tasks also engage affective control regions such as the subgenus anterior cingulate (sgACC), orbitofrontal cortex, amygdala, and insula, where higher WM load tends to increase frontoparietal activity while suppressing limbic responses.

Training with emotional n-back paradigms can strengthen affective cognitive control, with evidence showing increased sgACC activation and improved emotion regulation after training. Electrophysiological findings further support this interaction: negative valence decreases accuracy and slows responses, alongside reductions in theta and alpha power and alterations in P3 amplitude, reflecting increased conflict and attentional control demands.

#### Long-term n-back task

Long-term n-back tasks extend training across multiple sessions (typically ≥ 4 days and often ≥ 2 weeks) to examine sustained neurocognitive changes, whereas short-term n-back tasks mainly assess momentary WM performance. These long-term protocols have been applied to memory improvement, transfer effect, aging, exploration of brain activity, cognition or intelligence, affective control and rehabilitation.

However, long-term training outcomes show substantial individual variability, influenced by factors such as age, baseline cognitive ability, and motivation. This suggests that long-term n-back training protocols may require adaptive or personalized implementation to optimize benefits. Additionally, because most training is conducted under controlled laboratory conditions, the ecological validity of the improvements is limited. Gamified or context-embedded designs may help better align long-term n-back training with real-world cognitive demands, particularly in children.

### The association between n-back tasks and other paradigms

Beyond these variants, the n-back paradigm can be better understood when viewed in relation to other working memory tasks. Comparing it with classic paradigms such as the delayed-match-to-sample (DMTS), sequential recall, and Sternberg memory tasks helps clarify which cognitive components are unique to n-back (e.g., continuous updating) and which are shared across broader memory systems.

#### DMTS

The DMTS and n-back tasks are both cognitive tasks used to assess memory. In addition to commonly used stimuli such as numbers, letters, faces, etc., it also has richer stimuli such as polygons, dots, abstract design, object location, and ball tracking. The difficulty adjustment of DMTS mainly relies on the length of delay time, whereas the variant of DMTS can increase task difficulty by sequentially increasing the number of stimuli while asking participants if the test stimuli are present in the presented stimuli, or by increasing the background of the stimuli. The delay time depends on the research content. For example, when learning novel and well-learned recognition tasks like word memory, which are relatively familiar stimuli, the delay time may be as long as 60 s. The research focuses on DMTS, and n-back tasks are different. The DMTS task primarily measures short-term memory and recognition, which assesses the ability to maintain and retrieve information over a short delay. In contrast, the n-back task measures WM updating and monitoring, requiring participants to constantly update their WM with new information and monitor for matches, making it a more dynamic task than DMTS. This experimental process results in different emphases of cognitive load for the subjects. The participants in the n-back experiment focus on attention allocation, that is, they need to be highly focused to avoid being distracted by other interfering information, while the participants in DMTS pay more attention to information integration, that is, they pay more attention to the capacity and retrieval ability of WM. Although DMTS and n-back tasks are both WM paradigms, DMTS shows some neural divergence compared to that in n-back tasks. As mentioned in the meta-analysis of DMTS in WM, DMTS does not require constant source monitoring like an n-back task does, and there is a distributed DMTS neurofunctional network consisting of 16 clusters of consistent activation. The neurofunctional network of DMTS for verbal and nonverbal stimuli is quite different. For instance, the fusiform gyrus was active only in the right hemisphere in DMTS with only nonverbal stimuli, but no activation was found in n-back tasks. Furthermore, nonverbal stimulus creates much more brain activation in clusters located in the frontal, occipital, parietal, and limbic lobes of both hemispheres. These findings manifest that those spatial and phonological stimuli are maintained in different regions, and nonverbal stimulus sets recruit clusters from wider brain regions.

#### Sequential recall task

In SR tasks, participants need to remember the order (positive or negative) of a series of objects or stimuli and recall their order or specific location after a delay. Similar to n-back tasks, SR tasks also need to remember the sequence of the stimuli, and the participants need to reorganize information in the short term for reverse order tasks. Such experimental stimuli are not limited to numbers. For example, the Corsi blocks tests, which are mainly used for measuring spatial WM spans. Wechsler Memory Scale III spatial span board features 10 irregularly spaced blue cubes set up on a white rectangular board, with each cube featuring an identifying number on only the researcher’s side. The researchers will touch these numbered cubes with their fingers in a predetermined order, and the participants need to recall and touch the cubes in the same order after seeing these actions. To increase WM demand by requiring the use of rehearsal, the task incorporated a 10 s delay period (retention interval) between presentation and recall. Like the n-back task, this type of task is often used to compare the impact of age on WM and focuses more on detailed behavioral performance, such as age predicting backward recall performance for both young and older adults. However, the difference lies in the online updating for the n-back task with the increase in load factor, whereas SR tasks are of static memory load, which adjusts the difficulty by changing the length of the stimuli and adding the forward and backward recall for the response. Through neuroimaging, it was found that the activation areas of the n-back task are mainly the prefrontal cortex (especially the dorsolateral prefrontal cortex) and parietal lobe, while the activation areas of the SR task are different, such as the hippocampus, pre-supplementary motor area, prefrontal cortex, and parietal lobe, middle temporal gyrus, and bilateral rostral anterior cingulate and inferior frontal gyri. The meta-analysis also validates that the bilateral SFS and the DLPFC showed the greatest specialization among frontal regions for continuous updating and temporal order memory, whereas spatial storage tasks most frequently activated the superior parietal cortex, and object storage most frequently activated the inferior temporal cortex. Since the SR task and DMTS task paradigms focus on memory and recognition, respectively, neuropsychological tests for evaluating speech learning and memory abilities have emerged, such as the California Verbal Learning Test- second edition (CVLT-II), Rey Auditory Verbal Learning Test (RAVLT), or the Wechsler Memory Scale (WMS). These tests involve various experimental processes, such as various recalls and recognition tasks, and are often applied to the study of individual differences in cognitive tasks, such as the impact of age, gender, intelligence, etc., on task performance. In contrast, the n-back task cannot be used for measuring individual differences due to its low reliability. Furthermore, the validity analysis for DMTS and SR tasks is less extensive than that for the n-back task.

#### Sternberg memory task

The Sternberg memory task is a classic static WM task that contains three phases (encoding, retention, and testing). Participants are shown a set of grouped items (usually letters or numbers) that they must memorize in the encoding phase. The difficulty of the task depends on the size of the set of grouped items. Then, participants need to maintain the memorized items with WM during the delay period, with the disappearance of items in the retention phase. Finally, a probe item is shown on the screen, and participants are asked to decide whether the probe was part of the previously displayed set in the testing phase. Compared with the n-back task, the Sternberg memory task presents stimuli differently. It presents multiple stimuli simultaneously, and subjects do not need to perform cross-trial memory, resulting in a static memory load and lower experimental difficulty. Because they are both WM tasks, their brain regions also have similar performance. For example, used magnetoencephalography to study the oscillations of various brain regions in different frequency bands under two WM conditions (n-back and Sternberg memory task). The frontal midline theta oscillation is closely related to WM, and there is evidence to suggest that the intensity of frontal midline theta oscillation is directly proportional to the difficulty of WM tasks. As the difficulty of the task increased, under the n-back experimental conditions, theta power showed more significant changes in the medial frontal cortex, indicating that the n-back experiment was more challenging. Although the n-back task and Sternberg memory task both belong to the category of WM, the brain regions recruited by the two in the experiment were not completely the same. In the Sternberg memory task, β/γ power decreases were associated with the language area (insular cortex). The delay period of the Sternberg memory task led to significant changes in the left premotor regions and Broca’s areas, which is similar to that of β/γ power decrease. There is no difference in fMRI results between euthymic bipolar disorder patients and control groups at any WM load. In contrast, in the two-back task, bipolar disorder patients showed reductions in bilateral frontal, temporal, and parietal activation, and increased activations with the left precentral, right medial frontal, and left supramarginal gyri compared to control groups. Furthermore, researchers also investigated whether different areas of the cerebellar cortex and nuclei contribute to these two tasks (n-back and Sternberg memory task). It was shown that similar regions in the cerebellar cortex and dentate nuclei are involved in abstract and verbal n-back tasks, whereas cerebellar cortical activation was significantly stronger in the verbal version of the Sternberg memory task than in an abstract one. These findings manifest that different parts of the cerebellum seem to contribute to different aspects of WM, and right lobule VI may be more involved in verbal WM tasks.

#### Stroop task

In the Stroop task, participants are presented with color words like red, yellow, or blue printed in different colored inks and are asked to name the color of the ink, rather than reading the word itself. The Stroop task measures the delay in response time when naming the ink color in the incongruent condition. The delay occurs because reading is more automatic than color naming, making it challenging for the brain to suppress the impulse to read the word. Compared with the n-back task, this task evaluates cognitive control, selective attention, and response inhibition rather than WM. However, WM capacity influences the performance of the Stroop task. Subjects with higher WM capacity experience less color word interference than those with lower WM capacity. Moreover, even when lower-WM capacity subjects can respond according to goals, they take more time to resolve the interference created by each incongruent stimulus. In general, the Stroop task highlights attentional inhibition and conflict resolution, while the n-back task focuses more on WM updating and maintenance. The WM Stroop task, a variant of the Stroop task, increases the cognitive load by incorporating a WM component. For example, this task can be to name the color of a rectangular patch with a keypress while holding a color word in WM. The color patch could be congruent or incongruent with the color word being held in WM. WM, as an internally directed attention, its memory content can also affect subsequent behavior. The WM Stroop paradigm mainly distinguishes whether holding a color word in WM can produce interference in a color-discrimination task in the same manner as a color word that is perceived in the external environment. The WM Stroop paradigm is more inclined to study the guiding role of WM, while the n-back experiment focuses more on what influences WM, how to improve WM, and the relationship between WM and other cognitive abilities such as Gf. Interestingly, the Stroop task can be combined with the n-back task. Although the Stroop-n-back paradigm allows the simultaneous manipulation of interference inhibition and working memory updating, the cognitive processes involved are highly intertwined. The task imposes concurrent demands on response inhibition, attentional control, and set maintenance, making it difficult to isolate the neural mechanisms specific to working memory. For this reason, such combined paradigms are most used in clinical or diagnostic contexts, where the objective is to maximize sensitivity to cognitive impairment, rather than to characterize the core computational or neural mechanisms of working memory itself.

#### Go/no-go task

WM and response control are closely connected and integrated executive function systems. In the go/no-go task, participants are tested to perform an action on go stimuli and to inhibit their action for nogo stimuli. Thus, such a paradigm is used for investigating individual inhibition responses. The WM capacity also influences the inhibitory ability of an individual, as such inhibition response is related to selectively updating, maintaining, and retrieving information. For go/no-go tasks, the difficulty is typically adjusted by changing the ratio of go to no-go stimuli (e.g., increasing the frequency of go stimuli to make no-go stimuli less common, which makes inhibitory control more challenging). This task focuses primarily on inhibitory control with relatively low WM demands and thus, this experimental paradigm is more suitable for fine animal experiments, such as studying the changes in cognitive behavior driven by neuronal activity in specific brain regions. For example, through the go/no-go paradigm with different sounds and reinforcements, researchers observed how the primary auditory cortex transforms stimulus encoding from sensory representations to behavior-driven representations during task engagement, thereby specifically enhancing target stimuli across all paradigms. The go/no-go task is suitable for measuring attentional processing as it requires continuous attention to detect the go stimuli, and inhibition to withhold the response for the nogo stimuli. Therefore, the go/nogo paradigm is widely used in the study of ADHD, in which the underlying dysfunction is based on the frontal-basal-ganglia-thalamo-cortical networks of the brain. Still, some researchers have used the n-back paradigm to study and train ADHD patients. In addition, some researchers have combined these two paradigms by inserting nogo stimuli into the n-back paradigm, which requires subjects’ WM to continuously update and intermittently respond to inhibition. This experimental paradigm, combined with ERP recording, is an economic assessment of WM and inhibition response.

### Neuroimage for n-back tasks

Recent advancements in neuroimaging techniques have enhanced the use of n-back tasks, particularly due to the ability to manipulate WM load and systematically observe gradations in neural activity as cognitive demands increase. Key neuroimaging modalities that have been employed in conjunction with n-back tasks include fMRI, EEG, MEG, PET, and functional near-infrared spectroscopy (fNIRS). Table 2 provides a summary of n-back experiments utilizing different stimuli and neuroimaging methods.

EEG-based analyses of n-back tasks can be approached from both the time-domain (event-related potentials, ERPs) and frequency-domain perspectives (theta, alpha, beta, and gamma bands). Figure 3 highlights typical EEG changes during the n-back process under varying stimuli and cognitive loads. EEG signals, with their high temporal resolution, are particularly effective in capturing rapid changes in cognitive load, such as transitions from 1-back to 3-back. In addition, EEG is a valuable electrophysiological marker of cognitive workload. For example, a decrease in alpha-band power in the parieto-occipital region indicates increased cognitive load, while an increase in theta-band power in the prefrontal cortex reflects heightened attentional demands (; Figure 3). Thus, EEG can serve as an effective tool for detecting cognitive workload in n-back tasks.

![F3](ExploringTheNbackTaskInsights_2025_FrontiersInHumanNeuroscience_c0218be7.assets/fnhum-19-1721330-g003.jpg)

**Figure F3**: Representative EEG changes for different n-back tasks. (A,C–F) Different independent variables lead to brain regional changes of time domain and frequency domain features like N1, P3, and theta power, etc. The correspondence between the subfigure and literature is (A) for, (C) for, (D) for, (E) for, (F) for. (B) The inferior parietal lobe where applying transcranial alternating current stimulation (tACS) can improve verbal WM. The CP1 region is not only the stimulation area of transcranial alternating current but also the prominent point of betweenness centrality in the process of brain network construction in spatial n-back experiments.

Furthermore, ERPs, due to their component specificity and sensitivity to task parameters, provide insights into task-related cognitive processes. Components such as P2, N2, P3, and negative slow wave (NSW) are commonly studied to understand various cognitive functions involved in the n-back paradigm. For instance, P2 is associated with early sensory processing, N2 with inhibitory control, and P3 with cognitive updating. Notably, P3 is influenced by both the trial type (target vs non-target) and input valence, with the amplitude of P3 significantly increasing in the posterior regions.

Finally, EEG can bridge the gap between behavioral and electrophysiological measures, as changes in ERP components often correlate with task performance. For example, poorer performance on higher-load n-back trials is typically reflected in altered ERP patterns.

The majority of experimental analyses in n-back tasks come from fMRI, primarily due to its high spatial resolution, which allows precise localization of brain activation patterns. This capability is critical for studying the distributed networks involved in WM tasks. For example, different modalities of stimulus boost different brain regional activation, whereas the emotional dual n-back task promotes the increase or decrease of activation in different sites. Due to differences in activation of visual n-back and auditory n-back brain regions, as well as differences in application areas, we redrew activation maps of brain regions in the n-back experiment based on these two stimulus modalities (; Figure 2). It is shown that the cerebellum, which contributes to motor learning, also engages in the dual n-back task. We also summarized the activation of brain regions during the emotional dual n-back process, aiming to help us better understand the relationship between emotionally related brain regions and WM updating (; Figure 4). Additionally, fMRI intuitively tracks changes in brain activity as WM load increases, providing insights into the transition from simple to complex multimodal tasks. For instance, in a standard n-back task, frontal activation tends to decline when processing demands become excessive. However, observed an increase in prefrontal activation during dual n-back tasks, even when processing demands were at their highest, particularly in the most difficult conditions. This suggests that fMRI is an excellent tool for investigating both training effects and long-term changes associated with n-back tasks. Unlike EEG-based analysis, which primarily focuses on frequency bands and rough regional divisions, fMRI provides a more detailed examination of brain regional activation during n-back tasks.

![F4](ExploringTheNbackTaskInsights_2025_FrontiersInHumanNeuroscience_c0218be7.assets/fnhum-19-1721330-g004.jpg)

**Figure F4**: Brain activation regions for the emotional dual n-back task. The brain template and the plot method are the same as in Figure 2.

Neuroimaging for n-back experiments may also use fNIRS devices, mainly due to their portable performance and better spatial resolution than EEG. For example, in the verbal WM task, increased complexity needs greater executive control, thus leading to an increase in cerebral blood flow to the areas associated with verbal WM.

Overall, different neuroimaging modalities provide complementary insights into the neural mechanisms engaged during n-back performance. EEG-based n-back paradigms are typically conducted online, allowing millisecond-level tracking of rapid updating, attentional switching, and workload fluctuations. However, their spatial resolution is limited. In contrast, fMRI studies fall into two major designs: (1) pre-post training structural or resting-state scans, which capture longer-term plasticity but do not reflect real-time updating dynamics, and (2) online task-fMRI designs, which compare activation patterns across difficulty levels to localize fronto-parietal engagement, but remain constrained by the slow hemodynamic response and therefore cannot resolve the fine-grained temporal sequence of cognitive operations. Thus, even when fMRI is collected during task execution, it primarily reflects load-dependent activation differences, rather than the moment-by-moment updating processes that define the n-back paradigm.

Future research should therefore prioritize multimodal integration, especially approaches that combine EEG’s high temporal precision with fMRI’s high spatial specificity to construct dynamic functional network models of WM updating. Such joint acquisition and source-constrained analysis pipelines would allow researchers to map how neural representations evolve across stimulus encoding, delay, comparison, and response stages, an aspect that cannot be fully characterized by either modality alone. These multimodal frameworks are particularly critical for understanding n-back paradigms involving emotional or dual-task components, where multiple cognitive processes interact over short timescales. Accordingly, advancing n-back neuroimaging requires shifting from static localization toward temporally resolved network dynamics, which can leverage the strengths of both EEG and fMRI in a coordinated analytical framework.

### Stimulation effect (tDCS and tACS) on n-back tasks

Non-invasive electrical stimulation studies using tDCS and tACS show that the effects on n-back WM performance are strongly condition-dependent rather than uniformly facilitatory. Meta-analytic evidence indicates that single-session tDCS produces inconsistent or small behavioral effects, whereas multi-session stimulation combined with WM training is more likely to yield improvements, typically reflected in reduced reaction time rather than accuracy gains. Stimulation of the left dlPFC remains the most common approach, and its effects are supported by neural markers such as enhanced P3 amplitude and stronger task-related default-mode network suppression, which correlate with faster responding. In contrast, tACS exhibits more robust single-session effects, particularly when theta-band stimulation is applied across fronto-parietal networks to enhance phase synchronization, supporting updating and executive control during n-back performance. A recent meta-analysis confirms that theta tACS reliably improves cognitive performance in healthy adults, with stronger effects when stimulation is delivered online during task execution. Gamma-band tACS and cross-band tACS, on the other hand, often produce neural entrainment without consistent behavioral improvement, suggesting differential roles for frequency-specific circuit modulation.

Moreover, studies targeting the right dlPFC and parietal cortex highlight that WM performance is not exclusively governed by left prefrontal regions. Parietal stimulation may more robustly enhance spatial working memory, particularly under offline protocols. Finally, repetitive HD-tACS demonstrates that frequency-region combinations can selectively and durably enhance distinct memory systems, producing double dissociation between WM and LTM and effects lasting up to 1 month. These findings collectively support the view that network-level targeting and stimulation timing are critical determinants of cognitive outcomes, rather than stimulation modality alone (Table 3).

**Table T3**: tDCS/tACS effects on n-back task.

| Stimulation type | Typical target region/montage | Neural mechanism | WM subprocesses most affected (n-back) | Task timing (online/offline) | Typical behavioral effects | Network/neural effects | References |  | tDCS (left dlPFC) | F3 (standard bipolar) or HD-tDCS | Increased cortical excitability; facilitates prefrontal control | Updating and maintenance | Multi-session online or combined training | Single-session effects inconsistent; multi-session often reduces RT | Increased P3 amplitude; stronger task-related DMN suppression |  |  | tDCS (right dlPFC/PPC) | F4 or PPC | Attention allocation and fronto-parietal resource rebalancing | Spatial updating and visuospatial WM | Mostly offline | More consistent improvements in 3-back and spatial WM | Highlights functional relevance of parietal WM nodes |  |  | tDCS (broad-frontal) | F3/F4 with extracephalic return | Broad prefrontal excitability shift | Updating under moderate load | Online | Improved 2-back RT selectively | Montage strongly determines effect direction |  |  | tACS (theta 4–7 Hz) | Fronto-parietal dual-site | Synchronizes fronto-parietal network rhythms | Executive control and updating | Online | More reliable accuracy improvements vs. single-session tDCS | Increased theta coherence and task-phase coupling |  |  | tACS (gamma 30–80 Hz) | dlPFC or PPC | Enhances fast binding /activation cycles | Short-term maintenance | Online | Behavioral effects variable | Strong oscillatory entrainment without consistent accuracy gains |  |  | HD-tACS (rhythm-specific, older adults) | IPL-θ vs. dlPFC-γ | Frequency-region dissociation in memory systems | WM (θ) vs. LTM (γ) | 4-day multi-session | Double dissociation maintained ≥ 1 month | Long-term plasticity in WM/LTM circuits |  |  | Cross-frequency theta–gamma coupled | dlPFC | Peak-locked θ–γ coupling to enhance hierarchical control loops | High-load updating (2-back > 1-back) | 16-session multi-week training | Improved 2-back discriminability (sensitivity and decision criterion); no effect on 1-back | Behavioral gains accumulated across training weeks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

*tDCS, transcranial direct current stimulation; tACS, transcranial alternating current stimulation; HD-tDCS, high-definition transcranial direct current stimulation; PPC, posterior parietal cortex; dlPFC, dorsolateral prefrontal cortex; IPL, inferior parietal lobule; DMN, default mode network; RT, reaction time; LTM, long-term memory.*

## Applications of n-back experiments

### Cognitive training and transfer effects

Cognitive training needs to consider the transfer effect (TE) that improves cognitive functions through specialized training and examines the extent to which these improvements transfer to untrained tasks or real-world scenarios. In cognitive training, both standard experimental paradigms, such as letter memory, dual n-back tasks, and cognitive tasks hidden in games, may produce a certain degree of TE. However, the TE is often related to the age of the participants and the correlation between the training task and the transfer task. The TE can be categorized into near transfer and far transfer according to the relevance between the training activity and the skills to be improved. Usually, generating a near transfer indicates that the untrained task relies more on WM, while generating a far transfer means that the untrained task relies on other cognitive functions such as attention, reasoning, etc.. The TE of cognition needs to be confirmed through corresponding cognitive tests, such as the delayed-recognition WM task for TE of WM and the test of variables of attention for sustained attention after cognitive training. The TE of the n-back experiment involves a wide range of cognitive functions, such as spatial memory, attention, and Gf. Gf refers to the ability to reason, solve novel problems, and adapt to new situations independently of previously acquired knowledge or experience. Since the Gf relies on WM and both Gf and WM share variance like underlying neural circuitries, and the n-back experiment is considered to be able to test and improve WM, the n-back experiment is believed to have a positive transfer effect on Gf. The TE between n-back training and Gf was first systematically introduced by Jaeggi et al.. A dual n-back task that combined visual and auditory stimuli was given with an adaptive training strategy.

The pretesting and post-testing were provided for a measure of Gf with either the Raven’s Advanced Progressive Matrices (RAPM) test or the short version of the Bochumer Matrizen-Test (BOMAT) for different groups. Such TE to Gf was observed in both young and elderly groups with various neuroimaging methods. The meta-analysis of 20 studies also supports this conclusion that the effect size of the treatment/control group difference in Gf at posttest vs. baseline of Hedge’s g at 0.24 vs. -0.003. However, some studies have also found that the n-back experiment is not very significant for the TE of Gf. A multi-level meta-analysis including 33 studies focused on the TE of the n-back task to the untrained n-back task and other cognitive processes. The TE of n-back to Gf [g = 0.16, (0.08, 0.24), p < 0.001] is in line with that in. However, the TE is much smaller than the untrained n-back task [g = 0.63, (0.44, 0.82), p < 0.001), which manifests that the transfer following WM training with the n-back task is a task-specific one instead of a widespread TE. Further research suggests that the TE of dual n-back (containing visual-spatial components) may not depend on relational WM, which is highly correlated with the spatial n-back task, but rather on other mechanisms.

### Clinical applications

The n-back task is widely used in clinical settings to evaluate WM and related executive functions, demonstrating good sensitivity to WM load and neural engagement. Its clinical application spans diverse conditions beyond neurodegenerative diseases such as Alzheimer’s and Parkinson’s disease, including psychiatric disorders (e.g., schizophrenia), chronic pain, and spinal cord injury, where deviations in n-back performance and cortical activation patterns reflect impaired WM processing. Owing to its compatibility with neuroimaging and neurostimulation techniques such as fMRI, fNIRS, MEG, and rTMS, the n-back task has also been used to assess how measurement environments and neural modulation influence task behavior and brain activation patterns. For instance, reaction times are generally slower during fMRI scanning, and rTMS stimulation of the left dlPFC can alter activity in broader WM-related networks during n-back performance.

In addition to behavioral performance indices, computational and electrophysiological analyses of n-back behavior contribute to deeper cognitive and neurobiological interpretation. For example, drift-diffusion modeling has been used to relate n-back decision dynamics to genetic risk markers in youth populations, linking WM efficiency to polygenic vulnerability signatures.

Beyond assessment, the n-back task is also used as a rehabilitation tool. Training studies in traumatic brain injury (TBI), multiple sclerosis (MS), and stroke populations have shown that repeated n-back practice can improve WM task performance and enhance neural efficiency in frontoparietal networks. Similarly, improvements have been reported in hemodialysis patients and in children with ADHD following n-back-based cognitive training. However, these gains largely reflect near transfer, meaning improvements are typically limited to tasks sharing similar WM updating demands. For example, in children with ADHD, n-back training improved the trained task and yielded small-to-moderate gains in closely related inhibitory control measures (e.g., untrained n-back and inhibitory control, η2p = 0.13 at post-test), but did not produce reliable far-transfer effects on broader executive or academic outcomes, and some improvements diminished at follow-up.

Age-related cognitive changes further shape the clinical application of the n-back task. With aging, individuals shift from interference-resistant executive control strategies toward greater reliance on attentional and mnemonic support processes during n-back performance. This shift aligns with broader compensatory recruitment patterns described in aging, mild cognitive impairment (MCI), and Alzheimer’s disease. Correspondingly, electrophysiological features derived from n-back tasks, such as ERD/ERS and ERP components, have shown potential in early differentiation of healthy aging, MCI, and mild Alzheimer’s disease. Despite this diagnostic value, n-back training is not commonly adopted as a rehabilitation intervention for MCI or Alzheimer’s disease, likely due to the abstract nature and difficulty of the task, as well as evidence that cognitive training in these populations is more effective when integrated into ecologically relevant daily activities rather than isolated WM tasks.

While many studies report positive effects, several methodological constraints require caution: (1) sample sizes are often small (n < 30 in many trials), (2) training duration and intensity vary widely across studies, (3) outcome metrics differ across behavioral and neural endpoints, complicating effect estimation, and (4) placebo and active-control conditions are sometimes insufficient, particularly in home-based training protocols. Therefore, current evidence supports n-back as a clinically useful evaluation tool and as a targeted rehabilitation method in conditions such as TBI and MS. However, it should not be considered a universal cognitive training protocol, particularly in ADHD and MCI populations, where far-transfer effects remain unreliable.

### Children and education

Unlike n-back, which can be influenced by familiarity-based strategies, recall-based WM tasks require active maintenance and manipulation, making them developmentally appropriate and behaviorally sensitive training tools for children..

This does not mean that the n-back experiment is unimportant, on the contrary, the n-back task plays an important role in the education of children and adolescents, mainly manifested in the discrimination of neural and cognitive growth trajectories, data collection and children’s diseases exploration, the influence of family economic status on children’s cognition, intelligence and neuropsychological development assessment, development of educational tools, research on special children’s education. There are two main types of n-back experiments related to adolescents and education. One type uses n-back experiments for testing, such as testing WM and other factors that affect WM, such as volleyball, games, etc.. The test results of n-back can also reflect some social issues, such as the education level of parents and family income status. Another type of n-back experiment mainly studies the function of n-back on adolescents, such as its impact on growth trajectory or the improvement of reasoning ability. Sustained selective attention and WM are both crucial cognitive functions for children and adolescents.

However, interventions to enhance sustained attention for children and adolescents are usually continuous performance tasks (CPT) such as go/no-go tasks, although n-back cognitive training is believed to require sustained attention and has also been used for training tasks in children with ADHD. This is because the n-back task beyond the 1-back level may be difficult for young children. WM ability is closely related to various learning abilities, such as reasoning skills. Combining cognitive WM capacity training (n-back tasks) and reasoning strategy training can improve reasoning skills in history courses. In contrast, merely cognitive WM capacity training has less impact on improving school students’ reasoning skills. Such a result manifests that the combined training strategy facilitates the internalized reasoning structure in the WM.

The n-back tasks related to children’s education are usually made more gamified. The gamified version of n-back tasks leads to higher engagement and self-reported motivation, and some scholars reported that there is no performance difference from that in the standard version.

### Social sciences and the n-back task

The relationship between the WM and social cognition is the focus of discussions in the social sciences and n-back tasks. Social cognition involves the recognition of others as well as the recognition of oneself. As far as understanding oneself is concerned, the n-back task, together with other tasks like the Tower of Hanoi task, Stroop test, and Wisconsin card sorting test, is used for self-regulation empowerment training, which can improve the neurocognitive and social skills in students with dyscalculia. Improving social cognition requires regulating emotions well. As mentioned before, n-back tasks often introduce emotional dimensions, but the research content usually focuses on the impact of emotions on WM or attentional control, such as positive emotions can prolong attention span in WM. Several studies have confirmed that n-back training has a positive effect on affective control. There is a close connection between language and social sciences. Monolingual and bilingual young people have different results in emotional n-back experiments, such as differences in accuracy and the influence of emotional stimuli. An important aspect of social cognition is perspective-taking, and research has shown that social WM training improves perspective-taking accuracy. However, social WM training is not like an n-back task, it is more like an SR task. Participants need to rank friends along with trait dimensions in WM. Another experiment of perspective taking involves moving items on the bookshelf based on voice prompts, which is somewhat similar to the 1-back experiment. However, the difference is that the speaker is behind the bookshelf, while the observer (subject) is in front of the bookshelf, and a part of the back of the bookshelf is covered by a board. This requires empathy to determine whether the object being moved is what the speaker wants to move.

The impact of social pressure on individuals can also be achieved through n-back tasks. For example, cortisol responses provide an acute stress environment and higher cortisol responders for young people show better performance on n-back tasks. The generation of stress does not necessarily require the action of medication but rather involves informing participants of their performance and comparison with others during the n-back process. The social pressure that people feel may stem from prolonged exposure to socio-economic hardening. Poverty-related cognitive and emotional stress may exacerbate neurocognitive function and lead to impulsive delayed reward discounting and emotional reactivity is closely related to delayed reward discounting. In emerging adults with high emotional reactivity, the severity of socio-economic hardship indicates an increase in delayed reward discounting, which is achieved through a decrease in brain region responses activated during n-back WM tasks. In addition, the n-back experiments applied in social sciences also include the impact of family status on adolescents, such as household income, parental education level, and race.

## Limitations and challenges of n-back tasks

### N-back experiment and mental fatigue

Mental fatigue is a critical confounding factor in n-back research because it directly influences both behavioral performance and neural activation patterns. Prolonged cognitive load or sustained task engagement can lead to reduced accuracy, slower reaction times, and altered ERP and fMRI signals, making it difficult to determine whether observed effects reflect WM processes or the impact of fatigue.

However, despite its importance, mental fatigue is notoriously difficult to measure objectively. For instance, feelings of tiredness or reduced alertness are easily confounded with boredom. When the experimenter conducts a driving fatigue test on the simulation platform, it is difficult to objectively judge whether the subject is in a state of fatigue or boredom during the brief 1-h driving process. In many experiments studying mental fatigue, it is necessary to introduce a state of mental fatigue, and the n-back task is one of the means. N-back has been proven to be an acute way of introducing fatigue, typically taking only half an hour to an hour. The increase in difficulty of the n-back experiment has raised the cognitive demands for the task, making it easier to enter a state of fatigue, resulting in a decrease in the amplitude of the electroencephalogram (P3a) in the Fz, Cz, and Pz regions. However, experiments or training based on n-back rarely mention the issue of mental fatigue during the experimental process, which may be due to the following reasons. Firstly, the induce of mental fatigue state varies from person to person, even for individuals with similar traits such as age, disease, etc., especially when facing high WM load tasks, there may be significant differences in tolerance and fatigue performance. Secondly, for the induce of fatigue state, different experimental paradigms vary greatly. Due to the experimental setup, such as the gamification setting, the duration of the n-back experiment may not induce fatigue to most participants. Multi-sensory input (dual n-back tasks) may mobilize more brain resources, thereby reducing fatigue during the experimental process. Meanwhile, adding rest time in the experiment can avoid the occurrence of fatigue. Thirdly, many n-back tasks require continuous training over several days, so repeated training can help participants better adapt to the experimental process and ignore the effects of fatigue. Finally, measuring mental fatigue is relatively difficult, as it typically requires additional physiological or behavioral indicators to evaluate, such as decreased task performance, subjective fatigue reports, or physiological responses (such as skin conductance, heart rate variability, blink frequency, etc.). Moreover, the data to be observed in experiments is easily affected by fatigue, like accuracy and reaction time. Meanwhile, controlling for too many variables can affect the interpretability of research results. Therefore, sometimes the impact of mental fatigue is directly ignored.

To mitigate these effects, future studies should adopt more systematic approaches to monitor and control fatigue. First, experimenters can use adaptive task designs that automatically adjust difficulty based on performance or physiological indicators, thereby maintaining engagement without excessive strain. However, current adaptive task designs mainly consider the task difficulty for participants rather than the influence of mental fatigue (load factor in Table 2). Second, rest intervals or shorter task blocks should be incorporated to minimize cumulative fatigue, particularly in long or multi-session paradigms. Third, integrating objective physiological measures, such as electrodermal activity, heart rate variability, or ocular metrics (blink rate measure, pupillometry), can help detect early signs of mental fatigue and distinguish them from boredom or disengagement. In addition, self-report fatigue scales collected at regular intervals can provide complementary subjective data.

Finally, combining multimodal approaches such as fNIRS, EEG, and behavioral performance can allow researchers to model the temporal evolution of fatigue and its neural correlates in real-time. By incorporating these measures, future n-back studies can improve their internal validity, reduce the confounding effects of fatigue, and more accurately isolate the cognitive processes underlying WM performance.

### Validity and reliability of the n-back experiment

When assessing the validity of the n-back task, we need to consider both the face and convergent validity. Face validity is based on a subjective judgment which refers to whether the task appears to measure the cognitive ability it claims to assess. Face validity for an n-back task is generally high as the task explicitly requires participants to remember and respond to stimuli presented a certain number of steps back in a sequence, which intuitively engages WM. However, for convergent validity, there is a lack of convergence between n-back and other WM tasks like various span measures (operation span, reading span, symmetry span, and rotation span) due to the low correlation between n-back and these tasks. For example, the complex span and n-back correlation r+ equals to 0.2.

Due to the insufficient reliability, the n-back task is not a useful measure of individual differences in WM especially for clinical applications as it may influence the patients’ cognitive function assessments. The insufficient reliability of the n-back task may be derived from multiple aspects. The performance of participants may be driven by familiarity- and recognition-based discrimination processes instead of an active recall process. In addition, participants are prone to achieving ceiling effects under low load factor conditions and floor effects by adding a mere amount of load factor. Furthermore, the reliability of n-back experiments is also affected by the experimental environment such as the clinical environment with an in-scanner environment. Although previous studies reported weak convergent validity between the n-back task and complex span measures, recent psychometric evidence suggests that the n-back remains a valid measure of WM when construct validity is evaluated via known-groups comparisons. Specifically, the task reliably differentiates younger and older adults and shows good to excellent reliability in reaction time measures, supporting its suitability for detecting group-level WM differences rather than individual difference assessment.

### Multi-cognitive process of the n-back task

In addition to the traditional WM process, the n-back task also involves other cognitive processes that will induce conflict. For example, the measure of WM with n-back may induce conflict with familiarity and recollection process when the current stimulus matches a previous stimulus, but not the one n items back in the sequence. Furthermore, the n-back paradigm involves a binding process, which means that the memory content is bound to the chronological order. Furthermore, the n-back task also involves sustained attention and inhibitory control. Even in simple cases (e.g., A-B-A in 2-back), the participant cannot rely on familiarity alone. Instead, they must suppress the automatic familiarity response and use temporal-order binding to determine whether the current item matches the one two positions back. Therefore, correct performance depends not only on WM updating, but also on inhibitory control and temporal-sequence memory, demonstrating that the n-back task involves multiple interacting cognitive processes. Hence, the n-back task is a complex measure involving multiple processes and thus decreases its construct validity.

Participants who complete the n-back task multiple times may develop familiarity, leading to acquisition effects. Although ERP study has shown that P300 enhancements are derived from n-back training and practice, whereas N160 enhancements only originated from n-back training, it is difficult to interpret results accurately, as performance improvements might reflect the acquisition effect rather than the inherent enhancement of WM.

In addition, WM training based on n-back tasks does not necessarily produce transfer effects, whether they are near or far transfer effects. Although some studies have shown transfer effects, possibly due to small sample sizes. Meanwhile, as the n-back experiment is a multi-cognitive process, it is difficult to conduct targeted cognitive training. This multi-process nature of the n-back task reduces its construct validity, because improvements in performance may arise from strategy shifts (e.g., chunking, familiarity-based responding) rather than genuine enhancement of WM updating. This also explains why n-back training sometimes results in near-transfer effects to tasks involving similar conflict or updating demands, but fails to generalize to broader cognitive domains. Furthermore, there is no unified standard for the duration, intensity, interval, etc. of n-back training. Some studies may have only conducted short-term training, while others may have undergone several weeks of intensive training. This difference may result in inconsistent effects of Gf enhancement. Concurrently, this leads to a lack of normative data for n-back experiments. Thus, this may limit the application scenarios of n-back experiments, especially in education, rehabilitation, and clinical settings.

## Future work

At present, n-back experiments are mainly applied in laboratory environments, and although there are some gamified scenes, they are far from daily life scenarios. Therefore, by utilizing emerging technologies such as virtual reality (VR), more complex and realistic n-back tasks can be designed better to simulate WM usage scenarios in real life. We mentioned earlier the application of n-back experiments and social science, such as the impact of social cognition, language, social stress, etc., on WM. Cultural background plays a significant role in shaping individual perspectives, behaviors, and cognitive processes. Therefore, it is necessary to conduct n-back experiments on people from different cultural backgrounds, especially children, which may have some chain reactions, such as how culture affects personality and cognition.

In addition, the n-back experimental design is also worth studying as it has created too many derivative paradigms. Therefore, we need to standardize the training duration and intensity for more reliable comparisons. At the same time, it is necessary to design effective control groups in the experiment to improve the rigor of the experimental design. Furthermore, research based on n-back experiments may require long-term tracking. The study of Gf through n-back experiments is an example that long-term tracking can evaluate the persistence of Gf and transfer effects. Finally, due to the complexity of the n-back experiment and the multi-cognitive process, there are not many practical applications of n-back, and potential application areas include education, vocational training, rehabilitation, and sports psychology, which need further development.

## Conclusion

The n-back experiment remains a cornerstone in cognitive neuroscience for assessing and training WM across various domains. Its adaptability and integration with neuroimaging techniques have advanced our understanding of WM processes and their neural underpinnings. While the task has demonstrated utility in clinical and educational contexts, limitations such as inconsistent validity and reliability, as well as mixed evidence for transfer effects, warrant further exploration. Future work should focus on developing standardized protocols, leveraging emerging technologies like VR for more ecological applications, and investigating cross-cultural and long-term impacts. Addressing these challenges will enhance the utility of n-back experiments in both research and practical applications, bridging the gap between laboratory findings and real-world cognitive demands.

> Edited by: Kelly Rootes-Murdy, United States Department of Veterans Affairs, United States

> Reviewed by: Yuanjun Xie, Fourth Military Medical University, China

> Ronglong Xiong, University of Electronic Science and Technology of China, China

## Author contributions

SH: Writing – review & editing, Methodology, Writing – original draft, Visualization, Conceptualization. CC: Writing – original draft, Investigation, Validation, Writing – review & editing, Methodology. YM: Methodology, Data curation, Validation, Writing – original draft, Visualization. YZhao: Validation, Visualization, Writing – review & editing, Software. YZhu: Writing – review & editing, Visualization, Software. KD: Writing – review & editing, Visualization, Software. TX: Supervision, Writing – review & editing, Funding acquisition, Writing – original draft, Project administration.

## Conflict of interest

The authors declare that the research was conducted in the absence of any commercial or financial relationships that could be construed as a potential conflict of interest.

## Generative AI statement

The authors declare that no Generative AI was used in the creation of this manuscript.

Any alternative text (alt text) provided alongside figures in this article has been generated by Frontiers with the support of artificial intelligence and reasonable efforts have been made to ensure accuracy, including review by the authors wherever possible. If you identify any issues, please contact us.

## Publisher’s note

All claims expressed in this article are solely those of the authors and do not necessarily represent those of their affiliated organizations, or those of the publisher, the editors and the reviewers. Any product that may be evaluated in this article, or claim that may be made by its manufacturer, is not guaranteed or endorsed by the publisher.

## Supplementary material

The Supplementary Material for this article can be found online at: https://www.frontiersin.org/articles/10.3389/fnhum.2025.1721330/full#supplementary-material

## References

- Differential tDCS and tACS effects on working memory-related neural activity and resting-state connectivity.

- Repeated working memory training improves task performance and neural efficiency in multiple sclerosis patients and healthy controls.

- Parental education, household income, race, and children’s working memory: complexity of the effects.

- Is the binding of visual features in working memory resource-demanding?

- Computerized working memory training: can it lead to gains in cognitive skills in students?

- Dissociating the effects of Sternberg working memory demands in prefrontal cortex.

- Auditory versus visual stimulus effects on cognitive performance during the N-back task.

- Video game training enhances cognitive control in older adults.

- Effects of an n-back task on indicators of perceived cognitive fatigue and fatigability in healthy adults.

- Improving reasoning skills in secondary history education by working memory training.

- Neural correlates of the object-recall process in semantic memory.

- Family income mediates the effect of parental education on adolescents’ hippocampus activation during an n-back memory task.

- Parental education and left lateral orbitofrontal cortical activity during N-back task: an fMRI study of American adolescents.

- Improving fluid intelligence with training on working memory: a meta-analysis.

- Repetitive transcranial magnetic stimulation of the dorsolateral prefrontal cortex enhances working memory.

- Go/No-Go task engagement enhances population representation of target stimuli in primary auditory cortex.

- Cognitive control mechanisms, emotion and memory: a neural perspective with implications for psychopathology.

- Early selection of task-relevant features through population gating.

- Processing differences between monolingual and bilingual young adults on an emotion n-back task.

- Computer-based cognitive training for mild cognitive impairment: results from a pilot randomized, controlled trial.

- Effects of experimentally-induced emotional states on frontal lobe cognitive task performance.

- Neural substrates of successful working memory and long-term memory formation in a relational spatial memory task.

- Early and late stages of working-memory maintenance contribute differentially to long-term memory formation.

- No pain, no gain? Investigating motivational mechanisms of game elements in cognitive tasks.

- N-back versus complex span working memory training.

- Aging and n-back performance: a meta-analysis.

- Working memory training in older adults: evidence of transfer and maintenance effects.

- Working memory training in old age: an examination of transfer and maintenance effects.

- Investigating the impact on fluid intelligence by playing N-Back games with a kinesthetic modality

- Who comes first? The role of the prefrontal and parietal cortex in cognitive control.

- A parametric study of prefrontal cortex involvement in human working memory.

- Self-regulatory strength depletion and muscle-endurance performance: a test of the limited-strength model in older adults.

- Economical assessment of working memory and response inhibition in ADHD using a combined n-back/nogo paradigm: an ERP study.

- Changes in brain network activity during working memory tasks: a magnetoencephalography study.

- Estimating workload using EEG spectral power and ERPs in the n-back task.

- Spatial-sequential working memory in younger and older adults: age predicts backward recall performance within both age groups.

- Effect of mental fatigue on induced tremor in human knee extensors.

- Physiological characteristics of capacity constraints in working memory as revealed by functional MRI.

- Association of video gaming with cognitive performance among children.

- Distinguishing the visual working memory training and practice effects by the effective connectivity during n-back tasks: a DCM of ERP Study.

- Brain activation during the n-back working memory task in individuals with spinal cord injury: a functional near-infrared spectroscopy study.

- Functional abnormalities in symptomatic concussed athletes: an fMRI study.

- Working memory operates over the same representations as attention.

- Sub-processes of working memory in the N-back task: an investigation using ERPs.

- Working memory training does not improve intelligence in healthy young adults.

- Top-down control of MEG alpha-band activity in children performing Categorical N-Back Task.

- Developmental neural networks in children performing a Categorical N-Back Task.

- Distinct mechanisms for the impact of distraction and interruption on working memory in aging.

- Deficit in switching between functional brain networks underlies the impact of multitasking on working memory in older adults.

- Time-trial performance is not impaired in either competitive athletes or untrained individuals following a prolonged cognitive task.

- Working memory and intelligence are highly related constructs, but why?

- Neural basis of novel and well-learned recognition memory in schizophrenia: a positron emission tomography study.

- Modality effects in verbal working memory: differential prefrontal and parietal responses to auditory and visual stimuli.

- Transfer of learning after updating training mediated by the striatum.

- Plasticity of executive functioning in young and older adults: immediate training gains, transfer, and long-term maintenance.

- Delayed match-to-sample in working memory: a BrainMap meta-analysis.

- Integrating clinical assessment with cognitive neuroscience: construct validation of the California Verbal Learning Test.

- Boosting working memory in the elderly: driving prefrontal theta–gamma coupling via repeated neuromodulation.

- Effects of HD-tDCS combined with working memory training on event-related potentials

- Cognitive and emotional benefits of emotional dual dimension n-back training based on an APP.

- Measuring children’s sustained selective attention and working memory: validity of new minimally linguistic tasks.

- Meta-analysis of real-time fMRI neurofeedback studies using individual participant data: how is brain regulation mediated?

- Common default mode network dysfunction across psychopathologies: a neuroimaging meta-analysis of the n-back working memory paradigm.

- Learning cognitive skills by playing video games at home: testing the specific transfer of general skills theory.

- The n-back test and the attentional network task as measures of child neuropsychological development in epidemiological studies.

- Event-related synchronisation responses to N-back memory tasks discriminate between healthy ageing, mild cognitive impairment, and mild Alzheimer’s disease

- Early diagnosis of mild cognitive impairment and Alzheimer’s with event-related potentials and event-related desynchronization in N-back working memory tasks.

- Interactions between frontal cortex and basal ganglia in working memory: a computational model.

- What does the n-back task measure as we get older? relations between working-memory measures and other cognitive functions across the lifespan.

- Effect of two weeks of rTMS on brain activity in healthy subjects during an n-back task: a randomized double blind study.

- Brain bases of recovery following cognitive rehabilitation for traumatic brain injury: a preliminary study.

- Age-related changes in brain oscillatory patterns during an n-back task in children and adolescents.

- Effects of age and gender on recall and recognition discriminability.

- Neural mechanisms of general fluid intelligence.

- Neural mechanisms underlying the integration of emotion and working memory.

- Electroencephalography based analysis of working memory load and affective valence in an n-back task with emotional stimuli.

- Emotion regulation: affective, cognitive, and social consequences.

- Long-lasting, dissociable improvements in working memory and long-term memory in older adults with repetitive neuromodulation.

- Investigating mental workload-induced changes in cortical oxygenation and frontal theta activity during simulated flights.

- Alterations in functional activation in euthymic bipolar disorder and schizophrenia during a working memory task.

- A novel protocol to induce mental fatigue.

- Working memory load-dependent brain response predicts behavioral training gains in older adults.

- Neural correlates of training and transfer effects in working memory in older adults.

- Working memory training improvements and gains in non-trained cognitive tasks in young and older adults.

- Psychometric characteristics of the n-back task: construct validity across age and stimulus type, internal consistency, test-retest and alternate forms reliability.

- Mental workload during n-back task—quantified in the prefrontal cortex using fNIRS.

- Sex/gender differences in verbal fluency and verbal-episodic memory: a meta-analysis.

- The interactive effects of listwide control, item-based control, and working memory capacity on Stroop performance.

- Clinical utility of the n-back task in functional neuroimaging studies of working memory.

- Improving fluid intelligence with training on working memory.

- Short-and long-term benefits of cognitive training.

- The concurrent validity of the N-back task as a working memory measure.

- Does excessive memory load attenuate activation in the prefrontal cortex? Load-dependent processing in single and dual tasks: functional magnetic resonance imaging study.

- The relationship between n-back performance and matrix reasoning — implications for training and transfer.

- Validation of new online game-based executive function tasks for children.

- Practice effects in the developing brain: a pilot study.

- Exploring n-back cognitive training for children with ADHD.

- Sticky thoughts: depression and rumination are associated with difficulties manipulating emotional material in working memory.

- N-back training in middle adulthood: evidence for transfer only to structurally similar task.

- The role of prefrontal cortex in working-memory capacity, executive attention, and general fluid intelligence: an individual-differences perspective.

- Working-memory capacity and the control of attention: the contributions of goal neglect, response competition, and task set to Stroop interference.

- Working memory, attention control, and the N-back task: a question of construct validity.

- Merging clinical neuropsychology and functional neuroimaging to evaluate the construct validity and neural network engagement of the n-back task.

- Working memory of emotional stimuli: electrophysiological characterization.

- Examining the effect of stress induction on auditory working memory performance for emotional and non-emotional stimuli in female students.

- Age differences in short-term retention of rapidly changing information.

- Working memory and executive function decline across normal aging, mild cognitive impairment, and Alzheimer’s disease.

- The working memory Stroop effect: when internal representations clash with external stimuli.

- Training and plasticity of working memory.

- Brain activation in processing temporal sequence: an fMRI study.

- Reduced but broader prefrontal activity in patients with schizophrenia during n-back working memory tasks: a multi-channel near-infrared spectroscopy study.

- The Effect of emotional content on brain activation and the late positive potential in a word n-back task.

- Dual n-back working memory training in healthy adults: a randomized comparison to processing speed training.

- A meta-analysis showing improved cognitive performance in healthy young adults with transcranial alternating current stimulation.

- Influence of task combination on EEG spectrum modulation for driver workload estimation.

- Executive n-back tasks for the neuropsychological assessment of working memory.

- Cognitive intervention for persons with mild cognitive impairment: a meta-analysis.

- Working memory plasticity in old age: practice gain, transfer, and maintenance.

- Clinical utility of the dual n-back task in schizophrenia: a functional imaging approach.

- The resting-state cerebro-cerebellar function connectivity and associations with verbal working memory performance.

- Utilizing the n-back task to investigate working memory and extending gerontological educational tools for applicability in school-aged children.

- Individual differences under acute stress: higher cortisol responders performs better on N-back task in young men.

- Training and transfer effects of N-back training for brain-injured and healthy subjects.

- Effects of working memory training on neural correlates of Go/Nogo response control in adults with ADHD: a randomized controlled trial.

- Developmental trajectories in primary schoolchildren using n-back task.

- Cognitive stimulation as a mechanism linking socioeconomic status and neural function supporting working memory: a longitudinal fMRI study.

- The two-back task leads to activity in the left dorsolateral prefrontal cortex in schizophrenia patients with predominant negative symptoms: a fNIRS study and its implication for tDCS.

- Single-channel EEG features during n-back task correlate with working memory load.

- The effect of tDCS electrode montage on attention and working memory.

- Manipulation specific effects of mental fatigue: evidence from novelty processing and simulated driving.

- Working memory capacity and Stroop interference: global versus local indices of executive control.

- Is working memory training effective? A meta-analytic review.

- There is no convincing evidence that working memory training is effective: a reply to Au et al. (2014) and Karbach and Verhaeghen (2014).

- Working memory training does not improve performance on measures of intelligence or other measures of “far transfer”: evidence From a meta-analytic review.

- Neural correlates of N-back task performance and proposal for corresponding neuromodulation targets in psychiatric and neurodevelopmental disorders.

- Altered subprocesses of working memory in patients with fibromyalgia: an event-related potential study using N-back task.

- Social working memory training improves perspective-taking accuracy.

- The prefontral cortex and cognitive control.

- Is the n-back task a valid neuropsychological measure for assessing working memory?

- Long-term brain effects of N-back training: an fMRI study.

- Gaming is related to enhanced working memory performance and task-related cortical activity.

- N-backer: an auditory n-back task with automatic scoring of spoken responses.

- A functional MRI study of working memory task in euthymic bipolar disorder: evidence for task-specific dysfunction.

- Individual differences in fatigued performance.

- Does working memory training work? The promise and challenges of enhancing cognition by training working memory.

- Associations between neighborhood socioeconomic status, parental education, and executive system activation in youth.

- The role of the prefrontal cortex in the maintenance of verbal working memory: an event-related fMRI analysis.

- The effects of working memory training on brain activity.

- An investigation of working memory deficits in depression using the n-back task: a systematic review and meta-analysis.

- The effect of n-back training during hemodialysis on cognitive function in hemodialysis patients: a non-blind clinical trial.

- Examining specificity of neural correlates of childhood psychotic-like experiences during an emotional n-back task.

- Binding and inhibition in working memory: individual and age differences in short-term recognition.

- Working memory and intelligence–their correlation and their relation: comment on Ackerman, Beier, and Boyle (2005).

- Predicting clinical gains and side effects of stimulant medication in pediatric attention-deficit/hyperactivity disorder by combining measures from qEEG and ERPs in a cued go/nogo task.

- Exploring individual differences as predictors of performance change during dual-n-back training.

- Socioeconomic hardship and delayed reward discounting: associations with working memory and emotional reactivity.

- N-back working memory paradigm: a meta-analysis of normative functional neuroimaging studies.

- Improving attention control in dysphoria through cognitive training: transfer effects on working memory capacity and filtering efficiency.

- The effects of theta and gamma tACS on working memory and electrophysiology.

- Near transfer to an unrelated N-back task mediates the effect of N-back working memory training on matrix reasoning.

- The color-word Stroop effect driven by working memory maintenance.

- Revisiting congruency effects in the working memory Stroop task.

- Psychophysiological investigation of vigilance decrement: boredom or cognitive fatigue?

- Computational modeling of the n-back task in the ABCD study: associations of drift diffusion model parameters to polygenic scores of mental disorders and cardiometabolic diseases.

- Normative data on the n-back task for children and young adolescents.

- N-back training and transfer effects revealed by behavioral responses and EEG.

- Mental workload of young and older adults gauged with ERPs and spectral power during N-Back task performance.

- Dissociation in human prefrontal cortex of affective influences on working memory-related activity.

- Task-dependent representations of stimulus and choice in mouse parietal cortex.

- Using theta and alpha band power to assess cognitive workload in multitasking environments.

- When working memory is in a mood: combined effects of induced affect and processing of emotional words.

- The effect of self-regulation empowerment program training on neurocognitive and social skills in students with dyscalculia.

- Working memory maintenance contributes to long-term memory formation: neural and behavioral evidence.

- Complex span and n-back measures of working memory: a meta-analysis.

- Working memory capacity and go/no-go task performance: selective effects of updating, maintenance, and inhibition.

- No evidence of intelligence improvement after working memory training: a randomized, placebo-controlled study.

- Neural signatures for the n-back task with different loads: an event-related potential study.

- How does it STAC up? Revisiting the scaffolding theory of aging and cognition.

- How does allocation of emotional stimuli impact working memory tasks? an overview.

- Adaptive working memory training does not produce transfer effects in cognition and neuroimaging.

- Differential dorsolateral prefrontal cortex activation during a verbal n-back task according to sensory modality.

- The impact of working memory training in young people with social, emotional and behavioural difficulties.

- Mental fatigue and working memory load estimation: interaction and implications for EEG-based passive BCI

- Dual n-back training improves functional connectivity of the right inferior frontal gyrus at rest.

- Age-specific differences of dual n-back training.

- Transfer after dual n-back training depends on striatal activation change.

- Increased integrity of white matter pathways after dual n-back training.

- The development of non-spatial working memory capacity during childhood and adolescence and the role of interference control: an N-Back task study.

- Separating intra-modal and across-modal training effects in visual working memory: an fMRI Investigation.

- The impact of auditory working memory training on the fronto-parietal working memory network.

- PET evidence for an amodal verbal working memory system.

- Emotional working memory capacity in posttraumatic stress disorder (PTSD).

- Training the emotional brain: improving affective control through emotional working memory training.

- Extending brain-training to the affective domain: increasing cognitive and affective executive control through emotional working memory training.

- Boosting working memory: uncovering the differential effects of tDCS and tACS.

- N-Back related ERPs depend on stimulus type, task structure, pre-processing, and lab factors.

- Individual differences in delay discounting: relation to intelligence, working memory, and anterior prefrontal cortex.

- Is working memory training effective?

- The effect of cognitive fatigue on prefrontal cortex correlates of neuromuscular fatigue in older women.

- Functional MRI Correlates of Stroop N-Back test underpin the diagnosis of major depression.

- Popular interventions to enhance sustained attention in children and adolescents: a critical systematic review.

- Why do high working memory individuals choke? An examination of choking under pressure effects in math from a self-improvement perspective.

- Neuroimaging analyses of human working memory.

- Inhibitory processing during the Go/NoGo task: an ERP analysis of children with attention-deficit/hyperactivity disorder.

- Comparing the effects of three cognitive tasks on indicators of mental fatigue.

- Working memory training revisited: a multi-level meta-analysis of n-back training studies.

- Is training with the n-back task more effective than with other tasks? N-back vs. dichotic listening vs. simple listening.

- Personality traits modulate the impact of emotional stimuli during a working memory task: a near-infrared spectroscopy study.

- The influence of dual n-back training on fluid intelligence, working memory, and short-term memory in teenagers.

- Failure of working memory training to enhance cognition or intelligence.

- Involvement of the cerebellar cortex and nuclei in verbal and visuospatial working memory: a 7T fMRI study.

- Assessing the driver’s current level of working memory load with high density functional near-infrared spectroscopy: a realistic driving simulator study.

- Rehabilitation of the central executive of working memory after severe traumatic brain injury: two single-case studies.

- Modularity in rehabilitation of working memory: a single-case study.

- Ageing and switching of the focus of attention in working memory: results from a modified n-back task.

- Attentional control of emotional interference in children with ADHD and typically developing children: an emotional N-back study.

- A meta-analysis of the n-back task while driving and its effects on cognitive workload.

- Neuroimaging studies of working memory.

- A coordinate-based meta-analysis of the n-back working memory paradigm using activation likelihood estimation.

- Using wireless EEG signals to assess memory workload in the n-back task.

- An ERP investigation of the working memory stroop effect.

- Compared to outcome pressure, observation pressure produces differences in performance of N-back tasks: an ERP study.

- Examining the relationship between free recall and immediate serial recall: the effects of list length and output order.

- Variations in cognitive abilities across the life course: cross-sectional evidence from Understanding Society: the UK Household Longitudinal Study.

- Cognitive fatigue in individuals with traumatic brain injury is associated with caudate activation.

- BrainNet Viewer: a network visualization tool for human brain connectomics.

- The effect of multiple factors on working memory capacities: aging, task difficulty, and training.

- E-Key: an EEG-based biometric authentication and driving fatigue detection system.

- Working memory in junior high school students with reading difficulties: results from an n-back task.

- Meta-analyses of the n-back working memory task: fMRI evidence of age-related changes in prefrontal cortex involvement across the adult lifespan.

- N-back working memory task: meta-analysis of normative fMRI studies with children.

- Phase coherence of auditory steady-state response reflects the amount of cognitive workload in a modified N-back task.

- Working memory capacity as a moderator of load-related frontal midline theta variability in Sternberg task.

- Estimates of driver mental workload: A long-term field trial of two subsidiary tasks

- Volleyball training improves working memory in children aged 7 to 12 years old: an fNIRS study.

- The effects of offline and online prefrontal vs parietal transcranial direct current stimulation (tDCS) on verbal and spatial working memory.
