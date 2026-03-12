# requires: fastapi==0.104.1
"""
API 路由模块
定义所有 RESTful API 端点
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from pathlib import Path

from models import (
    Config, Tool, Skill, OperationResult,
    DistributeRequest, CleanupRequest, PreviewRequest,
    PreviewResult, PreviewAction,
    AgentFile, AgentStatus, AgentDistributeRequest,
)
from config_manager import ConfigManager
from skill_manager import SkillManager
from file_operations import FileOperations
from agent_manager import AgentManager

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api", tags=["api"])

# 全局实例
config_manager = ConfigManager()


# ==================== 配置相关 ====================

@router.get("/config", response_model=Config)
async def get_config():
    """获取全局配置"""
    try:
        config = config_manager.get_config()
        return config
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}"
        )


@router.post("/config", response_model=Config)
async def update_config(config: Config):
    """更新全局配置"""
    try:
        # 验证总技能库目录
        master_dir = Path(config.master_skills_dir).expanduser()
        if not master_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"总技能库目录不存在: {config.master_skills_dir}"
            )
        
        # 保存配置
        config_manager.save(config)
        logger.info("配置已更新")
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新配置失败: {str(e)}"
        )


# ==================== 工具管理 ====================

@router.get("/tools", response_model=List[Tool])
async def get_tools():
    """获取所有工具列表"""
    try:
        config = config_manager.get_config()
        return config.tools
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具列表失败: {str(e)}"
        )


@router.post("/tools", response_model=Tool)
async def add_tool(tool: Tool):
    """添加新工具"""
    try:
        # 验证技能目录
        skills_dir = Path(tool.skills_dir).expanduser()
        if not skills_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"工具技能目录不存在: {tool.skills_dir}"
            )
        
        # 添加工具
        config_manager.add_tool(tool)
        logger.info(f"工具已添加: {tool.name}")
        return tool
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加工具失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加工具失败: {str(e)}"
        )


@router.put("/tools/{tool_id}", response_model=Tool)
async def update_tool(tool_id: str, tool: Tool):
    """更新工具配置"""
    try:
        # 验证技能目录
        skills_dir = Path(tool.skills_dir).expanduser()
        if not skills_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"工具技能目录不存在: {tool.skills_dir}"
            )
        
        # 更新工具
        config_manager.update_tool(tool_id, tool)
        logger.info(f"工具已更新: {tool.name}")
        return tool
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新工具失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新工具失败: {str(e)}"
        )


@router.delete("/tools/{tool_id}", response_model=OperationResult)
async def delete_tool(tool_id: str):
    """删除工具"""
    try:
        config_manager.delete_tool(tool_id)
        logger.info(f"工具已删除: {tool_id}")
        return OperationResult(
            success=True,
            message=f"工具已删除: {tool_id}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"删除工具失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除工具失败: {str(e)}"
        )


# ==================== 技能管理 ====================

@router.get("/skills", response_model=List[Skill])
async def get_skills():
    """获取所有技能列表"""
    try:
        config = config_manager.get_config()
        # 解析相对路径为绝对路径
        master_skills_path = config_manager.resolve_path(config.master_skills_dir)
        skill_manager = SkillManager(str(master_skills_path))
        skills = skill_manager.scan_master_skills()
        logger.info(f"扫描到 {len(skills)} 个技能")
        return skills
    except Exception as e:
        logger.error(f"获取技能列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取技能列表失败: {str(e)}"
        )


@router.get("/skills/{skill_id:path}", response_model=Skill)
async def get_skill(skill_id: str):
    """获取技能详情"""
    try:
        config = config_manager.get_config()
        # 解析相对路径为绝对路径
        master_skills_path = config_manager.resolve_path(config.master_skills_dir)
        skill_manager = SkillManager(str(master_skills_path))
        skill = skill_manager.get_skill_by_id(skill_id)

        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"技能不存在: {skill_id}"
            )

        return skill
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取技能详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取技能详情失败: {str(e)}"
        )


@router.delete("/tools/{tool_id}/skills/{skill_id}", response_model=OperationResult)
async def delete_tool_skill(tool_id: str, skill_id: str):
    """删除工具目录下的指定技能（支持软链接和普通目录）"""
    try:
        config = config_manager.get_config()
        tool = config_manager.get_tool(tool_id)

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在: {tool_id}"
            )

        skill_path = Path(tool.skills_dir).expanduser() / skill_id

        if not skill_path.exists() and not skill_path.is_symlink():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"技能不存在: {skill_id}"
            )

        # 软链接直接删除链接本身，普通目录递归删除
        if skill_path.is_symlink():
            skill_path.unlink()
            logger.info(f"已删除软链接: {skill_path}")
        else:
            import shutil
            shutil.rmtree(skill_path)
            logger.info(f"已删除技能目录: {skill_path}")

        return OperationResult(
            success=True,
            message=f"技能已删除: {skill_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除技能失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除技能失败: {str(e)}"
        )


@router.get("/tools/{tool_id}/skills", response_model=List[Skill])
async def get_tool_skills(tool_id: str):
    """获取工具目录下的技能列表"""
    try:
        config = config_manager.get_config()
        tool = config_manager.get_tool(tool_id)

        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在: {tool_id}"
            )

        # 扫描工具目录下的技能
        tool_skills_path = Path(tool.skills_dir).expanduser()
        if not tool_skills_path.exists():
            logger.warning(f"工具技能目录不存在: {tool.skills_dir}")
            return []

        skill_manager = SkillManager(str(tool_skills_path))
        skills = skill_manager.scan_skills()
        logger.info(f"工具 {tool.name} 下扫描到 {len(skills)} 个技能")
        return skills
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具技能列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具技能列表失败: {str(e)}"
        )


# ==================== 分发操作 ====================

@router.post("/distribute", response_model=OperationResult)
async def distribute_skills(request: DistributeRequest):
    """执行技能分发"""
    try:
        config = config_manager.get_config()
        # 解析相对路径为绝对路径，与 get_skills 接口保持一致
        master_skills_path = config_manager.resolve_path(config.master_skills_dir)
        skill_manager = SkillManager(str(master_skills_path))

        # 验证工具ID
        tools_dict = {tool.id: tool for tool in config.tools}
        invalid_tool_ids = [tid for tid in request.tool_ids if tid not in tools_dict]
        if invalid_tool_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"工具不存在: {', '.join(invalid_tool_ids)}"
            )

        # 验证技能ID：validate_skill_ids 返回 {id: bool}，过滤出值为 False 的
        skill_valid_map = skill_manager.validate_skill_ids(request.skill_ids)
        invalid_skill_ids = [sid for sid, exists in skill_valid_map.items() if not exists]
        if invalid_skill_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"技能不存在: {', '.join(invalid_skill_ids)}"
            )

        # 检查重名：待分发技能与目标工具已有技能是否存在同名
        for tool_id in request.tool_ids:
            tool = tools_dict[tool_id]
            tool_skills_path = Path(tool.skills_dir).expanduser()
            if tool_skills_path.exists():
                tool_skill_mgr = SkillManager(str(tool_skills_path))
                existing_skills = tool_skill_mgr.scan_skills()
                existing_names = {s.name.lower() for s in existing_skills}

                duplicate_names = []
                for skill_id in request.skill_ids:
                    skill = skill_manager.get_skill_by_id(skill_id)
                    if skill and skill.name.lower() in existing_names:
                        duplicate_names.append(skill.name)

                if duplicate_names:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"目标工具「{tool.name}」已存在同名技能: {', '.join(duplicate_names)}，不允许分发"
                    )
        
        # 执行分发
        distributed = 0
        failed = 0
        skipped = 0
        errors = []
        
        for tool_id in request.tool_ids:
            tool = tools_dict[tool_id]
            
            for skill_id in request.skill_ids:
                skill = skill_manager.get_skill_by_id(skill_id)
                if not skill:
                    continue
                
                source = skill.path
                target_name = Path(skill_id).name
                target = str(Path(tool.skills_dir).expanduser() / target_name)

                success, message = FileOperations.distribute_skill(
                    source=source,
                    target=target,
                    # 优先使用前端指定的分发方式，否则使用工具自身配置
                    method=request.distribute_method or tool.distribute_method,
                    force=request.force
                )
                
                if success:
                    distributed += 1
                    logger.info(f"分发成功: {skill_id} -> {tool.name}")
                elif "已存在" in message:
                    skipped += 1
                    logger.info(f"跳过: {skill_id} -> {tool.name} (已存在)")
                else:
                    failed += 1
                    errors.append(f"{tool.name}/{skill_id}: {message}")
                    logger.error(f"分发失败: {skill_id} -> {tool.name}: {message}")
        
        return OperationResult(
            success=failed == 0,
            message=f"分发完成: 成功 {distributed}, 失败 {failed}, 跳过 {skipped}",
            details={
                "distributed": distributed,
                "failed": failed,
                "skipped": skipped,
                "errors": errors
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分发失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分发失败: {str(e)}"
        )


@router.post("/cleanup", response_model=OperationResult)
async def cleanup_skills(request: CleanupRequest):
    """执行清理操作"""
    try:
        config = config_manager.get_config()
        
        # 确定要清理的工具
        if request.tool_ids:
            tools_dict = {tool.id: tool for tool in config.tools}
            invalid_tool_ids = [tid for tid in request.tool_ids if tid not in tools_dict]
            if invalid_tool_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"工具不存在: {', '.join(invalid_tool_ids)}"
                )
            tools_to_clean = [tools_dict[tid] for tid in request.tool_ids]
        else:
            tools_to_clean = config.tools
        
        # 执行清理
        total_removed = 0
        errors = []
        
        for tool in tools_to_clean:
            skills_dir = tool.skills_dir
            
            # 清理失效软链接
            if request.remove_broken_symlinks:
                try:
                    removed = FileOperations.remove_broken_symlinks(skills_dir)
                    total_removed += len(removed)
                    if removed:
                        logger.info(f"清理失效软链接 {tool.name}: {len(removed)} 个")
                except Exception as e:
                    error_msg = f"{tool.name}: 清理失效软链接失败 - {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # 清理未使用文件（预留功能，MVP暂不实现）
            if request.remove_unused_files:
                # TODO: 实现清理未在配置中的技能文件
                pass
        
        return OperationResult(
            success=len(errors) == 0,
            message=f"清理完成: 共清理 {total_removed} 项",
            details={
                "removed": total_removed,
                "errors": errors
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理失败: {str(e)}"
        )


@router.post("/preview", response_model=PreviewResult)
async def preview_distribute(request: PreviewRequest):
    """预览分发操作"""
    try:
        config = config_manager.get_config()
        skill_manager = SkillManager(config.master_skills_dir)
        
        # 验证工具ID
        tools_dict = {tool.id: tool for tool in config.tools}
        invalid_tool_ids = [tid for tid in request.tool_ids if tid not in tools_dict]
        if invalid_tool_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"工具不存在: {', '.join(invalid_tool_ids)}"
            )
        
        # 验证技能ID
        invalid_skill_ids = skill_manager.validate_skill_ids(request.skill_ids)
        if invalid_skill_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"技能不存在: {', '.join(invalid_skill_ids)}"
            )
        
        # 生成预览
        actions = []
        
        for tool_id in request.tool_ids:
            tool = tools_dict[tool_id]
            
            for skill_id in request.skill_ids:
                skill = skill_manager.get_skill_by_id(skill_id)
                if not skill:
                    continue
                
                source = skill.path
                target_name = Path(skill_id).name
                target = str(Path(tool.skills_dir).expanduser() / target_name)
                target_path = Path(target)
                
                # 判断操作类型
                if target_path.exists() or target_path.is_symlink():
                    action = PreviewAction(
                        action="skip",
                        source=source,
                        target=target,
                        reason="目标已存在"
                    )
                else:
                    # 根据分发方式确定操作
                    method = tool.distribute_method
                    if method.value == "auto":
                        method = FileOperations.get_system_default_method()
                    
                    action_type = "create_symlink" if method.value == "symlink" else "copy_dir"
                    action = PreviewAction(
                        action=action_type,
                        source=source,
                        target=target,
                        reason=None
                    )
                
                actions.append(action)
        
        return PreviewResult(
            actions=actions,
            total=len(actions)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览失败: {str(e)}"
        )


# ==================== Agent 管理 ====================

def _get_agent_manager() -> AgentManager:
    """创建 AgentManager 实例（每次请求按需创建，保持无状态）"""
    agent_library_dir = config_manager.get_agent_library_dir()
    return AgentManager(agent_library_dir, config_manager)


@router.get("/agent/library", response_model=List[AgentFile])
async def get_agent_library():
    """获取 Agent 库中所有可用文件列表"""
    try:
        agent_mgr = _get_agent_manager()
        files = agent_mgr.scan_agent_library()
        logger.info(f"Agent 库扫描完成，共 {len(files)} 个文件")
        return files
    except Exception as e:
        logger.error(f"获取 Agent 库失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取 Agent 库失败: {str(e)}"
        )


@router.get("/tools/{tool_id}/agent", response_model=AgentStatus)
async def get_tool_agent_status(tool_id: str):
    """获取指定工具的 AGENT.md 文件状态"""
    try:
        # 工具不存在时返回 404
        tool = config_manager.get_tool(tool_id)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在: {tool_id}"
            )

        agent_mgr = _get_agent_manager()
        agent_status = agent_mgr.get_tool_agent_status(tool_id)

        if agent_status is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具 {tool_id} 无 agent_path 配置"
            )

        return agent_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工具 Agent 状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取工具 Agent 状态失败: {str(e)}"
        )


@router.delete("/tools/{tool_id}/agent", response_model=OperationResult)
async def delete_tool_agent(tool_id: str):
    """删除指定工具的 AGENT.md 文件（软链接仅删链接本身）"""
    try:
        # 工具不存在时返回 404
        tool = config_manager.get_tool(tool_id)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在: {tool_id}"
            )

        agent_mgr = _get_agent_manager()
        success, message = agent_mgr.delete_tool_agent(tool_id)

        if not success:
            # 文件不存在属于 404，其他失败属于 500
            if "不存在" in message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=message
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )

        logger.info(f"工具 {tool_id} Agent 文件已删除")
        return OperationResult(success=True, message=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除工具 Agent 文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除工具 Agent 文件失败: {str(e)}"
        )


@router.post("/agent/distribute", response_model=OperationResult)
async def distribute_agent(request: AgentDistributeRequest):
    """将 Agent 库中的文件分发到指定工具列表"""
    try:
        # 验证所有工具 ID 是否存在
        invalid_ids = [
            tid for tid in request.tool_ids
            if not config_manager.get_tool(tid)
        ]
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"工具不存在: {', '.join(invalid_ids)}"
            )

        agent_mgr = _get_agent_manager()
        result = agent_mgr.distribute_agent(
            tool_ids=request.tool_ids,
            agent_filename=request.agent_filename,
            method=request.distribute_method,
        )

        logger.info(f"Agent 分发完成: {result.message}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent 分发失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent 分发失败: {str(e)}"
        )
