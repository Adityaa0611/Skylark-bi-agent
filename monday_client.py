import requests

MONDAY_URL = "https://api.monday.com/v2"


def run_query(query: str, token: str, variables: dict = None) -> dict:
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "API-Version": "2024-10",
    }
    try:
        resp = requests.post(
            MONDAY_URL,
            json={"query": query, "variables": variables or {}},
            headers=headers,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            return {"success": False, "errors": data["errors"]}
        return {"success": True, "data": data}
    except requests.exceptions.RequestException as e:
        return {"success": False, "errors": [str(e)]}


def get_board_items(board_id: str, token: str, limit: int = 500) -> dict:
    all_items = []
    cursor = None
    board_name = None
    board_columns = []

    while True:
        query = """
        query($boardId: [ID!], $limit: Int!, $cursor: String) {
          boards(ids: $boardId) {
            name
            columns { id title type }
            items_page(limit: $limit, cursor: $cursor) {
              cursor
              items {
                id
                name
                column_values { id text type value }
              }
            }
          }
        }
        """
        variables = {"boardId": [board_id], "limit": limit, "cursor": cursor}
        result = run_query(query, token, variables)

        if not result["success"]:
            return {"success": False, "errors": result["errors"], "items": all_items, "columns": board_columns}

        boards = result["data"]["data"]["boards"]
        if not boards:
            return {"success": False, "errors": ["Board not found or no access"], "items": [], "columns": []}

        board = boards[0]
        board_name = board["name"]
        board_columns = board["columns"]
        page = board["items_page"]
        all_items.extend(page["items"])
        cursor = page.get("cursor")

        if not cursor:
            break

    return {"success": True, "board_name": board_name, "items": all_items, "columns": board_columns}