import unittest
import chat_history
from chat_history_copy import MongoDBChatMessageHistory
from pymongo import MongoClient

# MongoDB 配置
MONGO_URI = "mongodb://localhost:27017/"  # 替换为您的 MongoDB 连接字符串
DB_NAME = "langchain_chat"
COLLECTION_NAME = "chat_history_test"  # 使用不同的集合进行测试

class TestMongoDBChatMessageHistory(unittest.TestCase):
    def setUp(self):
        # 在每个测试用例运行前，连接到 MongoDB 并清除测试集合
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]
        self.collection.delete_many({})  # 清除集合中的所有数据
        self.session_id = "test_user"
        self.history = chat_history_copy.MongoDBChatMessageHistory(self.session_id)

    def tearDown(self):
        # 在每个测试用例运行后，清除测试集合
        self.collection.delete_many({})
        self.client.close()

    def test_add_message(self):
        # 测试添加消息
        self.history.add_message("human", "你好！")
        self.assertEqual(len(self.history.messages), 1)
        self.assertEqual(self.history.messages[0].content, "你好！")
        self.assertEqual(self.history.messages[0].type, "human")

    def test_get_messages(self):
        # 测试获取消息
        self.history.add_message("human", "你好！")
        self.history.add_message("ai", "你好，我是测试！")
        self.assertEqual(len(self.history.messages), 2)
        self.assertEqual(self.history.messages[0].content, "你好！")
        self.assertEqual(self.history.messages[1].content, "你好，我是测试！")

    def test_clear_history(self):
        # 测试清除历史
        self.history.add_message("human", "你好！")
        self.history.clear()
        self.assertEqual(len(self.history.messages), 0)
        # 验证 MongoDB 中是否已删除数据
        self.assertEqual(self.collection.count_documents({"session_id": self.session_id}), 0)

if __name__ == "__main__":
    unittest.main()