"""
Git服务模块
提供基于Git的配置文件版本管理服务
"""
import os
import shutil
import tempfile
from typing import Optional, Dict, Any
from git import Repo, GitCommandError

from app.models.models import GitConfig


class GitService:
    """
    Git仓库操作服务类
    提供Git仓库初始化、配置提交、推送等功能
    """

    def __init__(self):
        """初始化Git服务"""
        self.temp_repo_dir = None
        self.repo = None

    def _get_temp_dir(self) -> str:
        """
        获取临时目录

        Returns:
            临时目录路径
        """
        if not self.temp_repo_dir:
            self.temp_repo_dir = tempfile.mkdtemp()
        return self.temp_repo_dir

    def _cleanup_temp_dir(self):
        """
        清理临时目录
        """
        if self.temp_repo_dir and os.path.exists(self.temp_repo_dir):
            shutil.rmtree(self.temp_repo_dir)
            self.temp_repo_dir = None
        self.repo = None

    def init_repo(self, git_config: GitConfig, local_path: Optional[str] = None) -> bool:
        """
        初始化Git仓库

        Args:
            git_config: Git配置对象
            local_path: 本地仓库路径，默认使用临时目录

        Returns:
            初始化是否成功
        """
        try:
            repo_path = local_path or self._get_temp_dir()
            
            # 如果目录存在且是git仓库，直接返回
            if os.path.exists(os.path.join(repo_path, '.git')):
                self.repo = Repo(repo_path)
                return True
            
            # 克隆远程仓库
            if git_config.username and git_config.password:
                # 使用用户名密码认证
                repo_url = git_config.repo_url.replace('https://', f'https://{git_config.username}:{git_config.password}@')
            else:
                repo_url = git_config.repo_url
            
            self.repo = Repo.clone_from(repo_url, repo_path, branch=git_config.branch)
            return True
        except GitCommandError as e:
            print(f"Git初始化失败: {e}")
            self._cleanup_temp_dir()
            return False
        except Exception as e:
            print(f"初始化Git仓库时发生错误: {e}")
            self._cleanup_temp_dir()
            return False

    def commit_config(self, device_name: str, config_content: str, commit_message: str) -> Optional[str]:
        """
        提交配置文件

        Args:
            device_name: 设备名称
            config_content: 配置内容
            commit_message: 提交信息

        Returns:
            提交ID，失败返回None
        """
        if not self.repo:
            print("Git仓库未初始化")
            return None

        try:
            # 创建设备配置目录
            device_dir = os.path.join(self.repo.working_dir, device_name)
            os.makedirs(device_dir, exist_ok=True)
            
            # 写入配置文件
            config_file = os.path.join(device_dir, f"{device_name}.config")
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # 添加到暂存区
            self.repo.index.add([config_file])
            
            # 提交
            commit = self.repo.index.commit(commit_message)
            return str(commit)
        except GitCommandError as e:
            print(f"Git提交失败: {e}")
            return None
        except Exception as e:
            print(f"提交配置时发生错误: {e}")
            return None

    def push_to_remote(self) -> bool:
        """
        推送到远程仓库

        Returns:
            推送是否成功
        """
        if not self.repo:
            print("Git仓库未初始化")
            return False

        try:
            # 推送当前分支
            origin = self.repo.remote(name='origin')
            origin.push()
            return True
        except GitCommandError as e:
            print(f"Git推送失败: {e}")
            return False
        except Exception as e:
            print(f"推送到远程仓库时发生错误: {e}")
            return False

    def get_config_diff(self, device_name: str, commit1: str, commit2: str) -> Optional[str]:
        """
        获取两个提交之间的配置差异

        Args:
            device_name: 设备名称
            commit1: 第一个提交ID
            commit2: 第二个提交ID

        Returns:
            差异字符串，失败返回None
        """
        if not self.repo:
            print("Git仓库未初始化")
            return None

        try:
            config_file = f"{device_name}/{device_name}.config"
            diff = self.repo.git.diff(f"{commit1}:{config_file}", f"{commit2}:{config_file}")
            return diff
        except GitCommandError as e:
            print(f"获取Git差异失败: {e}")
            return None
        except Exception as e:
            print(f"获取配置差异时发生错误: {e}")
            return None

    @staticmethod
    def test_connection(git_config: GitConfig) -> Dict[str, Any]:
        """
        测试Git连接

        Args:
            git_config: Git配置对象

        Returns:
            连接测试结果
        """
        temp_dir = None
        repo = None
        try:
            # 使用临时目录进行测试
            temp_dir = tempfile.mkdtemp()
            
            # 克隆远程仓库
            if git_config.username and git_config.password:
                repo_url = git_config.repo_url.replace('https://', f'https://{git_config.username}:{git_config.password}@')
            else:
                repo_url = git_config.repo_url
            
            repo = Repo.clone_from(repo_url, temp_dir, branch=git_config.branch, depth=1)
            
            # 验证是否成功克隆
            if repo:
                result = {
                    "success": True,
                    "message": "Git连接测试成功",
                    "repo_info": {
                        "name": repo.remotes.origin.url.split('/')[-1].replace('.git', ''),
                        "branch": git_config.branch,
                        "commit_count": len(list(repo.iter_commits()))
                    }
                }
                return result
            else:
                return {
                    "success": False,
                    "message": "Git连接测试失败: 无法克隆仓库"
                }
        except GitCommandError as e:
            return {
                "success": False,
                "message": f"Git连接测试失败: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Git连接测试失败: {str(e)}"
            }
        finally:
            # 显式清理资源
            if repo:
                # 确保Git进程已终止
                del repo
            # 手动清理临时目录，不依赖上下文管理器
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as cleanup_error:
                    print(f"清理临时目录失败: {cleanup_error}")

    def close(self):
        """
        关闭Git服务，清理资源
        """
        self._cleanup_temp_dir()


# 创建全局GitService实例
git_service = GitService()


def get_git_service() -> GitService:
    """
    获取Git服务实例

    Returns:
        Git服务实例
    """
    return git_service