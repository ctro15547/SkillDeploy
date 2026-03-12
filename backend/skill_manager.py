"""
技能管理模块
负责扫描、列出和管理技能
"""
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict
from models import Skill

logger = logging.getLogger(__name__)


class SkillManager:
    """技能管理器"""
    
    def __init__(self, master_skills_dir: str):
        """
        初始化技能管理器
        
        Args:
            master_skills_dir: 总技能库目录路径
        """
        self.master_skills_dir = Path(master_skills_dir).expanduser()
    
    def get_skill_size(self, skill_path: Path) -> int:
        """
        计算技能目录的大小
        
        Args:
            skill_path: 技能目录路径
        
        Returns:
            int: 目录大小（字节）
        """
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(skill_path):
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    if filepath.exists():
                        total_size += filepath.stat().st_size
        except Exception as e:
            logger.warning(f"计算技能大小失败 {skill_path}: {e}")
        
        return total_size
    
    def get_skill_files(self, skill_path: Path) -> List[str]:
        """
        获取技能目录中的文件列表
        
        Args:
            skill_path: 技能目录路径
        
        Returns:
            List[str]: 文件名列表（相对于技能目录）
        """
        files = []
        try:
            for dirpath, dirnames, filenames in os.walk(skill_path):
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    relative_path = filepath.relative_to(skill_path)
                    files.append(str(relative_path))
        except Exception as e:
            logger.warning(f"获取技能文件列表失败 {skill_path}: {e}")
        
        return files
    
    def read_skill_description(self, skill_path: Path) -> Optional[str]:
        """
        读取技能描述（从README.md或skill.md的第一行）
        
        Args:
            skill_path: 技能目录路径
        
        Returns:
            Optional[str]: 技能描述，如果没有则返回None
        """
        # 尝试读取README.md
        readme_path = skill_path / "README.md"
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    # 去掉Markdown标题符号
                    if first_line.startswith('#'):
                        first_line = first_line.lstrip('#').strip()
                    return first_line if first_line else None
            except Exception as e:
                logger.warning(f"读取README.md失败 {readme_path}: {e}")
        
        # 尝试读取skill.md
        skill_md_path = skill_path / "skill.md"
        if skill_md_path.exists():
            try:
                with open(skill_md_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    # 去掉Markdown标题符号
                    if first_line.startswith('#'):
                        first_line = first_line.lstrip('#').strip()
                    return first_line if first_line else None
            except Exception as e:
                logger.warning(f"读取skill.md失败 {skill_md_path}: {e}")
        
        return None
    
    def scan_skills(self) -> List[Skill]:
        """
        扫描工具技能目录中的所有技能（单层扁平结构）
        适用于工具目录，如 ~/.claude/skills/技能名/

        Returns:
            List[Skill]: 技能列表
        """
        skills = []

        if not self.master_skills_dir.exists():
            logger.error(f"目录不存在: {self.master_skills_dir}")
            return skills

        if not self.master_skills_dir.is_dir():
            logger.error(f"路径不是目录: {self.master_skills_dir}")
            return skills

        try:
            for item in self.master_skills_dir.iterdir():
                if not item.is_dir():
                    continue
                if item.name.startswith('.'):
                    continue

                skill = Skill(
                    id=item.name,
                    group=None,
                    name=item.name.replace('-', ' ').replace('_', ' ').title(),
                    description=self.read_skill_description(item),
                    path=str(item),
                    files=self.get_skill_files(item),
                    size=self.get_skill_size(item)
                )
                skills.append(skill)
                logger.debug(f"发现技能: {skill.name} ({skill.id})")

        except Exception as e:
            logger.error(f"扫描技能失败: {e}")

        skills.sort(key=lambda s: s.name)
        logger.info(f"扫描到 {len(skills)} 个技能")
        return skills

    def scan_master_skills(self) -> List[Skill]:
        """
        扫描主技能库中的所有技能（两层结构）
        结构约定：skills-library/分组名/技能名/
        第一层全为分组目录，第二层全为技能目录，技能内容不限

        Returns:
            List[Skill]: 技能列表
        """
        skills = []

        if not self.master_skills_dir.exists():
            logger.error(f"总技能库目录不存在: {self.master_skills_dir}")
            return skills

        if not self.master_skills_dir.is_dir():
            logger.error(f"总技能库路径不是目录: {self.master_skills_dir}")
            return skills

        try:
            # 第一层：分组目录
            for group_dir in sorted(self.master_skills_dir.iterdir()):
                if not group_dir.is_dir():
                    continue
                if group_dir.name.startswith('.'):
                    continue

                group_name = group_dir.name

                # 第二层：技能目录
                try:
                    for skill_dir in sorted(group_dir.iterdir()):
                        if not skill_dir.is_dir():
                            continue
                        if skill_dir.name.startswith('.'):
                            continue

                        skill_id = f"{group_name}/{skill_dir.name}"
                        skill = Skill(
                            id=skill_id,
                            group=group_name,
                            name=skill_dir.name.replace('-', ' ').replace('_', ' ').title(),
                            description=self.read_skill_description(skill_dir),
                            path=str(skill_dir),
                            files=self.get_skill_files(skill_dir),
                            size=self.get_skill_size(skill_dir)
                        )
                        skills.append(skill)
                        logger.debug(f"发现技能: {skill_id}")

                except Exception as e:
                    logger.warning(f"扫描分组失败 {group_name}: {e}")

        except Exception as e:
            logger.error(f"扫描主技能库失败: {e}")

        logger.info(f"主技能库扫描到 {len(skills)} 个技能")
        return skills
    
    def get_skill_by_id(self, skill_id: str) -> Optional[Skill]:
        """
        根据ID获取技能
        skill_id 格式为 "分组名/技能名"

        Args:
            skill_id: 技能ID（相对路径）

        Returns:
            Optional[Skill]: 技能对象，如果不存在则返回None
        """
        skill_path = self.master_skills_dir / skill_id

        if not skill_path.exists() or not skill_path.is_dir():
            logger.warning(f"技能不存在: {skill_id}")
            return None

        # 从路径中解析分组名和技能名
        parts = Path(skill_id).parts
        group_name = parts[0] if len(parts) >= 2 else None
        skill_dir_name = parts[-1]

        skill = Skill(
            id=skill_id,
            group=group_name,
            name=skill_dir_name.replace('-', ' ').replace('_', ' ').title(),
            description=self.read_skill_description(skill_path),
            path=str(skill_path),
            files=self.get_skill_files(skill_path),
            size=self.get_skill_size(skill_path)
        )

        return skill
    
    def get_skills_by_ids(self, skill_ids: List[str]) -> List[Skill]:
        """
        根据ID列表获取技能列表
        
        Args:
            skill_ids: 技能ID列表
        
        Returns:
            List[Skill]: 技能列表（不存在的技能会被跳过）
        """
        skills = []
        for skill_id in skill_ids:
            skill = self.get_skill_by_id(skill_id)
            if skill:
                skills.append(skill)
        
        return skills
    
    def validate_skill_ids(self, skill_ids: List[str]) -> Dict[str, bool]:
        """
        验证技能ID列表
        
        Args:
            skill_ids: 技能ID列表
        
        Returns:
            Dict[str, bool]: {skill_id: 是否存在}
        """
        result = {}
        for skill_id in skill_ids:
            skill_path = self.master_skills_dir / skill_id
            result[skill_id] = skill_path.exists() and skill_path.is_dir()
        
        return result
