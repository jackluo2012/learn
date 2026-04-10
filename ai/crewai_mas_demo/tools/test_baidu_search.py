"""
BaiduSearchTool 单元测试

测试覆盖：
  - BaiduSearchInput：输入参数验证（query、top_k、sites、recency_filter）
  - BaiduSearchTool._run()：正常搜索流程、API Key 缺失、错误响应、网络异常、空结果

运行：
  cd crewai_mas_demo && pytest tools/test_baidu_search.py -v
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

_TOOLS_DIR = Path(__file__).parent
_PROJECT_ROOT = _TOOLS_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from tools.baidu_search import BaiduSearchInput, BaiduSearchTool

_MODULE = "tools.baidu_search"


class TestBaiduSearchInputValidation:
    """测试 BaiduSearchInput 的 Pydantic 验证器"""

    def test_valid_query(self):
        input_data = BaiduSearchInput(query="Python 教程")
        assert input_data.query == "Python 教程"
        assert input_data.top_k == 20

    def test_empty_query_raises_error(self):
        with pytest.raises(ValueError) as exc_info:
            BaiduSearchInput(query="")
        assert "查询内容不能为空" in str(exc_info.value)

    def test_whitespace_only_query_raises_error(self):
        with pytest.raises(ValueError) as exc_info:
            BaiduSearchInput(query="   ")
        assert "查询内容不能为空" in str(exc_info.value)

    def test_query_strips_whitespace(self):
        input_data = BaiduSearchInput(query="  Python  ")
        assert input_data.query == "Python"

    def test_top_k_default_value(self):
        input_data = BaiduSearchInput(query="测试")
        assert input_data.top_k == 20

    def test_top_k_valid_range(self):
        input_data = BaiduSearchInput(query="测试", top_k=10)
        assert input_data.top_k == 10

    def test_top_k_zero_valid(self):
        input_data = BaiduSearchInput(query="测试", top_k=0)
        assert input_data.top_k == 0

    def test_top_k_max_valid(self):
        input_data = BaiduSearchInput(query="测试", top_k=50)
        assert input_data.top_k == 50

    def test_top_k_negative_raises_error(self):
        with pytest.raises(ValueError) as exc_info:
            BaiduSearchInput(query="测试", top_k=-1)
        assert "top_k必须大于等于0" in str(exc_info.value)

    def test_top_k_over_50_raises_error(self):
        with pytest.raises(ValueError) as exc_info:
            BaiduSearchInput(query="测试", top_k=51)
        assert "top_k调整为50以内" in str(exc_info.value)

    def test_top_k_string_input(self):
        input_data = BaiduSearchInput(query="测试", top_k="5.0")
        assert input_data.top_k == 5

    def test_top_k_invalid_string_raises_error(self):
        with pytest.raises(ValueError) as exc_info:
            BaiduSearchInput(query="测试", top_k="abc")
        assert "无法将值" in str(exc_info.value)

    def test_sites_valid_list(self):
        sites = ["www.example.com", "www.test.com"]
        input_data = BaiduSearchInput(query="测试", sites=sites)
        assert input_data.sites == sites

    def test_sites_empty_list(self):
        input_data = BaiduSearchInput(query="测试", sites=[])
        assert input_data.sites == []

    def test_sites_none(self):
        input_data = BaiduSearchInput(query="测试", sites=None)
        assert input_data.sites is None

    def test_sites_over_20_raises_error(self):
        sites = [f"site{i}.com" for i in range(21)]
        with pytest.raises(ValueError) as exc_info:
            BaiduSearchInput(query="测试", sites=sites)
        assert "站点列表数量超出限制" in str(exc_info.value)

    def test_recency_filter_valid_values(self):
        valid_filters = ["week", "month", "semiyear", "year"]
        for filter_val in valid_filters:
            input_data = BaiduSearchInput(query="测试", recency_filter=filter_val)
            assert input_data.recency_filter == filter_val

    def test_recency_filter_none(self):
        input_data = BaiduSearchInput(query="测试", recency_filter=None)
        assert input_data.recency_filter is None

    def test_recency_filter_invalid_raises_error(self):
        with pytest.raises(ValueError):
            BaiduSearchInput(query="测试", recency_filter="invalid")


class TestBaiduSearchTool:
    """测试 BaiduSearchTool 的核心属性"""

    @pytest.fixture
    def tool(self):
        return BaiduSearchTool()

    def test_tool_name(self, tool):
        assert tool.name == "search_web"

    def test_tool_description_exists(self, tool):
        assert tool.description is not None
        assert len(tool.description) > 0
        assert "百度" in tool.description

    def test_tool_args_schema(self, tool):
        assert tool.args_schema == BaiduSearchInput


class TestBaiduSearchToolRun:
    """测试 BaiduSearchTool._run() 方法"""

    @pytest.fixture
    def tool(self):
        return BaiduSearchTool()

    @pytest.fixture
    def mock_api_key(self):
        with patch.dict(os.environ, {"BAIDU_API_KEY": "test-api-key"}):
            yield "test-api-key"

    @pytest.fixture
    def mock_success_response(self):
        return {
            "request_id": "test-request-id",
            "references": [
                {"id": 1, "title": "Python 官方文档", "url": "https://docs.python.org", "content": "Python 是一种解释型编程语言..."},
                {"id": 2, "title": "Python 教程", "url": "https://www.python-tutorial.com", "content": "学习 Python 编程的基础知识..."},
            ],
        }

    def test_missing_api_key(self, tool):
        """API Key 缺失时返回错误信息"""
        with patch.dict(os.environ, {}, clear=True):
            result = tool._run(query="Python")
            assert "缺少API认证密钥" in result
            assert "BAIDU_API_KEY" in result

    @patch(f"{_MODULE}.requests.post")
    def test_successful_search(self, mock_post, tool, mock_api_key, mock_success_response):
        """正常搜索返回格式化结果"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_success_response
        mock_post.return_value = mock_response

        result = tool._run(query="Python")

        assert "找到 2 条搜索结果" in result
        assert "Python 官方文档" in result
        assert "https://docs.python.org" in result

    @patch(f"{_MODULE}.requests.post")
    def test_search_with_sites_filter(self, mock_post, tool, mock_api_key, mock_success_response):
        """带站点过滤的搜索"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_success_response
        mock_post.return_value = mock_response

        sites = ["www.python.org"]
        tool._run(query="Python", sites=sites)

        call_args = mock_post.call_args
        payload = call_args.kwargs.get("json")
        assert payload["search_filter"]["match"]["site"] == sites

    @patch(f"{_MODULE}.requests.post")
    def test_search_with_recency_filter(self, mock_post, tool, mock_api_key, mock_success_response):
        """带时间筛选的搜索"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_success_response
        mock_post.return_value = mock_response

        tool._run(query="Python", recency_filter="week")

        call_args = mock_post.call_args
        payload = call_args.kwargs.get("json")
        assert payload["search_recency_filter"] == "week"

    @patch(f"{_MODULE}.requests.post")
    def test_api_error_response(self, mock_post, tool, mock_api_key):
        """API 返回错误码时返回错误信息"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "request_id": "test-id",
            "code": 400,
            "message": "参数错误",
        }
        mock_post.return_value = mock_response

        result = tool._run(query="Python")

        assert "API返回错误" in result
        assert "错误码400" in result

    @patch(f"{_MODULE}.requests.post")
    def test_empty_references(self, mock_post, tool, mock_api_key):
        """搜索结果为空时返回提示"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "request_id": "test-id",
            "references": [],
        }
        mock_post.return_value = mock_response

        result = tool._run(query="Python")

        assert "未找到相关搜索结果" in result

    @patch(f"{_MODULE}.requests.post")
    def test_timeout_error(self, mock_post, tool, mock_api_key):
        """请求超时时返回错误信息"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()

        result = tool._run(query="Python")

        assert "请求超时" in result

    @patch(f"{_MODULE}.requests.post")
    def test_http_error(self, mock_post, tool, mock_api_key):
        """HTTP 错误时返回错误信息"""
        import requests
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.side_effect = requests.exceptions.HTTPError(response=mock_response)

        result = tool._run(query="Python")

        assert "HTTP请求错误" in result

    @patch(f"{_MODULE}.requests.post")
    def test_request_exception(self, mock_post, tool, mock_api_key):
        """网络请求异常时返回错误信息"""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("连接失败")

        result = tool._run(query="Python")

        assert "网络请求异常" in result

    @patch(f"{_MODULE}.requests.post")
    def test_json_decode_error(self, mock_post, tool, mock_api_key):
        """JSON 解析错误时返回错误信息"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        result = tool._run(query="Python")

        assert "响应解析错误" in result
