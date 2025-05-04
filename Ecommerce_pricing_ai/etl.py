import os
import pandas as pd
from sqlalchemy import create_engine, text

def clean_columns(df):
    df.columns = (
        df.columns.str.strip()
                  .str.lower()
                  .str.replace(" ", "_")
                  .str.replace(r"[^\w_]", "", regex=True)
    )
    return df.drop_duplicates()

def ensure_column_type(df, column, dtype):
    if column in df.columns:
        df[column] = df[column].astype(dtype, errors='ignore')
    return df


def read_csv_with_encoding(path):
    try:
        return pd.read_csv(path, encoding='utf-8')
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='latin1')


def main():
    # DB connection
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    engine = create_engine(
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    base_path = "data/Raw"
    df_txn       = read_csv_with_encoding(f"{base_path}/Indian_sales_data.csv")
    df_ret_price = read_csv_with_encoding(f"{base_path}/retail_sales_dataset.csv")
    df_sales     = read_csv_with_encoding(f"{base_path}/sales.csv")
    df_store     = read_csv_with_encoding(f"{base_path}/store_sales_data.csv")

    df_txn       = clean_columns(df_txn)
    df_ret_price = clean_columns(df_ret_price)
    df_sales     = clean_columns(df_sales)
    df_store     = clean_columns(df_store)

    if "purchase_date" in df_sales.columns:
        df_sales = df_sales.rename(columns={"purchase_date": "sales_date"})

    # Enforce customer_id as string where present
    for df in [df_txn, df_ret_price, df_sales, df_store]:
        df = ensure_column_type(df, "customer_id", str)

    if "order_date" in df_txn.columns:
        df_txn["order_date"] = pd.to_datetime(
            df_txn["order_date"], dayfirst=True, errors="coerce"
        ).dt.date
    if "date" in df_ret_price.columns:
        df_ret_price["order_date"] = pd.to_datetime(
            df_ret_price["date"], dayfirst=False, errors="coerce"
        ).dt.date
    if "sales_date" in df_sales.columns:
        df_sales["sales_date"] = pd.to_datetime(
            df_sales["sales_date"], dayfirst=True, errors="coerce"
        ).dt.date
    if "order_date" in df_store.columns:
        df_store["order_date"] = pd.to_datetime(
            df_store["order_date"], dayfirst=False, errors="coerce"
        ).dt.date

    # Stage raw tables into MySQL
    staging = {
        "stg_india_trans": df_txn,
        "stg_dynamic_pricing": df_ret_price,
        "stg_sales_summary": df_sales,
        "stg_store_sales": df_store,
    }
    for name, df in staging.items():
        try:
            df.to_sql(name, engine, if_exists="replace", index=False)
            print(f"✅ Loaded staging table: {name}")
        except Exception as e:
            print(f"❌ Failed to load {name}: {e}")

    # 1) Enrich store sales with transactions on geographic+date
    txn_keys = [
        c for c in ["country", "state", "region", "city", "order_date"]
        if c in df_store.columns and c in df_txn.columns
    ]
    master = pd.merge(df_store, df_txn, how="outer", on=txn_keys)


    price_keys = [
        k for k in ["customer_id", "order_date"]
        if k in master.columns and k in df_ret_price.columns
    ]
    if price_keys:
        master = pd.merge(master, df_ret_price, how="outer", on=price_keys)

    # 3) Aggregate to summary grain and join sales
        # Create unified sales and profit columns
        master['sales'] = master[['sales_x', 'sales_y']].sum(axis=1, skipna=True)
        master['profit'] = master[['profit_x', 'profit_y']].sum(axis=1, skipna=True)
        agg = master.groupby(["customer_id", "sales_date"]).agg(
            total_sales=("sales", "sum"),
            total_profit=("profit", "sum")
        ).reset_index()
        master = pd.merge(
            df_sales, agg, how="outer", on=["customer_id", "sales_date"]
        )
    else:
        print(f"⚠️ Could not find sales/profit columns, found: {master.columns.tolist()}")
        
    
    
    # for col in master.select_dtypes(include='object').columns:
    #     mode = master[col].mode().iloc[0] if not master[col].mode().empty else "Unknown"
    #     master[col].fillna(mode, inplace=True)

    
    # for col in master.select_dtypes(include='number').columns:
    #     median = master[col].median() if not master[col].isnull().all() else 0
    #     master[col].fillna(median, inplace=True)

    
    # for col in master.select_dtypes(include='datetime').columns:
    #     master[col].fillna(pd.Timestamp.now().normalize(), inplace=True)

    
    # for col in master.select_dtypes(include='bool').columns:
    #     master[col].fillna(False, inplace=True)
        
        
    # print("🔍 Columns in master DataFrame:")
    # print(master.columns.tolist())
    
    # master = master.loc[:, ~master.columns.duplicated()]
    # print("🔍 Columns after removing duplicates:")


    # Save to DB & CSV
    master.to_sql(
        "sales_pricing_master", engine, if_exists="replace", index=False
    )
    master.to_csv("data/Processed/final_output.csv", index=False)

    # Verification
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM sales_pricing_master")).scalar()
        print(f"✅ Loaded {count} rows into sales_pricing_master")
        last_row = conn.execute(text(
        "SELECT * FROM sales_pricing_master ORDER BY sales_date DESC LIMIT 1"
        )).fetchone()

        print(f"✅ Last entry: {last_row}")
        
        
    
    


if __name__ == "__main__":
    main()

