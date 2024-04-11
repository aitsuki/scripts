"""
功能：
对A目录中所有图片进行压缩，保存到B目录。
- 支持增量文件和变更文件
- 支持文件名加密
- 支持png转换成webp
- 自动生成dart常量文件
- 支持修改文件名或删除文件

示例：
images/icon_foo.png 压缩为 assets/images/ghYmKtb.webp，并生成常量 static const String iconFoo = "assets/images/ghYmKtb.webp";

注意：
1. 输入目录中的文件名必须使用 snake_case 格式命名，不能以数字开头，例如：icon_foo.png
2. 输入目录中的文件名不能重复，例如：icon_foo.jpg 和 icon_foo.png 相同，后者会覆盖前者
3. 输入目录中的文件需要持久保留，删除输入目录中的文件会导致输出目录文件也被删除，
   可以利用这一点删除不需要的图片或者修改图片名

用法：
1. 将脚本放到flutter项目根目录下
2. 修改 CFG_ 开头的配置，其中 CFG_ENCRYPT_SALT 必须修改，推荐设为App名字
3. 安装pillow依赖：pip install pillow
4. 在项目根目录下执行脚本：python flutter_image_compress.py
"""

import hashlib
import os
import re
from typing import List

from PIL import Image

###################################################################################################################
## 加密配置
CFG_ENCRYPT_ENABLED = True
CFG_ENCRYPT_SALT = "xyz"  # 加盐是为了区分不同的App相同名字的图片，防止出现相同hash值
CFG_ENCRYPT_LEN = 5  # 加密长度
CFG_ENCRYPT_ENHANCED = True  # 是否增强加密算法，生成的文件名会被加密成更随机的字符串（大小写字母+数字），且长度会稍微变长。

## 生成dart文件配置: /lib/res/images.g.dart
CFG_DART_DIR = "res"  # /lib/res/
CFG_DART_CLASS_NAME = "Images"  # 文件名为images.g.dart，类名为 Images

## 图片输入/输出目录
CFG_INPUT_DIR = "images"
CFG_OUTPUT_DIR = os.path.join("assets", "images")
CFG_MAPPING = "imgs_mapping.txt"

## 图片压缩质量
CFG_COMPRESS_QUALITY = 75
###################################################################################################################

input_re = r"^[a-z](_?[0-9a-z])*\.(png|jpg|jpeg|webp)$"
output_re = r"^[a-zA-Z0-9]*\.(jpg|jpeg|webp)$"
alphabet = "abcdefghijkmnopqrstuvwxyz123456789ABCDEFGHJKLMNPQRSTUVWXYZ"


class File:
    def __init__(self, filename: str):
        self.f = filename
        self.path = os.path.join(CFG_INPUT_DIR, filename)
        self.name = os.path.splitext(filename)[0]
        self.ext = os.path.splitext(filename)[1][1:]
        self.should_compress = False
        self.o_name = encrypt(self.name)
        self.o_ext = "webp" if self.ext == "png" or self.ext == "webp" else "jpg"
        self.o_filename = self.o_name + "." + self.o_ext
        self.o_path = os.path.join(CFG_OUTPUT_DIR, self.o_filename)


def encrypt(name: str) -> str:
    if not CFG_ENCRYPT_ENABLED:
        return name
    hash = hashlib.sha1((name + CFG_ENCRYPT_SALT).encode())
    hash_str = hash.hexdigest()[:CFG_ENCRYPT_LEN]
    if CFG_ENCRYPT_ENHANCED:
        num = int.from_bytes(hash_str.encode("ascii"), byteorder="big")
        hash_str = ""
        while num > 0:
            num, mod = divmod(num, len(alphabet))
            hash_str = alphabet[mod] + hash_str
        return hash_str
    return hash_str

def file_sha1(file: File) -> str:
    with open(file.path, 'rb') as f:
        return hashlib.sha1(f.read()).hexdigest()

def resolve_files() -> List[File]:
    files: List[File] = []
    # 读取输入目录
    for f in os.listdir(CFG_INPUT_DIR):
        if re.match(input_re, f):
            files.append(File(f))
        else:
            print("ignore illegal input file: " + f)

    if not os.path.exists(CFG_OUTPUT_DIR):
        os.makedirs(CFG_OUTPUT_DIR)

    # 删除输出目录中不需要的文件（已在输入目录中删除或更名的文件）
    existing_names: List[str] = []
    for f in os.listdir(CFG_OUTPUT_DIR):
        name = os.path.splitext(f)[0]
        if name not in [ff.o_name for ff in files]:
            os.remove(os.path.join(CFG_OUTPUT_DIR, f))
            print("delete file: " + f)
        else:
            existing_names.append(name)

    # 读取mapping，用于检测文件是否发生变化（同名文件，不同内容）
    old_mapping = {}
    with open(CFG_MAPPING, "a+") as mf:
        mf.seek(0)
        for line in mf.read().splitlines():
            m = line.split(" -> ")
            if len(m) == 2:
                old_mapping[m[0]] = m[1]

    new_mapping = {}
    for file in files:
        new_mapping[file.name] = file_sha1(file)
        if file.o_name not in existing_names:
            file.should_compress = True
        elif new_mapping[file.name] != old_mapping.get(file.name):
            print(f"file has been changed: {file.path}")
            file.should_compress = True

    # 重新写入mapping
    with open(CFG_MAPPING, "w") as mf:
         for k, v in new_mapping.items():
             mf.write(f"{k} -> {v}\n")

    return files

def humansize(filepath: str):
    nbytes: float = os.path.getsize(filepath)
    suffixes = ["b", "kb", "mb"]
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.0
        i += 1
    f = ("%.2f" % nbytes).rstrip("0").rstrip(".")
    return "%s %s" % (f, suffixes[i])


def compress_file(f: File):
    Image.open(f.path).save(
        f.o_path, f.o_ext, optimize=True, quality=CFG_COMPRESS_QUALITY
    )
    print(
        f"compress file: {f.name} -> {f.o_name}, {humansize(f.path)} -> {humansize(f.o_path)}"
    )


def snake_to_camel_case(snake: str):
    components = snake.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def generate_dart_file(files: List[File]):
    dart_filepath = os.path.join(
        "lib", CFG_DART_DIR, CFG_DART_CLASS_NAME.lower() + ".g.dart"
    )
    if not os.path.exists(dart_filepath):
        os.makedirs(os.path.dirname(dart_filepath), exist_ok=True)

    with open(dart_filepath, "w") as df:
        df.write("// This file is generated by python and should not be modified\n\n")
        df.write("class " + CFG_DART_CLASS_NAME + " {\n")
        for f in files:
            image_path = f.o_path.replace("\\", "/")
            df.write(
                f"  static const String {snake_to_camel_case(f.name)} = '{image_path}';\n"
            )
        df.write("}\n")


files = resolve_files()
for f in files:
    if f.should_compress:
        compress_file(f)
generate_dart_file(files)
