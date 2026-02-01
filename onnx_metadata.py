#!/usr/bin/env python3
"""
ONNX模型Custom Metadata处理工具
支持导出和导入ONNX模型的custom metadata
"""

import sys
import argparse
import onnx
from pathlib import Path


def export_metadata(model_path, output_file):
    """导出ONNX模型的custom metadata到文本文件

    Args:
        model_path: ONNX模型文件路径
        output_file: 输出的文本文件路径

    Returns:
        0成功, 1失败
    """
    try:
        onnx.checker.check_model(model_path)
        model = onnx.load(model_path)

        if not model.metadata_props:
            print(f"警告: 模型中没有custom metadata", file=sys.stderr)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("")
            return 0

        with open(output_file, 'w', encoding='utf-8') as f:
            for prop in model.metadata_props:
                f.write(f"{prop.key}\t{prop.value}\n")

        print(f"成功导出 {len(model.metadata_props)} 条metadata到: {output_file}")
        return 0

    except FileNotFoundError:
        print(f"错误: 找不到文件 '{model_path}'", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


def import_metadata(model_path, metadata_file, output_path, mode="merge"):
    """从文本文件导入custom metadata到ONNX模型

    Args:
        model_path: 输入ONNX模型文件路径
        metadata_file: metadata文本文件路径
        output_path: 输出ONNX模型文件路径
        mode: 导入模式, "replace"=完全替换, "merge"=合并(默认)

    Returns:
        0成功, 1失败
    """
    try:
        # 读取metadata文件
        metadata_dict = {}
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if not line:
                        continue
                    # 按第一个tab分割
                    parts = line.split('\t', 1)
                    if len(parts) == 2:
                        key, value = parts
                        metadata_dict[key] = value
                    else:
                        print(f"警告: 跳过无效行: {line}", file=sys.stderr)
        except FileNotFoundError:
            print(f"错误: 找不到metadata文件 '{metadata_file}'", file=sys.stderr)
            return 1

        if not metadata_dict:
            print(f"警告: metadata文件为空", file=sys.stderr)

        # 加载模型
        onnx.checker.check_model(model_path)
        model = onnx.load(model_path)

        original_count = len(model.metadata_props)

        # 根据模式处理metadata
        if mode == "replace":
            # 完全替换: 清空所有metadata
            del model.metadata_props[:]

        # 合并模式: 先删除文件中存在的key的旧值
        elif mode == "merge":
            keys_to_remove = []
            for i, prop in enumerate(model.metadata_props):
                if prop.key in metadata_dict:
                    keys_to_remove.append(i)
            # 从后往前删除, 避免索引问题
            for i in reversed(keys_to_remove):
                del model.metadata_props[i]

        # 添加新的metadata
        for key, value in metadata_dict.items():
            prop = model.metadata_props.add()
            prop.key = key
            prop.value = value

        # 保存模型
        onnx.save(model, output_path)

        if mode == "replace":
            print(f"成功导入 {len(metadata_dict)} 条metadata到: {output_path}")
            print(f"  (原 {original_count} 条已全部替换)")
        else:
            new_count = len(model.metadata_props)
            added_count = new_count - (original_count - len(keys_to_remove))
            print(f"成功导入 {len(metadata_dict)} 条metadata到: {output_path}")
            print(f"  (更新 {len(keys_to_remove)} 条, 新增 {added_count} 条, 保留 {new_count - len(metadata_dict)} 条原有)")

        return 0

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


def list_metadata(model_path):
    """列出ONNX模型的custom metadata

    Args:
        model_path: ONNX模型文件路径

    Returns:
        0成功, 1失败
    """
    try:
        onnx.checker.check_model(model_path)
        model = onnx.load(model_path)

        if not model.metadata_props:
            print("模型中没有custom metadata")
            return 0

        print(f"\n模型 '{model.graph.name or '(未命名)'}' 的Custom Metadata:")
        print(f"共 {len(model.metadata_props)} 条:\n")
        for i, prop in enumerate(model.metadata_props, 1):
            print(f"  [{i}] {prop.key}: {prop.value}")
        print()

        return 0

    except FileNotFoundError:
        print(f"错误: 找不到文件 '{model_path}'", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="ONNX模型Custom Metadata处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s export model.onnx metadata.txt          # 导出metadata到文件
  %(prog)s import model.onnx metadata.txt new.onnx # 导入metadata(合并模式)
  %(prog)s import model.onnx metadata.txt new.onnx --mode replace  # 完全替换模式
  %(prog)s list model.onnx                         # 列出模型的metadata

metadata文件格式:
  key1<TAB>value1
  key2<TAB>value2
  ...
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # export命令
    export_parser = subparsers.add_parser("export", help="导出metadata到文本文件")
    export_parser.add_argument("model", help="输入ONNX模型文件 (.onnx)")
    export_parser.add_argument("output", help="输出metadata文本文件")

    # import命令
    import_parser = subparsers.add_parser("import", help="从文本文件导入metadata")
    import_parser.add_argument("model", help="输入ONNX模型文件 (.onnx)")
    import_parser.add_argument("metadata", help="metadata文本文件")
    import_parser.add_argument("output", help="输出ONNX模型文件 (.onnx)")
    import_parser.add_argument(
        "--mode",
        choices=["merge", "replace"],
        default="merge",
        help="导入模式: merge=合并更新(默认), replace=完全替换"
    )

    # list命令
    list_parser = subparsers.add_parser("list", help="列出模型的metadata")
    list_parser.add_argument("model", help="ONNX模型文件 (.onnx)")

    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s v1.0.0"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "export":
        return export_metadata(args.model, args.output)
    elif args.command == "import":
        return import_metadata(args.model, args.metadata, args.output, args.mode)
    elif args.command == "list":
        return list_metadata(args.model)

    return 1


if __name__ == "__main__":
    sys.exit(main())
