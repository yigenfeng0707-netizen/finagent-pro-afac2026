# AFAC2026 提交材料包索引

> 更新日期：2026-06-30 · 截止提交：7 月 15 日

## 一、在线提交字段（复制粘贴用）

| 字段 | 内容 |
|------|------|
| 项目名称 | FinAgent Pro |
| 赛道 | 初创组 · 智能财富 / 前沿金融AI |
| 一句话 | 7×24 金融数字投研团队，6 智能体主动协同 + 合规内嵌 |
| Demo URL | `http://47.103.35.132/` · `http://yunliyuan.cn/`（部署后生效） |
| 代码仓库 | `https://github.com/yigenfeng0707-netizen/finagent-pro-afac2026` |
| 视频链接 | `[待填: 3min Demo 网盘]` |

## 二、文档清单（docs/）

| 文件 | 状态 | 用途 |
|------|------|------|
| BusinessPlan.md | ✅ | 商业计划书源文件 |
| TechnicalSpec.md | ✅ | 技术方案源文件 |
| PilotCaseStudy.md | ✅ | 试点案例 |
| PilotMOU_Template.md | ⚠️ 待签字 | 试用确认函 |
| ExecutiveSummary.md | ✅ | 一页纸 |
| JudgeFAQ.md | ✅ | 答辩 Q&A |
| PitchDeck_Slides.md | ✅ | 10 页 PPT 内容 |
| ChampionNarrative.md | ✅ | 叙事主线 |
| TeamOnePager.md | ⚠️ 待填姓名 | 团队信息 |
| SelfAssessment.md | ✅ | 自评 ~87 分 |
| SubmissionChecklist.md | ✅ | 总清单 |

## 三、Word 文档（已生成）

- `FinAgentPro_MVP_POC实验数据.docx`
- `FinAgentPro市场竞争分析.docx`
- `FinAgentPro技术方案与架构图.docx`
- `AFAC2026报名信息表.docx`

## 四、部署方案

| 方案 | 文档 | 适用 |
|------|------|------|
| 阿里云 ECS | `AliyunDeployGuide.md` | **决赛推荐** |
| Render + Vercel | `DeployGuide.md` | 初筛快速上线 |
| 本地录屏 | `LocalDemoGuide.md` | 视频录制 |

## 五、部署命令速查（阿里云）

```bash
cp .env.production.example .env
# 编辑 .env 填入 API Key
./deploy/aliyun/deploy.sh
```

## 六、提交前必做（人工）

- [ ] TeamOnePager 填真实姓名/邮箱/电话
- [ ] PilotMOU 试点方签字或邮件确认
- [ ] 阿里云 / Render 部署并填 Demo URL
- [ ] 录制 3 分钟视频（RecordingGuide.md）
- [ ] 网络稳定时重跑 Benchmark 30 股
- [ ] 7/15 前官方系统提交 + 截图

## 七、答辩核心数字

- 试点：晨报效率 ↑73%，合规 100%
- Benchmark：信号成功率 100%，合规通过率 100%
- 产品：6 智能体 + ReAct + 思维链可视化
