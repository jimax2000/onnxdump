#!/usr/bin/env python3
"""
ONNX模型信息查看器 - CLI版本
快速查看ONNX模型的基本信息
"""

import sys
import argparse
import onnx
from collections import Counter


def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")


def print_tensor_info(tensor, prefix=""):
    """打印张量信息"""
    shape = get_tensor_shape(tensor)
    dtype = get_dtype_name(tensor.type.tensor_type.elem_type)
    print(f"{prefix}{tensor.name}")
    print(f"{prefix}  形状: {shape}")
    print(f"{prefix}  类型: {dtype}")


def get_tensor_shape(tensor):
    """获取张量形状"""
    try:
        dims = tensor.type.tensor_type.shape.dim
        shape = []
        for dim in dims:
            if dim.dim_value > 0:
                shape.append(str(dim.dim_value))
            elif dim.dim_param:
                shape.append(dim.dim_param)
            else:
                shape.append("?")
        return f"[{', '.join(shape)}]"
    except:
        return "[?]"


def get_dtype_name(dtype):
    """获取数据类型名称"""
    dtype_names = {
        0: "UNDEFINED", 1: "FLOAT32", 2: "UINT8", 3: "INT8",
        4: "UINT16", 5: "INT16", 6: "INT32", 7: "INT64",
        8: "STRING", 9: "BOOL", 10: "FLOAT16", 11: "DOUBLE",
        12: "UINT32", 13: "UINT64", 14: "COMPLEX64",
        15: "COMPLEX128", 16: "BFLOAT16"
    }
    return dtype_names.get(dtype, f"UNKNOWN({dtype})")


def show_model_info(model_path, show_operators=False):
    """显示模型信息"""
    try:
        onnx.checker.check_model(model_path)
        model = onnx.load(model_path)
        graph = model.graph

        # ========== 1. 元信息 ==========
        print_section("1. 元信息")

        print(f"\n模型名称: {model.graph.name or '(未命名)'}")

        # IR版本
        print(f"IR版本: {model.ir_version}")

        # Opset版本
        print("\nOpset版本:")
        for opset in model.opset_import:
            domain = opset.domain if opset.domain else "ai.onnx"
            print(f"  - {domain}: v{opset.version}")

        # 生产者信息
        if model.producer_name:
            version = f" {model.producer_version}" if model.producer_version else ""
            print(f"\n生产者: {model.producer_name}{version}")

        # Custom Metadata
        if model.metadata_props:
            print(f"\n自定义元数据 ({len(model.metadata_props)} 项):")
            for prop in model.metadata_props:
                print(f"  - {prop.key}: {prop.value}")
        else:
            print(f"\n自定义元数据: (无)")

        # ========== 2. 输入输出信息 ==========
        print_section("2. 输入输出信息")

        # 输入
        print(f"\n输入 ({len(graph.input)} 个):")
        for i, inp in enumerate(graph.input, 1):
            print(f"\n  [{i}] ", end="")
            print_tensor_info(inp, prefix="     ")

        # 输出
        print(f"\n输出 ({len(graph.output)} 个):")
        for i, out in enumerate(graph.output, 1):
            print(f"\n  [{i}] ", end="")
            print_tensor_info(out, prefix="     ")

        # ========== 3. 算子信息 ==========
        if show_operators:
            print_section("3. 算子信息")

            # 统计算子
            op_counter = Counter(node.op_type for node in graph.node)

            print(f"\n总节点数: {len(graph.node)}")
            print(f"算子种类: {len(op_counter)}")
            print(f"\n算子列表 (按使用次数排序):")

            for op_type, count in op_counter.most_common():
                print(f"  - {op_type:20s} : {count:4d} 个")

        # 额外统计
        initializer_count = len(graph.initializer)
        if initializer_count > 0:
            # 计算参数量
            import numpy as np
            total_params = sum(int(np.prod(init.dims)) for init in graph.initializer if init.dims)
            if total_params >= 1_000_000:
                params_str = f"{total_params / 1_000_000:.2f}M"
            elif total_params >= 1_000:
                params_str = f"{total_params / 1_000:.2f}K"
            else:
                params_str = str(total_params)
            print(f"\n其他: 初始值(权重) {initializer_count} 个 | 参数量: {params_str}")

        print(f"\n{'='*55}")
        print("  分析完成")
        print(f"{'='*55}\n")

        return 0

    except FileNotFoundError:
        print(f"错误: 找不到文件 '{model_path}'", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="ONNX模型信息查看器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s model.onnx              # 查看基本信息
  %(prog)s model.onnx --ops        # 显示算子信息
        """
    )

    parser.add_argument(
        "model",
        help="ONNX模型文件路径 (.onnx)"
    )

    parser.add_argument(
        "-o", "--ops",
        action="store_true",
        help="显示算子信息"
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s v1.0.0"
    )

    args = parser.parse_args()

    return show_model_info(args.model, show_operators=args.ops)


if __name__ == "__main__":
    sys.exit(main())
