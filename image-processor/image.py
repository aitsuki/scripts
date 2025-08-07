import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Dict

from PIL import Image


class ImageProcessor:
    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        generate_file: str,
        ts_path: str,
        mapping_file: str,
        compress_quality: int,
        encrypt_length: int,
        encrypt_sault: str,
    ):
        self.input_re = re.compile(r"^[a-z](\w)*(@2x|@3x)?\.(png|jpg|jpeg|webp)$")
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.generate_file = generate_file
        self.ts_path = ts_path
        self.mapping_path = Path(mapping_file)
        self.mapping: Dict[str, str] = {}
        self.current_state: Dict[str, str] = self._scan_input_dir()
        self.compress_quality = compress_quality
        self.encrypt_length = encrypt_length
        self.encrypt_sault = encrypt_sault

    def run(self) -> None:
        self._load_mapping()
        self._scan_input_dir()
        self._sync_output_dir()
        self._save_mapping()
        self._generate_file()

    def _load_mapping(self) -> None:
        if self.mapping_path.exists():
            with open(self.mapping_path, "r") as f:
                self.mapping = json.load(f)

    def _save_mapping(self) -> None:
        os.makedirs(os.path.dirname(self.mapping_path), exist_ok=True)
        with open(self.mapping_path, "w") as f:
            json.dump(self.current_state, f, indent=2)

    def _scan_input_dir(self) -> Dict[str, str]:
        """扫描输入目录并返回当前状态"""
        current_state: Dict[str, str] = {}
        input_dir_path = Path(self.input_dir)
        for root, _, files in os.walk(self.input_dir):
            for filename in files:
                if not self.input_re.match(filename):
                    # 忽略 mapping.json
                    if filename == self.mapping_path.name:
                        continue
                    print(f"跳过不符合命名规则的文件: {filename}")
                    continue

                input_path = Path(root) / filename
                # 使用相对路径作为键名
                rel_path = input_path.relative_to(input_dir_path).as_posix()
                file_hash = self._calculate_hash(input_path)
                current_state[rel_path] = file_hash
        return current_state

    def _sync_output_dir(self):
        """同步输出目录"""
        os.makedirs(self.output_dir, exist_ok=True)
        input_dir_path = Path(self.input_dir)

        # 删除输出目录中不需要的文件
        existing_files = set()
        for root, _, files in os.walk(self.output_dir):
            for filename in files:
                rel_path = Path(root) / filename
                existing_files.add(rel_path.relative_to(self.output_dir).as_posix())

        needed_files = {
            self._get_output_name(rel_path) for rel_path in self.current_state.keys()
        }
        for filename in existing_files - needed_files:
            file_path = Path(self.output_dir) / filename
            os.remove(file_path)
            print("删除文件：" + filename)

        # 处理需要更新的文件
        for rel_path, hash_val in self.current_state.items():
            input_path = input_dir_path / rel_path
            output_path = Path(self.output_dir) / self._get_output_name(rel_path)

            # 检查是否需要处理
            if (
                rel_path in self.mapping
                and self.mapping[rel_path] == hash_val
                and output_path.exists()
            ):
                continue

            # 执行图片处理
            try:
                self._process_image(input_path, output_path)
            except Exception as e:
                print(f"处理图片失败: {rel_path} - {str(e)}")

    def _get_output_name(self, rel_path: str) -> str:
        """生成输出文件名（加密文件名）"""
        path_obj = Path(rel_path)
        # 获取目录部分
        dir_part = path_obj.parent
        # 处理文件名部分
        filename = path_obj.name
        name, ext = os.path.splitext(filename)

        # 分离基础名称和倍率后缀
        scale_match = re.search(r"(@\dx)$", name)
        if scale_match:
            base_name = name[: scale_match.start()]
            scale_suffix = scale_match.group(1)
        else:
            base_name = name
            scale_suffix = ""

        # 只加密基础名称部分
        encrypted_base = self._encrypt(base_name)
        # 重新组合：加密后的基础名 + 倍率后缀
        encrypted_name = encrypted_base + scale_suffix

        if ext.lower() == ".png":
            ext = ".webp"
        # 组合目录和加密后的文件名
        return str(dir_part / f"{encrypted_name}{ext}")

    def _process_image(self, input_path: Path, output_path: Path):
        """处理图片"""
        img = Image.open(input_path)  # type: ignore

        ext = output_path.suffix.lower()
        save_kwargs = {"quality": self.compress_quality}

        if ext == ".webp":
            save_kwargs["method"] = 6

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        img.save(output_path, **save_kwargs)  # type: ignore

        # 获取压缩后文件大小（KB）
        original_size = os.path.getsize(input_path) / 1024
        compressed_size = os.path.getsize(output_path) / 1024  # KB
        print(
            f"{os.path.basename(input_path):<30} {original_size:8.2f} KB → {compressed_size:8.2f} KB ({compressed_size / original_size * 100:6.2f}%)"
        )

    def _calculate_hash(self, filepath: Path) -> str:
        """计算文件哈希"""
        with open(filepath, "rb") as f:
            return hashlib.sha1(f.read()).hexdigest()

    def _encrypt(self, name: str) -> str:
        """加密文件名（不影响常量名）"""
        if self.encrypt_length == 0:
            return name
        hash_obj = hashlib.sha1((name + self.encrypt_sault).encode())
        return hash_obj.hexdigest()[: self.encrypt_length]

    def _generate_file(self):
        """生成常量文件"""
        if not self.generate_file:
            return

        # 生成文件扩展名
        ext = os.path.splitext(self.generate_file)[1].lower()
        if ext == ".ts":
            self._generate_ts_file(self.current_state)
        elif ext == ".dart":
            self._generate_dart_file(self.current_state)
        else:
            print(f"不支持的文件类型: {ext}")

    def _generate_ts_file(self, current_state: Dict[str, str]):
        """生成 TypeScript 文件"""
        os.makedirs(os.path.dirname(self.generate_file), exist_ok=True)
        with open(self.generate_file, "w") as f:
            f.write("// Auto-generated by image processor\n")
            const_name = os.path.splitext(os.path.basename(self.generate_file))[0]
            f.write("export const " + const_name + " = {\n")

            # 用于存储变量名和路径的映射
            var_path_map = {}

            for rel_path in current_state.keys():
                # 获取原始文件名（用于生成常量名）
                path_obj = Path(rel_path)
                # 获取基本名（不含扩展名）
                name_without_ext = path_obj.stem
                # 去掉倍率后缀
                name_without_scale = re.sub(r"@(\d)x", "", name_without_ext)
                # 生成变量名
                var_name = re.sub(
                    r"_(\w)", lambda m: m.group(1).upper(), name_without_scale
                )

                # 获取加密后的输出路径
                output_name = self._get_output_name(rel_path)
                # 去除路径中的@xx后缀
                output_name = re.sub(r"@(\d)x", "", output_name)
                # 组合完整路径
                full_path = f"{self.ts_path}/{self.output_dir}/{output_name}"

                # 存储变量名和路径
                var_path_map[var_name] = full_path

            # 按变量名排序
            sorted_var_names = sorted(var_path_map.keys())
            for var_name in sorted_var_names:
                full_path = var_path_map[var_name]
                f.write(f'  {var_name}: require("{full_path}"),\n')

            f.write("};\n")

    def _generate_dart_file(self, current_state: Dict[str, str]):
        """生成 Dart 文件"""
        os.makedirs(os.path.dirname(self.generate_file), exist_ok=True)
        with open(self.generate_file, "w") as f:
            f.write("// Generate by python, should not be modified\n")
            class_name = os.path.splitext(os.path.basename(self.generate_file))[0]
            class_name = "".join(word.capitalize() for word in class_name.split("_"))
            f.write("class " + class_name + " {\n")

            # 用于存储变量名和路径的映射
            var_path_map = {}

            for rel_path in current_state.keys():
                # 获取原始文件名（用于生成常量名）
                path_obj = Path(rel_path)
                # 获取基本名（不含扩展名）
                name_without_ext = path_obj.stem
                # 去掉倍率后缀
                name_without_scale = re.sub(r"@(\d)x", "", name_without_ext)
                # 生成变量名
                var_name = re.sub(
                    r"_(\w)", lambda m: m.group(1).upper(), name_without_scale
                )

                # 获取加密后的输出路径
                output_name = self._get_output_name(rel_path)

                # 组合完整路径
                full_path = f"{self.output_dir}/{output_name}"

                # 存储变量名和路径
                var_path_map[var_name] = full_path

            # 按变量名排序
            sorted_var_names = sorted(var_path_map.keys())
            for var_name in sorted_var_names:
                full_path = var_path_map[var_name]
                f.write(f'  static const String {var_name} = "{full_path}";\n')

            f.write("}\n")


def parse_args():
    parser = argparse.ArgumentParser(
        usage="image.py -i raw/images -o assets/images -g constants/images.ts",
        description="说明：将 raw/images 目录下的图片，压缩到 assets/images 目录，并生成 images.ts 常量文件",
    )

    parser.add_argument(
        "-i",
        "--input-dir",
        help="输入目录路径 (必须：例如 raw/images)",
        default="raw",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        help="输出目录路径 (必须: 例如 assets/images)",
        default="images/3.0x",
    )
    parser.add_argument(
        "-g",
        "--generate-file",
        help="生成常量文件（可选：支持ts和dart，例如：constants/images.ts）",
        default="lib/images.dart",
    )
    parser.add_argument(
        "--ts-path",
        default="@",
        help="ts 相对路径（默认 @）",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=75,
        help="压缩质量 (1-100, 默认: 75)",
    )
    parser.add_argument(
        "-e",
        "--encrypt-length",
        type=int,
        default=6,
        help="加密后hash截取长度，0~40，0表示不加密，推荐6",
    )
    parser.add_argument(
        "-es",
        "--encrypt-sault",
        default="myapp",
        help="加密加盐，通常是app名字",
    )

    args = parser.parse_args()

    # 校验参数
    if not args.input_dir:
        parser.error("-i 或 --input-dir 参数缺失")

    if not args.output_dir:
        parser.error("-o 或 --output-dir 参数缺失")

    return args


if __name__ == "__main__":
    args = parse_args()
    processor = ImageProcessor(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        generate_file=args.generate_file,
        ts_path=args.ts_path,
        mapping_file=f"{args.input_dir}/_mapping.json",
        compress_quality=args.quality,
        encrypt_length=args.encrypt_length,
        encrypt_sault=args.encrypt_sault,
    )
    processor.run()
