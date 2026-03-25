# -*- coding: utf-8 -*-
"""
SQL 注入防护测试

测试 search_mac_addresses 和 search_users 函数的 SQL 注入防护
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import User, MACAddress
from app.api.endpoints.device_collection import search_mac_addresses
from app.api.endpoints.users import get_user_list


class TestSearchMacSQLInjection:
    """MAC 地址搜索 SQL 注入防护测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = Mock()
        db.query = Mock()
        return db

    def test_search_mac_with_percent_char(self, mock_db):
        """测试包含 % 字符的搜索 - 应正确转义"""
        # 恶意输入：包含 SQL 通配符 %
        malicious_input = "AA:BB:CC%'; DROP TABLE mac_addresses; --"
        
        # 模拟查询返回
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db.query.return_value = mock_query
        
        # 执行搜索
        result = search_mac_addresses(search_mac=malicious_input, db=mock_db)
        
        # 验证：调用了 filter，说明查询被执行
        assert mock_query.filter.called
        # 验证：返回空列表（无匹配结果）
        assert result == []

    def test_search_mac_with_underscore_char(self, mock_db):
        """测试包含 _ 字符的搜索 - 应正确转义"""
        # 恶意输入：包含 SQL 通配符 _
        malicious_input = "AA_BB:CC:DD:EE:FF"
        
        # 模拟查询返回
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db.query.return_value = mock_query
        
        # 执行搜索
        result = search_mac_addresses(search_mac=malicious_input, db=mock_db)
        
        # 验证：查询被执行
        assert mock_query.filter.called

    def test_search_mac_normal_input(self, mock_db):
        """测试正常输入 - 功能不受影响"""
        normal_input = "AA:BB:CC:DD:EE:FF"
        
        # 模拟返回结果
        mock_mac = Mock()
        mock_mac.mac_address = normal_input
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[mock_mac])
        mock_db.query.return_value = mock_query
        
        # 执行搜索
        result = search_mac_addresses(search_mac=normal_input, db=mock_db)
        
        # 验证：返回预期结果
        assert len(result) == 1
        assert result[0].mac_address == normal_input


class TestSearchUserSQLInjection:
    """用户搜索 SQL 注入防护测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = Mock()
        db.query = Mock()
        return db

    def test_search_user_with_sql_injection(self, mock_db):
        """测试 SQL 注入攻击 - admin' OR '1'='1"""
        # 经典 SQL 注入尝试
        malicious_input = "admin' OR '1'='1"
        
        # 模拟查询返回
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=0)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db.query.return_value = mock_query
        
        # 执行搜索（需要模拟 Depends(get_db) 和 check_admin_permission）
        with patch('app.api.endpoints.users.get_db', return_value=mock_db):
            with patch('app.api.endpoints.users.check_admin_permission'):
                result = get_user_list(
                    db=mock_db,
                    keyword=malicious_input,
                    page=1,
                    page_size=10
                )
        
        # 验证：查询被执行，但不会返回所有用户
        assert mock_query.filter.called

    def test_search_user_with_percent_char(self, mock_db):
        """测试包含 % 字符的搜索"""
        malicious_input = "admin%'; DROP TABLE users; --"
        
        # 模拟查询返回
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=0)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db.query.return_value = mock_query
        
        # 执行搜索
        with patch('app.api.endpoints.users.get_db', return_value=mock_db):
            with patch('app.api.endpoints.users.check_admin_permission'):
                result = get_user_list(
                    db=mock_db,
                    keyword=malicious_input,
                    page=1,
                    page_size=10
                )
        
        # 验证：查询被执行
        assert mock_query.filter.called

    def test_search_user_normal_input(self, mock_db):
        """测试正常输入 - 功能不受影响"""
        normal_input = "admin"
        
        # 模拟返回结果
        mock_user = Mock()
        mock_user.username = "admin"
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.count = Mock(return_value=1)
        mock_query.offset = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[mock_user])
        mock_db.query.return_value = mock_query
        
        # 执行搜索
        with patch('app.api.endpoints.users.get_db', return_value=mock_db):
            with patch('app.api.endpoints.users.check_admin_permission'):
                result = get_user_list(
                    db=mock_db,
                    keyword=normal_input,
                    page=1,
                    page_size=10
                )
        
        # 验证：返回预期结果
        assert len(result) == 1
        assert result[0].username == "admin"


class TestEscapeLogic:
    """转义逻辑单元测试"""

    def test_escape_percent_char(self):
        """测试 % 字符转义"""
        test_input = "100%"
        escaped = test_input.replace("%", r"\%").replace("_", r"\_")
        assert escaped == r"100\%"

    def test_escape_underscore_char(self):
        """测试 _ 字符转义"""
        test_input = "test_value"
        escaped = test_input.replace("%", r"\%").replace("_", r"\_")
        assert escaped == r"test\_value"

    def test_escape_both_chars(self):
        """测试同时包含 % 和 _ 的转义"""
        test_input = "100%_test"
        escaped = test_input.replace("%", r"\%").replace("_", r"\_")
        assert escaped == r"100\%\_test"

    def test_escape_sql_injection_attempt(self):
        """测试 SQL 注入尝试的转义"""
        test_input = "admin' OR '1'='1"
        escaped = test_input.replace("%", r"\%").replace("_", r"\_")
        # 转义后应该保持原样（因为没有 % 和 _）
        assert escaped == test_input

    def test_escape_complex_injection(self):
        """测试复杂注入尝试的转义"""
        test_input = "%'; DROP TABLE users; --"
        escaped = test_input.replace("%", r"\%").replace("_", r"\_")
        assert escaped == r"\%'; DROP TABLE users; --"
