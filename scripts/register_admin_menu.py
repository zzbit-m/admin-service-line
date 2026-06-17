import os
import sys
import httpx
from dotenv import load_dotenv

# Load env file
load_dotenv()

LINE_MESSAGING_ACCESS_TOKEN = os.getenv("LINE_MESSAGING_ACCESS_TOKEN")
LINE_LIFF_ID = os.getenv("LINE_LIFF_ID")

if not LINE_MESSAGING_ACCESS_TOKEN:
    print("Error: LINE_MESSAGING_ACCESS_TOKEN not found in .env")
    sys.exit(1)

if not LINE_LIFF_ID:
    print("Error: LINE_LIFF_ID not found in .env")
    sys.exit(1)


def create_rich_menu():
    url = "https://api.line.me/v2/bot/richmenu"
    headers = {
        "Authorization": f"Bearer {LINE_MESSAGING_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Define a 3-column compact rich menu (2500x843)
    # Area A: New Request, Area B: My Requests, Area C: Admin Dashboard
    payload = {
        "size": {
            "width": 2500,
            "height": 843
        },
        "selected": False,  # False so it's not the default menu for everyone
        "name": "Admin Rich Menu",
        "chatBarText": "Admin Menu",
        "areas": [
            {
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": 833,
                    "height": 843
                },
                "action": {
                    "type": "uri",
                    "label": "New Request",
                    "uri": f"https://liff.line.me/{LINE_LIFF_ID}?page=new"
                }
            },
            {
                "bounds": {
                    "x": 833,
                    "y": 0,
                    "width": 833,
                    "height": 843
                },
                "action": {
                    "type": "uri",
                    "label": "My Requests",
                    "uri": f"https://liff.line.me/{LINE_LIFF_ID}?page=requests"
                }
            },
            {
                "bounds": {
                    "x": 1666,
                    "y": 0,
                    "width": 834,
                    "height": 843
                },
                "action": {
                    "type": "uri",
                    "label": "Admin Dashboard",
                    "uri": f"https://liff.line.me/{LINE_LIFF_ID}?page=admin"
                }
            }
        ]
    }

    print("Registering Rich Menu structure with LINE...")
    resp = httpx.post(url, headers=headers, json=payload)
    if resp.status_code not in [200, 201]:
        print(f"Failed to create rich menu: {resp.status_code} {resp.text}")
        sys.exit(1)

    rich_menu_id = resp.json().get("richMenuId")
    print(f"Successfully registered Rich Menu. ID: {rich_menu_id}")
    return rich_menu_id


def upload_rich_menu_image(rich_menu_id: str, image_path: str):
    if not os.path.exists(image_path):
        print(f"Error: Image path does not exist: {image_path}")
        sys.exit(1)

    url = f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content"
    headers = {
        "Authorization": f"Bearer {LINE_MESSAGING_ACCESS_TOKEN}",
        "Content-Type": "image/png"
    }

    print(f"Uploading image {image_path} for Rich Menu {rich_menu_id}...")
    with open(image_path, "rb") as f:
        image_data = f.read()

    resp = httpx.post(url, headers=headers, content=image_data)
    if resp.status_code != 200:
        print(f"Failed to upload image: {resp.status_code} {resp.text}")
        sys.exit(1)

    print("Successfully uploaded Rich Menu background image!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/register_admin_menu.py <path_to_resized_3_button_image>")
        sys.exit(1)

    img_path = sys.argv[1]
    rich_menu_id = create_rich_menu()
    upload_rich_menu_image(rich_menu_id, img_path)

    print("\n" + "="*50)
    print("STEP COMPLETED!")
    print(f"Please copy the following line and add it to your .env file:")
    print(f"LINE_ADMIN_RICH_MENU_ID={rich_menu_id}")
    print("="*50)
