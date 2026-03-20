"""向量数据库服务 - 使用 ChromaDB 存储和检索向量"""

import csv
import logging
import os
from typing import List, Dict, Any, Optional
import chromadb
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class VectorStore:
    """向量数据库服务"""

    def __init__(self, persist_directory: str = "./data/chroma_db"):
        """
        初始化向量数据库

        Args:
            persist_directory: 数据库持久化目录
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = None

    def get_or_create_collection(self, name: str = "products"):
        """获取或创建集合"""
        self.collection = self.client.get_or_create_collection(
            name=name, metadata={"description": "产品向量库"}
        )
        return self.collection

    def load_products_from_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """从 CSV 文件读取产品数据"""
        products = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                products.append(
                    {
                        "product_id": row["product_id"],
                        "product_name": row["product_name"],
                        "description": row["description"],
                        "category": row["category"],
                        "price": float(row["price"]),
                        "stock": int(row["stock"]),
                    }
                )
        return products

    async def index_products(self, csv_path: str) -> int:
        """
        从 CSV 导入产品数据并生成向量索引

        Args:
            csv_path: 产品数据 CSV 文件路径

        Returns:
            索引的产品数量
        """
        # 读取产品数据
        products = self.load_products_from_csv(csv_path)
        logger.info(f"读取到 {len(products)} 个产品")

        # 获取或创建集合
        collection = self.get_or_create_collection("products")

        # 清除旧数据（删除所有）
        try:
            all_ids = collection.get()["ids"]
            if all_ids:
                collection.delete(ids=all_ids)
        except Exception:
            pass  # 集合为空时忽略

        # 生成向量
        texts = []
        metadatas = []
        ids = []

        for product in products:
            # 组合文本用于生成向量
            text = f"{product['product_name']} {product['description']} {product['category']}"
            texts.append(text)

            # 元数据
            metadatas.append(
                {
                    "product_id": product["product_id"],
                    "product_name": product["product_name"],
                    "description": product["description"],
                    "category": product["category"],
                    "price": product["price"],
                    "stock": product["stock"],
                }
            )

            ids.append(product["product_id"])

        # 批量生成嵌入
        embeddings = await embedding_service.embed_texts(texts)

        # 添加到向量数据库
        collection.add(
            embeddings=embeddings, documents=texts, metadatas=metadatas, ids=ids
        )

        logger.info(f"已索引 {len(products)} 个产品向量")
        return len(products)

    async def search_similar_products(
        self, query: str, k: int = 5, category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似产品

        Args:
            query: 查询文本
            k: 返回结果数量
            category_filter: 可选的分类过滤

        Returns:
            相似产品列表
        """
        if self.collection is None:
            self.get_or_create_collection("products")

        # 生成查询向量
        query_embedding = await embedding_service.embed_text(query)

        # 构建查询条件
        where = {"category": category_filter} if category_filter else None

        # 执行搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        # 格式化结果
        similar_products = []
        if results["ids"] and results["ids"][0]:
            for i, product_id in enumerate(results["ids"][0]):
                similar_products.append(
                    {
                        "product_id": product_id,
                        "product_name": results["metadatas"][0][i]["product_name"],
                        "description": results["metadatas"][0][i]["description"],
                        "category": results["metadatas"][0][i]["category"],
                        "price": results["metadatas"][0][i]["price"],
                        "stock": results["metadatas"][0][i]["stock"],
                        "score": 1 - results["distances"][0][i],  # 转换距离为相似度
                    }
                )

        return similar_products

    def get_product_count(self) -> int:
        """获取索引的产品数量"""
        if self.collection is None:
            self.get_or_create_collection("products")
        return self.collection.count()


# 全局实例
vector_store = VectorStore()
