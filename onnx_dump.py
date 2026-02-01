#!/usr/bin/env python3
"""
ONNX模型信息查看器 - CLI Pretty版本
使用rich库输出漂亮的表格
"""

import sys
import argparse
import onnx
from collections import Counter
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
except ImportError as e:
    print(f"错误: 需要安装 rich 库")
    print(f"详情: {e}")
    print("请运行: pip install rich")
    sys.exit(1)


console = Console()


def get_tensor_shape(tensor):
    """获取张量形状"""
    try:
        dims = tensor.type.tensor_type.shape.dim
        shape = []
        for dim in dims:
            if dim.dim_value > 0:
                shape.append(str(dim.dim_value))
            elif dim.dim_param:
                shape.append(f"[dim]{dim.dim_param}[/dim]")
            else:
                shape.append("[dim]?[/dim]")
        return f"[{' × '.join(shape)}]"
    except:
        return "[?]"


def get_dtype_name(dtype):
    """获取数据类型名称"""
    dtype_names = {
        0: "UNDEFINED", 1: "[green]FLOAT32[/green]", 2: "UINT8", 3: "INT8",
        4: "UINT16", 5: "INT16", 6: "INT32", 7: "[cyan]INT64[/cyan]",
        8: "STRING", 9: "BOOL", 10: "[yellow]FLOAT16[/yellow]",
        11: "[blue]DOUBLE[/blue]", 12: "UINT32", 13: "UINT64",
        14: "COMPLEX64", 15: "COMPLEX128", 16: "[magenta]BFLOAT16[/magenta]"
    }
    return dtype_names.get(dtype, f"[red]UNKNOWN({dtype})[/red]")


def show_metadata(model):
    """显示元信息"""
    graph = model.graph

    # 构建元信息内容
    content = []

    # 模型名称
    name = model.graph.name or "[dim](未命名)[/dim]"
    content.append(f"[bold cyan]模型名称:[/bold cyan] {name}")

    # IR版本
    content.append(f"[bold cyan]IR版本:[/bold cyan] {model.ir_version}")

    # Opset版本
    opset_lines = []
    for opset in model.opset_import:
        domain = opset.domain if opset.domain else "ai.onnx"
        opset_lines.append(f"    • [yellow]{domain}[/yellow]: v{opset.version}")
    content.append(f"[bold cyan]Opset版本:[/bold cyan]\n" + "\n".join(opset_lines))

    # 生产者信息
    if model.producer_name:
        version = f" [dim]v{model.producer_version}[/dim]" if model.producer_version else ""
        content.append(f"[bold cyan]生产者:[/bold cyan] {model.producer_name}{version}")

    # 自定义元数据
    if model.metadata_props:
        meta_lines = []
        for prop in model.metadata_props:
            # 截断过长的值
            value = prop.value
            if len(value) > 50:
                value = value[:47] + "..."
            meta_lines.append(f"    • [blue]{prop.key}[/blue]: {value}")
        content.append(f"[bold cyan]自定义元数据[/bold cyan] [dim]({len(model.metadata_props)} 项)[/dim]:\n" + "\n".join(meta_lines))
    else:
        content.append(f"[bold cyan]自定义元数据:[/bold cyan] [dim](无)[/dim]")

    # 统计摘要
    total_nodes = len(graph.node)
    total_inputs = len(graph.input)
    total_outputs = len(graph.output)
    total_initializers = len(graph.initializer)
    op_types = len(set(node.op_type for node in graph.node))

    # 计算参数量
    import numpy as np
    total_params = sum(int(np.prod(init.dims)) for init in graph.initializer if init.dims)
    if total_params >= 1_000_000:
        params_str = f"{total_params / 1_000_000:.2f}M"
    elif total_params >= 1_000:
        params_str = f"{total_params / 1_000:.2f}K"
    else:
        params_str = str(total_params)

    content.append(f"\n[bold cyan]统计摘要:[/bold cyan]")
    content.append(f"    • 输入: [yellow]{total_inputs}[/yellow] | 输出: [yellow]{total_outputs}[/yellow] | 节点: [yellow]{total_nodes}[/yellow]")
    content.append(f"    • 算子种类: [yellow]{op_types}[/yellow] | 权重: [yellow]{total_initializers}[/yellow] | 参数量: [bold green]{params_str}[/bold green]")

    console.print(Panel("\n".join(content), title="[bold white]1. 元信息[/bold white]", title_align="left", border_style="bright_blue"))


def show_inputs_outputs(graph):
    """显示输入输出表格"""
    table = Table(title="[bold white]2. 输入/输出[/bold white]", show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("类型", style="cyan", width=8)
    table.add_column("名称", style="white", ratio=3)
    table.add_column("形状", style="yellow", ratio=2)
    table.add_column("数据类型", style="green", width=12)

    # 输入
    for inp in graph.input:
        shape = get_tensor_shape(inp)
        dtype = get_dtype_name(inp.type.tensor_type.elem_type)
        table.add_row("[green]IN[/green]", inp.name, shape, dtype)

    # 输出
    for out in graph.output:
        shape = get_tensor_shape(out)
        dtype = get_dtype_name(out.type.tensor_type.elem_type)
        table.add_row("[blue]OUT[/blue]", out.name, shape, dtype)

    console.print(table)


def show_operators_table(graph):
    """显示算子表格"""
    op_counter = Counter(node.op_type for node in graph.node)
    total_nodes = len(graph.node)

    table = Table(title="[bold white]3. 算子信息[/bold white]", show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("算子类型", style="cyan", ratio=3)
    table.add_column("数量", style="yellow", width=8)
    table.add_column("占比", style="green", width=10)
    table.add_column("分布", style="white", ratio=2)

    # 计算百分比并生成条形图
    for op_type, count in op_counter.most_common():
        percentage = (count / total_nodes) * 100
        bar_length = int(percentage / 2)
        bar = "█" * bar_length

        table.add_row(
            op_type,
            f"[yellow]{count}[/yellow]",
            f"[green]{percentage:.1f}%[/green]",
            f"[bright_black]{bar}[/bright_black]"
        )

    console.print(table)


def show_initializers(graph):
    """显示权重信息（如果有）"""
    if not graph.initializer:
        return

    table = Table(title="[bold white]4. 权重/初始值[/bold white]", show_header=True, header_style="bold magenta", box=box.ROUNDED, caption=f"[dim]共 {len(graph.initializer)} 个[/dim]")
    table.add_column("名称", style="white", ratio=3)
    table.add_column("形状", style="yellow", ratio=2)
    table.add_column("数据类型", style="green", width=12)
    table.add_column("元素数", style="cyan", width=10)

    import numpy as np
    for init in graph.initializer[:20]:  # 最多显示20个
        shape = str(list(init.dims))
        dtype = get_dtype_name(init.data_type)
        total_elements = int(np.prod(init.dims)) if init.dims else 0

        # 格式化数字
        if total_elements >= 1_000_000:
            elements_str = f"{total_elements/1_000_000:.1f}M"
        elif total_elements >= 1_000:
            elements_str = f"{total_elements/1_000:.1f}K"
        else:
            elements_str = str(total_elements)

        table.add_row(init.name, shape, dtype, elements_str)

    if len(graph.initializer) > 20:
        table.add_row(
            f"[dim]... 还有 {len(graph.initializer) - 20} 个[/dim]",
            "[dim]...[/dim]",
            "[dim]...[/dim]",
            "[dim]...[/dim]"
        )

    console.print(table)


def show_model_info(model_path, show_operators=True, show_weights=False):
    """显示模型信息"""
    try:
        onnx.checker.check_model(model_path)
        model = onnx.load(model_path)
        graph = model.graph

        console.print()
        console.print(Panel(f"[bold cyan]ONNX 模型分析[/bold cyan]", border_style="bright_blue", padding=(0, 1)))

        show_metadata(model)
        console.print()
        show_inputs_outputs(graph)
        console.print()

        if show_operators:
            show_operators_table(graph)
            console.print()

        if show_weights:
            show_initializers(graph)
            console.print()

        return 0

    except FileNotFoundError:
        console.print(Text(f"错误: 找不到文件 '{model_path}'", style="red"))
        return 1
    except Exception as e:
        import traceback
        console.print(Text(f"错误: {str(e)}", style="red"))
        console.print(traceback.format_exc())
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="ONNX模型信息查看器 - 漂亮输出版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s model.onnx              # 查看所有信息
  %(prog)s model.onnx --no-ops     # 不显示算子信息
  %(prog)s model.onnx -w           # 显示权重信息
        """
    )

    parser.add_argument(
        "model",
        help="ONNX模型文件路径 (.onnx)"
    )

    parser.add_argument(
        "--no-ops",
        action="store_true",
        help="不显示算子信息"
    )

    parser.add_argument(
        "-w", "--weights",
        action="store_true",
        help="显示权重/初始值信息"
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s v2.0.0"
    )

    args = parser.parse_args()

    return show_model_info(args.model, show_operators=not args.no_ops, show_weights=args.weights)


if __name__ == "__main__":
    sys.exit(main())
