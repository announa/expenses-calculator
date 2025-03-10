import pandas as pd
import camelot
from dateutil import parser
import datetime

date_header = ""
value_headers = []
unwanted_rows = []


def get_table_headers():
    date_header_input = input("Name of the date column: ")
    value_headers_input = input(
        "Names of the expenses columns (separated by commas ..., ...): "
    )

    global date_header
    global value_headers
    date_header = date_header_input
    value_headers = value_headers_input.split(",")


def get_unwanted_rows():
    unwanted_rows_input = input(
        "Are there any rows you want to exclude from the calculation? Enter containing words separated by commas ..., ...: "
    )
    if unwanted_rows_input:
        global unwanted_rows
        unwanted_rows = unwanted_rows_input.split(",")
    print("UNWANTED: ", unwanted_rows)


def set_headers(table):
    headers = [date_header] + value_headers
    for header in headers:
        col_with_entry = table.df.astype(str).map(
            lambda x: header.lower() in x.lower() if isinstance(x, str) else False
        )
        if col_with_entry.any().any():
            col_index = table.df.columns[col_with_entry.any(axis=0)].tolist()[0]
            table.df.rename(columns={col_index: header}, inplace=True)
        start_index = table.df.apply(
            lambda row: row.str.contains(
                "|".join(value_headers), case=False, na=False
            ).any(),
            axis=1,
        ).idxmax()
        table.df = table.df.iloc[start_index:].reset_index(drop=True)
    return table.df


def remove_empty_rows(table):
    table.df = table.df[
        table.df[value_headers].apply(lambda row: row.str.strip().any(), axis=1)
    ]
    return table.df


def remove_unwanted_rows(table):
    table.df = table.df[
        ~table.df.apply(
            lambda row: row.str.contains(
                "|".join(unwanted_rows), case=False, na=False
            ).any(),
            axis=1,
        )
    ]
    return table.df


def safe_parse_date(string):
    list = string.split(" ")
    date = None
    for item in list:
        if not isinstance(date, datetime.datetime):
            try:
                if pd.notna(item) and isinstance(item, str):
                    date = parser.parse(item, dayfirst=True)
            except:
                pass

    return date if isinstance(date, datetime.datetime) else pd.NA


def find_dates(table, date_from, date_to):
    parsed_from = parser.parse(date_from, dayfirst=True)
    parsed_to = parser.parse(date_to, dayfirst=True)

    table.df[date_header] = table.df[date_header].apply(lambda x: safe_parse_date(x))
    table.df = table.df[
        (table.df[date_header] >= parsed_from) & (table.df[date_header] <= parsed_to)
    ]
    return table.df


def get_sum(table):
    sum = 0
    for entry in value_headers:

        newSum = (
            table.df[entry]
            .replace("", pd.NA)
            .str.replace(".", "")
            .str.replace(",", ".")
            .apply(pd.to_numeric, errors="coerce")
            .astype(float)
            .sum()
        )

        print(entry, "TOTAL: ", newSum)
        sum = sum + newSum
        print("SUM FOR TABLE: ", sum)
    return sum


def calculate_expenses():
    pdf_path = input("Path to pdf file: ")
    tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
    date_from = input("Start of date range to consider: ")
    date_to = input("End of date range to consider (included): ")
    get_table_headers()
    get_unwanted_rows()

    sum = 0
    for table in tables:
        table.df = set_headers(table)
        table_headers = table.df.columns.tolist()
        if len(table_headers) == len([date_header] + value_headers):
            table.df = remove_unwanted_rows(table)
            table.df = remove_empty_rows(table)
            table.df = find_dates(table, date_from, date_to)
            print("DATES TO CONSIDER: ", table.df)
            sum = sum + get_sum(table)
    print("---------------------------------------------------------")
    print("EXPENSES FOR SELECTED DATES: ", sum)


if __name__ == "__main__":
    calculate_expenses()
