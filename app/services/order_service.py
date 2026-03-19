from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Order, OrderItem, Product


def get_order_by_order_number(db: Session, order_number: str) -> Optional[Order]:
    """根据订单号查询订单"""
    return db.query(Order).filter(Order.order_number == order_number).first()


def get_order_by_tracking_number(db: Session, tracking_number: str) -> Optional[Order]:
    """根据快递单号查询订单"""
    return db.query(Order).filter(Order.tracking_number == tracking_number).first()


def get_order_status(
    db: Session,
    order_number: Optional[str] = None,
    tracking_number: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    查询订单状态

    Args:
        db: 数据库会话
        order_number: 订单号
        tracking_number: 快递单号

    Returns:
        订单信息字典，如果未找到返回None
    """
    order = None

    if order_number:
        order = get_order_by_order_number(db, order_number)
    elif tracking_number:
        order = get_order_by_tracking_number(db, tracking_number)

    if not order:
        return None

    # 构建订单信息
    order_info = {
        "order_number": order.order_number,
        "status": order.status,
        "shipping_status": order.shipping_status,
        "tracking_number": order.tracking_number,
        "shipping_address": order.shipping_address,
        "total_amount": order.total_amount,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
        "items": []
    }

    # 获取订单商品信息
    for item in order.items:
        order_info["items"].append({
            "product_name": item.product.name if item.product else "未知商品",
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "subtotal": item.subtotal
        })

    return order_info


def search_orders_by_product(db: Session, product_name: str) -> List[Dict[str, Any]]:
    """
    根据商品名称模糊查询订单

    Args:
        db: 数据库会话
        product_name: 商品名称关键词

    Returns:
        订单列表
    """
    # 模糊搜索商品
    products = db.query(Product).filter(
        Product.name.like(f"%{product_name}%")
    ).all()

    if not products:
        return []

    product_ids = [p.id for p in products]

    # 查询包含这些商品的订单
    order_items = db.query(OrderItem).filter(
        OrderItem.product_id.in_(product_ids)
    ).all()

    if not order_items:
        return []

    # 获取订单ID列表并去重
    order_ids = list(set([item.order_id for item in order_items]))

    # 查询订单
    orders = db.query(Order).filter(Order.id.in_(order_ids)).all()

    results = []
    for order in orders:
        order_info = {
            "order_number": order.order_number,
            "status": order.status,
            "shipping_status": order.shipping_status,
            "tracking_number": order.tracking_number,
            "total_amount": order.total_amount,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "items": []
        }

        # 获取订单中匹配的商品
        for item in order.items:
            if item.product_id in product_ids:
                order_info["items"].append({
                    "product_name": item.product.name if item.product else "未知商品",
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": item.subtotal
                })

        results.append(order_info)

    return results


def get_user_orders(db: Session, user_id: int) -> List[Order]:
    """获取用户的所有订单"""
    return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
