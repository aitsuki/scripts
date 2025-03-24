# Image Processor

## 介绍

持续性的管理和压缩 Flutter 或 ReacNative 项目图片资源，有效的减小包体积。

- 将 `A` 目录的原始图片资源压缩到 `B` 目录，并生成常量类
- 此脚本会在 `A` 生成 `mapping` 文件，重复执行脚本不会导致图片重新压缩
- 删除/修改 `A` 目录中的图片会反应到 `B` 目录（删除或重新压缩）

ps：不要手动修改 `B` 目录的文件和生成的常量类，因为每次执行脚本后会被覆盖

## 使用

此脚本依赖 pillow 库，需要先安装：

```shell
pip install -r requirements.txt
```

然后查看脚本帮助文档，脚本必须从项目根目录执行。

```shell
python scripts/image.py -h
```

```
usage: image.py -i raw/images -o assets/images -g constants/images.ts

说明：将 raw/images 目录下的图片，压缩到 assets/images 目录，并生成 images.ts 常量文件

options:
  -h, --help            show this help message and exit
  -i INPUT_DIR, --input-dir INPUT_DIR
                        输入目录路径 (必须：例如 raw/images)
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        输出目录路径 (必须: 例如 assets/images)
  -g GENERATE_FILE, --generate-file GENERATE_FILE
                        生成常量文件（可选：支持ts和dart，例如：constants/images.ts）
  --ts-path TS_PATH     ts 相对路径（默认 @）
  -q QUALITY, --quality QUALITY
                        压缩质量 (1-100, 默认: 75)
  --no-webp             禁用PNG转WEBP (默认启用)
```

### React Native

React Native 的分辨率自适应图片资源使用文件名进行区分，可以将所有图片都放置在同一个目录。

- `icon.png` : 1 倍图，对应 android 的 dranwable-hdpi
- `icon@2x.png` : 2 倍图， 对应 android 的 drawable-xhdpi
- `icon@3x.png` : 3 倍图， 对应 android 的 drawable-xxhdpi

原始图片命名规则： `xxx_yyy_zzz.png`, `xxx_yyy_zzz@2x.png`, `xxx_yyy_zzz@3x.png`

```shell
python image.py -i images -o assets/images -g lib/res/images.dart
```

### Flutter

Flutter 的分辨率自适应图片资源是使用目录进行区分的（推荐只其中一种分辨率资源，例如2.0x）

- `images` : 1 倍图，对应 android 的 dranwable-hdpi
- `images/2.0x` ：2 倍图， 对应 android 的 drawable-xhdpi
- `images/3.0x` ：3 倍图， 对应 android 的 drawable-xxhdpi

原始图片命名规则：`xxx_yyy_zzz.png`

```shell
python image.py -i images -o assets/images/2.0x -g lib/res/images.dart
```

为了简单起见，脚本不支持同时输出多种分辨率的资源。
