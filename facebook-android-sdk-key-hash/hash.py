import base64
import argparse


def main():
    parser = argparse.ArgumentParser(description="Process SHA1 hex string.")
    parser.add_argument("sha1_hex_string", type=str, help="SHA1 hex string to process")
    args = parser.parse_args()

    sha1_hex_string = args.sha1_hex_string
    # 处理 sha1_hex_string 的逻辑
    print(f"Processing SHA1 hex string: {sha1_hex_string}")
    sha1_bytes = bytes.fromhex(sha1_hex_string.replace(":", ""))
    facebook_hash = base64.b64encode(sha1_bytes).decode("utf-8")
    print(facebook_hash)


if __name__ == "__main__":
    main()
