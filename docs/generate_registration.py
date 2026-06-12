# -*- coding: utf-8 -*-
"""生成 AFAC2026 报名信息表 Word 文档（完整版）"""

import os
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

DARK_BLUE = RGBColor(0x1A, 0x3C, 0x6E)
ACCENT_BLUE = RGBColor(0x2B, 0x5C, 0x9E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT_NAME = "微软雅黑"
LIGHT_BG = "E8F0FE"

OUTPUT_PATH = r"D:\AFAC2026金融智能创新大赛\FinAgent-Pro\docs\AFAC2026报名信息表.docx"


def set_cell_shading(cell, color_hex):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_run_font(run, size=Pt(10.5), bold=False, color=None, font_name=FONT_NAME):
    run.font.size = size
    run.bold = bold
    if color:
        run.font.color.rgb = color
    run.font.name = font_name
    r = run._element
    rPr = r.find(qn("w:rPr"))
    if rPr is None:
        rPr = parse_xml(f'<w:rPr {nsdecls("w")}/>')
        r.insert(0, rPr)
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:eastAsia"), font_name)


def add_styled_paragraph(doc, text, size=Pt(10.5), bold=False, color=None,
                         alignment=WD_ALIGN_PARAGRAPH.LEFT, space_after=Pt(6),
                         space_before=Pt(0), font_name=FONT_NAME):
    p = doc.add_paragraph()
    p.alignment = alignment
    p.paragraph_format.space_after = space_after
    p.paragraph_format.space_before = space_before
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, color=color, font_name=font_name)
    return p


def add_section_title(doc, text):
    p = add_styled_paragraph(doc, text, size=Pt(16), bold=True, color=DARK_BLUE,
                             space_before=Pt(18), space_after=Pt(10))
    pPr = p._element.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'  <w:bottom w:val="single" w:sz="8" w:space="4" w:color="1A3C6E"/>'
        f'</w:pBdr>'
    )
    pPr.append(pBdr)
    return p


def add_rich_text_paragraph(doc, text, size=Pt(10.5), first_line_indent=Cm(0.74)):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = first_line_indent
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = Pt(20)
    run = p.add_run(text)
    set_run_font(run, size=size)
    return p


def add_kv_table(doc, rows, key_width=Cm(4), val_width=Cm(12)):
    """添加键值对表格"""
    table = doc.add_table(rows=len(rows), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    for i, (key, val) in enumerate(rows):
        cell_key = table.rows[i].cells[0]
        cell_key.text = ""
        p = cell_key.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(key)
        set_run_font(run, size=Pt(11), bold=True, color=WHITE)
        set_cell_shading(cell_key, "1A3C6E")
        cell_key.width = key_width

        cell_val = table.rows[i].cells[1]
        cell_val.text = ""
        p = cell_val.paragraphs[0]
        run = p.add_run(str(val))
        set_run_font(run, size=Pt(10.5))
        if i % 2 == 1:
            set_cell_shading(cell_val, "EDF2F9")
        cell_val.width = val_width

    return table


def add_list_table(doc, headers, rows, col_widths=None):
    """添加列表表格"""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        set_run_font(run, size=Pt(11), bold=True, color=WHITE)
        set_cell_shading(cell, "1A3C6E")

    for r_idx, row_data in enumerate(rows):
        for c_idx, val in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx == 0 else WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(str(val))
            set_run_font(run, size=Pt(10.5), bold=(c_idx == 0))
            if r_idx % 2 == 1:
                set_cell_shading(cell, "EDF2F9")

    if col_widths:
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = w

    return table


def add_tag_paragraph(doc, tags, label=None):
    """添加标签式段落"""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    if label:
        run = p.add_run(label)
        set_run_font(run, size=Pt(11), bold=True, color=DARK_BLUE)
    for tag in tags:
        run = p.add_run(f"  [{tag}]  ")
        set_run_font(run, size=Pt(10.5), bold=True, color=ACCENT_BLUE)


def main():
    doc = Document()

    # 全局默认字体
    style = doc.styles["Normal"]
    style.font.name = FONT_NAME
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT_NAME)

    # 页面设置
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)

    # 页眉
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hr = hp.add_run("AFAC2026金融智能创新大赛  报名信息表")
    set_run_font(hr, size=Pt(9), color=DARK_BLUE)
    pPr = hp._element.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'  <w:bottom w:val="single" w:sz="4" w:space="1" w:color="1A3C6E"/>'
        f'</w:pBdr>'
    )
    pPr.append(pBdr)

    # 页脚（页码）
    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fldChar1 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
    fp._element.append(fldChar1)
    instrText = parse_xml(f'<w:instrText {nsdecls("w")} xml:space="preserve"> PAGE </w:instrText>')
    fp._element.append(instrText)
    fldChar2 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
    fp._element.append(fldChar2)

    # ══════════════════════════════════════════════════════
    # 封面页
    # ══════════════════════════════════════════════════════

    p_line = doc.add_paragraph()
    p_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_line.paragraph_format.space_before = Pt(80)
    run_line = p_line.add_run("━" * 30)
    set_run_font(run_line, size=Pt(14), color=DARK_BLUE)

    add_styled_paragraph(doc, "AFAC2026", size=Pt(36), bold=True, color=DARK_BLUE,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(30), space_after=Pt(4))
    add_styled_paragraph(doc, "金融智能创新大赛", size=Pt(28), bold=True, color=DARK_BLUE,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(20))

    add_styled_paragraph(doc, "初创组", size=Pt(22), bold=True, color=DARK_BLUE,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(30))

    p_line2 = doc.add_paragraph()
    p_line2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_line2 = p_line2.add_run("━" * 30)
    set_run_font(run_line2, size=Pt(14), color=DARK_BLUE)

    add_styled_paragraph(doc, "报 名 信 息 表", size=Pt(26), bold=True, color=DARK_BLUE,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, space_before=Pt(40), space_after=Pt(60))

    add_styled_paragraph(doc, "团队名称：智融先锋", size=Pt(14), color=DARK_BLUE,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(8))
    add_styled_paragraph(doc, "项目名称：FinAgent Pro 金融自主智能体平台", size=Pt(14), color=DARK_BLUE,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(8))
    add_styled_paragraph(doc, "负责人：冯亦根", size=Pt(14), color=DARK_BLUE,
                         alignment=WD_ALIGN_PARAGRAPH.CENTER, space_after=Pt(60))

    add_styled_paragraph(doc, "2026年6月", size=Pt(12), color=RGBColor(0x66, 0x66, 0x66),
                         alignment=WD_ALIGN_PARAGRAPH.CENTER)

    doc.add_page_break()

    # ══════════════════════════════════════════════════════
    # 一、基本信息
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "一、基本信息")

    add_kv_table(doc, [
        ("赛道", "初创组"),
        ("方向", "前沿技术 - 自主智能体（Agentic AI）"),
        ("项目名称", "FinAgent Pro 金融自主智能体平台"),
        ("团队名称", "智融先锋"),
        ("负责人", "冯亦根"),
        ("学历", "本科（浙江大学 计算机通信工程）"),
        ("单位名称", "个人独立创业"),
        ("团队模式", "OPC一人团队"),
        ("GitHub", "https://github.com/yigenfeng0707-netizen/finagent-pro-afac2026"),
    ])

    doc.add_paragraph()

    # ══════════════════════════════════════════════════════
    # 二、项目简介（500字内）
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "二、项目简介（500字内）")

    add_rich_text_paragraph(doc,
        'FinAgent Pro解决金融行业三大核心痛点：'
        '一是分析师过劳，日均仅覆盖3-5只标的，研报撰写耗时4-6小时；'
        '二是风控滞后，80%风险事件事后才发现；'
        '三是现有AI工具被动响应，需人工提问才工作，无法主动发现机会和风险。')

    add_rich_text_paragraph(doc,
        '目标客户覆盖四类：'
        '券商研究所（研报撰写、标的跟踪）、'
        '基金公司（组合监控、风险预警）、'
        '银行理财（产品分析、合规审查）、'
        '个人投资者（智能投顾、市场解读）。')

    add_rich_text_paragraph(doc,
        '核心创新点：'
        '（1）ReAct推理引擎——每个智能体具备"思考→行动→观察"循环，真正自主推理；'
        '（2）持久记忆系统——工作记忆+情节记忆+语义记忆三层架构，让数字员工"记住"上下文和历史经验；'
        '（3）主动智能——定时巡检+事件驱动+阈值预警，推动金融服务从被动响应迈向主动智能；'
        '（4）合规内嵌——内置银保监会/证监会监管规则引擎，每步操作可审计可追溯；'
        '（5）多智能体协商——6大专业智能体（市场分析/新闻舆情/风控合规/'
        '投资策略/报告生成/执行监控）协同工作，加权协商生成最终建议；'
        '（6）思维链可视化——实时展示AI推理过程，让决策"看得见"。'
        '以国产大模型为基座，数据不出境，安全可信。')

    # ══════════════════════════════════════════════════════
    # 三、团队简介（200字内）
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "三、团队简介（200字内）")

    add_rich_text_paragraph(doc,
        '智融先锋由浙江大学计算机通信工程专业本科生冯亦根独立创立，'
        '是一支聚焦金融自主智能体（Agentic AI）的OPC一人团队。'
        '冯亦根兼具AI与通信工程复合背景，'
        '独立完成FinAgent Pro金融智能体平台从架构设计到全栈开发的全流程'
        '——涵盖ReAct推理引擎、三层记忆系统、6大专业'
        '智能体协同调度、合规规则引擎及Vue3前端，'
        '以一人之力构建了完整的金融数字员工系统。'
        '团队坚持"技术创新+合规内嵌"双轮驱动，'
        '以国产大模型为基座，打造安全可信的金融智能体平台，推动'
        '金融服务从被动响应迈向主动智能。'
        '一个人，一支队，以一当十。')

    # ══════════════════════════════════════════════════════
    # 四、目标客户群体（多选）
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "四、目标客户群体（多选）")

    add_tag_paragraph(doc, ["银行", "证券公司", "基金公司", "个人投资者"], label="已选：")

    add_rich_text_paragraph(doc,
        '银行：财富管理部、资产管理部需要智能投研和合规审计；'
        '证券公司：最直接客户，需要市场分析、交易信号、风控合规；'
        '基金公司：组合分析、风险评估、投资策略生成；'
        '个人投资者：C端产品方向，降低专业投资门槛。')

    # ══════════════════════════════════════════════════════
    # 五、预计市场规模（年）
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "五、预计市场规模（年）")

    add_tag_paragraph(doc, [">10亿元"], label="已选：")

    add_rich_text_paragraph(doc,
        '中国AI+金融市场2026年预计超千亿规模，金融自主智能体是核心增长赛道。'
        'B端：100+证券公司×100-500万/年 + 150+基金公司×100-300万/年 + 数千家银行财富管理部×50-200万/年，仅B端就超10亿。'
        'C端：数千万A股个人投资者，订阅制/SaaS模式潜力巨大。')

    # ══════════════════════════════════════════════════════
    # 六、主要收入模式（多选）
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "六、主要收入模式（多选）")

    add_tag_paragraph(doc, ["软件订阅", "技术服务费", "数据服务"], label="已选：")

    add_rich_text_paragraph(doc,
        '软件订阅：核心模式，SaaS按年/按席位收费，B端稳定现金流，C端会员订阅；'
        '技术服务费：金融机构定制化部署、私有化适配、系统集成，单项目几十万起；'
        '数据服务：智能体产出的投研报告、风控数据、舆情指标作为数据产品出售。')

    # ══════════════════════════════════════════════════════
    # 七、项目解决的主要痛点（多选）
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "七、项目解决的主要痛点（多选）")

    add_tag_paragraph(doc, ["信息孤岛", "合规风险", "效率低下", "决策黑盒"], label="已选：")

    add_rich_text_paragraph(doc,
        '信息孤岛：市场数据、新闻舆情、风控合规分散在不同系统，FinAgent Pro通过6大智能体协同打通信息壁垒；'
        '合规风险：AI决策过程不透明，难以满足监管审计要求，合规规则引擎确保每步可追溯；'
        '效率低下：分析师日均仅覆盖3-5只标的，数字员工7×24小时全市场扫描；'
        '决策黑盒：思维链可视化让AI推理过程实时可见，黑盒变白盒。')

    # ══════════════════════════════════════════════════════
    # 八、最大优势（多选）
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "八、与现有解决方案相比最大优势（多选）")

    add_tag_paragraph(doc, ["技术创新", "合规内嵌", "主动智能", "国产自主"], label="已选：")

    add_rich_text_paragraph(doc,
        '技术创新：ReAct推理引擎+三层记忆+多智能体协商，三层架构是技术护城河；'
        '合规内嵌：规则引擎+审计中间件，金融机构采购的硬性准入壁垒；'
        '主动智能：定时巡检+事件驱动+阈值预警，从被动响应到主动服务的体验壁垒；'
        '国产自主：GLM-5.1/DeepSeek/SenseNova国产大模型基座，数据不出境，安全可信。')

    # ══════════════════════════════════════════════════════
    # 九、市场竞争分析
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "九、市场竞争分析")

    add_rich_text_paragraph(doc,
        '当前金融智能体市场主要有三类竞争者：')

    # 竞争对比表
    add_list_table(doc,
        ["竞争者", "优势", "劣势", "FinAgent Pro差异化"],
        [
            ("传统金融终端\n(同花顺/Wind)", "数据覆盖广\n用户基数大", "被动工具\nAI能力薄弱", "主动智能体替代被动工具\n从人找数据到数据找人"),
            ("通用AI平台\n(文心/通义/GLM)", "大模型能力强\n算力资源丰富", "缺乏金融垂直深度\n无合规引擎", "金融垂直深度定制\n6智能体协同+合规内嵌"),
            ("海外金融AI\n(Bloomberg GPT)", "技术成熟\n海外验证", "不支持A股\n数据出境风险", "国产基座+A股数据\n中文NLP+合规引擎"),
        ],
        col_widths=[Cm(3), Cm(3.5), Cm(3.5), Cm(5)])

    doc.add_paragraph()

    add_rich_text_paragraph(doc,
        'FinAgent Pro的核心竞争壁垒：'
        '（1）技术护城河：三层架构（智能体引擎+协同调度+主动智能），竞品仅做到单层；'
        '（2）准入壁垒：合规内嵌是金融机构采购的硬性要求；'
        '（3）体验壁垒：主动智能让用户一旦习惯就难以回到被动模式。')

    # ══════════════════════════════════════════════════════
    # 十、核心技术与创新
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "十、核心技术与创新")

    add_list_table(doc,
        ["技术领域", "核心技术", "关键能力"],
        [
            ("大语言模型", "ReAct推理引擎", "Thought-Action-Observation自主推理循环"),
            ("多智能体协同", "Master Orchestrator", "三阶段流水线+加权协商+LLM增强推理"),
            ("记忆系统", "三层记忆架构", "工作记忆+情节记忆+语义记忆"),
            ("主动智能", "APScheduler+WebSocket", "定时巡检+事件驱动+阈值预警"),
            ("合规引擎", "规则引擎+审计中间件", "四维风控+合规约束+全链路审计"),
            ("金融计算", "AKShare+ta-lib", "A股行情+技术指标+VaR风险计算"),
            ("工程架构", "FastAPI+Vue3+Docker", "异步API+暗色主题+容器化部署"),
        ],
        col_widths=[Cm(3), Cm(4.5), Cm(8)])

    doc.add_paragraph()

    # ══════════════════════════════════════════════════════
    # 十一、参赛期望（多选）
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "十一、参赛期望（多选）")

    add_tag_paragraph(doc, ["行业认可", "投资机会", "业务合作", "专家指导"], label="已选：")

    add_rich_text_paragraph(doc,
        '行业认可：AFAC是蚂蚁集团主办，获奖即获金融科技领域背书；'
        '投资机会：大赛对接蚂蚁战投、红杉等头部机构，是融资快车道；'
        '业务合作：蚂蚁生态内金融机构资源，B端客户对接效率高10倍；'
        '专家指导：蚂蚁技术专家1对1辅导，对产品打磨和商业模式优化价值极大。')

    # ══════════════════════════════════════════════════════
    # 十二、Demo材料清单
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "十二、项目Demo材料清单")

    add_list_table(doc,
        ["材料项", "类型", "文件/链接"],
        [
            ("a.可运行产品原型", "网页/App/小程序/文件",
             "GitHub: https://github.com/yigenfeng0707-netizen/finagent-pro-afac2026\n本地部署: 前端localhost:3000 + 后端localhost:8000"),
            ("b.3分钟功能演示视频", "视频格式/链接",
             "待录制（按DemoScript.md脚本操作录屏）"),
            ("c.高保真交互设计图/逻辑流程图", "图片/PDF/链接",
             "FinAgentPro交互设计与流程图.docx\n含4个页面原型+5个系统流程图"),
            ("d.MVP/POC实验数据", "文档/PDF/链接",
             "FinAgentPro_MVP_POC实验数据.docx\n含8项KPI+5项功能实验+性能基准"),
        ],
        col_widths=[Cm(4), Cm(3.5), Cm(8)])

    doc.add_paragraph()

    # ══════════════════════════════════════════════════════
    # 十三、提交制品清单
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "十三、提交制品清单")

    add_list_table(doc,
        ["序号", "材料名称", "文件名"],
        [
            ("1", "项目申报书", "FinAgentPro项目申报书.docx"),
            ("2", "商业计划书", "FinAgentPro商业计划书.docx"),
            ("3", "技术方案", "FinAgentPro技术方案.docx"),
            ("4", "路演PPT", "FinAgentPro路演PPT.pptx"),
            ("5", "用户手册", "FinAgentPro用户使用手册.docx"),
            ("6", "解决方案描述", "FinAgentPro解决方案描述.docx"),
            ("7", "市场竞争分析", "FinAgentPro市场竞争分析.docx"),
            ("8", "核心技术", "FinAgentPro核心技术.docx"),
            ("9", "交互设计与流程图", "FinAgentPro交互设计与流程图.docx"),
            ("10", "MVP/POC实验数据", "FinAgentPro_MVP_POC实验数据.docx"),
            ("11", "报名信息表", "AFAC2026报名信息表.docx"),
            ("12", "源代码", "GitHub仓库"),
        ],
        col_widths=[Cm(2), Cm(5), Cm(9)])

    doc.add_paragraph()

    # ══════════════════════════════════════════════════════
    # 十四、关键时间节点
    # ══════════════════════════════════════════════════════

    add_section_title(doc, "十四、关键时间节点")

    add_list_table(doc,
        ["时间", "事项"],
        [
            ("2026年6月", "报名通道开启"),
            ("2026年7月", "成果初选"),
            ("2026年8月中旬", "成果路演"),
            ("2026年9月", "上海Inclusion·外滩大会颁奖"),
        ],
        col_widths=[Cm(5), Cm(11)])

    # 保存
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    doc.save(OUTPUT_PATH)
    print(f"文档已生成: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
