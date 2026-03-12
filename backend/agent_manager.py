"""
Agent 管理模块
负责扫描 Agent 库、检测工具 Agent 状态、分发和删除 Agent 文件
参照 skill_manager.py 的设计模式，针对单文件场景做适配
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from config_manager import ConfigManager
from file_operations import FileOperations
from models import AgentFile, AgentStatus, DistributeMethod, OperationResult

logger = logging.getLogger(__name__)


class AgentManager:
    """Agent 管理器"""

    def __init__(self, agent_library_dir: str, config_manager: ConfigManager):
        """
        Args:
            agent_library_dir: Agent 库目录路径（相对或绝对）
            config_manager: 配置管理器实例，用于获取工具信息和路径
        """
        self.config_manager = config_manager
        # 解析路径：相对路径相对于项目根目录
        self.agent_library_dir = config_manager.resolve_path(agent_library_dir)
        logger.info(f"AgentManager 初始化，Agent 库目录: {self.agent_library_dir}")

    def scan_agent_library(self) -> List[AgentFile]:
        """
        扫描 agent-library/ 下所有 .md 文件，返回 AgentFile 列表。
        目录不存在或为空时返回空列表，不报错。

        Returns:
            List[AgentFile]: Agent 文件列表，按文件名排序
        """
        result = []

        if not self.agent_library_dir.exists():
            logger.warning(f"Agent 库目录不存在: {self.agent_library_dir}")
            return result

        if not self.agent_library_dir.is_dir():
            logger.warning(f"Agent 库路径不是目录: {self.agent_library_dir}")
            return result

        try:
            for item in sorted(self.agent_library_dir.iterdir()):
                # 只扫描 .md 文件，跳过隐藏文件和其他类型
                if not item.is_file() or item.suffix.lower() != ".md":
                    continue
                if item.name.startswith("."):
                    continue

                try:
                    size = item.stat().st_size
                except OSError as e:
                    logger.warning(f"获取文件大小失败 {item}: {e}")
                    size = 0

                result.append(AgentFile(
                    filename=item.name,
                    path=str(item),
                    size=size,
                ))
                logger.debug(f"发现 Agent 文件: {item.name} ({size} bytes)")

        except Exception as e:
            logger.error(f"扫描 Agent 库失败: {e}")

        logger.info(f"Agent 库扫描完成，共 {len(result)} 个文件")
        return result

    def get_tool_agent_status(self, tool_id: str) -> Optional[AgentStatus]:
        """
        检测指定工具的 AGENT.md 文件状态。
        返回文件是否存在、是否为软链接、大小、修改时间等信息。

        Args:
            tool_id: 工具 ID

        Returns:
            Optional[AgentStatus]: 状态对象；工具不存在或无 agent_path 时返回 None
        """
        tool = self.config_manager.get_tool(tool_id)
        if not tool:
            logger.warning(f"工具不存在: {tool_id}")
            return None

        agent_path_str = self.config_manager.get_tool_agent_path(tool_id)
        if not agent_path_str:
            logger.warning(f"工具 {tool_id} 无 agent_path 配置")
            return None

        agent_path = Path(agent_path_str).expanduser()

        # 检测文件状态
        exists = agent_path.exists() or agent_path.is_symlink()
        is_symlink = agent_path.is_symlink()
        symlink_target: Optional[str] = None
        file_size: Optional[int] = None
        modified_time: Optional[str] = None

        if is_symlink:
            try:
                symlink_target = str(agent_path.resolve())
            except Exception:
                symlink_target = str(agent_path.readlink())

        if exists and agent_path.is_file():
            try:
                stat = agent_path.stat()
                file_size = stat.st_size
                modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except OSError as e:
                logger.warning(f"获取文件状态失败 {agent_path}: {e}")

        logger.debug(
            f"工具 {tool_id} Agent 状态: exists={exists}, "
            f"is_symlink={is_symlink}, size={file_size}"
        )
        return AgentStatus(
            tool_id=tool_id,
            tool_name=tool.name,
            agent_path=agent_path_str,
            exists=exists,
            is_symlink=is_symlink,
            symlink_target=symlink_target,
            file_size=file_size,
            modified_time=modified_time,
        )

    def get_all_tools_agent_status(self) -> List[AgentStatus]:
        """
        获取所有已启用工具的 Agent 状态。
        无 agent_path 配置的工具会被跳过。

        Returns:
            List[AgentStatus]: 各工具 Agent 状态列表
        """
        result = []
        config = self.config_manager.get_config()

        for tool in config.tools:
            if not tool.enabled:
                continue

            status = self.get_tool_agent_status(tool.id)
            if status is not None:
                result.append(status)

        logger.info(f"获取所有工具 Agent 状态完成，共 {len(result)} 个工具")
        return result

    def delete_tool_agent(self, tool_id: str) -> Tuple[bool, str]:
        """
        删除指定工具的 AGENT.md 文件。
        若为软链接，仅删除链接本身，保留源文件。

        Args:
            tool_id: 工具 ID

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        tool = self.config_manager.get_tool(tool_id)
        if not tool:
            return False, f"工具不存在: {tool_id}"

        agent_path_str = self.config_manager.get_tool_agent_path(tool_id)
        if not agent_path_str:
            return False, f"工具 {tool_id} 无 agent_path 配置"

        agent_path = Path(agent_path_str).expanduser()

        # 文件不存在（包括失效软链接也算不存在）
        if not agent_path.exists() and not agent_path.is_symlink():
            return False, f"Agent 文件不存在: {agent_path_str}"

        try:
            if agent_path.is_symlink():
                # 软链接：只删链接，不动源文件
                agent_path.unlink()
                logger.info(f"已删除软链接: {agent_path}")
                return True, f"软链接已删除: {agent_path_str}"
            elif agent_path.is_file():
                agent_path.unlink()
                logger.info(f"已删除 Agent 文件: {agent_path}")
                return True, f"Agent 文件已删除: {agent_path_str}"
            else:
                return False, f"目标不是文件或软链接: {agent_path_str}"

        except PermissionError:
            msg = f"权限不足，无法删除: {agent_path_str}"
            logger.error(msg)
            return False, msg

        except Exception as e:
            msg = f"删除失败: {e}"
            logger.error(msg)
            return False, msg

    def distribute_agent(self, **kwargs) -> OperationResult:
        """
        将 Agent 库中的文件分发到指定工具列表。

        Args (via kwargs):
            tool_ids (List[str]): 目标工具 ID 列表
            agent_filename (str): Agent 库中的文件名
            method (DistributeMethod): 分发方式

        Returns:
            OperationResult: 包含成功数、失败数和错误详情
        """
        tool_ids: List[str] = kwargs.get("tool_ids", [])
        agent_filename: str = kwargs.get("agent_filename", "")
        method: DistributeMethod = kwargs.get("method", DistributeMethod.COPY)

        # 验证源文件存在
        source_path = self.agent_library_dir / agent_filename
        if not source_path.exists() or not source_path.is_file():
            return OperationResult(
                success=False,
                message=f"Agent 源文件不存在: {agent_filename}",
                details={"distributed": 0, "failed": len(tool_ids), "errors": [
                    f"源文件不存在: {agent_filename}"
                ]}
            )

        distributed = 0
        failed = 0
        errors = []

        for tool_id in tool_ids:
            agent_path_str = self.config_manager.get_tool_agent_path(tool_id)
            if not agent_path_str:
                failed += 1
                msg = f"{tool_id}: 无 agent_path 配置"
                errors.append(msg)
                logger.warning(msg)
                continue

            success, msg = FileOperations.distribute_file(
                source=str(source_path),
                target=agent_path_str,
                method=method,
                force=True,  # Agent 分发始终强制覆盖
            )

            if success:
                distributed += 1
                logger.info(f"Agent 分发成功: {agent_filename} -> {tool_id} ({agent_path_str})")
            else:
                failed += 1
                errors.append(f"{tool_id}: {msg}")
                logger.error(f"Agent 分发失败: {agent_filename} -> {tool_id}: {msg}")

        total = distributed + failed
        return OperationResult(
            success=failed == 0,
            message=f"分发完成: 成功 {distributed}/{total}，失败 {failed}/{total}",
            details={
                "distributed": distributed,
                "failed": failed,
                "errors": errors,
            }
        )
