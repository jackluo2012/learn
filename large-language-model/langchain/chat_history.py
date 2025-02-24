# 导入必要的库
from langchain.memory import ChatMessageHistory
from pymongo import MongoClient
from datetime import datetime

# MongoDB 配置
MONGO_URI = "mongodb://localhost:27017/"  # 替换为您的 MongoDB 连接字符串
DB_NAME = "langchain_chat"
COLLECTION_NAME = "chat_history"

# 连接到 MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

class MongoDBChatMessageHistory(ChatMessageHistory):
    """
    使用 MongoDB 存储聊天历史
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.collection = collection
        self._load()

    def _load(self):
        """
        从 MongoDB 加载聊天历史
        """
        history = self.collection.find_one({"session_id": self.session_id})
        self.messages = []
        if history:
            for message in history.get("messages", []):
                self.add_message(message["role"], message["content"])

    def add_message(self, role: str, content: str):
        """
        添加消息到聊天历史
        """
        super().add_message(role, content)
        self._save()

    def clear(self):
        """
        清除聊天历史
        """
        super().clear()
        self.collection.delete_one({"session_id": self.session_id})

    def _save(self):
        """
        将聊天历史保存到 MongoDB
        """
        message_dicts = [{"role": m.type, "content": m.content} for m in self.messages]
        self.collection.update_one(
            {"session_id": self.session_id},
            {"$set": {"messages": message_dicts, "updated_at": datetime.utcnow()}},
            upsert=True,
        )

if __name__ == "__main__":
    # 创建一个聊天历史对象
    session_id = "user123"
    history = MongoDBChatMessageHistory(session_id)

    # 添加消息
    history.add_message("human", "你好！")
    history.add_message("ai", "你好，我是 LangChain！")

    # 获取聊天历史
    print(history.messages)

    # 清除聊天历史
    # history.clear()