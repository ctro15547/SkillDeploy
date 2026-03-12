# requires: pydantic==2.5.0
"""
配置管理模块
负责读取、写入和验证配置文件
"""
import json
import os
import logging
from pathlib import Path
from typing import List, Optional
from models import Config, Tool

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""

    # 预设工具的默认 Agent 路径，优先级低于配置文件中的 agent_path
    PRESET_AGENT_PATHS = {
        "claude":    "~/.claude/AGENT.md",
        "kiro":      "~/.kiro/steering/AGENT.md",
        "cursor":    "~/.cursor/rules/AGENT.md",
        "opencode":  "~/.config/opencode/AGENT.md",
    }

    def __init__(self, config_path: str = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为项目根目录下的 config/config.json
        """
        if config_path is None:
            # 获取项目根目录（backend的父目录）
            backend_dir = Path(__file__).parent
            self.project_root = backend_dir.parent
            config_path = self.project_root / "config" / "config.json"
        else:
            # 如果提供了配置路径，尝试推断项目根目录
            self.project_root = Path(config_path).parent.parent

        self.config_path = Path(config_path).expanduser()
        self.config: Optional[Config] = None
        self._ensure_config_exists()
        self.load()
    
    def _ensure_config_exists(self):
        """确保配置文件存在，不存在则创建默认配置"""
        if not self.config_path.exists():
            logger.info(f"配置文件不存在，创建默认配置: {self.config_path}")
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # 创建默认配置
            default_config = Config(
                master_skills_dir="skills-library",
                tools=[]
            )

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config.model_dump(), f, indent=2, ensure_ascii=False)

            logger.info("默认配置已创建")
    
    def load(self) -> Config:
        """
        加载配置文件
        
        Returns:
            Config: 配置对象
        
        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: 配置文件格式错误
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.config = Config(**data)
            logger.info(f"配置加载成功: {self.config_path}")
            return self.config
        
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {self.config_path}")
            raise
        
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            raise
        
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise
    
    def save(self, config: Optional[Config] = None):
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置对象，为空则保存当前配置
        
        Raises:
            ValueError: 没有配置可保存
        """
        if config:
            self.config = config
        
        if not self.config:
            raise ValueError("没有配置可保存")
        
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self.config.model_dump(),
                    f,
                    indent=2,
                    ensure_ascii=False
                )
            
            logger.info(f"配置保存成功: {self.config_path}")
        
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def get_config(self) -> Config:
        """
        获取当前配置

        Returns:
            Config: 当前配置对象
        """
        if not self.config:
            self.load()
        return self.config

    def resolve_path(self, path: str) -> Path:
        """
        解析路径，支持相对路径和绝对路径
        相对路径相对于项目根目录

        Args:
            path: 路径字符串

        Returns:
            Path: 解析后的绝对路径
        """
        path_obj = Path(path).expanduser()
        if path_obj.is_absolute():
            return path_obj
        else:
            # 相对路径相对于项目根目录
            return (self.project_root / path_obj).resolve()
    
    def update_config(self, master_skills_dir: Optional[str] = None) -> Config:
        """
        更新全局配置
        
        Args:
            master_skills_dir: 总技能库目录路径
        
        Returns:
            Config: 更新后的配置对象
        """
        if not self.config:
            self.load()
        
        if master_skills_dir:
            # 验证路径
            path = Path(master_skills_dir).expanduser()
            if not path.exists():
                logger.warning(f"总技能库目录不存在: {master_skills_dir}")
            
            self.config.master_skills_dir = master_skills_dir
        
        self.save()
        logger.info("全局配置已更新")
        return self.config
    
    def add_tool(self, tool: Tool) -> Config:
        """
        添加工具
        
        Args:
            tool: 工具对象
        
        Returns:
            Config: 更新后的配置对象
        
        Raises:
            ValueError: 工具ID已存在
        """
        if not self.config:
            self.load()
        
        # 检查ID是否已存在
        if any(t.id == tool.id for t in self.config.tools):
            raise ValueError(f"工具ID已存在: {tool.id}")
        
        # 验证技能目录路径
        path = Path(tool.skills_dir).expanduser()
        if not path.exists():
            logger.warning(f"工具技能目录不存在: {tool.skills_dir}")
        
        self.config.tools.append(tool)
        self.save()
        logger.info(f"工具已添加: {tool.name} ({tool.id})")
        return self.config
    
    def update_tool(self, tool_id: str, tool: Tool) -> Config:
        """
        更新工具配置
        
        Args:
            tool_id: 工具ID
            tool: 新的工具对象
        
        Returns:
            Config: 更新后的配置对象
        
        Raises:
            ValueError: 工具不存在
        """
        if not self.config:
            self.load()
        
        # 查找工具
        for i, t in enumerate(self.config.tools):
            if t.id == tool_id:
                # 验证技能目录路径
                path = Path(tool.skills_dir).expanduser()
                if not path.exists():
                    logger.warning(f"工具技能目录不存在: {tool.skills_dir}")
                
                self.config.tools[i] = tool
                self.save()
                logger.info(f"工具已更新: {tool.name} ({tool.id})")
                return self.config
        
        raise ValueError(f"工具不存在: {tool_id}")
    
    def delete_tool(self, tool_id: str) -> Config:
        """
        删除工具
        
        Args:
            tool_id: 工具ID
        
        Returns:
            Config: 更新后的配置对象
        
        Raises:
            ValueError: 工具不存在
        """
        if not self.config:
            self.load()
        
        # 查找并删除工具
        for i, t in enumerate(self.config.tools):
            if t.id == tool_id:
                removed = self.config.tools.pop(i)
                self.save()
                logger.info(f"工具已删除: {removed.name} ({removed.id})")
                return self.config
        
        raise ValueError(f"工具不存在: {tool_id}")
    
    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """
        获取指定工具
        
        Args:
            tool_id: 工具ID
        
        Returns:
            Tool: 工具对象，不存在则返回None
        """
        if not self.config:
            self.load()
        
        for tool in self.config.tools:
            if tool.id == tool_id:
                return tool
        
        return None
    
    def get_all_tools(self) -> List[Tool]:
        """
        获取所有工具
        
        Returns:
            List[Tool]: 工具列表
        """
        if not self.config:
            self.load()
        
        return self.config.tools
    
    def auto_scan_tools(self) -> List[str]:
        """
        自动扫描常见工具目录
        扫描 ~/.config/*/skills 和 ~/.*/skills 目录

        Returns:
            List[str]: 发现的工具技能目录列表
        """
        discovered = []
        home = Path.home()

        # 扫描 ~/.config/*/skills
        config_dir = home / ".config"
        if config_dir.exists():
            for item in config_dir.iterdir():
                if item.is_dir():
                    skills_dir = item / "skills"
                    if skills_dir.exists() and skills_dir.is_dir():
                        discovered.append(str(skills_dir))
                        logger.info(f"发现工具技能目录: {skills_dir}")

        # 扫描 ~/.*/skills（排除 .config）
        for item in home.iterdir():
            if item.is_dir() and item.name.startswith('.') and item.name != '.config':
                skills_dir = item / "skills"
                if skills_dir.exists() and skills_dir.is_dir():
                    discovered.append(str(skills_dir))
                    logger.info(f"发现工具技能目录: {skills_dir}")

        logger.info(f"自动扫描完成，发现 {len(discovered)} 个工具技能目录")
        return discovered

    def scan_preset_tools(self) -> List[Tool]:
        """
        扫描预设的常见 AI 工具技能目录，自动检测分发方式。
        预设目录：
          ~/.config/opencode/skills
          ~/.claude/skills
          ~/.kiro/skills
          ~/.cursor/skills-cursor

        检测逻辑：
          - 目录内全是软链接 → symlink
          - 目录内全是普通目录 → copy
          - 混合存在 → smart（智能检测）
          - 目录为空 → auto（默认）

        Returns:
            List[Tool]: 发现的工具列表（仅目录存在的）
        """
        from models import DistributeMethod

        # 预设工具配置：(工具ID, 工具名称, 技能目录路径)
        PRESET_TOOLS = [
            ("opencode", "OpenCode", "~/.config/opencode/skills"),
            ("claude",   "Claude",   "~/.claude/skills"),
            ("kiro",     "Kiro",     "~/.kiro/skills"),
            ("cursor",   "Cursor",   "~/.cursor/skills-cursor"),
        ]

        found_tools = []
        for tool_id, tool_name, skills_dir_str in PRESET_TOOLS:
            skills_dir = Path(skills_dir_str).expanduser()
            if not skills_dir.exists() or not skills_dir.is_dir():
                logger.debug(f"预设目录不存在，跳过: {skills_dir}")
                continue

            # 统计目录内软链接和普通目录数量
            symlink_count = 0
            copy_count = 0
            try:
                for item in skills_dir.iterdir():
                    if item.name.startswith('.'):
                        continue
                    if item.is_symlink():
                        symlink_count += 1
                    elif item.is_dir():
                        copy_count += 1
            except Exception as e:
                logger.warning(f"检测 {skills_dir} 内容失败: {e}")

            total = symlink_count + copy_count
            if total == 0:
                method = DistributeMethod.AUTO
            elif symlink_count > 0 and copy_count > 0:
                method = DistributeMethod.SMART   # 混合 → 智能检测
            elif symlink_count > 0:
                method = DistributeMethod.SYMLINK
            else:
                method = DistributeMethod.COPY

            logger.info(
                f"发现预设工具: {tool_name} | 路径: {skills_dir} | "
                f"软链接:{symlink_count} 拷贝:{copy_count} → {method.value}"
            )
            found_tools.append(Tool(
                id=tool_id,
                name=tool_name,
                skills_dir=skills_dir_str,
                enabled=True,
                distribute_method=method,
            ))

        logger.info(f"预设扫描完成，发现 {len(found_tools)} 个工具")
        return found_tools

    def apply_preset_scan(self) -> List[Tool]:
        """
        执行预设扫描并将新发现的工具写入配置（已存在的跳过）。

        Returns:
            List[Tool]: 本次新增的工具列表
        """
        found = self.scan_preset_tools()
        existing_ids = {t.id for t in self.config.tools}
        newly_added = []

        for tool in found:
            if tool.id in existing_ids:
                logger.info(f"工具已存在，跳过: {tool.id}")
                continue
            self.config.tools.append(tool)
            newly_added.append(tool)
            logger.info(f"自动添加工具: {tool.name} ({tool.id})")

        if newly_added:
            self.save()
            logger.info(f"预设扫描新增 {len(newly_added)} 个工具")

        return newly_added
    
    def validate_paths(self) -> dict:
        """
        验证配置中的所有路径
        
        Returns:
            dict: 验证结果
                {
                    "master_skills_dir": {"exists": bool, "path": str},
                    "tools": [{"id": str, "name": str, "exists": bool, "path": str}]
                }
        """
        result = {
            "master_skills_dir": {
                "exists": False,
                "path": self.config.master_skills_dir
            },
            "tools": []
        }
        
        # 验证总技能库目录
        master_path = Path(self.config.master_skills_dir).expanduser()
        result["master_skills_dir"]["exists"] = master_path.exists()
        
        # 验证工具目录
        for tool in self.config.tools:
            tool_path = Path(tool.skills_dir).expanduser()
            result["tools"].append({
                "id": tool.id,
                "name": tool.name,
                "exists": tool_path.exists(),
                "path": tool.skills_dir
            })
        
        return result

    def get_tool_agent_path(self, tool_id: str) -> Optional[str]:
        """
        获取工具的 Agent 文件路径。
        优先级：配置文件中的 agent_path > 预设默认值 > None

        Args:
            tool_id: 工具 ID

        Returns:
            Optional[str]: Agent 文件路径，未找到则返回 None
        """
        tool = self.get_tool(tool_id)
        if tool and tool.agent_path:
            logger.debug(f"使用配置文件中的 agent_path: {tool.agent_path}")
            return tool.agent_path

        preset = self.PRESET_AGENT_PATHS.get(tool_id)
        if preset:
            logger.debug(f"使用预设 agent_path: {preset}")
            return preset

        logger.debug(f"工具 {tool_id} 无 agent_path 配置")
        return None

    def get_agent_library_dir(self) -> str:
        """
        获取 Agent 库目录路径。
        优先级：配置文件中的 agent_library_dir > 默认值 'agent-library'

        Returns:
            str: Agent 库目录路径（相对或绝对路径）
        """
        if not self.config:
            self.load()

        if self.config.agent_library_dir:
            logger.debug(f"使用配置文件中的 agent_library_dir: {self.config.agent_library_dir}")
            return self.config.agent_library_dir

        logger.debug("使用默认 agent_library_dir: agent-library")
        return "agent-library"
