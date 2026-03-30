---
name: b1-morning-scanner
description: >
  A股早盘竞价评分系统。触发条件：用户说"竞价评分"、"开盘诊断"、"今日持仓怎么样"、
  "帮我打分"、"有什么好的股票"。功能：(1)读取持仓配置 (2)调用行情API获取竞价数据 
  (3)B1超卖评分+竞价分+技术面+筹码四维打分 (4)输出持仓诊断+精选票池Top5+操作建议 (5)推送飞书。
  适用人群：短线交易者、没时间盯早盘的上班族、想系统化决策的投资者。
license: MIT
metadata:
  version: "1.0"
  category: productivity
  tags: [stock, A股, 量化, 竞价分析, T+0]
  sources:
    - https://github.com/MiniMax-AI/skills
---

# B1 Morning Scanner | 早盘竞价评分系统

## 产品简介

每日9:25集合竞价结束后，自动对持仓股+精选票池进行综合评分，输出持仓诊断 + 精选票池Top5 + 具体操作建议，推送至飞书。

**解决问题：** 每天9:25-9:30信息量太大来不及分析，B1 Morning Scanner在开盘前3分钟给出决策建议。

## 评分体系

| 维度 | 满分 | 评分逻辑 |
|------|:----:|------|
| B1超卖信号 | 25 | RSI<30/K<30/量能缩/20日低位 → 超卖共振加分 |
| 竞价分 | 20 | 高开≥2%→20分 / 平开→12分 / 低开≥2%→0分 |
| 技术面 | 10 | 均线多头排列 + 布林带超卖加分 |
| 筹码分布 | 10 | BB<20%=机构控盘信号 |

**综合评分：**
- 🟢 >=72分：强势，可买入
- 🟡 57-71分：中性，等回调
- ⚪/🔴 <57分：回避

## 使用方法

```
【B1竞价评分 · 持仓诊断】
请执行: cd /workspace && python3 scripts/bid_score.py
```

## 配置说明

### 1. 数据源配置
使用 codebuddy.cn 行情API（需注册获取Token）：
```
API_ENDPOINT = "https://www.codebuddy.cn/v2/tool/financedata"
```

### 2. 飞书Webhook配置
```
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID"
```

### 3. 持仓配置
编辑 `references/holdings_config.py`：
```python
HOLD_STOCKS = {
    "300442": ("润泽科技", 89.92, 4800),
    "600096": ("云天化", 35.30, 0),
}
```

## 盘中调仓后

盘中换仓后**立即更新** `references/holdings_config.py`，下一个推送自动使用新持仓。

## OpenClaw定时任务（可选）
```bash
openclaw cron add --name "B1竞价评分" --cron "25 9 * * 1-5" \
  --session isolated --announce --channel feishu \
  --to "user:USER_OPEN_ID" \
  --message "【B1竞价评分】请执行: cd /workspace && python3 scripts/bid_score.py"
```
