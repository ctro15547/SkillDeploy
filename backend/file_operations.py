"""
文件操作模块
负责软链接、拷贝、清理等文件操作
"""
import os
import shutil
import platform
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from models import DistributeMethod

logger = logging.getLogger(__name__)


class FileOperations:
    """文件操作类"""
    
    @staticmethod
    def get_system_default_method() -> DistributeMethod:
        """
        获取系统默认的分发方式
        
        Returns:
            DistributeMethod: Mac/Linux返回SYMLINK，Windows返回COPY
        """
        system = platform.system()
        if system in ["Darwin", "Linux"]:
            return DistributeMethod.SYMLINK
        else:
            return DistributeMethod.COPY
    
    @staticmethod
    def create_symlink(source: str, target: str, force: bool = False) -> Tuple[bool, str]:
        """
        创建软链接
        
        Args:
            source: 源路径（总技能库中的技能目录）
            target: 目标路径（工具技能目录中的链接）
            force: 是否强制覆盖已存在的文件
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            source_path = Path(source).expanduser().resolve()
            target_path = Path(target).expanduser()
            
            # 检查源路径是否存在
            if not source_path.exists():
                return False, f"源路径不存在: {source}"
            
            # 检查目标是否已存在
            if target_path.exists() or target_path.is_symlink():
                if not force:
                    return False, f"目标已存在: {target}"
                
                # 删除已存在的文件或链接
                if target_path.is_symlink():
                    target_path.unlink()
                    logger.info(f"删除已存在的软链接: {target}")
                elif target_path.is_dir():
                    shutil.rmtree(target_path)
                    logger.info(f"删除已存在的目录: {target}")
                else:
                    target_path.unlink()
                    logger.info(f"删除已存在的文件: {target}")
            
            # 确保目标目录存在
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建软链接
            os.symlink(source_path, target_path)
            logger.info(f"创建软链接: {target} -> {source}")
            return True, f"软链接创建成功: {target}"
        
        except PermissionError:
            msg = f"权限不足，无法创建软链接: {target}"
            logger.error(msg)
            return False, msg
        
        except OSError as e:
            msg = f"创建软链接失败: {e}"
            logger.error(msg)
            return False, msg
        
        except Exception as e:
            msg = f"未知错误: {e}"
            logger.error(msg)
            return False, msg
    
    @staticmethod
    def copy_directory(source: str, target: str, force: bool = False) -> Tuple[bool, str]:
        """
        拷贝目录
        
        Args:
            source: 源路径（总技能库中的技能目录）
            target: 目标路径（工具技能目录）
            force: 是否强制覆盖已存在的文件
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            source_path = Path(source).expanduser().resolve()
            target_path = Path(target).expanduser()
            
            # 检查源路径是否存在
            if not source_path.exists():
                return False, f"源路径不存在: {source}"
            
            if not source_path.is_dir():
                return False, f"源路径不是目录: {source}"
            
            # 检查目标是否已存在
            if target_path.exists():
                if not force:
                    return False, f"目标已存在: {target}"
                
                # 删除已存在的目录
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                    logger.info(f"删除已存在的目录: {target}")
                else:
                    target_path.unlink()
                    logger.info(f"删除已存在的文件: {target}")
            
            # 确保父目录存在
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 拷贝目录
            shutil.copytree(source_path, target_path)
            logger.info(f"拷贝目录: {source} -> {target}")
            return True, f"目录拷贝成功: {target}"
        
        except PermissionError:
            msg = f"权限不足，无法拷贝目录: {target}"
            logger.error(msg)
            return False, msg
        
        except OSError as e:
            msg = f"拷贝目录失败: {e}"
            logger.error(msg)
            return False, msg
        
        except Exception as e:
            msg = f"未知错误: {e}"
            logger.error(msg)
            return False, msg
    
    @staticmethod
    def distribute_skill(
        source: str,
        target: str,
        method: DistributeMethod,
        force: bool = False
    ) -> Tuple[bool, str]:
        """
        分发技能到工具目录
        
        Args:
            source: 源路径（总技能库中的技能目录）
            target: 目标路径（工具技能目录）
            method: 分发方式
            force: 是否强制覆盖
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        # 自动检测分发方式
        if method == DistributeMethod.AUTO:
            method = FileOperations.get_system_default_method()
        
        # 执行分发
        if method == DistributeMethod.SYMLINK:
            return FileOperations.create_symlink(source, target, force)
        else:
            return FileOperations.copy_directory(source, target, force)
    
    @staticmethod
    def is_broken_symlink(path: str) -> bool:
        """
        检查是否为失效的软链接
        
        Args:
            path: 路径
        
        Returns:
            bool: 是否为失效的软链接
        """
        path_obj = Path(path).expanduser()
        return path_obj.is_symlink() and not path_obj.exists()
    
    @staticmethod
    def remove_broken_symlinks(directory: str) -> List[str]:
        """
        清理目录中的失效软链接
        
        Args:
            directory: 要清理的目录
        
        Returns:
            List[str]: 已清理的软链接列表
        """
        removed = []
        try:
            dir_path = Path(directory).expanduser()
            
            if not dir_path.exists():
                logger.warning(f"目录不存在: {directory}")
                return removed
            
            # 遍历目录
            for item in dir_path.iterdir():
                if FileOperations.is_broken_symlink(str(item)):
                    try:
                        item.unlink()
                        removed.append(str(item))
                        logger.info(f"删除失效软链接: {item}")
                    except Exception as e:
                        logger.error(f"删除失效软链接失败 {item}: {e}")
        
        except Exception as e:
            logger.error(f"清理失效软链接失败: {e}")
        
        return removed
    
    @staticmethod
    def remove_unused_files(
        directory: str,
        used_skill_ids: List[str]
    ) -> List[str]:
        """
        清理未在配置中的技能文件
        
        Args:
            directory: 工具技能目录
            used_skill_ids: 配置中使用的技能ID列表
        
        Returns:
            List[str]: 已清理的文件列表
        """
        removed = []
        try:
            dir_path = Path(directory).expanduser()
            
            if not dir_path.exists():
                logger.warning(f"目录不存在: {directory}")
                return removed
            
            # 遍历目录
            for item in dir_path.iterdir():
                # 跳过非目录项
                if not item.is_dir() and not item.is_symlink():
                    continue
                
                # 检查是否在使用列表中
                skill_id = item.name
                if skill_id not in used_skill_ids:
                    try:
                        if item.is_symlink():
                            item.unlink()
                            logger.info(f"删除未使用的软链接: {item}")
                        elif item.is_dir():
                            shutil.rmtree(item)
                            logger.info(f"删除未使用的目录: {item}")
                        
                        removed.append(str(item))
                    
                    except Exception as e:
                        logger.error(f"删除未使用文件失败 {item}: {e}")
        
        except Exception as e:
            logger.error(f"清理未使用文件失败: {e}")
        
        return removed
    
    @staticmethod
    def get_directory_size(directory: str) -> int:
        """
        获取目录大小（字节）
        
        Args:
            directory: 目录路径
        
        Returns:
            int: 目录大小（字节）
        """
        total_size = 0
        try:
            dir_path = Path(directory).expanduser()
            
            if not dir_path.exists():
                return 0
            
            for item in dir_path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        
        except Exception as e:
            logger.error(f"获取目录大小失败: {e}")
        
        return total_size
    
    @staticmethod
    def list_files_in_directory(directory: str) -> List[str]:
        """
        列出目录中的所有文件（相对路径）
        
        Args:
            directory: 目录路径
        
        Returns:
            List[str]: 文件列表
        """
        files = []
        try:
            dir_path = Path(directory).expanduser()
            
            if not dir_path.exists():
                return files
            
            for item in dir_path.rglob('*'):
                if item.is_file():
                    rel_path = item.relative_to(dir_path)
                    files.append(str(rel_path))
        
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
        
        return files

    @staticmethod
    def copy_file(source: str, target: str, force: bool = False) -> Tuple[bool, str]:
        """
        拷贝单个文件（使用 shutil.copy2 保留元数据）。
        与 copy_directory 对应，用于 Agent 单文件分发场景。

        Args:
            source: 源文件路径
            target: 目标文件路径
            force: 是否强制覆盖已存在的文件

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            source_path = Path(source).expanduser().resolve()
            target_path = Path(target).expanduser()

            # 检查源文件是否存在
            if not source_path.exists():
                return False, f"源文件不存在: {source}"

            if not source_path.is_file():
                return False, f"源路径不是文件: {source}"

            # 检查目标是否已存在
            if target_path.exists() or target_path.is_symlink():
                if not force:
                    return False, f"目标已存在: {target}"

                # 删除已存在的文件或软链接
                if target_path.is_symlink() or target_path.is_file():
                    target_path.unlink()
                    logger.info(f"删除已存在的文件/软链接: {target}")
                elif target_path.is_dir():
                    shutil.rmtree(target_path)
                    logger.info(f"删除已存在的目录: {target}")

            # 自动创建目标父目录
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 拷贝文件，保留元数据
            shutil.copy2(source_path, target_path)
            logger.info(f"拷贝文件: {source} -> {target}")
            return True, f"文件拷贝成功: {target}"

        except PermissionError:
            msg = f"权限不足，无法拷贝文件: {target}"
            logger.error(msg)
            return False, msg

        except OSError as e:
            msg = f"拷贝文件失败: {e}"
            logger.error(msg)
            return False, msg

        except Exception as e:
            msg = f"未知错误: {e}"
            logger.error(msg)
            return False, msg

    @staticmethod
    def distribute_file(
        source: str,
        target: str,
        method: DistributeMethod,
        force: bool = False
    ) -> Tuple[bool, str]:
        """
        分发单个文件到目标路径（对应 distribute_skill 的单文件版本）。
        AUTO 模式根据系统自动选择软链接或拷贝。

        Args:
            source: 源文件路径
            target: 目标文件路径
            method: 分发方式（AUTO/SYMLINK/COPY）
            force: 是否强制覆盖

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        # AUTO 模式：根据系统选择默认方式
        if method == DistributeMethod.AUTO:
            method = FileOperations.get_system_default_method()
            logger.info(f"AUTO 模式，系统默认分发方式: {method.value}")

        if method == DistributeMethod.SYMLINK:
            return FileOperations.create_symlink(source, target, force)
        else:
            # COPY / SMART 均使用文件拷贝
            return FileOperations.copy_file(source, target, force)
