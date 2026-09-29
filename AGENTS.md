# FrontierNeuroscience agent 入口

先讀 README、STATUS、VALIDATION 與治理 9c3ae2dbaa1c814f3ef451c041dedfe3b77d926f。所有 agent 用 <agent>/NEURO-xxx-<topic> 分支，不直接 main、不自合。

每輪 start → 本輪 fresh search → 凍結 subject/session/stimulus split、主要假說與 evaluator → admit → baseline → exploration → verifier/skeptic → PR。

特別規則：subject/session leakage 必查；decoding≠representation≠causal use；觀察研究不能自動升格因果。不得自動設計侵入式刺激、醫療處置或個人神經資料收集。公開臨床資料只能做研究級、非診斷分析。
