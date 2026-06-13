"""导出API路由 - 导出分析结果、报告、对话记录为Word文档"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from io import BytesIO

from services.export_service import export_analysis_to_word, export_report_to_word, export_chat_to_word

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/export", tags=["导出"])


class ExportAnalysisRequest(BaseModel):
    """导出分析结果请求"""
    symbol: str
    company_name: Optional[str] = ""
    current_price: Optional[float] = None
    recommendation: Optional[Dict[str, Any]] = None
    agent_results: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None


class ExportReportRequest(BaseModel):
    """导出报告请求"""
    report_id: Optional[str] = None
    title: Optional[str] = ""
    report_type: Optional[str] = ""
    content: Optional[str] = ""
    summary: Optional[str] = ""
    symbols: Optional[List[str]] = None
    generated_at: Optional[str] = None
    key_findings: Optional[List[str]] = None
    risk_factors: Optional[List[str]] = None


class ExportChatRequest(BaseModel):
    """导出对话记录请求"""
    messages: List[Dict[str, Any]]


def _make_word_response(doc_bytes: bytes, filename: str) -> StreamingResponse:
    """构造Word文档下载响应"""
    return StreamingResponse(
        BytesIO(doc_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
        }
    )


@router.post("/analysis", summary="导出分析结果为Word")
async def export_analysis(request: ExportAnalysisRequest):
    """将股票分析结果导出为Word文档"""
    try:
        analysis_data = request.model_dump()
        doc_bytes = export_analysis_to_word(analysis_data)
        symbol = request.symbol or "analysis"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_分析报告_{timestamp}.docx"
        return _make_word_response(doc_bytes, filename)
    except Exception as e:
        logger.error(f"导出分析结果失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/report", summary="导出报告为Word")
async def export_report(request: ExportReportRequest):
    """将金融报告导出为Word文档"""
    try:
        report_data = request.model_dump()
        # 如果提供了report_id，从数据库获取完整数据
        if request.report_id:
            from services.database_service import db_service
            reports = await db_service.get_reports(limit=100)
            for r in reports:
                if r.get("report_id") == request.report_id:
                    report_data.update(r)
                    break
        doc_bytes = export_report_to_word(report_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_type = request.report_type or "report"
        filename = f"{report_type}_报告_{timestamp}.docx"
        return _make_word_response(doc_bytes, filename)
    except Exception as e:
        logger.error(f"导出报告失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/chat", summary="导出对话记录为Word")
async def export_chat(request: ExportChatRequest):
    """将对话记录导出为Word文档"""
    try:
        messages = request.messages
        if not messages:
            raise HTTPException(status_code=400, detail="对话记录为空")
        doc_bytes = export_chat_to_word(messages)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"对话记录_{timestamp}.docx"
        return _make_word_response(doc_bytes, filename)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出对话记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
