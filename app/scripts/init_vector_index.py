"""初始化产品向量索引"""
import asyncio
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_store import vector_store


async def main():
    """初始化向量索引"""
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "products.csv"
    )

    print(f"从 {csv_path} 加载产品数据...")

    try:
        count = await vector_store.index_products(csv_path)
        print(f"成功索引 {count} 个产品向量")

        # 验证
        total = vector_store.get_product_count()
        print(f"向量库中共有 {total} 个产品")

    except Exception as e:
        print(f"初始化失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
