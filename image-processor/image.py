import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Dict, List

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
        for root, _, files in os.walk(self.input_dir):
            for filename in files:
                if not self.input_re.match(filename):
                    # 忽略 mapping.json
                    if filename == self.mapping_path.name:
                        continue
                    print(f"跳过不符合命名规则的文件: {filename}")
                    continue

                input_path = Path(root) / filename
                file_hash = self._calculate_hash(input_path)
                current_state[filename] = file_hash
        return current_state

    def _sync_output_dir(self):
        """同步输出目录"""
        os.makedirs(self.output_dir, exist_ok=True)

        # 删除输出目录中不需要的文件（已在输入目录中删除或更名的文件）
        existing_files = set(os.listdir(self.output_dir))
        needed_files = {self._get_output_name(v) for v in self.current_state.keys()}
        for filename in existing_files - needed_files:
            os.remove(os.path.join(self.output_dir, filename))
            print("删除文件：" + filename)

        # 处理需要更新的文件
        for filename, hash in self.current_state.items():
            output_name = self._get_output_name(filename)
            output_path = Path(self.output_dir) / output_name
            input_path = Path(self.input_dir) / filename

            # 检查是否需要处理
            if (
                filename in self.mapping
                and self.mapping[filename] == hash
                and output_path.exists()
            ):
                continue

            # 执行图片处理
            try:
                self._process_image(input_path, output_path)
            except Exception as e:
                print(f"处理图片失败: {filename} - {str(e)}")

    def _get_output_name(self, filename: str) -> str:
        """生成输出文件名"""
        name, ext = os.path.splitext(filename)
        if ext.lower() == ".png":
            ext = ".webp"
        return f"{name}{ext}"

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
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

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

            output_names: List[str] = []
            for input_name in current_state.keys():
                output_name = self._get_output_name(input_name)
                output_name = re.sub(r"@(\d)x", "", output_name)  # 去掉 @2x 或 @3x
                output_names.append(output_name)

            output_names = sorted(output_names)
            for output_name in output_names:
                var_name = output_name.split(".")[0]
                var_name = re.sub(r"_(\w)", lambda m: m.group(1).upper(), var_name)
                path = self.output_dir + "/" + output_name
                f.write(f'  {var_name}: require("{self.ts_path}/{path}"),\n')
            f.write("};\n")

    def _generate_dart_file(self, current_state: Dict[str, str]):
        """生成 Dart 文件"""
        os.makedirs(os.path.dirname(self.generate_file), exist_ok=True)
        with open(self.generate_file, "w") as f:
            f.write("// Generate by python, should not be modified\n")
            class_name = os.path.splitext(os.path.basename(self.generate_file))[0]
            class_name = "".join(word.capitalize() for word in class_name.split("_"))
            f.write("class " + class_name + " {\n")

            output_names: List[str] = []
            for input_name in current_state.keys():
                output_name = self._get_output_name(input_name)
                output_name = re.sub(r"@(\d)x", "", output_name)  # 去掉 @2x 或 @3x
                output_names.append(output_name)

            output_names = sorted(output_names)
            for output_name in output_names:
                var_name = output_name.split(".")[0]
                var_name = re.sub(r"_(\w)", lambda m: m.group(1).upper(), var_name)
                path = self.output_dir + "/" + output_name
                f.write(f'  static const String {var_name} = "{path}";\n')
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

    # 校验参数
    if not parser.parse_args().input_dir:
        parser.error("-i 或 --input-dir 参数缺失")

    if not parser.parse_args().output_dir:
        parser.error("-o 或 --output-dir 参数缺失")

    return parser.parse_args()


if __name__ == "__main__":
    # 如果提供了参数，则使用命令行参数
    args = parse_args()
    processor = ImageProcessor(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        generate_file=args.generate_file,
        ts_path=args.ts_path,
        mapping_file=f"{args.input_dir}/_mapping.json",
        compress_quality=args.quality,
    )
    processor.run()
