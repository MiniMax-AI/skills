# MiniMax Agent Skills 投递指南

## 投递内容

| Skill | 名称 | 说明 |
|-------|------|------|
| b1-morning-scanner | 早盘竞价评分系统 | 每日9:25自动评分+飞书推送 |
| t0-pulse-monitor | T+0盘中脉冲监控系统 | 4节点自动推送持仓诊断 |

## 投递步骤

### 1. Fork 仓库
访问 https://github.com/MiniMax-AI/skills ，点击 Fork

### 2. 创建目录并添加文件
```bash
# 克隆你的fork
git clone https://github.com/YOUR_USERNAME/skills
cd skills

# 创建目录
mkdir -p skills/b1-morning-scanner
mkdir -p skills/t0-pulse-monitor

# 复制文件（从本仓库对应目录）
cp b1-morning-scanner/SKILL.md skills/b1-morning-scanner/
cp t0-pulse-monitor/SKILL.md skills/t0-pulse-monitor/
```

### 3. 更新 README
在 `README.md` 和 `README_zh.md` 的 Skills 列表中添加：

**README.md:**
```markdown
| b1-morning-scanner | A股早盘竞价评分系统，每日9:25自动评分+飞书推送 | Community | MIT |
| t0-pulse-monitor | A股T+0盘中监控系统，4节点自动推送持仓诊断 | Community | MIT |
```

**README_zh.md:**
```markdown
| b1-morning-scanner | A股早盘竞价评分系统，每日9:25自动评分+飞书推送 | Community | MIT |
| t0-pulse-monitor | A股T+0盘中脉冲监控系统，4节点自动推送持仓诊断 | Community | MIT |
```

### 4. 提交 PR
```bash
git add .
git commit -m "feat(b1-morning-scanner t0-pulse-monitor): add A股交易辅助工具"
git push origin main
```
然后在 GitHub 上创建 Pull Request

## PR 标题参考
```
feat(b1-morning-scanner): add A股早盘竞价评分系统
feat(t0-pulse-monitor): add A股T+0盘中脉冲监控系统
```

## 产品说明

### B1 Morning Scanner | 早盘竞价评分系统
**解决问题：** 每天9:25-9:30信息量太大来不及分析，开盘前3分钟给出决策建议
**功能：** B1超卖×竞价分×技术面×筹码四维打分，输出持仓诊断+精选票池Top5+操作建议
**适用：** 短线交易者、没时间盯早盘的上班族

### T0 Pulse Monitor | T+0盘中脉冲监控系统
**解决问题：** 持仓跌了不知道该不该卖、涨了不知道该不该加
**功能：** 4节点(10:00/11:00/13:30/14:30)自动推送持仓诊断+T信号
**适用：** 持仓过夜但白天无法盯盘的上班族
