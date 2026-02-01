#!/usr/bin/env python3
"""
Script chính để khởi tạo database kho thuốc.
Chạy script này để tạo mới hoặc reset database.

Usage:
    python main.py          # Tạo mới database (nếu chưa có) hoặc sử dụng existing
    python main.py --reset  # Reset và tạo lại database từ đầu
    python main.py --test   # Test query sau khi khởi tạo
"""

import sys
import argparse
from pathlib import Path

# Thêm parent directory vào path
sys.path.insert(0, str(Path(__file__).parent))

from init import (
    initialize_database,
    get_database_connection,
    get_table_stats,
    test
)


def main():
    parser = argparse.ArgumentParser(
        description="Khởi tạo database kho thuốc MedAgent"
    )
    parser.add_argument(
        "--reset", 
        action="store_true",
        help="Reset và tạo lại database từ đầu"
    )
    parser.add_argument(
        "--test",
        action="store_true", 
        help="Chạy các test query sau khi khởi tạo"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("MedAgent Database Initialization")
    print("=" * 60)
    
    # Khởi tạo database
    conn = initialize_database(reset=args.reset)
    
    if args.test:
        run_tests(conn)
    
    print("\nDatabase initialization completed!")
    print(f"Database location: sqlite-db/database/drug-warehouse.db")
    
    conn.close()


def run_tests(conn):
    """Chạy các test query để kiểm tra database."""
    print("\n" + "=" * 60)
    print("Running Test Queries")
    print("=" * 60)
    
    # Test 1: Top 5 nhà cung cấp
    print("\nTop 5 Nha cung cap:")
    results = test(conn, """
        SELECT s.name, COUNT(i.import_id) as total_imports, 
               SUM(i.total_amount) as total_value
        FROM suppliers s
        LEFT JOIN imports i ON s.supplier_id = i.supplier_id
        GROUP BY s.supplier_id
        ORDER BY total_value DESC
        LIMIT 5
    """)
    for row in results:
        print(f"  - {row[0]}: {row[1]} lần nhập, giá trị: {row[2]:,} VND")
    
    # Test 2: Top 5 thuốc có tồn kho nhiều nhất
    print("\nTop 5 Thuoc ton kho nhieu nhat:")
    results = test(conn, """
        SELECT m.name, SUM(inv.quantity) as total_qty
        FROM inventory inv
        JOIN medicines m ON inv.medicine_id = m.medicine_id
        GROUP BY inv.medicine_id
        ORDER BY total_qty DESC
        LIMIT 5
    """)
    for row in results:
        print(f"  - {row[0][:50]}...: {row[1]:,} {{}}")
    
    # Test 3: Thống kê nhập hàng theo tháng (2025)
    print("\nThong ke nhap hang theo thang (2025):")
    results = test(conn, """
        SELECT strftime('%Y-%m', import_date) as month,
               COUNT(*) as num_imports,
               SUM(total_amount) as total_value
        FROM imports
        WHERE import_date LIKE '2025%'
        GROUP BY strftime('%Y-%m', import_date)
        ORDER BY month
        LIMIT 10
    """, size=10)
    for row in results:
        print(f"  - {row[0]}: {row[1]} đơn, giá trị: {row[2]:,} VND")
    
    # Test 4: Thuốc sắp hết hạn (trong 6 tháng)
    print("\nThuoc sap het han (trong 6 thang):")
    results = test(conn, """
        SELECT m.name, inv.batch_code, inv.expired_date, inv.quantity
        FROM inventory inv
        JOIN medicines m ON inv.medicine_id = m.medicine_id
        WHERE inv.expired_date <= date('now', '+6 months')
        AND inv.quantity > 0
        ORDER BY inv.expired_date
        LIMIT 5
    """)
    for row in results:
        print(f"  - {row[0][:40]}... (Batch: {row[1]}, HSD: {row[2]}, SL: {row[3]})")


if __name__ == "__main__":
    main()
