---
name: ai-singing
description: 用纯 CPU、离线模型给中文歌词做"真唱"人声 + 伴奏 + 抖音竖屏歌词 MV，并用客观指标自动迭代。凡是"做歌/唱出来/AI 唱歌/MV/抖音 30 秒版/优化人声/太塑料/像念的"等请求都用本技能。
---

# AI 唱歌流水线（自迭代版）

## 引擎（按音质排序）
1. **DiffSinger · 绮萱 v2.7.0**（女声，真唱训练）— `scripts/ds.py`。首选。
   - 声库：`https://github.com/yqzhishen/qixuan-diffsinger/releases/download/v2.7.0/Qixuan_v2.7.0_DiffSinger_OpenUtau.zip`
   - 声码器：`https://github.com/openvpi/vocoders/releases/download/pc-nsf-hifigan-44.1k-hop512-128bin-2025.02/pc_nsf_hifigan_44.1k_hop512_128bin_2025.02.oudep`（zip）
   - 下载会被代理中断：`curl -L -C -` 循环续传。
   - **合规**：发布时必须标注"AI 合成"+"绮萱"+"DiffSinger"；声码器 CC BY-NC-SA 4.0 → 仅限非商用。
2. **Kokoro 改造成歌手**（男声 zm_yunxi）— `kgraph.py` 改 ONNX 图把时长/F0/能量变成输入，`singk.py` 渲染。
   - 坑：长元音会衰减（InstanceNorm）→ 句子前后垫长"载体句"再剪掉 + 长音电平补偿；高音短字偶发跳八度 → 每句 3 take 选最准。
3. WORLD 重合成（`sing.py`，已淘汰，仅作对照）。

## 流程
1. `score.py` 写旋律（逐字：拍位、时值、音高、重音）。不要随机生成旋律。
2. 渲染人声 → `evalv.py` 打分（harvest 音高；中位/p90 音分误差、发声覆盖率、起音延迟、音高图 PNG，读图检查）。
3. `arrange.py`（FluidSynth + FluidR3_GM，apt 装 `fluidsynth fluid-soundfont-gm`）→ `mix.py`（-14 LUFS，人声 1–4kHz 高于伴奏 7–9 dB）。
4. `video.py` 1080×1920 逐字卡拉 OK、drop 闪白、台阶进度。需要 `fonts-noto-cjk`。
5. 每轮记录指标，跟上一版比；只改最差的一项。

## 验收线
pitch 中位 ≤8c、p90 ≤25c、>50c 的音 ≤1；覆盖率 ≥0.95；LUFS -14±0.5；峰值 ≤ -1 dBFS。

## 耳朵（`scripts/ears.py`，已装，不依赖 HuggingFace）
- **SenseVoice ASR**（sherpa-onnx，模型在 GitHub releases：`https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2`，放 `../models/`）：逐句歌词识别 → CER，报出"被听成了什么"。
- **DNSMOS**（`pip install speechmos librosa`，模型随 wheel 附带）：只对**干声**有意义；对整首混音会把音乐当噪声，分数无参考价值。
- 实测：v3 Kokoro 男声可懂度 36% → DiffSinger 绮萱 82–84%。

## 自迭代经验（耳朵发现的问题 → 改法）
- **倒字**是中文歌听不清的头号原因：旋律走向和声调相反就会被听成别的字（闪亮→善良、向上→享受）。
  改法：去声字(4)用"高起下落"（score 里 fall=2 半音的落音），上声字(3)放低音，句尾 4 声字不要往上跳。
- **编曲遮字**：铜管/弦乐不能压在长音的尾韵(-ng/-n)上，否则"上"被听成"山"、"向上"被听成"潇洒"。应答放在字唱完之后。
- ASR 逐句窗口会串进邻句的字，要同时看整首 CER；重复的副歌 ASR 会合并，CER 偏高，只作相对比较。
- 同一参数不同 seed 的 take 之间 CER 差 ±0.05 属于噪声：每轮渲 3 个 take，用"音高误差 + 混音 CER"选。
