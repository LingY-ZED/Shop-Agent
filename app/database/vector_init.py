"""向量数据库初始化模块"""
import logging
import os
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)


async def init_vector_store() -> int:
    """
    初始化向量数据库（如果为空则自动初始化）

    Returns:
        索引的产品数量，0 表示未执行初始化
    """
    product_count = vector_store.get_product_count()
    if product_count > 0:
        logger.info(f"向量数据库已存在，共 {product_count} 个产品")
        return product_count

    logger.info("向量数据库为空，开始初始化向量索引...")

    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "products.csv"
    )

    if not os.path.exists(csv_path):
        logger.warning(f"产品数据文件不存在: {csv_path}")
        return 0

    try:
        count = await vector_store.index_products(csv_path)
        logger.info(f"向量索引初始化完成，已索引 {count} 个产品")
        return count
    except Exception as e:
        logger.error(f"向量索引初始化失败: {e}")
        raise
