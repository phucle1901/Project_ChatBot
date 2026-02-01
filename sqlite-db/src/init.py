"""
Module khởi tạo và quản lý database SQLite cho hệ thống kho thuốc.
Hỗ trợ tạo schema, import dữ liệu từ CSV, và các utility functions.
"""
import sqlite3
from sqlite3 import Connection
import pandas as pd
from pathlib import Path
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Đường dẫn mặc định
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR
DB_DIR = BASE_DIR / "database"


def _init_db(conn: Connection) -> None:
    """
    Khởi tạo schema database với đầy đủ các bảng.
    
    Tables:
        - suppliers: Nhà cung cấp thuốc
        - medicines: Danh mục thuốc
        - imports: Đơn nhập hàng
        - import_items: Chi tiết các mặt hàng trong đơn nhập
        - inventory: Tồn kho hiện tại
    
    Args:
        conn: Kết nối SQLite database
    """
    cur = conn.cursor()
    
    # Bảng nhà cung cấp
    cur.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT,
            address TEXT
        );
    """)
    logger.info("Created table: suppliers")
    
    # Bảng thuốc
    cur.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            medicine_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            unit TEXT DEFAULT 'Hộp'
        );
    """)
    logger.info("Created table: medicines")
    
    # Bảng đơn nhập hàng
    cur.execute("""
        CREATE TABLE IF NOT EXISTS imports (
            import_id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_date TEXT NOT NULL,
            total_amount INTEGER DEFAULT 0,
            supplier_id INTEGER,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        );
    """)
    logger.info("Created table: imports")
    
    # Bảng chi tiết đơn nhập
    cur.execute("""
        CREATE TABLE IF NOT EXISTS import_items (
            import_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_id INTEGER NOT NULL,
            medicine_id INTEGER NOT NULL,
            batch_code TEXT,
            quantity INTEGER DEFAULT 0,
            expiry_date TEXT,
            import_price INTEGER DEFAULT 0,
            FOREIGN KEY (import_id) REFERENCES imports(import_id),
            FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id)
        );
    """)
    logger.info("Created table: import_items")
    
    # Bảng tồn kho
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_id INTEGER,
            medicine_id INTEGER NOT NULL,
            batch_code TEXT,
            expired_date TEXT,
            import_price INTEGER DEFAULT 0,
            selling_price INTEGER DEFAULT 0,
            quantity INTEGER DEFAULT 0,
            FOREIGN KEY (import_id) REFERENCES imports(import_id),
            FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id),
            UNIQUE (medicine_id, batch_code)
        );
    """)
    logger.info("Created table: inventory")
    
    # Tạo indexes để tăng tốc query
    cur.execute("CREATE INDEX IF NOT EXISTS idx_imports_date ON imports(import_date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_imports_supplier ON imports(supplier_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_import_items_import ON import_items(import_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_import_items_medicine ON import_items(medicine_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_medicine ON inventory(medicine_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inventory_expired ON inventory(expired_date);")
    logger.info("Created indexes")
    
    conn.commit()
    logger.info("Database schema initialized successfully!")


def drop_all_tables(conn: Connection) -> None:
    """
    Xóa tất cả các bảng trong database (dùng khi cần reset).
    
    Args:
        conn: Kết nối SQLite database
    """
    cur = conn.cursor()
    tables = ["inventory", "import_items", "imports", "medicines", "suppliers"]
    
    for table in tables:
        cur.execute(f"DROP TABLE IF EXISTS {table};")
        logger.info(f"Dropped table: {table}")
    
    conn.commit()
    logger.info("All tables dropped successfully!")


def import_suppliers(conn: Connection, csv_path: Path = None) -> int:
    """
    Import dữ liệu nhà cung cấp từ CSV.
    
    Args:
        conn: Kết nối SQLite database
        csv_path: Đường dẫn file CSV (mặc định: suppliers.csv)
    
    Returns:
        Số lượng records đã import
    """
    if csv_path is None:
        csv_path = DATA_DIR / "suppliers.csv"
    
    df = pd.read_csv(csv_path)
    df.to_sql("suppliers", conn, if_exists="append", index=False)
    
    count = len(df)
    logger.info(f"Imported {count} suppliers")
    return count


def import_medicines(conn: Connection, csv_path: Path = None) -> int:
    """
    Import dữ liệu thuốc từ CSV.
    
    Args:
        conn: Kết nối SQLite database
        csv_path: Đường dẫn file CSV (mặc định: medicines.csv)
    
    Returns:
        Số lượng records đã import
    """
    if csv_path is None:
        csv_path = DATA_DIR / "medicines.csv"
    
    df = pd.read_csv(csv_path)
    df.to_sql("medicines", conn, if_exists="append", index=False)
    
    count = len(df)
    logger.info(f"Imported {count} medicines")
    return count


def import_imports(conn: Connection, csv_path: Path = None) -> int:
    """
    Import dữ liệu đơn nhập hàng từ CSV.
    
    Args:
        conn: Kết nối SQLite database
        csv_path: Đường dẫn file CSV (mặc định: imports.csv)
    
    Returns:
        Số lượng records đã import
    """
    if csv_path is None:
        csv_path = DATA_DIR / "imports.csv"
    
    df = pd.read_csv(csv_path)
    df.to_sql("imports", conn, if_exists="append", index=False)
    
    count = len(df)
    logger.info(f"Imported {count} imports")
    return count


def import_import_items(conn: Connection, csv_path: Path = None) -> int:
    """
    Import dữ liệu chi tiết đơn nhập từ CSV.
    
    Args:
        conn: Kết nối SQLite database
        csv_path: Đường dẫn file CSV (mặc định: import_items.csv)
    
    Returns:
        Số lượng records đã import
    """
    if csv_path is None:
        csv_path = DATA_DIR / "import_items.csv"
    
    df = pd.read_csv(csv_path)
    df.to_sql("import_items", conn, if_exists="append", index=False)
    
    count = len(df)
    logger.info(f"Imported {count} import_items")
    return count


def import_inventory(conn: Connection, csv_path: Path = None) -> int:
    """
    Import dữ liệu tồn kho từ CSV.
    
    Args:
        conn: Kết nối SQLite database
        csv_path: Đường dẫn file CSV (mặc định: inventory.csv)
    
    Returns:
        Số lượng records đã import
    """
    if csv_path is None:
        csv_path = DATA_DIR / "inventory.csv"
    
    df = pd.read_csv(csv_path)
    df.to_sql("inventory", conn, if_exists="append", index=False)
    
    count = len(df)
    logger.info(f"Imported {count} inventory records")
    return count


def test(conn: Connection, sql: str, size: int = 5) -> list:
    """
    Thực thi SQL query và trả về kết quả.
    
    Args:
        conn: Kết nối SQLite database
        sql: Câu lệnh SQL
        size: Số lượng records trả về (mặc định: 5)
    
    Returns:
        Danh sách kết quả
    """
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchmany(size=size)


def get_table_stats(conn: Connection) -> dict:
    """
    Lấy thống kê số lượng records trong mỗi bảng.
    
    Args:
        conn: Kết nối SQLite database
    
    Returns:
        Dict với tên bảng và số lượng records
    """
    cur = conn.cursor()
    tables = ["suppliers", "medicines", "imports", "import_items", "inventory"]
    stats = {}
    
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        stats[table] = cur.fetchone()[0]
    
    return stats


def get_database_connection(db_path: Path = None) -> Connection:
    """
    Tạo kết nối tới database.
    
    Args:
        db_path: Đường dẫn file database (mặc định: database/drug-warehouse.db)
    
    Returns:
        Connection object
    """
    if db_path is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        db_path = DB_DIR / "drug-warehouse.db"
    
    return sqlite3.connect(str(db_path))


def initialize_database(reset: bool = False) -> Connection:
    """
    Khởi tạo database đầy đủ: tạo schema và import dữ liệu.
    
    Args:
        reset: Nếu True, xóa database cũ và tạo mới
    
    Returns:
        Connection object
    """
    # Đảm bảo thư mục database tồn tại
    DB_DIR.mkdir(parents=True, exist_ok=True)
    db_path = DB_DIR / "drug-warehouse.db"
    
    # Nếu reset, xóa file database cũ
    if reset and db_path.exists():
        db_path.unlink()
        logger.info(f"Deleted existing database: {db_path}")
    
    # Tạo kết nối
    conn = sqlite3.connect(str(db_path))
    logger.info(f"Connected to database: {db_path}")
    
    # Khởi tạo schema
    _init_db(conn)
    
    # Import dữ liệu
    logger.info("Starting data import...")
    import_suppliers(conn)
    import_medicines(conn)
    import_imports(conn)
    import_import_items(conn)
    import_inventory(conn)
    
    # Hiển thị thống kê
    stats = get_table_stats(conn)
    logger.info("=" * 50)
    logger.info("Database Statistics:")
    for table, count in stats.items():
        logger.info(f"  {table}: {count:,} records")
    logger.info("=" * 50)
    
    return conn


if __name__ == "__main__":
    # Test khởi tạo database
    conn = initialize_database(reset=True)
    
    # Test query
    print("\n" + "=" * 50)
    print("Sample Data from Inventory:")
    print("=" * 50)
    results = test(conn, """
        SELECT i.inventory_id, m.name as medicine_name, i.quantity, i.selling_price
        FROM inventory i
        JOIN medicines m ON i.medicine_id = m.medicine_id
        LIMIT 5
    """)
    for row in results:
        print(row)
    
    conn.close()
