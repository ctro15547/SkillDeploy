# requires: pydantic==2.5.0
"""
数据模型定义
使用 Pydantic 定义所有 API 的请求和响应模型
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DistributeMethod(str, Enum):
    """分发方式枚举"""
    AUTO = "auto"        # 自动检测（Mac/Linux用软链接，Windows用拷贝）
    SYMLINK = "symlink"  # 强制使用软链接
    COPY = "copy"        # 强制使用拷贝
    SMART = "smart"      # 智能检测（目录内软链接和拷贝混合存在）


class Tool(BaseModel):
    """工具模型"""
    id: str = Field(..., description="工具唯一标识")
    name: str = Field(..., description="工具名称")
    skills_dir: str = Field(..., description="工具的技能目录路径")
    enabled: bool = Field(default=True, description="是否启用")
    distribute_method: DistributeMethod = Field(
        default=DistributeMethod.COPY,
        description="分发方式"
    )
    # 新增：Agent 文件路径，可选，向后兼容旧配置
    agent_path: Optional[str] = Field(default=None, description="工具的 AGENT.md 文件路径")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "tool_001",
                "name": "OpenCode",
                "skills_dir": "~/.config/opencode/skills",
                "enabled": True,
                "distribute_method": "copy",
                "agent_path": "~/.config/opencode/AGENT.md"
            }
        }


class Skill(BaseModel):
    """技能模型"""
    id: str = Field(..., description="技能唯一标识（相对路径，格式：分组名/技能名）")
    group: Optional[str] = Field(None, description="所属分组目录名，根级技能为空")
    name: str = Field(..., description="技能名称")
    description: Optional[str] = Field(None, description="技能描述")
    path: str = Field(..., description="技能在总库中的完整路径")
    files: List[str] = Field(default_factory=list, description="技能包含的文件列表")
    size: int = Field(default=0, description="技能大小（字节）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "git-master",
                "name": "Git Master",
                "description": "Git 操作专家技能",
                "path": "/path/to/skills-library/git-master",
                "files": ["skill.md", "examples.md"],
                "size": 10240
            }
        }


class Config(BaseModel):
    """全局配置模型"""
    master_skills_dir: str = Field(..., description="总技能库目录路径")
    tools: List[Tool] = Field(default_factory=list, description="工具列表")
    # 新增：Agent 库目录路径，缺失时默认 "agent-library"
    agent_library_dir: Optional[str] = Field(default=None, description="Agent 库目录路径")

    class Config:
        json_schema_extra = {
            "example": {
                "master_skills_dir": "技能管理工具/skills-library",
                "agent_library_dir": "agent-library",
                "tools": []
            }
        }


class DistributeRequest(BaseModel):
    """分发请求模型"""
    tool_ids: List[str] = Field(..., description="要分发到的工具ID列表")
    skill_ids: List[str] = Field(..., description="要分发的技能ID列表")
    force: bool = Field(default=False, description="是否强制覆盖已存在的文件")
    distribute_method: Optional[DistributeMethod] = Field(
        default=None,
        description="前端指定的分发方式，为空则使用工具自身配置"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool_ids": ["tool_001", "tool_002"],
                "skill_ids": ["git-master", "frontend-ui-ux"],
                "force": False,
                "distribute_method": "copy"
            }
        }


class CleanupRequest(BaseModel):
    """清理请求模型"""
    tool_ids: Optional[List[str]] = Field(
        None,
        description="要清理的工具ID列表，为空则清理所有工具"
    )
    remove_broken_symlinks: bool = Field(
        default=True,
        description="是否清理失效的软链接"
    )
    remove_unused_files: bool = Field(
        default=True,
        description="是否清理未在配置中的技能文件"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool_ids": ["tool_001"],
                "remove_broken_symlinks": True,
                "remove_unused_files": True
            }
        }


class PreviewRequest(BaseModel):
    """预览请求模型"""
    tool_ids: List[str] = Field(..., description="要预览的工具ID列表")
    skill_ids: List[str] = Field(..., description="要预览的技能ID列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool_ids": ["tool_001"],
                "skill_ids": ["git-master"]
            }
        }


class OperationResult(BaseModel):
    """操作结果模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作结果消息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "分发完成",
                "details": {
                    "distributed": 2,
                    "failed": 0,
                    "skipped": 0
                }
            }
        }


class PreviewAction(BaseModel):
    """预览操作模型"""
    action: str = Field(..., description="操作类型（create_symlink/copy_dir/skip）")
    source: str = Field(..., description="源路径")
    target: str = Field(..., description="目标路径")
    reason: Optional[str] = Field(None, description="操作原因或跳过原因")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "create_symlink",
                "source": "/path/to/skills-library/git-master",
                "target": "~/.config/opencode/skills/git-master",
                "reason": None
            }
        }


class PreviewResult(BaseModel):
    """预览结果模型"""
    actions: List[PreviewAction] = Field(..., description="将要执行的操作列表")
    total: int = Field(..., description="总操作数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "actions": [],
                "total": 0
            }
        }


# ==================== Agent 管理相关模型 ====================

class AgentFile(BaseModel):
    """Agent 库中的文件模型"""
    filename: str = Field(..., description="文件名，如 AGENT.md")
    path: str = Field(..., description="完整路径")
    size: int = Field(..., description="文件大小（字节）")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "AGENT.md",
                "path": "/path/to/agent-library/AGENT.md",
                "size": 2048
            }
        }


class AgentStatus(BaseModel):
    """工具的 Agent 文件状态模型"""
    tool_id: str = Field(..., description="工具 ID")
    tool_name: str = Field(..., description="工具名称")
    agent_path: str = Field(..., description="Agent 文件目标路径")
    exists: bool = Field(..., description="文件是否存在")
    is_symlink: bool = Field(..., description="是否为软链接")
    symlink_target: Optional[str] = Field(default=None, description="软链接指向的源路径")
    file_size: Optional[int] = Field(default=None, description="文件大小（字节）")
    modified_time: Optional[str] = Field(default=None, description="最后修改时间（ISO 格式）")

    class Config:
        json_schema_extra = {
            "example": {
                "tool_id": "claude",
                "tool_name": "Claude",
                "agent_path": "~/.claude/AGENT.md",
                "exists": True,
                "is_symlink": True,
                "symlink_target": "/path/to/agent-library/AGENT.md",
                "file_size": 2048,
                "modified_time": "2024-01-01T00:00:00"
            }
        }


class AgentDistributeRequest(BaseModel):
    """Agent 分发请求模型"""
    tool_ids: List[str] = Field(..., description="目标工具 ID 列表")
    agent_filename: str = Field(..., description="Agent 库中的文件名")
    # 默认使用拷贝，与 Skills 分发保持一致
    distribute_method: DistributeMethod = Field(
        default=DistributeMethod.COPY,
        description="分发方式"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tool_ids": ["claude", "kiro"],
                "agent_filename": "AGENT.md",
                "distribute_method": "copy"
            }
        }
